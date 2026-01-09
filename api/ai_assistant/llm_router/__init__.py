"""
LLM Router Module

This module provides intelligent routing of LLM requests based on
data sensitivity and query complexity.

Routing Rules:
1. High sensitivity data -> Ollama (local, never leaves infrastructure)
2. Security module content -> Ollama (always local)
3. Complex reasoning + low sensitivity -> Groq (for speed)
4. Default -> Ollama (privacy-first)

Main components:
- LLMRouter: Main routing logic
- SensitivityClassifier: Determines routing based on content
- Providers: Ollama and Groq implementations
"""

from .router import LLMRouter, RoutingDecision, RoutingContext, get_llm_router
from .sensitivity import SensitivityClassifier

__all__ = [
    'LLMRouter',
    'RoutingDecision',
    'RoutingContext',
    'get_llm_router',
    'SensitivityClassifier',
]
