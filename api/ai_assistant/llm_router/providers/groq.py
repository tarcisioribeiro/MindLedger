"""
Groq Provider

Cloud LLM provider using Groq API.
"""

import os
import logging
from typing import Optional

from django.conf import settings

from .base import BaseLLMProvider, GenerationResult

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """
    Groq-based LLM provider for fast cloud inference.

    This provider uses the Groq API for fast inference on
    low-sensitivity data that requires complex reasoning.

    IMPORTANT: Only use this provider when:
    1. No high-sensitivity data is in the context
    2. No security module content is involved
    3. The query benefits from cloud inference speed

    Attributes
    ----------
    client : Groq
        Groq API client
    _model : str
        Model to use for generation
    """

    def __init__(self, model: Optional[str] = None):
        groq_config = getattr(settings, 'GROQ_CONFIG', {})
        self._model = model or groq_config.get('MODEL', 'llama-3.3-70b-versatile')
        self._api_key = groq_config.get('API_KEY') or os.getenv('GROQ_API_KEY')
        self._client = None

    def _get_client(self):
        """Lazy-load the Groq client."""
        if self._client is None:
            if not self._api_key or self._api_key == 'your_groq_api_key_here':
                raise ValueError(
                    "Groq API key not configured. "
                    "Set GROQ_API_KEY in environment or settings."
                )
            try:
                from groq import Groq
                self._client = Groq(api_key=self._api_key)
            except ImportError:
                raise ImportError("groq package not installed")
        return self._client

    @property
    def name(self) -> str:
        return 'groq'

    @property
    def model(self) -> str:
        return self._model

    @property
    def is_local(self) -> bool:
        return False

    def is_available(self) -> bool:
        """Check if Groq API is configured and accessible."""
        try:
            if not self._api_key or self._api_key == 'your_groq_api_key_here':
                return False
            # Try to import and create client
            self._get_client()
            return True
        except Exception as e:
            logger.warning(f"Groq availability check failed: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> GenerationResult:
        """
        Generate text using Groq API.

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
        client = self._get_client()

        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})

        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            choice = response.choices[0]
            usage = response.usage

            return GenerationResult(
                text=choice.message.content,
                model=response.model,
                provider=self.name,
                tokens_used=usage.total_tokens if usage else None,
                metadata={
                    'prompt_tokens': usage.prompt_tokens if usage else None,
                    'completion_tokens': usage.completion_tokens if usage else None,
                    'finish_reason': choice.finish_reason
                }
            )

        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise
