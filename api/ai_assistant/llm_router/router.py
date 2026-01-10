"""
LLM Router

Routes LLM requests based on data sensitivity and query complexity.
"""

import logging
from typing import List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from django.conf import settings

from ..retrieval.service import RetrievalResult
from .sensitivity import SensitivityClassifier, SensitivityAnalysis, QueryComplexity
from .providers.base import BaseLLMProvider, GenerationResult
from .providers.ollama import OllamaProvider
from .providers.groq import GroqProvider
from .prompts import get_system_prompt, build_context_prompt

logger = logging.getLogger(__name__)


class RoutingDecision(Enum):
    """Routing decision for LLM selection."""
    LOCAL = 'local'    # Use Ollama (sensitive data or default)
    CLOUD = 'cloud'    # Use Groq (complex query, low sensitivity)


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
    Routes LLM requests based on content sensitivity.

    Routing Rules:
    1. If ANY result has sensibilidade='alta' -> LOCAL (Ollama)
    2. If query involves security module content -> LOCAL
    3. If query mentions security topics -> LOCAL
    4. If query is complex AND sensitivity is low -> CLOUD (Groq)
    5. Default: LOCAL (privacy-first)

    Attributes
    ----------
    ollama_provider : OllamaProvider
        Local LLM provider
    groq_provider : GroqProvider
        Cloud LLM provider
    classifier : SensitivityClassifier
        Sensitivity analysis
    prefer_local : bool
        If True, always use local when possible
    """

    def __init__(
        self,
        ollama_provider: Optional[OllamaProvider] = None,
        groq_provider: Optional[GroqProvider] = None,
        classifier: Optional[SensitivityClassifier] = None,
        prefer_local: bool = True
    ):
        self.ollama = ollama_provider or OllamaProvider()
        self.groq = groq_provider or GroqProvider()
        self.classifier = classifier or SensitivityClassifier()
        self.prefer_local = prefer_local

    def route(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> Tuple[RoutingDecision, BaseLLMProvider, RoutingContext]:
        """
        Determine which LLM to use based on context.

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
        # Analyze sensitivity
        analysis = self.classifier.analyze(query, results)

        # Determine routing
        if analysis.requires_local:
            decision = RoutingDecision.LOCAL
            provider = self.ollama
        elif self.prefer_local:
            decision = RoutingDecision.LOCAL
            provider = self.ollama
            analysis = SensitivityAnalysis(
                max_sensitivity=analysis.max_sensitivity,
                has_security_content=analysis.has_security_content,
                query_complexity=analysis.query_complexity,
                requires_local=True,
                reason="Preferencia por processamento local"
            )
        elif self.groq.is_available():
            decision = RoutingDecision.CLOUD
            provider = self.groq
        else:
            # Fallback to local if cloud not available
            decision = RoutingDecision.LOCAL
            provider = self.ollama
            analysis = SensitivityAnalysis(
                max_sensitivity=analysis.max_sensitivity,
                has_security_content=analysis.has_security_content,
                query_complexity=analysis.query_complexity,
                requires_local=True,
                reason="Groq indisponivel, usando Ollama"
            )

        # Check if selected provider is available
        if not provider.is_available():
            if decision == RoutingDecision.LOCAL:
                # Try fallback to cloud if not sensitive
                if not analysis.requires_local and self.groq.is_available():
                    logger.warning("Ollama nao disponivel, usando Groq como fallback")
                    decision = RoutingDecision.CLOUD
                    provider = self.groq
                    analysis = SensitivityAnalysis(
                        max_sensitivity=analysis.max_sensitivity,
                        has_security_content=analysis.has_security_content,
                        query_complexity=analysis.query_complexity,
                        requires_local=False,
                        reason="Fallback para Groq (Ollama indisponivel)"
                    )
                elif self.groq.is_available() and not analysis.has_security_content:
                    # Allow Groq for non-security content even if high sensitivity
                    logger.warning("Ollama nao disponivel, usando Groq (dados nao-seguranca)")
                    decision = RoutingDecision.CLOUD
                    provider = self.groq
                    analysis = SensitivityAnalysis(
                        max_sensitivity=analysis.max_sensitivity,
                        has_security_content=False,
                        query_complexity=analysis.query_complexity,
                        requires_local=False,
                        reason="Fallback para Groq (Ollama indisponivel)"
                    )
                else:
                    logger.error("Ollama nao disponivel e Groq nao pode ser usado")
                    raise RuntimeError(
                        "Ollama nao esta disponivel. Instale o modelo com: "
                        "docker compose exec ollama ollama pull mistral:7b"
                    )
            else:
                # Try fallback to local
                if self.ollama.is_available():
                    decision = RoutingDecision.LOCAL
                    provider = self.ollama
                    analysis = SensitivityAnalysis(
                        max_sensitivity=analysis.max_sensitivity,
                        has_security_content=analysis.has_security_content,
                        query_complexity=analysis.query_complexity,
                        requires_local=True,
                        reason="Fallback para Ollama"
                    )
                else:
                    raise RuntimeError("Nenhum provedor LLM disponivel")

        context = RoutingContext(
            max_sensitivity=analysis.max_sensitivity,
            has_security_content=analysis.has_security_content,
            query_complexity=analysis.query_complexity.value,
            decision=decision,
            reason=analysis.reason,
            provider_name=provider.name
        )

        logger.info(
            f"Routing decision: {decision.value} ({provider.name}) - {analysis.reason}"
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
        if routing_ctx.query_complexity == 'simple':
            query_type = 'simple'
        elif routing_ctx.query_complexity == 'complex':
            query_type = 'analytical'

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
        Get status of all providers.

        Returns
        -------
        dict
            Provider status information
        """
        return {
            'ollama': {
                'available': self.ollama.is_available(),
                'model': self.ollama.model,
                'is_local': True
            },
            'groq': {
                'available': self.groq.is_available(),
                'model': self.groq.model,
                'is_local': False
            },
            'prefer_local': self.prefer_local
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
