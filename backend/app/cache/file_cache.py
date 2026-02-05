"""
File-based cache persistence.
Survives server restarts by storing cache on disk.
"""

import os
import json
import time
import gzip
from pathlib import Path
from typing import Optional, Any, Dict
from threading import RLock
import logging

logger = logging.getLogger(__name__)


class FileCache:
    """
    File-based cache with compression support.

    Features:
    - Gzip compression for space efficiency
    - Atomic writes to prevent corruption
    - TTL support with metadata
    - Directory-based organization
    """

    def __init__(self, cache_dir: str = "cache_data", compress: bool = True):
        """
        Initialize file cache.

        Args:
            cache_dir: Directory to store cache files
            compress: Whether to compress cache files
        """
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._compress = compress
        self._lock = RLock()
        self._metadata_file = self._cache_dir / "metadata.json"
        self._metadata: Dict[str, Dict] = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Dict]:
        """Load metadata from disk."""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        return {}

    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            with open(self._metadata_file, 'w') as f:
                json.dump(self._metadata, f)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Use first 2 chars of key as subdirectory for better file distribution
        safe_key = key.replace(':', '_').replace('/', '_')
        subdir = safe_key[:2] if len(safe_key) >= 2 else "00"
        dir_path = self._cache_dir / subdir
        dir_path.mkdir(exist_ok=True)

        ext = ".json.gz" if self._compress else ".json"
        return dir_path / f"{safe_key}{ext}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from file cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            # Check metadata for TTL
            if key in self._metadata:
                meta = self._metadata[key]
                if meta.get('ttl', 0) > 0:
                    if time.time() - meta.get('created_at', 0) > meta['ttl']:
                        self.delete(key)
                        return None

            file_path = self._get_file_path(key)
            if not file_path.exists():
                return None

            try:
                if self._compress:
                    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read cache file {key}: {e}")
                return None

    def set(self, key: str, value: Any, ttl: float = 0) -> bool:
        """
        Set value in file cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (0 = no expiration)

        Returns:
            True if successful
        """
        with self._lock:
            file_path = self._get_file_path(key)
            temp_path = file_path.with_suffix('.tmp')

            try:
                # Write to temp file first (atomic write)
                if self._compress:
                    with gzip.open(temp_path, 'wt', encoding='utf-8') as f:
                        json.dump(value, f)
                else:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        json.dump(value, f)

                # Rename to final path (atomic on most systems)
                temp_path.replace(file_path)

                # Update metadata
                self._metadata[key] = {
                    'created_at': time.time(),
                    'ttl': ttl,
                    'size': file_path.stat().st_size
                }
                self._save_metadata()

                return True
            except Exception as e:
                logger.error(f"Failed to write cache file {key}: {e}")
                if temp_path.exists():
                    temp_path.unlink()
                return False

    def delete(self, key: str) -> bool:
        """
        Delete entry from file cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            file_path = self._get_file_path(key)

            if key in self._metadata:
                del self._metadata[key]
                self._save_metadata()

            if file_path.exists():
                try:
                    file_path.unlink()
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete cache file {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            if key in self._metadata:
                meta = self._metadata[key]
                if meta.get('ttl', 0) > 0:
                    if time.time() - meta.get('created_at', 0) > meta['ttl']:
                        self.delete(key)
                        return False

            return self._get_file_path(key).exists()

    def clear(self) -> int:
        """
        Clear all cache files.

        Returns:
            Number of files deleted
        """
        with self._lock:
            count = 0
            for key in list(self._metadata.keys()):
                if self.delete(key):
                    count += 1
            return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired = []
            current_time = time.time()

            for key, meta in self._metadata.items():
                ttl = meta.get('ttl', 0)
                if ttl > 0 and current_time - meta.get('created_at', 0) > ttl:
                    expired.append(key)

            for key in expired:
                self.delete(key)

            return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """Get file cache statistics."""
        with self._lock:
            total_size = sum(
                meta.get('size', 0) for meta in self._metadata.values()
            )
            return {
                'entries': len(self._metadata),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_dir': str(self._cache_dir),
                'compressed': self._compress
            }

    def get_all_keys(self) -> list:
        """Get all cache keys."""
        with self._lock:
            return list(self._metadata.keys())
