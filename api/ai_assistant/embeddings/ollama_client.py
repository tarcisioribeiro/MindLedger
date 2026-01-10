"""
Ollama HTTP Client

Low-level HTTP client for communicating with the Ollama API.
Handles connection management, retries, and error handling.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import httpx
from django.conf import settings

from .exceptions import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    EmbeddingGenerationError
)

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResponse:
    """Response from Ollama embedding API."""
    embedding: List[float]
    model: str
    prompt_eval_count: Optional[int] = None


@dataclass
class GenerationResponse:
    """Response from Ollama generation API."""
    response: str
    model: str
    done: bool
    total_duration: Optional[int] = None
    eval_count: Optional[int] = None


class OllamaClient:
    """
    HTTP client for Ollama API.

    This client handles all communication with the Ollama server,
    including embedding generation and text generation.

    Attributes
    ----------
    base_url : str
        The base URL for the Ollama API (default from settings)
    timeout : int
        Request timeout in seconds
    embed_model : str
        Model to use for embeddings (default: nomic-embed-text)
    llm_model : str
        Model to use for text generation (default: mistral:7b)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        embed_model: Optional[str] = None,
        llm_model: Optional[str] = None
    ):
        ollama_config = getattr(settings, 'OLLAMA_CONFIG', {})

        self.base_url = (base_url or ollama_config.get('URL', 'http://localhost:11435')).rstrip('/')
        self.timeout = timeout or ollama_config.get('TIMEOUT', 120)
        self.embed_model = embed_model or ollama_config.get('EMBED_MODEL', 'nomic-embed-text')
        self.llm_model = llm_model or ollama_config.get('LLM_MODEL', 'mistral:7b')

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=2.0)  # Fast fail if Ollama not available
        )

    def __del__(self):
        """Close HTTP client on cleanup."""
        if hasattr(self, '_client'):
            self._client.close()

    def health_check(self) -> bool:
        """
        Check if Ollama server is reachable.

        Returns
        -------
        bool
            True if server is healthy, False otherwise
        """
        try:
            response = self._client.get('/api/tags', timeout=2.0)  # Quick check
            return response.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            logger.debug(f"Ollama health check failed at {self.base_url}")
            return False

    def list_models(self) -> List[str]:
        """
        List all available models in Ollama.

        Returns
        -------
        List[str]
            List of model names

        Raises
        ------
        OllamaConnectionError
            If unable to connect to Ollama
        """
        try:
            response = self._client.get('/api/tags')
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except httpx.RequestError as e:
            raise OllamaConnectionError(self.base_url, e)

    def is_model_available(self, model: str) -> bool:
        """
        Check if a specific model is available.

        Parameters
        ----------
        model : str
            Model name to check

        Returns
        -------
        bool
            True if model is available
        """
        try:
            models = self.list_models()
            # Check both exact match and base name (e.g., 'mistral' matches 'mistral:7b')
            return any(
                m == model or m.startswith(f"{model}:") or model.startswith(f"{m.split(':')[0]}:")
                for m in models
            )
        except OllamaConnectionError:
            return False

    def ensure_model(self, model: str) -> bool:
        """
        Ensure a model is available, raising error if not.

        Parameters
        ----------
        model : str
            Model name to check

        Returns
        -------
        bool
            True if model is available

        Raises
        ------
        OllamaModelNotFoundError
            If model is not available
        """
        if not self.is_model_available(model):
            raise OllamaModelNotFoundError(model)
        return True

    def generate_embedding(self, text: str, model: Optional[str] = None) -> EmbeddingResponse:
        """
        Generate embedding for a single text.

        Parameters
        ----------
        text : str
            Text to generate embedding for
        model : str, optional
            Model to use (defaults to self.embed_model)

        Returns
        -------
        EmbeddingResponse
            Embedding response with vector

        Raises
        ------
        OllamaConnectionError
            If unable to connect to Ollama
        EmbeddingGenerationError
            If embedding generation fails
        """
        model = model or self.embed_model

        try:
            response = self._client.post(
                '/api/embed',
                json={
                    'model': model,
                    'input': text
                }
            )
            response.raise_for_status()
            data = response.json()

            # Handle response format - Ollama returns embeddings in 'embeddings' array
            embeddings = data.get('embeddings', [])
            if not embeddings:
                raise EmbeddingGenerationError(text, Exception("Empty embeddings response"))

            return EmbeddingResponse(
                embedding=embeddings[0],
                model=data.get('model', model),
                prompt_eval_count=data.get('prompt_eval_count')
            )

        except httpx.ConnectError as e:
            raise OllamaConnectionError(self.base_url, e)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(model)
            raise EmbeddingGenerationError(text, e)
        except httpx.RequestError as e:
            raise EmbeddingGenerationError(text, e)

    def generate_embeddings_batch(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[EmbeddingResponse]:
        """
        Generate embeddings for multiple texts.

        Note: Ollama processes these sequentially, but this method
        provides a convenient batch interface.

        Parameters
        ----------
        texts : List[str]
            Texts to generate embeddings for
        model : str, optional
            Model to use (defaults to self.embed_model)

        Returns
        -------
        List[EmbeddingResponse]
            List of embedding responses
        """
        model = model or self.embed_model

        # Ollama's /api/embed can accept multiple inputs
        try:
            response = self._client.post(
                '/api/embed',
                json={
                    'model': model,
                    'input': texts
                }
            )
            response.raise_for_status()
            data = response.json()

            embeddings = data.get('embeddings', [])
            return [
                EmbeddingResponse(
                    embedding=emb,
                    model=data.get('model', model)
                )
                for emb in embeddings
            ]

        except httpx.ConnectError as e:
            raise OllamaConnectionError(self.base_url, e)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(model)
            raise EmbeddingGenerationError(str(texts[:2]), e)
        except httpx.RequestError as e:
            raise EmbeddingGenerationError(str(texts[:2]), e)

    def generate_text(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> GenerationResponse:
        """
        Generate text using the LLM model.

        Parameters
        ----------
        prompt : str
            User prompt
        system : str, optional
            System prompt
        model : str, optional
            Model to use (defaults to self.llm_model)
        temperature : float
            Sampling temperature (0.0-1.0)
        max_tokens : int
            Maximum tokens to generate
        stream : bool
            Whether to stream response (not implemented)

        Returns
        -------
        GenerationResponse
            Generated text response

        Raises
        ------
        OllamaConnectionError
            If unable to connect to Ollama
        """
        model = model or self.llm_model

        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})

        try:
            response = self._client.post(
                '/api/chat',
                json={
                    'model': model,
                    'messages': messages,
                    'stream': False,
                    'options': {
                        'temperature': temperature,
                        'num_predict': max_tokens
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

            return GenerationResponse(
                response=data.get('message', {}).get('content', ''),
                model=data.get('model', model),
                done=data.get('done', True),
                total_duration=data.get('total_duration'),
                eval_count=data.get('eval_count')
            )

        except httpx.ConnectError as e:
            raise OllamaConnectionError(self.base_url, e)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(model)
            raise
        except httpx.RequestError as e:
            raise OllamaConnectionError(self.base_url, e)

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a specific model.

        Parameters
        ----------
        model : str
            Model name

        Returns
        -------
        Dict[str, Any]
            Model information
        """
        try:
            response = self._client.post(
                '/api/show',
                json={'name': model}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(model)
            raise
        except httpx.RequestError as e:
            raise OllamaConnectionError(self.base_url, e)


# Singleton instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """
    Get the singleton Ollama client instance.

    Returns
    -------
    OllamaClient
        Configured Ollama client
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
