"""
Embedding Service

Centralized service for generating and managing embeddings.
This service uses Ollama for local embedding generation to ensure
sensitive data never leaves the infrastructure.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

from django.conf import settings

from .ollama_client import OllamaClient, get_ollama_client, EmbeddingResponse
from .exceptions import EmbeddingError, EmbeddingGenerationError

logger = logging.getLogger(__name__)


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
    Service for generating embeddings using Ollama.

    This service provides a high-level interface for embedding generation,
    with support for single and batch operations. All embeddings are
    generated locally using Ollama to protect sensitive data.

    Attributes
    ----------
    model : str
        The embedding model to use (default: nomic-embed-text)
    dimensions : int
        Expected embedding dimensions (768 for nomic-embed-text)
    batch_size : int
        Maximum batch size for batch operations
    """

    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        batch_size: Optional[int] = None
    ):
        self.client = client or get_ollama_client()

        ollama_config = getattr(settings, 'OLLAMA_CONFIG', {})
        ai_config = getattr(settings, 'AI_ASSISTANT_CONFIG', {})

        self.model = model or ollama_config.get('EMBED_MODEL', 'nomic-embed-text')
        self.dimensions = dimensions or ollama_config.get('EMBED_DIMENSIONS', 768)
        self.batch_size = batch_size or ai_config.get('EMBEDDING_BATCH_SIZE', 32)

        self._model_verified = False

    def _ensure_model(self) -> None:
        """Verify model is available (cached after first check)."""
        if not self._model_verified:
            self.client.ensure_model(self.model)
            self._model_verified = True

    def is_available(self) -> bool:
        """
        Check if the embedding service is available.

        Returns
        -------
        bool
            True if Ollama is reachable and model is available
        """
        try:
            return self.client.health_check() and self.client.is_model_available(self.model)
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
            response = self.client.generate_embedding(text, self.model)
            return EmbeddingResult(
                text=text,
                embedding=response.embedding,
                model=response.model,
                dimensions=len(response.embedding)
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
                responses = self.client.generate_embeddings_batch(batch_texts, self.model)

                for (original_idx, text), response in zip(batch, responses):
                    results[original_idx] = EmbeddingResult(
                        text=text,
                        embedding=response.embedding,
                        model=response.model,
                        dimensions=len(response.embedding)
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
