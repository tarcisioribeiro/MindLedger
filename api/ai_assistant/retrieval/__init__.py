"""
Retrieval Module

This module provides the RAG retrieval layer using pgvector for
semantic similarity search.

Main components:
- RetrievalService: Main search interface
- FilterBuilder: Query filter construction
- Extractors: Legacy content extraction (for migration)
"""

from .service import RetrievalService, RetrievalFilter, RetrievalResult, get_retrieval_service
from .filters import FilterBuilder

__all__ = [
    'RetrievalService',
    'RetrievalFilter',
    'RetrievalResult',
    'get_retrieval_service',
    'FilterBuilder',
]
