"""
In-memory LRU cache implementation.
Provides fast access with automatic eviction.
"""

import time
from collections import OrderedDict
from threading import RLock
from typing import Optional, Any, Dict
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    value: Any
    created_at: float
    ttl: float  # Time to live in seconds
    hits: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl <= 0:  # TTL of 0 or negative means no expiration
            return False
        return time.time() - self.created_at > self.ttl


class MemoryCache:
    """
    Thread-safe LRU cache with TTL support.

    Features:
    - LRU eviction when max_size is reached
    - TTL-based expiration
    - Hit counting for analytics
    - Thread-safe operations
    """

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (1 hour)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None

            entry = self._cache[key]

            if entry.is_expired():
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats['hits'] += 1

            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override in seconds
        """
        with self._lock:
            # Remove if exists to update position
            if key in self._cache:
                del self._cache[key]

            # Evict if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)  # Remove oldest
                self._stats['evictions'] += 1

            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl if ttl is not None else self._default_ttl
            )

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            if key not in self._cache:
                return False
            if self._cache[key].is_expired():
                del self._cache[key]
                return False
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0

            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': round(hit_rate * 100, 2),
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations']
            }

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            self._stats['expirations'] += len(expired_keys)
            return len(expired_keys)

    def get_all_keys(self) -> list:
        """Get all cache keys (for debugging)."""
        with self._lock:
            return list(self._cache.keys())
