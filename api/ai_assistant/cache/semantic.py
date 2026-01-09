"""
Semantic Cache

Similarity-based cache for AI responses.
Uses embedding similarity to find cached responses for semantically similar queries.
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

import numpy as np
from django.conf import settings
from django.core.cache import caches

from .keys import CacheKeyGenerator

logger = logging.getLogger(__name__)


@dataclass
class CachedQuery:
    """A cached query with its embedding and response."""
    query: str
    embedding: List[float]
    response: Dict[str, Any]
    filters_hash: str


class SemanticCache:
    """
    Semantic similarity cache for AI responses.

    This cache stores query embeddings and responses, allowing
    similar queries to return cached responses based on embedding
    similarity rather than exact string matching.

    Attributes
    ----------
    similarity_threshold : float
        Minimum similarity score to consider a cache hit (default: 0.92)
    max_entries : int
        Maximum entries per user in the semantic index
    ttl : int
        Time-to-live for cached entries in seconds
    """

    def __init__(
        self,
        cache_alias: str = 'redis',
        similarity_threshold: Optional[float] = None,
        max_entries: int = 100,
        ttl: Optional[int] = None
    ):
        self.cache = caches[cache_alias]
        self.keys = CacheKeyGenerator

        ai_config = getattr(settings, 'AI_ASSISTANT_CONFIG', {})
        self.similarity_threshold = (
            similarity_threshold or
            ai_config.get('CACHE_SEMANTIC_THRESHOLD', 0.92)
        )
        self.max_entries = max_entries
        self.ttl = ttl or ai_config.get('CACHE_TTL_SEMANTIC', 1800)

    def _cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        a = np.array(embedding1)
        b = np.array(embedding2)

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def _get_index(self, owner_id: int) -> List[CachedQuery]:
        """Get the semantic index for a user."""
        key = self.keys.semantic_index_key(owner_id)
        data = self.cache.get(key)

        if not data:
            return []

        try:
            entries = json.loads(data)
            return [
                CachedQuery(
                    query=e['query'],
                    embedding=e['embedding'],
                    response=e['response'],
                    filters_hash=e.get('filters_hash', '')
                )
                for e in entries
            ]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse semantic index: {e}")
            return []

    def _save_index(self, owner_id: int, entries: List[CachedQuery]) -> None:
        """Save the semantic index for a user."""
        key = self.keys.semantic_index_key(owner_id)

        # Trim to max entries (keep most recent)
        entries = entries[-self.max_entries:]

        data = json.dumps([
            {
                'query': e.query,
                'embedding': e.embedding,
                'response': e.response,
                'filters_hash': e.filters_hash
            }
            for e in entries
        ])

        self.cache.set(key, data, self.ttl)

    def get(
        self,
        query_embedding: List[float],
        owner_id: int,
        filters_hash: str = ''
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """
        Find a cached response for a semantically similar query.

        Parameters
        ----------
        query_embedding : List[float]
            Embedding of the current query
        owner_id : int
            Owner's ID
        filters_hash : str
            Hash of the filters used (must match exactly)

        Returns
        -------
        Tuple[Dict, float] or None
            (cached_response, similarity_score) if found, None otherwise
        """
        index = self._get_index(owner_id)

        if not index:
            return None

        best_match = None
        best_score = 0.0

        for entry in index:
            # Filters must match exactly
            if entry.filters_hash != filters_hash:
                continue

            score = self._cosine_similarity(query_embedding, entry.embedding)

            if score >= self.similarity_threshold and score > best_score:
                best_match = entry.response
                best_score = score

        if best_match:
            logger.debug(f"Semantic cache hit with score {best_score:.4f}")
            return (best_match, best_score)

        return None

    def set(
        self,
        query: str,
        query_embedding: List[float],
        response: Dict[str, Any],
        owner_id: int,
        filters_hash: str = ''
    ) -> None:
        """
        Add a query and response to the semantic cache.

        Parameters
        ----------
        query : str
            The original query
        query_embedding : List[float]
            Embedding of the query
        response : Dict[str, Any]
            The response to cache
        owner_id : int
            Owner's ID
        filters_hash : str
            Hash of the filters used
        """
        index = self._get_index(owner_id)

        # Remove existing entry for the same query (if any)
        index = [e for e in index if e.query.lower().strip() != query.lower().strip()]

        # Add new entry
        index.append(CachedQuery(
            query=query,
            embedding=query_embedding,
            response=response,
            filters_hash=filters_hash
        ))

        self._save_index(owner_id, index)

    def invalidate(self, owner_id: int) -> None:
        """
        Invalidate all semantic cache entries for a user.

        Parameters
        ----------
        owner_id : int
            Owner's ID
        """
        key = self.keys.semantic_index_key(owner_id)
        self.cache.delete(key)
        logger.debug(f"Invalidated semantic cache for owner {owner_id}")
