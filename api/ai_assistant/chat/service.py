"""
Chat Service

Main orchestrator for the RAG pipeline with SQL query support.
LLM-agnostic chat service that combines retrieval, routing, generation,
and direct database queries based on user intent.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from django.conf import settings

from ..retrieval.service import RetrievalService, RetrievalFilter, RetrievalResult, get_retrieval_service
from ..llm_router.router import LLMRouter, RoutingContext, get_llm_router
from ..cache.service import CacheService, get_cache_service
from ..embeddings.service import EmbeddingService, get_embedding_service
from ..intent_classifier import IntentClassifier, IntentResult, ExecutionMode, get_intent_classifier
from ..query_engine.generator import SQLGenerator, SQLGenerationError, get_sql_generator
from ..query_engine.validator import SQLValidator, SQLValidationError
from ..query_engine.executor import QueryExecutor, QueryExecutionError, get_query_executor
from ..query_engine.formatter import QueryResultFormatter, get_query_result_formatter
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
    sql_query : str, optional
        SQL query executed (if SQL mode)
    sql_explanation : str, optional
        Explanation of the SQL query
    data_rows : List[Dict], optional
        Raw data from SQL query
    execution_mode : str
        Execution mode used (sql/rag/hybrid)
    visualization : Dict, optional
        Visualization configuration
    """
    answer: str
    sources: List[Dict[str, Any]]
    routing_decision: str
    provider: str
    cached: bool = False
    cache_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # SQL-specific fields
    sql_query: Optional[str] = None
    sql_explanation: Optional[str] = None
    data_rows: Optional[List[Dict[str, Any]]] = None
    execution_mode: str = 'rag'
    visualization: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'answer': self.answer,
            'sources': self.sources,
            'routing_decision': self.routing_decision,
            'provider': self.provider,
            'cached': self.cached,
            'cache_type': self.cache_type,
            'metadata': self.metadata,
            'execution_mode': self.execution_mode,
        }
        # Include SQL fields if present
        if self.sql_query:
            result['sql_query'] = self.sql_query
        if self.sql_explanation:
            result['sql_explanation'] = self.sql_explanation
        if self.data_rows is not None:
            result['data_rows'] = self.data_rows
        if self.visualization:
            result['visualization'] = self.visualization
        return result


class ChatService:
    """
    Main chat service orchestrating the RAG pipeline with SQL support.

    This service:
    1. Classifies intent to determine execution mode (SQL/RAG/Hybrid)
    2. For SQL mode: generates, validates, executes SQL and formats results
    3. For RAG mode: uses semantic search and LLM generation
    4. Caches results for future queries

    The service supports both RAG-based semantic search and direct
    database queries for precise data retrieval.

    Attributes
    ----------
    retrieval_service : RetrievalService
        For semantic search (RAG mode)
    llm_router : LLMRouter
        For LLM selection
    cache_service : CacheService
        For caching
    embedding_service : EmbeddingService
        For query embeddings
    context_builder : ContextBuilder
        For context formatting
    intent_classifier : IntentClassifier
        For intent and execution mode detection
    sql_generator : SQLGenerator
        For SQL generation (SQL mode)
    sql_validator : SQLValidator
        For SQL validation (SQL mode)
    query_executor : QueryExecutor
        For SQL execution (SQL mode)
    result_formatter : QueryResultFormatter
        For formatting SQL results (SQL mode)
    """

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_router: Optional[LLMRouter] = None,
        cache_service: Optional[CacheService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        context_builder: Optional[ContextBuilder] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        sql_generator: Optional[SQLGenerator] = None,
        query_executor: Optional[QueryExecutor] = None,
        result_formatter: Optional[QueryResultFormatter] = None
    ):
        # RAG services
        self.retrieval = retrieval_service or get_retrieval_service()
        self.router = llm_router or get_llm_router()
        self.cache = cache_service or get_cache_service()
        self.embedding_service = embedding_service or get_embedding_service()
        self.context_builder = context_builder or get_context_builder()
        # SQL services
        self.intent_classifier = intent_classifier or get_intent_classifier()
        self.sql_generator = sql_generator or get_sql_generator()
        self.sql_validator = SQLValidator()
        self.query_executor = query_executor or get_query_executor()
        self.result_formatter = result_formatter or get_query_result_formatter()

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
        Process a user query through SQL or RAG pipeline based on intent.

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

        # Step 1: Classify intent to determine execution mode
        intent_result = self.intent_classifier.classify(question, conversation_history)
        logger.info(
            f"Intent classified: module={intent_result.module}, "
            f"intent_type={intent_result.intent_type}, "
            f"execution_mode={intent_result.execution_mode.value}"
        )

        # Step 2: Route based on execution mode
        if intent_result.should_use_sql:
            try:
                return self._handle_sql_query(
                    question=question,
                    owner_id=owner_id,
                    intent_result=intent_result,
                    use_cache=use_cache,
                    conversation_history=conversation_history
                )
            except (SQLGenerationError, SQLValidationError, QueryExecutionError) as e:
                logger.warning(f"SQL execution failed, falling back to RAG: {e}")
                # Fall back to RAG on SQL failure

        # Step 3: Use RAG pipeline
        return self._handle_rag_query(
            question=question,
            owner_id=owner_id,
            filters=filters,
            top_k=top_k,
            use_cache=use_cache,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history
        )

    def _handle_sql_query(
        self,
        question: str,
        owner_id: int,
        intent_result: IntentResult,
        use_cache: bool = True,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ChatResponse:
        """
        Handle query using SQL execution.

        Parameters
        ----------
        question : str
            User's question
        owner_id : int
            Owner's ID for data access
        intent_result : IntentResult
            Classified intent
        use_cache : bool
            Whether to use caching
        conversation_history : List[Dict[str, str]], optional
            Previous messages

        Returns
        -------
        ChatResponse
            Response with SQL results and formatted answer
        """
        logger.info(f"Handling SQL query for: {question[:50]}...")

        # Step 1: Generate SQL
        generation_result = self.sql_generator.generate(
            question=question,
            owner_id=owner_id
        )
        logger.info(f"Generated SQL: {generation_result.sql[:100]}...")

        # Step 2: Validate and sanitize SQL
        validation_result = self.sql_validator.validate(
            sql=generation_result.sql,
            owner_id=owner_id,
            inject_owner_filter=True,
            inject_limit=True
        )

        if validation_result.warnings:
            logger.warning(f"SQL validation warnings: {validation_result.warnings}")

        # Step 3: Execute SQL
        query_result = self.query_executor.execute(validation_result.sanitized_sql)
        logger.info(
            f"SQL executed: {query_result.row_count} rows in "
            f"{query_result.execution_time_ms:.2f}ms"
        )

        # Step 4: Format results
        formatted = self.result_formatter.format(
            query_result=query_result,
            generation_result=generation_result,
            question=question,
            generate_summary=True
        )

        # Step 5: Build response
        response = ChatResponse(
            answer=formatted.summary,
            sources=[],  # SQL queries don't have RAG sources
            routing_decision='sql',
            provider='groq',
            cached=False,
            sql_query=formatted.sql_query,
            sql_explanation=formatted.sql_explanation,
            data_rows=formatted.data,
            execution_mode='sql',
            visualization=formatted.visualization,
            metadata={
                'row_count': formatted.row_count,
                'truncated': formatted.truncated,
                'execution_time_ms': formatted.execution_time_ms,
                'query_type': formatted.metadata.get('query_type'),
                'module': formatted.metadata.get('module'),
                'tables': formatted.metadata.get('tables', []),
                'confidence': formatted.metadata.get('confidence', 0),
                'intent': {
                    'module': intent_result.module,
                    'intent_type': intent_result.intent_type,
                    'confidence': intent_result.confidence,
                }
            }
        )

        return response

    def _handle_rag_query(
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
        Handle query using RAG pipeline.

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
            Previous messages

        Returns
        -------
        ChatResponse
            Response from RAG pipeline
        """
        logger.info(f"Handling RAG query for: {question[:50]}...")

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
            execution_mode='rag',
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
            f"RAG query processed: provider={routing_ctx.provider_name}, "
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
