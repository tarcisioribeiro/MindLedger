"""
Cache Key Generators

Utilities for generating consistent cache keys.
"""

import hashlib
import json
from typing import Optional, Dict, Any, List


class CacheKeyGenerator:
    """
    Generates cache keys for various cache operations.

    All keys are prefixed with 'ai:' to namespace AI Assistant cache entries.
    """

    PREFIX = 'ai'

    @classmethod
    def _hash(cls, data: str) -> str:
        """Generate a short hash for the given data."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    @classmethod
    def query_key(
        cls,
        query: str,
        owner_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a key for caching query responses.

        Parameters
        ----------
        query : str
            The user's query
        owner_id : int
            Owner's ID for isolation
        filters : dict, optional
            Query filters (tipo, sensibilidade, etc.)

        Returns
        -------
        str
            Cache key
        """
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()

        # Create a deterministic string from filters
        filter_str = ""
        if filters:
            # Sort keys for consistency
            sorted_filters = {k: filters[k] for k in sorted(filters.keys()) if filters[k]}
            filter_str = json.dumps(sorted_filters, sort_keys=True)

        # Combine all parts
        key_data = f"{normalized_query}:{owner_id}:{filter_str}"
        key_hash = cls._hash(key_data)

        return f"{cls.PREFIX}:query:{owner_id}:{key_hash}"

    @classmethod
    def embedding_key(cls, text: str, model: str = 'nomic-embed-text') -> str:
        """
        Generate a key for caching embeddings.

        Parameters
        ----------
        text : str
            Text to embed
        model : str
            Embedding model name

        Returns
        -------
        str
            Cache key
        """
        text_hash = cls._hash(text)
        return f"{cls.PREFIX}:emb:{model}:{text_hash}"

    @classmethod
    def semantic_index_key(cls, owner_id: int) -> str:
        """
        Generate a key for the semantic cache index.

        Parameters
        ----------
        owner_id : int
            Owner's ID

        Returns
        -------
        str
            Cache key for the semantic index
        """
        return f"{cls.PREFIX}:sem_idx:{owner_id}"

    @classmethod
    def user_cache_pattern(cls, owner_id: int) -> str:
        """
        Generate a pattern to match all cache keys for a user.

        Parameters
        ----------
        owner_id : int
            Owner's ID

        Returns
        -------
        str
            Pattern for cache key matching
        """
        return f"{cls.PREFIX}:*:{owner_id}:*"

    @classmethod
    def content_invalidation_key(
        cls,
        content_type: str,
        content_id: int,
        owner_id: int
    ) -> str:
        """
        Generate a key for tracking content invalidation.

        Parameters
        ----------
        content_type : str
            Type of content
        content_id : int
            Content ID
        owner_id : int
            Owner's ID

        Returns
        -------
        str
            Cache key
        """
        return f"{cls.PREFIX}:inv:{owner_id}:{content_type}:{content_id}"

    @classmethod
    def rate_limit_key(cls, owner_id: int, action: str = 'query') -> str:
        """
        Generate a key for rate limiting.

        Parameters
        ----------
        owner_id : int
            Owner's ID
        action : str
            Action being rate limited

        Returns
        -------
        str
            Cache key
        """
        return f"{cls.PREFIX}:rate:{action}:{owner_id}"
