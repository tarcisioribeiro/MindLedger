"""
Embedding Service

Centralized service for generating and managing embeddings.
This service supports two modes:
1. HTTP mode (default): Uses external embeddings microservice via HTTP
2. Local mode: Uses sentence-transformers directly (fallback/development)

The mode is determined by the EMBEDDING_SERVICE_URL setting:
- If set: Uses HTTP client to call external service
- If not set or 'local': Falls back to local sentence-transformers

Benefits of HTTP mode:
- Faster builds (no model download in main container)
- Reusable service across projects
- Independent scaling of embedding workloads
"""

import logging
import os
from typing import List, Optional, Union, Protocol
from dataclasses import dataclass

from django.conf import settings

from .exceptions import EmbeddingError, EmbeddingGenerationError

logger = logging.getLogger(__name__)


# =============================================================================
# Protocol for Embedding Clients
# =============================================================================

class EmbeddingClientProtocol(Protocol):
    """Protocol defining the interface for embedding clients."""
    model_name: str
    dimensions: int

    def is_available(self) -> bool: ...
    def health_check(self) -> bool: ...
    def generate_embedding(self, text: str): ...
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32): ...


# =============================================================================
# Client Factory
# =============================================================================

def _get_embedding_client() -> EmbeddingClientProtocol:
    """
    Factory function to get the appropriate embedding client.

    Returns HTTP client if EMBEDDING_SERVICE_URL is configured,
    otherwise falls back to local sentence-transformers.

    Returns:
        Configured embedding client (HTTP or local)
    """
    embedding_url = getattr(settings, 'EMBEDDING_SERVICE_URL', None)

    # Check if we should use HTTP client
    if embedding_url and embedding_url.lower() != 'local':
        logger.info(f"Using HTTP embedding client: {embedding_url}")
        from .http_client import get_http_embedding_client
        return get_http_embedding_client(embedding_url)

    # Fallback to local sentence-transformers
    logger.info("Using local sentence-transformers client")
    try:
        from .sentence_transformer_client import get_sentence_transformer_client
        return get_sentence_transformer_client()
    except ImportError:
        raise ImportError(
            "sentence-transformers not installed and EMBEDDING_SERVICE_URL not configured. "
            "Either install sentence-transformers or set EMBEDDING_SERVICE_URL in settings."
        )


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    text: str
    embedding: List[float]
    model: str
    dimensions: int

    def to_list(self) -> List[float]:
        """Return embedding as a list."""
        return self.embedding


class EmbeddingService:
    """
    Service for generating embeddings.

    This service provides a high-level interface for embedding generation,
    with support for single and batch operations. Supports two modes:

    1. HTTP mode (default): Uses external microservice via HTTP
       - Faster builds (no model in main container)
       - Reusable across projects
       - Configure via EMBEDDING_SERVICE_URL setting

    2. Local mode: Uses sentence-transformers directly
       - Set EMBEDDING_SERVICE_URL='local' or leave unset
       - Requires sentence-transformers installed

    Both modes use the all-MiniLM-L6-v2 model which:
    - Produces 384-dimensional embeddings
    - Is fast (5x faster than larger models)
    - Supports multilingual text (including Portuguese)
    - Uses L2 normalization for cosine similarity

    Attributes
    ----------
    model : str
        The embedding model to use (default: all-MiniLM-L6-v2)
    dimensions : int
        Expected embedding dimensions (384 for all-MiniLM-L6-v2)
    batch_size : int
        Maximum batch size for batch operations
    """

    def __init__(
        self,
        client: Optional[EmbeddingClientProtocol] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        batch_size: Optional[int] = None
    ):
        self.client = client or _get_embedding_client()

        embedding_config = getattr(settings, 'EMBEDDING_CONFIG', {})
        ai_config = getattr(settings, 'AI_ASSISTANT_CONFIG', {})

        self._model = model or embedding_config.get('MODEL', 'all-MiniLM-L6-v2')
        self._dimensions = dimensions or embedding_config.get('DIMENSIONS', 384)
        self.batch_size = batch_size or ai_config.get('EMBEDDING_BATCH_SIZE', 32)
        self._model_verified = False

    def _ensure_model(self) -> None:
        """Verify model is available (cached after first check)."""
        if not self._model_verified:
            if not self.client.is_available():
                embedding_url = getattr(settings, 'EMBEDDING_SERVICE_URL', None)
                if embedding_url and embedding_url.lower() != 'local':
                    raise ValueError(
                        f"Embedding service not available at {embedding_url}. "
                        "Check if the embeddings container is running."
                    )
                else:
                    raise ValueError(
                        "sentence-transformers not available. Either:\n"
                        "1. Install with: pip install sentence-transformers\n"
                        "2. Or configure EMBEDDING_SERVICE_URL to use HTTP service"
                    )
            self._model_verified = True
            logger.info(f"Embedding service ready: {self._model} ({self._dimensions}D)")

    @property
    def model(self) -> str:
        """Get active model name."""
        return self._model

    @property
    def dimensions(self) -> int:
        """Get active embedding dimensions."""
        return self._dimensions

    def is_available(self) -> bool:
        """
        Check if the embedding service is available.

        Works with both HTTP and local clients.

        Returns
        -------
        bool
            True if embedding service is available and ready
        """
        try:
            return self.client.is_available()
        except Exception:
            return False

    def generate(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.

        Parameters
        ----------
        text : str
            Text to generate embedding for

        Returns
        -------
        EmbeddingResult
            Embedding result with vector and metadata

        Raises
        ------
        EmbeddingError
            If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingGenerationError("", Exception("Empty text provided"))

        self._ensure_model()

        try:
            response = self.client.generate_embedding(text)
            return EmbeddingResult(
                text=text,
                embedding=response.embedding,
                model=response.model,
                dimensions=response.dimensions
            )
        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingGenerationError(text, e)

    def generate_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.

        Handles batching automatically based on batch_size configuration.

        Parameters
        ----------
        texts : List[str]
            List of texts to generate embeddings for

        Returns
        -------
        List[EmbeddingResult]
            List of embedding results in same order as input

        Raises
        ------
        EmbeddingError
            If any embedding generation fails
        """
        if not texts:
            return []

        # Filter empty texts but keep track of indices
        indexed_texts = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
        if not indexed_texts:
            raise EmbeddingGenerationError("", Exception("All texts are empty"))

        self._ensure_model()

        results: List[Optional[EmbeddingResult]] = [None] * len(texts)

        # Process in batches
        for batch_start in range(0, len(indexed_texts), self.batch_size):
            batch = indexed_texts[batch_start:batch_start + self.batch_size]
            batch_texts = [t for _, t in batch]

            try:
                responses = self.client.generate_embeddings_batch(batch_texts, self.batch_size)
                for (original_idx, text), response in zip(batch, responses):
                    results[original_idx] = EmbeddingResult(
                        text=text,
                        embedding=response.embedding,
                        model=response.model,
                        dimensions=response.dimensions
                    )

            except EmbeddingError:
                raise
            except Exception as e:
                logger.error(f"Batch embedding generation failed: {e}")
                raise EmbeddingGenerationError(str(batch_texts[:2]), e)

        # Return only non-None results (maintaining order)
        return [r for r in results if r is not None]

    def get_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        This is a convenience method that returns just the embedding vector,
        suitable for similarity search operations.

        Parameters
        ----------
        query : str
            Search query text

        Returns
        -------
        List[float]
            Embedding vector
        """
        result = self.generate(query)
        return result.embedding

    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate an embedding vector.

        Parameters
        ----------
        embedding : List[float]
            Embedding vector to validate

        Returns
        -------
        bool
            True if embedding is valid
        """
        if not embedding:
            return False
        if len(embedding) != self.dimensions:
            return False
        return True

    def health_check(self) -> bool:
        """
        Perform health check on embedding service.

        Returns
        -------
        bool
            True if service is healthy and ready
        """
        return self.is_available()


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get the singleton EmbeddingService instance.

    Returns
    -------
    EmbeddingService
        Configured embedding service
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
