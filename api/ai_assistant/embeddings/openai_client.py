"""
OpenAI Embeddings Client

Fallback client for generating embeddings when Ollama is unavailable.
Uses OpenAI's text-embedding-3-small model.
"""

import logging
from typing import List, Optional
import os

from django.conf import settings

logger = logging.getLogger(__name__)


class OpenAIEmbeddingClient:
    """
    OpenAI embeddings client for fallback when Ollama is unavailable.

    Uses text-embedding-3-small which is:
    - Very cost effective (~$0.02 per 1M tokens)
    - Fast
    - Good quality (1536 dimensions)
    """

    def __init__(self, api_key: Optional[str] = None):
        openai_config = getattr(settings, 'OPENAI_CONFIG', {})
        self._api_key = api_key or openai_config.get('API_KEY') or os.getenv('OPENAI_API_KEY')
        self.model = openai_config.get('EMBED_MODEL', 'text-embedding-3-small')
        self.dimensions = openai_config.get('EMBED_DIMENSIONS', 1536)
        self._client = None

    def _get_client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            if not self._api_key or self._api_key == 'your_openai_key_here':
                raise ValueError(
                    "OpenAI API key not configured. "
                    "Set OPENAI_API_KEY in environment or .env file. "
                    "Get key at: https://platform.openai.com/api-keys"
                )
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI API is configured."""
        try:
            if not self._api_key or self._api_key == 'your_openai_key_here':
                return False
            self._get_client()
            return True
        except Exception as e:
            logger.debug(f"OpenAI not available: {e}")
            return False

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Parameters
        ----------
        text : str
            Text to embed

        Returns
        -------
        List[float]
            Embedding vector
        """
        client = self._get_client()

        try:
            response = client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Parameters
        ----------
        texts : List[str]
            Texts to embed

        Returns
        -------
        List[List[float]]
            List of embedding vectors
        """
        client = self._get_client()

        try:
            response = client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI batch embedding generation failed: {e}")
            raise


# Singleton instance
_openai_client: Optional[OpenAIEmbeddingClient] = None


def get_openai_client() -> OpenAIEmbeddingClient:
    """Get the singleton OpenAI embedding client."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIEmbeddingClient()
    return _openai_client
