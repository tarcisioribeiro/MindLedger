"""
Sensitivity Classifier

Analyzes query and context to determine routing decisions.
"""

import re
import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from ..models import Sensibilidade, TipoConteudo
from ..retrieval.service import RetrievalResult

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels."""
    GREETING = 'greeting'   # Greetings and casual interactions
    SIMPLE = 'simple'       # Factual, direct answer
    MODERATE = 'moderate'   # Some reasoning needed
    COMPLEX = 'complex'     # Multi-step reasoning, analysis


@dataclass
class SensitivityAnalysis:
    """Result of sensitivity analysis."""
    max_sensitivity: str
    has_security_content: bool
    query_complexity: QueryComplexity
    requires_local: bool
    reason: str


class SensitivityClassifier:
    """
    Classifies queries and content for routing decisions.

    Analyzes both the query text and retrieved results to determine
    whether local (Ollama) or cloud (Groq) processing is appropriate.
    """

    # Keywords that suggest complex reasoning
    COMPLEX_KEYWORDS = [
        'analise', 'compare', 'explique', 'por que', 'porque',
        'qual a diferenca', 'resuma', 'sintetize', 'avalie',
        'quanto gastei', 'total', 'soma', 'media', 'tendencia',
        'previsao', 'planeje', 'sugira', 'recomende'
    ]

    # Keywords that suggest simple queries
    SIMPLE_KEYWORDS = [
        'qual', 'quais', 'quando', 'onde', 'quem',
        'existe', 'tem', 'ha', 'mostre', 'liste'
    ]

    # Security-related keywords
    SECURITY_KEYWORDS = [
        'senha', 'senhas', 'password', 'credencial', 'login',
        'usuario', 'cartao', 'cvv', 'codigo', 'seguranca',
        'arquivo', 'secreto', 'privado'
    ]

    # Greeting keywords
    GREETING_KEYWORDS = [
        'oi', 'ola', 'bom dia', 'boa tarde', 'boa noite',
        'hey', 'hello', 'hi', 'e ai', 'eai', 'tudo bem',
        'como vai', 'opa', 'fala', 'salve', 'obrigado',
        'obrigada', 'valeu', 'vlw', 'brigado', 'tchau',
        'ate mais', 'ate logo', 'ajuda', 'me ajuda',
        'o que voce faz', 'o que você faz', 'quem e voce',
        'quem é você', 'pode me ajudar'
    ]

    def analyze(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> SensitivityAnalysis:
        """
        Analyze query and results for routing decision.

        Parameters
        ----------
        query : str
            User's query
        results : List[RetrievalResult]
            Retrieved context results

        Returns
        -------
        SensitivityAnalysis
            Analysis result with routing recommendation
        """
        query_lower = query.lower()

        # Check content sensitivity
        max_sensitivity = self._get_max_sensitivity(results)
        has_security = self._has_security_content(results)

        # Check query complexity
        complexity = self._classify_complexity(query_lower)

        # Check if query mentions security topics
        mentions_security = self._mentions_security(query_lower)

        # Determine if local processing is required
        requires_local, reason = self._should_use_local(
            max_sensitivity,
            has_security,
            mentions_security,
            complexity
        )

        return SensitivityAnalysis(
            max_sensitivity=max_sensitivity,
            has_security_content=has_security,
            query_complexity=complexity,
            requires_local=requires_local,
            reason=reason
        )

    def _get_max_sensitivity(self, results: List[RetrievalResult]) -> str:
        """Get maximum sensitivity level from results."""
        if not results:
            return Sensibilidade.BAIXA

        sensitivity_order = {
            Sensibilidade.BAIXA: 0,
            Sensibilidade.MEDIA: 1,
            Sensibilidade.ALTA: 2
        }

        max_level = Sensibilidade.BAIXA
        max_order = 0

        for result in results:
            level = result.sensibilidade
            order = sensitivity_order.get(level, 0)
            if order > max_order:
                max_order = order
                max_level = level

        return max_level

    def _has_security_content(self, results: List[RetrievalResult]) -> bool:
        """Check if any results are from security module."""
        return any(r.tipo == TipoConteudo.SEGURANCA for r in results)

    def _classify_complexity(self, query: str) -> QueryComplexity:
        """Classify query complexity."""
        # Check for greetings first
        if self._is_greeting(query):
            return QueryComplexity.GREETING

        # Check for complex keywords
        complex_count = sum(1 for kw in self.COMPLEX_KEYWORDS if kw in query)
        simple_count = sum(1 for kw in self.SIMPLE_KEYWORDS if kw in query)

        # Length-based heuristic
        word_count = len(query.split())

        if complex_count >= 2 or (complex_count >= 1 and word_count > 15):
            return QueryComplexity.COMPLEX
        elif simple_count >= 1 and word_count < 10:
            return QueryComplexity.SIMPLE
        else:
            return QueryComplexity.MODERATE

    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting or casual interaction."""
        query_clean = query.strip().lower()
        # Short queries that match greeting patterns
        if len(query_clean.split()) <= 5:
            return any(kw in query_clean for kw in self.GREETING_KEYWORDS)
        return False

    def _mentions_security(self, query: str) -> bool:
        """Check if query mentions security-related topics."""
        return any(kw in query for kw in self.SECURITY_KEYWORDS)

    def _should_use_local(
        self,
        max_sensitivity: str,
        has_security: bool,
        mentions_security: bool,
        complexity: QueryComplexity
    ) -> tuple[bool, str]:
        """
        Determine if local processing is required.

        Returns
        -------
        tuple[bool, str]
            (requires_local, reason)
        """
        # Rule 1: High sensitivity ALWAYS local
        if max_sensitivity == Sensibilidade.ALTA:
            return True, "Dados de alta sensibilidade detectados"

        # Rule 2: Security content ALWAYS local
        if has_security:
            return True, "Conteudo do modulo de seguranca detectado"

        # Rule 3: Query mentions security topics
        if mentions_security:
            return True, "Pergunta menciona topicos de seguranca"

        # Rule 4: Medium sensitivity with simple query -> local (fast enough)
        if max_sensitivity == Sensibilidade.MEDIA and complexity == QueryComplexity.SIMPLE:
            return True, "Sensibilidade media com query simples"

        # Rule 5: Complex query with low sensitivity -> can use cloud
        if complexity == QueryComplexity.COMPLEX and max_sensitivity == Sensibilidade.BAIXA:
            return False, "Query complexa com baixa sensibilidade"

        # Default: prefer local for privacy
        return True, "Preferencia padrao por privacidade"

    def should_allow_cloud(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> tuple[bool, str]:
        """
        Check if cloud processing is allowed.

        This is the inverse of requires_local, with explicit check.

        Parameters
        ----------
        query : str
            User's query
        results : List[RetrievalResult]
            Retrieved results

        Returns
        -------
        tuple[bool, str]
            (allowed, reason)
        """
        analysis = self.analyze(query, results)
        return (not analysis.requires_local, analysis.reason)
