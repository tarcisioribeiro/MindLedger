"""
Base LLM Provider

Abstract base class for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class GenerationResult:
    """Result of text generation."""
    text: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    duration_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement the generate method and provide
    information about their capabilities.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'ollama', 'groq')."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier."""
        pass

    @property
    @abstractmethod
    def is_local(self) -> bool:
        """Whether this provider runs locally."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> GenerationResult:
        """
        Generate text from a prompt.

        Parameters
        ----------
        prompt : str
            User prompt with context
        system : str, optional
            System prompt
        temperature : float
            Sampling temperature (0.0-1.0)
        max_tokens : int
            Maximum tokens to generate

        Returns
        -------
        GenerationResult
            Generated text with metadata
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model}, local={self.is_local})"
