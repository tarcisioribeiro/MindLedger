"""
Ollama Provider

Local LLM provider using Ollama.
"""

import logging
from typing import Optional

from django.conf import settings

from ...embeddings.ollama_client import OllamaClient, get_ollama_client
from .base import BaseLLMProvider, GenerationResult

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama-based LLM provider for local inference.

    This provider uses Ollama running locally to ensure
    sensitive data never leaves the infrastructure.

    Attributes
    ----------
    client : OllamaClient
        Ollama HTTP client
    _model : str
        Model to use for generation
    """

    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        model: Optional[str] = None
    ):
        self.client = client or get_ollama_client()

        ollama_config = getattr(settings, 'OLLAMA_CONFIG', {})
        self._model = model or ollama_config.get('LLM_MODEL', 'mistral:7b')

    @property
    def name(self) -> str:
        return 'ollama'

    @property
    def model(self) -> str:
        return self._model

    @property
    def is_local(self) -> bool:
        return True

    def is_available(self) -> bool:
        """Check if Ollama is available and model is ready."""
        try:
            return self.client.health_check() and self.client.is_model_available(self._model)
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> GenerationResult:
        """
        Generate text using Ollama.

        Parameters
        ----------
        prompt : str
            User prompt
        system : str, optional
            System prompt
        temperature : float
            Sampling temperature
        max_tokens : int
            Maximum tokens

        Returns
        -------
        GenerationResult
            Generated text
        """
        try:
            response = self.client.generate_text(
                prompt=prompt,
                system=system,
                model=self._model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return GenerationResult(
                text=response.response,
                model=response.model,
                provider=self.name,
                tokens_used=response.eval_count,
                duration_ms=response.total_duration // 1_000_000 if response.total_duration else None,
                metadata={'done': response.done}
            )

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
