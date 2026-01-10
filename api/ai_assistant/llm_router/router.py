"""
LLM Router

Simplified router using only Groq for all LLM operations.
All data is processed using Groq's fast cloud inference.
"""

import logging
from typing import List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from django.conf import settings

from ..retrieval.service import RetrievalResult
from .sensitivity import SensitivityClassifier, SensitivityAnalysis, QueryComplexity
from .providers.base import BaseLLMProvider, GenerationResult
from .providers.groq import GroqProvider
from .prompts import get_system_prompt, build_context_prompt

logger = logging.getLogger(__name__)


class RoutingDecision(Enum):
    """Routing decision for LLM selection."""
    CLOUD = 'cloud'    # Use Groq for all operations


@dataclass
class RoutingContext:
    """Context for routing decision."""
    max_sensitivity: str
    has_security_content: bool
    query_complexity: str
    decision: RoutingDecision
    reason: str
    provider_name: str


class LLMRouter:
    """
    Simplified LLM router using only Groq.

    All queries are processed using Groq's fast cloud inference.
    Embeddings are generated locally using sentence-transformers,
    so sensitive data is only sent to Groq for final text generation.

    Attributes
    ----------
    groq_provider : GroqProvider
        Groq LLM provider for all text generation
    classifier : SensitivityClassifier
        Sensitivity analysis (for logging/monitoring)
    """

    def __init__(
        self,
        groq_provider: Optional[GroqProvider] = None,
        classifier: Optional[SensitivityClassifier] = None
    ):
        self.groq = groq_provider or GroqProvider()
        self.classifier = classifier or SensitivityClassifier()

    def route(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> Tuple[RoutingDecision, BaseLLMProvider, RoutingContext]:
        """
        Route request to Groq (always uses Groq now).

        Parameters
        ----------
        query : str
            User's query
        results : List[RetrievalResult]
            Retrieved context results

        Returns
        -------
        Tuple[RoutingDecision, BaseLLMProvider, RoutingContext]
            (decision, provider, context)
        """
        # Analyze sensitivity (for logging/monitoring only)
        analysis = self.classifier.analyze(query, results)

        # Always use Groq
        decision = RoutingDecision.CLOUD
        provider = self.groq

        # Check if Groq is available
        if not provider.is_available():
            logger.error("Groq nao esta disponivel")
            raise RuntimeError(
                "Groq nao esta disponivel. Verifique:\n"
                "1. GROQ_API_KEY esta configurada no .env\n"
                "2. A chave API e valida\n"
                "3. Acesso a internet esta funcionando"
            )

        context = RoutingContext(
            max_sensitivity=analysis.max_sensitivity,
            has_security_content=analysis.has_security_content,
            query_complexity=analysis.query_complexity.value,
            decision=decision,
            reason="Usando Groq para inferencia rapida",
            provider_name=provider.name
        )

        logger.info(
            f"Routing decision: {decision.value} ({provider.name}) - "
            f"sensitivity={analysis.max_sensitivity}, security={analysis.has_security_content}"
        )

        return (decision, provider, context)

    def generate(
        self,
        query: str,
        context_text: str,
        results: List[RetrievalResult],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        conversation_history: Optional[List[dict]] = None
    ) -> Tuple[GenerationResult, RoutingContext]:
        """
        Route and generate response.

        Parameters
        ----------
        query : str
            User's query
        context_text : str
            Formatted context from retrieval
        results : List[RetrievalResult]
            Original retrieval results (for routing)
        temperature : float
            Sampling temperature
        max_tokens : int
            Maximum tokens
        conversation_history : List[dict], optional
            Previous messages [{'role': 'user'/'assistant', 'content': '...'}]

        Returns
        -------
        Tuple[GenerationResult, RoutingContext]
            (generation_result, routing_context)
        """
        # Route to appropriate provider
        decision, provider, routing_ctx = self.route(query, results)

        # Determine query type for prompt selection
        query_type = 'default'
        if routing_ctx.query_complexity == 'greeting':
            query_type = 'greeting'
        elif routing_ctx.query_complexity == 'simple':
            query_type = 'simple'
        elif routing_ctx.query_complexity == 'complex':
            query_type = 'analytical'

        # Check if context is limited (few results or low relevance)
        if len(results) <= 2 and query_type not in ['greeting']:
            # Use limited context prompt for better handling
            query_type = 'limited'

        # Get prompts (with conversation history support)
        system_prompt = get_system_prompt(query_type, with_conversation=bool(conversation_history))
        user_prompt = build_context_prompt(query, context_text, conversation_history)

        # Generate
        result = provider.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return (result, routing_ctx)

    def get_provider_status(self) -> dict:
        """
        Get status of Groq provider.

        Returns
        -------
        dict
            Provider status information
        """
        return {
            'groq': {
                'available': self.groq.is_available(),
                'model': self.groq.model,
                'is_local': False
            },
            'note': 'Using Groq for all LLM operations (embeddings are local via sentence-transformers)'
        }


# Singleton instance
_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """
    Get the singleton LLMRouter instance.

    Returns
    -------
    LLMRouter
        Configured router
    """
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
