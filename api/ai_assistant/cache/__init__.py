"""
Cache Module

This module provides semantic caching for the AI Assistant using Redis.
Caching reduces LLM calls and improves response latency.

Main components:
- CacheService: Main cache orchestrator
- SemanticCache: Similarity-based cache lookup
- CacheKeyGenerator: Consistent key generation
"""

from .service import CacheService, get_cache_service
from .keys import CacheKeyGenerator
from .semantic import SemanticCache

__all__ = [
    'CacheService',
    'get_cache_service',
    'CacheKeyGenerator',
    'SemanticCache',
]
