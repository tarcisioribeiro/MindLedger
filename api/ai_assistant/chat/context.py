"""
Context Builder

Builds formatted context from retrieval results for LLM consumption.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

from django.conf import settings

from ..retrieval.service import RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class BuiltContext:
    """
    Built context ready for LLM.

    Attributes
    ----------
    text : str
        Formatted context text
    token_count : int
        Estimated token count
    result_count : int
        Number of results included
    truncated : bool
        Whether context was truncated
    """
    text: str
    token_count: int
    result_count: int
    truncated: bool


class ContextBuilder:
    """
    Builds formatted context from retrieval results.

    This class takes retrieval results and formats them into
    a context string suitable for LLM consumption, respecting
    token limits.

    Attributes
    ----------
    max_tokens : int
        Maximum tokens for context
    chars_per_token : float
        Estimated characters per token
    """

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        chars_per_token: float = 4.0
    ):
        ai_config = getattr(settings, 'AI_ASSISTANT_CONFIG', {})
        self.max_tokens = max_tokens or ai_config.get('MAX_CONTEXT_TOKENS', 4000)
        self.chars_per_token = chars_per_token
        self.max_chars = int(self.max_tokens * chars_per_token)

    def build(
        self,
        results: List[RetrievalResult],
        include_metadata: bool = True,
        include_scores: bool = False
    ) -> BuiltContext:
        """
        Build context from retrieval results.

        Parameters
        ----------
        results : List[RetrievalResult]
            Retrieval results
        include_metadata : bool
            Include metadata in context
        include_scores : bool
            Include similarity scores

        Returns
        -------
        BuiltContext
            Built context with metadata
        """
        if not results:
            return BuiltContext(
                text="Nenhuma informacao relevante encontrada.",
                token_count=5,
                result_count=0,
                truncated=False
            )

        context_parts = []
        total_chars = 0
        truncated = False
        included_count = 0

        for i, result in enumerate(results, 1):
            # Build entry
            entry = self._format_result(result, i, include_metadata, include_scores)
            entry_chars = len(entry)

            # Check if we can include this entry
            if total_chars + entry_chars > self.max_chars:
                truncated = True
                # Try to include a partial entry
                remaining = self.max_chars - total_chars
                if remaining > 100:  # Minimum meaningful chunk
                    entry = entry[:remaining] + "..."
                    context_parts.append(entry)
                    included_count += 1
                break

            context_parts.append(entry)
            total_chars += entry_chars
            included_count += 1

        context_text = "\n\n".join(context_parts)
        token_count = int(len(context_text) / self.chars_per_token)

        return BuiltContext(
            text=context_text,
            token_count=token_count,
            result_count=included_count,
            truncated=truncated
        )

    def _format_result(
        self,
        result: RetrievalResult,
        index: int,
        include_metadata: bool,
        include_scores: bool
    ) -> str:
        """
        Format a single retrieval result.

        Parameters
        ----------
        result : RetrievalResult
            The result to format
        index : int
            Result index
        include_metadata : bool
            Include metadata
        include_scores : bool
            Include scores

        Returns
        -------
        str
            Formatted result string
        """
        parts = []

        # Header with type info
        tipo_map = {
            'planejamento': 'Planejamento',
            'seguranca': 'Seguranca',
            'financeiro': 'Financeiro',
            'leitura': 'Biblioteca'
        }
        tipo_label = tipo_map.get(result.tipo, result.tipo.title())

        header = f"[{index}. {tipo_label.upper()} - {result.content_type}]"
        if include_scores:
            header += f" (relevancia: {result.score:.2%})"

        parts.append(header)

        # Main content
        parts.append(result.texto_original)

        # Metadata
        if include_metadata and result.metadata:
            metadata_parts = []
            for key, value in result.metadata.items():
                if value is not None and key not in ['id', 'uuid']:
                    if isinstance(value, float):
                        metadata_parts.append(f"{key}: R$ {value:.2f}" if 'value' in key.lower() else f"{key}: {value:.2f}")
                    else:
                        metadata_parts.append(f"{key}: {value}")

            if metadata_parts:
                parts.append(f"  ({', '.join(metadata_parts)})")

        # Date reference
        if result.content_embedding.data_referencia:
            date_str = result.content_embedding.data_referencia.strftime('%d/%m/%Y')
            parts.append(f"  Data: {date_str}")

        return "\n".join(parts)

    def build_summary(self, results: List[RetrievalResult]) -> str:
        """
        Build a brief summary of results.

        Parameters
        ----------
        results : List[RetrievalResult]
            Retrieval results

        Returns
        -------
        str
            Summary text
        """
        if not results:
            return "Nenhum resultado encontrado."

        tipo_counts = {}
        for r in results:
            tipo_counts[r.tipo] = tipo_counts.get(r.tipo, 0) + 1

        parts = [f"{count} resultado(s) de {tipo}" for tipo, count in tipo_counts.items()]
        return f"Encontrados: {', '.join(parts)}"


# Singleton instance
_context_builder: Optional[ContextBuilder] = None


def get_context_builder() -> ContextBuilder:
    """Get singleton ContextBuilder instance."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder
