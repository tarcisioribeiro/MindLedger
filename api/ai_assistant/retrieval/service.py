"""
Retrieval Service

RAG retrieval layer using pgvector for semantic similarity search.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import date

from django.conf import settings
from django.db.models import QuerySet
from pgvector.django import CosineDistance

from ..models import ContentEmbedding, TipoConteudo, Sensibilidade
from ..embeddings.service import EmbeddingService, get_embedding_service
from .filters import FilterBuilder

logger = logging.getLogger(__name__)


@dataclass
class RetrievalFilter:
    """
    Filter configuration for retrieval queries.

    Attributes
    ----------
    tipos : List[str], optional
        Content types to include (planejamento, seguranca, etc.)
    sensibilidades : List[str], optional
        Sensitivity levels to include
    tags : List[str], optional
        Tags to match
    content_types : List[str], optional
        Entity types to include (expense, book, etc.)
    data_inicio : date, optional
        Start date filter
    data_fim : date, optional
        End date filter
    """
    tipos: Optional[List[str]] = None
    sensibilidades: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for cache key generation."""
        return {
            'tipos': self.tipos,
            'sensibilidades': self.sensibilidades,
            'tags': self.tags,
            'content_types': self.content_types,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
        }


@dataclass
class RetrievalResult:
    """
    A single retrieval result.

    Attributes
    ----------
    content_embedding : ContentEmbedding
        The matched embedding record
    score : float
        Similarity score (0-1, higher is better)
    distance : float
        Cosine distance (0-2, lower is better)
    """
    content_embedding: ContentEmbedding
    score: float
    distance: float

    @property
    def content_type(self) -> str:
        return self.content_embedding.content_type

    @property
    def content_id(self) -> int:
        return self.content_embedding.content_id

    @property
    def tipo(self) -> str:
        return self.content_embedding.tipo

    @property
    def sensibilidade(self) -> str:
        return self.content_embedding.sensibilidade

    @property
    def texto_original(self) -> str:
        return self.content_embedding.texto_original

    @property
    def metadata(self) -> Dict[str, Any]:
        return self.content_embedding.metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'content_type': self.content_type,
            'content_id': self.content_id,
            'tipo': self.tipo,
            'sensibilidade': self.sensibilidade,
            'score': round(self.score, 4),
            'texto_original': self.texto_original,
            'metadata': self.metadata,
            'tags': self.content_embedding.tags,
            'data_referencia': (
                self.content_embedding.data_referencia.isoformat()
                if self.content_embedding.data_referencia else None
            ),
        }


class RetrievalService:
    """
    RAG retrieval service using pgvector.

    Performs semantic similarity search on indexed content with
    support for filtering and pagination.

    Attributes
    ----------
    embedding_service : EmbeddingService
        Service for generating query embeddings
    default_top_k : int
        Default number of results to return
    max_top_k : int
        Maximum allowed top_k value
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        default_top_k: Optional[int] = None,
        max_top_k: int = 50
    ):
        self.embedding_service = embedding_service or get_embedding_service()
        self.filter_builder = FilterBuilder()

        ai_config = getattr(settings, 'AI_ASSISTANT_CONFIG', {})
        self.default_top_k = default_top_k or ai_config.get('DEFAULT_TOP_K', 10)
        self.max_top_k = max_top_k

    def search(
        self,
        query: str,
        owner_id: int,
        filters: Optional[RetrievalFilter] = None,
        top_k: Optional[int] = None,
        query_embedding: Optional[List[float]] = None
    ) -> List[RetrievalResult]:
        """
        Perform semantic search on indexed content.

        Parameters
        ----------
        query : str
            Search query
        owner_id : int
            Owner's ID
        filters : RetrievalFilter, optional
            Filters to apply
        top_k : int, optional
            Number of results to return
        query_embedding : List[float], optional
            Pre-computed query embedding (to avoid regeneration)

        Returns
        -------
        List[RetrievalResult]
            Ranked list of matching results
        """
        top_k = min(top_k or self.default_top_k, self.max_top_k)

        # Generate query embedding if not provided
        if query_embedding is None:
            query_embedding = self.embedding_service.get_query_embedding(query)

        # Build filters
        filter_q = self.filter_builder.build(
            owner_id=owner_id,
            tipos=filters.tipos if filters else None,
            sensibilidades=filters.sensibilidades if filters else None,
            tags=filters.tags if filters else None,
            content_types=filters.content_types if filters else None,
            data_inicio=filters.data_inicio if filters else None,
            data_fim=filters.data_fim if filters else None,
            only_indexed=True
        )

        # Query with pgvector similarity
        queryset = (
            ContentEmbedding.objects
            .filter(filter_q)
            .annotate(distance=CosineDistance('embedding', query_embedding))
            .order_by('distance')[:top_k]
        )

        results = []
        for embedding in queryset:
            # Convert cosine distance to similarity score
            # Cosine distance is 1 - cosine_similarity, so score = 1 - distance
            score = 1 - embedding.distance

            results.append(RetrievalResult(
                content_embedding=embedding,
                score=score,
                distance=embedding.distance
            ))

        logger.debug(f"Retrieved {len(results)} results for query: {query[:50]}...")
        return results

    def search_by_tipo(
        self,
        query: str,
        owner_id: int,
        tipo: str,
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        Search within a specific content type.

        Parameters
        ----------
        query : str
            Search query
        owner_id : int
            Owner's ID
        tipo : str
            Content type (planejamento, seguranca, etc.)
        top_k : int, optional
            Number of results

        Returns
        -------
        List[RetrievalResult]
            Matching results
        """
        filters = RetrievalFilter(tipos=[tipo])
        return self.search(query, owner_id, filters, top_k)

    def search_excluding_sensitive(
        self,
        query: str,
        owner_id: int,
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        Search excluding high-sensitivity content.

        Use this when sending context to external LLMs.

        Parameters
        ----------
        query : str
            Search query
        owner_id : int
            Owner's ID
        top_k : int, optional
            Number of results

        Returns
        -------
        List[RetrievalResult]
            Matching results (no high sensitivity)
        """
        filters = RetrievalFilter(sensibilidades=['baixa', 'media'])
        return self.search(query, owner_id, filters, top_k)

    def get_max_sensitivity(self, results: List[RetrievalResult]) -> str:
        """
        Get the maximum sensitivity level from results.

        Parameters
        ----------
        results : List[RetrievalResult]
            Search results

        Returns
        -------
        str
            Maximum sensitivity level ('baixa', 'media', or 'alta')
        """
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

    def has_security_content(self, results: List[RetrievalResult]) -> bool:
        """
        Check if any results are from the security module.

        Parameters
        ----------
        results : List[RetrievalResult]
            Search results

        Returns
        -------
        bool
            True if any result is from security module
        """
        return any(r.tipo == TipoConteudo.SEGURANCA for r in results)

    def get_content_summary(self, results: List[RetrievalResult]) -> Dict[str, Any]:
        """
        Get a summary of the retrieved content.

        Parameters
        ----------
        results : List[RetrievalResult]
            Search results

        Returns
        -------
        dict
            Summary with counts by tipo and sensibilidade
        """
        tipo_counts = {}
        sens_counts = {}

        for result in results:
            tipo_counts[result.tipo] = tipo_counts.get(result.tipo, 0) + 1
            sens_counts[result.sensibilidade] = sens_counts.get(result.sensibilidade, 0) + 1

        return {
            'total': len(results),
            'by_tipo': tipo_counts,
            'by_sensibilidade': sens_counts,
            'max_sensitivity': self.get_max_sensitivity(results),
            'has_security': self.has_security_content(results)
        }


# Singleton instance
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """
    Get the singleton RetrievalService instance.

    Returns
    -------
    RetrievalService
        Configured retrieval service
    """
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
