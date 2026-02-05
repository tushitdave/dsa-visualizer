"""
Cache Manager - Orchestrates multi-level caching system.
Provides unified interface for all cache operations.
"""

import asyncio
import logging
from typing import Optional, Any, Dict, List
from pathlib import Path

from .memory_cache import MemoryCache
from .file_cache import FileCache
from .cache_keys import CacheKeys

logger = logging.getLogger(__name__)

# Singleton instance
_cache_manager_instance: Optional['CacheManager'] = None


class CacheManager:
    """
    Multi-level cache manager for AlgoInsight.

    Cache Levels:
    - L1 (Memory): Exact problem match -> Full trace
    - L2 (Memory): Normalized problem -> Strategy
    - L3 (Memory + File): Algorithm pattern -> Template

    Features:
    - Automatic fallback between levels
    - Background persistence to file
    - Cache warming on startup
    - Statistics and monitoring
    """

    # TTL configurations (in seconds)
    TTL_L1_EXACT = 24 * 3600      # 24 hours for exact matches
    TTL_L2_NORMALIZED = 7 * 24 * 3600  # 7 days for normalized
    TTL_L3_ALGORITHM = 30 * 24 * 3600  # 30 days for algorithm templates

    def __init__(
        self,
        cache_dir: str = "cache_data",
        l1_max_size: int = 500,
        l2_max_size: int = 1000,
        l3_max_size: int = 2000
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for file-based cache
            l1_max_size: Max entries for L1 cache
            l2_max_size: Max entries for L2 cache
            l3_max_size: Max entries for L3 cache
        """
        self._cache_dir = Path(cache_dir)

        # Initialize memory caches for each level
        self._l1_cache = MemoryCache(max_size=l1_max_size, default_ttl=self.TTL_L1_EXACT)
        self._l2_cache = MemoryCache(max_size=l2_max_size, default_ttl=self.TTL_L2_NORMALIZED)
        self._l3_cache = MemoryCache(max_size=l3_max_size, default_ttl=self.TTL_L3_ALGORITHM)

        # File cache for persistence
        self._file_cache = FileCache(cache_dir=str(self._cache_dir / "persistent"))

        logger.info(f"CacheManager initialized with dir: {cache_dir}")

    # ==================== L1: Exact Match ====================

    async def get_exact_trace(self, problem_text: str, context_toggles: List[str]) -> Optional[Dict]:
        """
        Get full trace for exact problem match.

        Args:
            problem_text: Original problem text
            context_toggles: Context options selected

        Returns:
            Full trace data or None
        """
        key = CacheKeys.l1_exact_match(problem_text, context_toggles)

        # Check memory first
        result = self._l1_cache.get(key)
        if result:
            logger.debug(f"L1 cache HIT (memory): {key[:20]}...")
            return result

        # Check file cache
        result = self._file_cache.get(key)
        if result:
            logger.debug(f"L1 cache HIT (file): {key[:20]}...")
            # Promote to memory cache
            self._l1_cache.set(key, result, self.TTL_L1_EXACT)
            return result

        logger.debug(f"L1 cache MISS: {key[:20]}...")
        return None

    async def store_exact_trace(self, problem_text: str, context_toggles: List[str], trace: Dict) -> None:
        """Store full trace for exact problem match."""
        key = CacheKeys.l1_exact_match(problem_text, context_toggles)

        # Store in both memory and file
        self._l1_cache.set(key, trace, self.TTL_L1_EXACT)
        self._file_cache.set(key, trace, self.TTL_L1_EXACT)

        logger.debug(f"L1 cache STORE: {key[:20]}...")

    # ==================== L2: Normalized Match ====================

    async def get_strategy(self, objective: str, input_structure: str, output_structure: str) -> Optional[Dict]:
        """
        Get strategy for normalized problem structure.

        Args:
            objective: Problem objective
            input_structure: Input data structure
            output_structure: Output data structure

        Returns:
            Strategy data or None
        """
        key = CacheKeys.l2_normalized_match(objective, input_structure, output_structure)

        result = self._l2_cache.get(key)
        if result:
            logger.debug(f"L2 cache HIT: {key[:20]}...")
            return result

        # Check file cache
        result = self._file_cache.get(key)
        if result:
            self._l2_cache.set(key, result, self.TTL_L2_NORMALIZED)
            return result

        logger.debug(f"L2 cache MISS: {key[:20]}...")
        return None

    async def store_strategy(self, objective: str, input_structure: str, output_structure: str, strategy: Dict) -> None:
        """Store strategy for normalized problem."""
        key = CacheKeys.l2_normalized_match(objective, input_structure, output_structure)

        self._l2_cache.set(key, strategy, self.TTL_L2_NORMALIZED)
        self._file_cache.set(key, strategy, self.TTL_L2_NORMALIZED)

        logger.debug(f"L2 cache STORE: {key[:20]}...")

    # ==================== L3: Algorithm Template ====================

    async def get_algorithm_template(self, algorithm_name: str, input_size: str = "medium") -> Optional[Dict]:
        """
        Get pre-computed template for algorithm.

        Args:
            algorithm_name: Name of algorithm
            input_size: Size category (small/medium/large)

        Returns:
            Algorithm template or None
        """
        key = CacheKeys.l3_algorithm_match(algorithm_name, input_size)

        result = self._l3_cache.get(key)
        if result:
            logger.debug(f"L3 cache HIT: {key}")
            return result

        # Check file cache
        result = self._file_cache.get(key)
        if result:
            self._l3_cache.set(key, result, self.TTL_L3_ALGORITHM)
            return result

        logger.debug(f"L3 cache MISS: {key}")
        return None

    async def store_algorithm_template(self, algorithm_name: str, input_size: str, template: Dict) -> None:
        """Store algorithm template."""
        key = CacheKeys.l3_algorithm_match(algorithm_name, input_size)

        self._l3_cache.set(key, template, self.TTL_L3_ALGORITHM)
        self._file_cache.set(key, template, self.TTL_L3_ALGORITHM)

        logger.debug(f"L3 cache STORE: {key}")

    # ==================== Code Cache ====================

    async def get_cached_code(self, algorithm_name: str, input_signature: str) -> Optional[Dict]:
        """Get cached generated code for algorithm + inputs."""
        key = CacheKeys.code_cache(algorithm_name, input_signature)
        return self._l2_cache.get(key) or self._file_cache.get(key)

    async def store_cached_code(self, algorithm_name: str, input_signature: str, code_data: Dict) -> None:
        """Store generated code."""
        key = CacheKeys.code_cache(algorithm_name, input_signature)
        self._l2_cache.set(key, code_data, self.TTL_L2_NORMALIZED)
        self._file_cache.set(key, code_data, self.TTL_L2_NORMALIZED)

    # ==================== Utility Methods ====================

    async def smart_lookup(self, problem_text: str, context_toggles: List[str], normalized_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform smart multi-level cache lookup.

        Returns dict with:
        - hit_level: 'l1', 'l2', 'l3', or None
        - data: cached data if found
        - cache_key: key that matched
        """
        # Try L1 first
        l1_result = await self.get_exact_trace(problem_text, context_toggles)
        if l1_result:
            return {
                'hit_level': 'l1',
                'data': l1_result,
                'cache_key': CacheKeys.l1_exact_match(problem_text, context_toggles)
            }

        # Try L2 if normalized data available
        if normalized_data:
            l2_result = await self.get_strategy(
                normalized_data.get('objective', ''),
                normalized_data.get('input_structure', ''),
                normalized_data.get('output_structure', '')
            )
            if l2_result:
                return {
                    'hit_level': 'l2',
                    'data': l2_result,
                    'cache_key': 'l2_normalized'
                }

        return {'hit_level': None, 'data': None, 'cache_key': None}

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            'l1_memory': self._l1_cache.get_stats(),
            'l2_memory': self._l2_cache.get_stats(),
            'l3_memory': self._l3_cache.get_stats(),
            'file_cache': self._file_cache.get_stats()
        }

    async def cleanup(self) -> Dict[str, int]:
        """Cleanup expired entries from all caches."""
        return {
            'l1_expired': self._l1_cache.cleanup_expired(),
            'l2_expired': self._l2_cache.cleanup_expired(),
            'l3_expired': self._l3_cache.cleanup_expired(),
            'file_expired': self._file_cache.cleanup_expired()
        }

    async def warm_cache(self, precomputed_dir: str = None) -> int:
        """
        Warm cache with pre-computed algorithm templates.

        Args:
            precomputed_dir: Directory containing pre-computed JSON files

        Returns:
            Number of entries loaded
        """
        if precomputed_dir is None:
            precomputed_dir = Path(__file__).parent.parent / "algorithms" / "precomputed"

        precomputed_path = Path(precomputed_dir)
        if not precomputed_path.exists():
            logger.warning(f"Precomputed directory not found: {precomputed_dir}")
            return 0

        count = 0
        import json

        for json_file in precomputed_path.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                algo_id = data.get('algorithm_id', json_file.stem)

                # Store each size variation
                templates = data.get('templates', {})
                for size_key, template in templates.items():
                    size = size_key.split('_')[0] if '_' in size_key else 'medium'
                    await self.store_algorithm_template(algo_id, size, {
                        'algorithm_id': algo_id,
                        'algorithm_name': data.get('algorithm_name', algo_id),
                        'category': data.get('category', 'unknown'),
                        'complexity': data.get('complexity', {}),
                        'strategy': data.get('strategy', ''),
                        'strategy_details': data.get('strategy_details', ''),
                        'template': template,
                        'quiz_bank': data.get('quiz_bank', [])
                    })
                    count += 1

                logger.debug(f"Loaded algorithm template: {algo_id}")

            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        logger.info(f"Cache warmed with {count} algorithm templates")
        return count

    def clear_all(self) -> None:
        """Clear all caches."""
        self._l1_cache.clear()
        self._l2_cache.clear()
        self._l3_cache.clear()
        self._file_cache.clear()
        logger.info("All caches cleared")


def get_cache_manager() -> CacheManager:
    """Get singleton CacheManager instance."""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager()
    return _cache_manager_instance


def reset_cache_manager() -> None:
    """Reset singleton instance (for testing)."""
    global _cache_manager_instance
    _cache_manager_instance = None
