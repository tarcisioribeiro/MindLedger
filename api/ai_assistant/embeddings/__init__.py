"""
Embeddings Module

This module provides embedding generation services using Ollama local inference.
All embeddings are generated locally to ensure sensitive data never leaves
the infrastructure.

Main components:
- OllamaClient: HTTP client for Ollama API
- EmbeddingService: Centralized embedding generation
- EmbeddingIndexer: Background indexing of content
"""

from .service import EmbeddingService, get_embedding_service
from .ollama_client import OllamaClient
from .exceptions import (
    EmbeddingError,
    OllamaConnectionError,
    OllamaModelNotFoundError,
    EmbeddingGenerationError
)

__all__ = [
    'EmbeddingService',
    'get_embedding_service',
    'OllamaClient',
    'EmbeddingError',
    'OllamaConnectionError',
    'OllamaModelNotFoundError',
    'EmbeddingGenerationError',
]
