"""
Cache Service

Main caching orchestrator for the AI Assistant.
Combines exact-match and semantic caching for optimal performance.
"""

import json
import hashlib
import logging
from typing import Optional, Dict, Any, List

from django.conf import settings
from django.core.cache import caches

from .keys import CacheKeyGenerator
from .semantic import SemanticCache

logger = logging.getLogger(__name__)


class CacheService:
    """
    Unified cache service for the AI Assistant.

    This service provides:
    1. Exact query caching (fast, hash-based)
    2. Semantic caching (similarity-based)
    3. Embedding caching (avoid regenerating)
    4. Cache invalidation on content updates

    Attributes
    ----------
    cache_alias : str
        Django cache alias to use (default: 'redis')
    exact_ttl : int
        TTL for exact match cache entries
    embedding_ttl : int
        TTL for cached embeddings
    """

    def __init__(
        self,
        cache_alias: str = 'redis',
        exact_ttl: Optional[int] = None,
        embedding_ttl: Optional[int] = None
    ):
        self.cache_alias = cache_alias
        self.cache = caches[cache_alias]
        self.keys = CacheKeyGenerator
        self.semantic = SemanticCache(cache_alias=cache_alias)

        ai_config = getattr(settings, 'AI_ASSISTANT_CONFIG', {})
        self.exact_ttl = exact_ttl or ai_config.get('CACHE_TTL_EXACT', 3600)
        self.embedding_ttl = embedding_ttl or 86400  # 24 hours

    def _filters_hash(self, filters: Optional[Dict[str, Any]]) -> str:
        """Generate a hash of the filters for cache key generation."""
        if not filters:
            return ''
        sorted_filters = {k: filters[k] for k in sorted(filters.keys()) if filters[k]}
        return hashlib.md5(json.dumps(sorted_filters, sort_keys=True).encode()).hexdigest()[:8]

    def get_exact(
        self,
        query: str,
        owner_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for exact query match.

        Parameters
        ----------
        query : str
            The user's query
        owner_id : int
            Owner's ID
        filters : dict, optional
            Query filters

        Returns
        -------
        dict or None
            Cached response if found
        """
        key = self.keys.query_key(query, owner_id, filters)
        data = self.cache.get(key)

        if data:
            try:
                result = json.loads(data)
                result['cached'] = True
                result['cache_type'] = 'exact'
                logger.debug(f"Exact cache hit for query: {query[:50]}...")
                return result
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse cached response for key {key}")
                return None

        return None

    def get_semantic(
        self,
        query_embedding: List[float],
        owner_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for semantically similar query.

        Parameters
        ----------
        query_embedding : List[float]
            Embedding of the query
        owner_id : int
            Owner's ID
        filters : dict, optional
            Query filters

        Returns
        -------
        dict or None
            Cached response if found with sufficient similarity
        """
        filters_hash = self._filters_hash(filters)
        result = self.semantic.get(query_embedding, owner_id, filters_hash)

        if result:
            response, score = result
            response['cached'] = True
            response['cache_type'] = 'semantic'
            response['similarity_score'] = score
            return response

        return None

    def get(
        self,
        query: str,
        query_embedding: List[float],
        owner_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response, trying exact match first, then semantic.

        Parameters
        ----------
        query : str
            The user's query
        query_embedding : List[float]
            Embedding of the query
        owner_id : int
            Owner's ID
        filters : dict, optional
            Query filters

        Returns
        -------
        dict or None
            Cached response if found
        """
        # Try exact match first (faster)
        result = self.get_exact(query, owner_id, filters)
        if result:
            return result

        # Fall back to semantic matching
        return self.get_semantic(query_embedding, owner_id, filters)

    def set(
        self,
        query: str,
        query_embedding: List[float],
        response: Dict[str, Any],
        owner_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache a response for both exact and semantic retrieval.

        Parameters
        ----------
        query : str
            The user's query
        query_embedding : List[float]
            Embedding of the query
        response : dict
            Response to cache
        owner_id : int
            Owner's ID
        filters : dict, optional
            Query filters
        """
        # Remove cache metadata before storing
        cache_response = {k: v for k, v in response.items() if k not in ['cached', 'cache_type', 'similarity_score']}

        # Store exact match
        key = self.keys.query_key(query, owner_id, filters)
        self.cache.set(key, json.dumps(cache_response), self.exact_ttl)

        # Store in semantic index
        filters_hash = self._filters_hash(filters)
        self.semantic.set(query, query_embedding, cache_response, owner_id, filters_hash)

        logger.debug(f"Cached response for query: {query[:50]}...")

    def get_embedding(self, text: str, model: str = 'nomic-embed-text') -> Optional[List[float]]:
        """
        Get a cached embedding.

        Parameters
        ----------
        text : str
            Text that was embedded
        model : str
            Model used for embedding

        Returns
        -------
        List[float] or None
            Cached embedding if found
        """
        key = self.keys.embedding_key(text, model)
        data = self.cache.get(key)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None

        return None

    def set_embedding(
        self,
        text: str,
        embedding: List[float],
        model: str = 'nomic-embed-text'
    ) -> None:
        """
        Cache an embedding.

        Parameters
        ----------
        text : str
            Text that was embedded
        embedding : List[float]
            The embedding vector
        model : str
            Model used for embedding
        """
        key = self.keys.embedding_key(text, model)
        self.cache.set(key, json.dumps(embedding), self.embedding_ttl)

    def invalidate_user(self, owner_id: int) -> int:
        """
        Invalidate all cache entries for a user.

        Note: This requires Redis SCAN, which may not be available
        with all cache backends.

        Parameters
        ----------
        owner_id : int
            Owner's ID

        Returns
        -------
        int
            Number of keys deleted (approximate)
        """
        # Invalidate semantic cache
        self.semantic.invalidate(owner_id)

        # For exact match cache, we can't easily delete by pattern
        # without Redis SCAN. The entries will expire naturally.
        # If using django-redis, we could use delete_pattern.
        try:
            if hasattr(self.cache, 'delete_pattern'):
                pattern = self.keys.user_cache_pattern(owner_id)
                deleted = self.cache.delete_pattern(pattern)
                logger.info(f"Invalidated {deleted} cache entries for owner {owner_id}")
                return deleted
        except Exception as e:
            logger.warning(f"Could not delete by pattern: {e}")

        return 0

    def invalidate_content(
        self,
        content_type: str,
        content_id: int,
        owner_id: int
    ) -> None:
        """
        Invalidate cache when content is updated.

        This marks the content as invalidated and clears related caches.

        Parameters
        ----------
        content_type : str
            Type of content that changed
        content_id : int
            ID of the content
        owner_id : int
            Owner's ID
        """
        # Mark content as invalidated (for future reference)
        inv_key = self.keys.content_invalidation_key(content_type, content_id, owner_id)
        self.cache.set(inv_key, '1', 300)  # 5 minute marker

        # Invalidate semantic cache for this user (content context changed)
        self.semantic.invalidate(owner_id)

        logger.debug(f"Invalidated cache for {content_type}:{content_id}")

    def health_check(self) -> bool:
        """
        Check if the cache service is healthy.

        Returns
        -------
        bool
            True if cache is accessible
        """
        try:
            self.cache.set('ai:health', '1', 10)
            return self.cache.get('ai:health') == '1'
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get the singleton CacheService instance.

    Returns
    -------
    CacheService
        Configured cache service
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
