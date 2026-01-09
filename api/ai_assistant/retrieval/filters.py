"""
Filter Builder

Constructs database filters for retrieval queries.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from django.db.models import Q

from ..models import ContentEmbedding, TipoConteudo, Sensibilidade


class FilterBuilder:
    """
    Builds Django ORM filters for ContentEmbedding queries.

    Supports filtering by:
    - Content type (tipo)
    - Sensitivity level (sensibilidade)
    - Tags
    - Date range
    - Entity types
    """

    @staticmethod
    def build(
        owner_id: int,
        tipos: Optional[List[str]] = None,
        sensibilidades: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        only_indexed: bool = True
    ) -> Q:
        """
        Build a Q object for filtering ContentEmbedding queries.

        Parameters
        ----------
        owner_id : int
            Owner's ID (required)
        tipos : List[str], optional
            Content types to include (planejamento, seguranca, etc.)
        sensibilidades : List[str], optional
            Sensitivity levels to include
        tags : List[str], optional
            Tags to match (any match)
        content_types : List[str], optional
            Entity types to include (expense, book, etc.)
        data_inicio : date, optional
            Start date for data_referencia
        data_fim : date, optional
            End date for data_referencia
        only_indexed : bool
            If True, only return indexed content

        Returns
        -------
        Q
            Combined filter expression
        """
        filters = Q(owner_id=owner_id, is_deleted=False)

        if only_indexed:
            filters &= Q(is_indexed=True, embedding__isnull=False)

        if tipos:
            valid_tipos = [t for t in tipos if t in TipoConteudo.values]
            if valid_tipos:
                filters &= Q(tipo__in=valid_tipos)

        if sensibilidades:
            valid_sens = [s for s in sensibilidades if s in Sensibilidade.values]
            if valid_sens:
                filters &= Q(sensibilidade__in=valid_sens)

        if tags:
            # Match any of the provided tags
            tag_filter = Q()
            for tag in tags:
                tag_filter |= Q(tags__contains=[tag])
            filters &= tag_filter

        if content_types:
            filters &= Q(content_type__in=content_types)

        if data_inicio:
            filters &= Q(data_referencia__gte=data_inicio)

        if data_fim:
            filters &= Q(data_referencia__lte=data_fim)

        return filters

    @staticmethod
    def exclude_high_sensitivity() -> Q:
        """
        Return a filter that excludes high sensitivity content.

        Use this when routing to external LLMs.

        Returns
        -------
        Q
            Filter to exclude high sensitivity
        """
        return ~Q(sensibilidade=Sensibilidade.ALTA)

    @staticmethod
    def security_only() -> Q:
        """
        Return a filter for security module content only.

        Returns
        -------
        Q
            Filter for security content
        """
        return Q(tipo=TipoConteudo.SEGURANCA)

    @staticmethod
    def finance_only() -> Q:
        """
        Return a filter for finance module content only.

        Returns
        -------
        Q
            Filter for finance content
        """
        return Q(tipo=TipoConteudo.FINANCEIRO)

    @staticmethod
    def library_only() -> Q:
        """
        Return a filter for library module content only.

        Returns
        -------
        Q
            Filter for library content
        """
        return Q(tipo=TipoConteudo.LEITURA)

    @staticmethod
    def planning_only() -> Q:
        """
        Return a filter for personal planning module content only.

        Returns
        -------
        Q
            Filter for planning content
        """
        return Q(tipo=TipoConteudo.PLANEJAMENTO)
