"""
Chat Service

Main orchestrator for the RAG pipeline.
LLM-agnostic chat service that combines retrieval, routing, and generation.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from django.conf import settings

from ..retrieval.service import RetrievalService, RetrievalFilter, RetrievalResult, get_retrieval_service
from ..llm_router.router import LLMRouter, RoutingContext, get_llm_router
from ..cache.service import CacheService, get_cache_service
from ..embeddings.service import EmbeddingService, get_embedding_service
from .context import ContextBuilder, get_context_builder

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    """
    Complete response from the chat service.

    Attributes
    ----------
    answer : str
        Generated answer text
    sources : List[Dict]
        Source information for attribution
    routing_decision : str
        LLM routing decision (local/cloud)
    provider : str
        LLM provider used
    cached : bool
        Whether response was from cache
    cache_type : str
        Type of cache hit (exact/semantic)
    metadata : Dict
        Additional metadata
    """
    answer: str
    sources: List[Dict[str, Any]]
    routing_decision: str
    provider: str
    cached: bool = False
    cache_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'answer': self.answer,
            'sources': self.sources,
            'routing_decision': self.routing_decision,
            'provider': self.provider,
            'cached': self.cached,
            'cache_type': self.cache_type,
            'metadata': self.metadata
        }


class ChatService:
    """
    Main chat service orchestrating the RAG pipeline.

    This service:
    1. Checks semantic cache for cached responses
    2. Retrieves relevant context using pgvector
    3. Routes to appropriate LLM based on sensitivity
    4. Generates response
    5. Caches result for future queries

    The service is completely LLM-agnostic and never directly
    accesses the database - all data comes through the retrieval layer.

    Attributes
    ----------
    retrieval_service : RetrievalService
        For semantic search
    llm_router : LLMRouter
        For LLM selection
    cache_service : CacheService
        For caching
    embedding_service : EmbeddingService
        For query embeddings
    context_builder : ContextBuilder
        For context formatting
    """

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_router: Optional[LLMRouter] = None,
        cache_service: Optional[CacheService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        context_builder: Optional[ContextBuilder] = None
    ):
        self.retrieval = retrieval_service or get_retrieval_service()
        self.router = llm_router or get_llm_router()
        self.cache = cache_service or get_cache_service()
        self.embedding_service = embedding_service or get_embedding_service()
        self.context_builder = context_builder or get_context_builder()

    def query(
        self,
        question: str,
        owner_id: int,
        filters: Optional[RetrievalFilter] = None,
        top_k: int = 10,
        use_cache: bool = True,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ChatResponse:
        """
        Process a user query through the complete RAG pipeline.

        Parameters
        ----------
        question : str
            User's question
        owner_id : int
            Owner's ID for data access
        filters : RetrievalFilter, optional
            Retrieval filters
        top_k : int
            Number of results to retrieve
        use_cache : bool
            Whether to use caching
        temperature : float
            LLM temperature
        max_tokens : int
            Maximum response tokens
        conversation_history : List[Dict[str, str]], optional
            Previous messages in format [{'role': 'user'/'assistant', 'content': '...'}]

        Returns
        -------
        ChatResponse
            Complete response with answer and metadata
        """
        logger.info(f"Processing query for owner {owner_id}: {question[:50]}...")

        # Generate query embedding (needed for both cache and retrieval)
        query_embedding = self.embedding_service.get_query_embedding(question)

        # Step 1: Check cache (skip if conversation history present)
        if use_cache and not conversation_history:
            cached = self._check_cache(question, query_embedding, owner_id, filters)
            if cached:
                logger.info("Cache hit, returning cached response")
                return cached

        # Step 2: Retrieve context
        results = self.retrieval.search(
            query=question,
            owner_id=owner_id,
            filters=filters,
            top_k=top_k,
            query_embedding=query_embedding
        )

        # Step 3: Handle empty results
        if not results:
            return self._empty_response()

        # Step 4: Build context
        built_context = self.context_builder.build(results)

        # Step 5: Route and generate (with conversation history if provided)
        generation_result, routing_ctx = self.router.generate(
            query=question,
            context_text=built_context.text,
            results=results,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history
        )

        # Step 6: Build response
        response = ChatResponse(
            answer=generation_result.text,
            sources=[r.to_dict() for r in results],
            routing_decision=routing_ctx.decision.value,
            provider=routing_ctx.provider_name,
            cached=False,
            metadata={
                'tokens_used': generation_result.tokens_used,
                'context_tokens': built_context.token_count,
                'result_count': built_context.result_count,
                'context_truncated': built_context.truncated,
                'max_sensitivity': routing_ctx.max_sensitivity,
                'has_security_content': routing_ctx.has_security_content,
                'routing_reason': routing_ctx.reason
            }
        )

        # Step 7: Cache response (only if not sensitive and no conversation history)
        if use_cache and routing_ctx.max_sensitivity != 'alta' and not conversation_history:
            self._cache_response(
                question, query_embedding, response, owner_id, filters
            )

        logger.info(
            f"Query processed: provider={routing_ctx.provider_name}, "
            f"results={len(results)}, tokens={generation_result.tokens_used}"
        )

        return response

    def _check_cache(
        self,
        question: str,
        query_embedding: List[float],
        owner_id: int,
        filters: Optional[RetrievalFilter]
    ) -> Optional[ChatResponse]:
        """Check cache for existing response."""
        try:
            filters_dict = filters.to_dict() if filters else None
            cached = self.cache.get(
                query=question,
                query_embedding=query_embedding,
                owner_id=owner_id,
                filters=filters_dict
            )

            if cached:
                return ChatResponse(
                    answer=cached.get('answer', ''),
                    sources=cached.get('sources', []),
                    routing_decision=cached.get('routing_decision', 'unknown'),
                    provider=cached.get('provider', 'cache'),
                    cached=True,
                    cache_type=cached.get('cache_type', 'unknown'),
                    metadata=cached.get('metadata', {})
                )
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        return None

    def _cache_response(
        self,
        question: str,
        query_embedding: List[float],
        response: ChatResponse,
        owner_id: int,
        filters: Optional[RetrievalFilter]
    ) -> None:
        """Cache a response."""
        try:
            filters_dict = filters.to_dict() if filters else None
            self.cache.set(
                query=question,
                query_embedding=query_embedding,
                response=response.to_dict(),
                owner_id=owner_id,
                filters=filters_dict
            )
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    def _empty_response(self) -> ChatResponse:
        """Return response when no results found."""
        return ChatResponse(
            answer="Desculpe, nao encontrei informacoes relevantes para sua pergunta no sistema.",
            sources=[],
            routing_decision='none',
            provider='none',
            cached=False,
            metadata={'no_results': True}
        )

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all services.

        Returns
        -------
        dict
            Status information
        """
        return {
            'cache': self.cache.health_check(),
            'embedding_service': self.embedding_service.health_check(),
            'llm_router': self.router.get_provider_status()
        }


# Singleton instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """
    Get the singleton ChatService instance.

    Returns
    -------
    ChatService
        Configured chat service
    """
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
