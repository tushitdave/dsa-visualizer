"""
Smart Router - Routes requests through optimal execution paths.
Enables sub-second responses for cached/known algorithms.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.cache import CacheManager, get_cache_manager, CacheKeys
from app.algorithms import PatternMatcher, get_pattern_matcher, AlgorithmLibrary, get_algorithm_library, TemplateEngine

logger = logging.getLogger(__name__)

# Singleton instance
_smart_router_instance: Optional['SmartRouter'] = None


class RoutePath(Enum):
    """Execution path types."""
    INSTANT = "instant"      # Cache hit or library match - <100ms
    FAST = "fast"           # Partial cache + customization - <500ms
    FULL = "full"           # Full LLM pipeline - 20-60s


@dataclass
class RouteResult:
    """Result of routing decision."""
    path: RoutePath
    data: Optional[Dict] = None
    algorithm_id: Optional[str] = None
    cache_key: Optional[str] = None
    confidence: float = 0.0
    timing_ms: float = 0.0
    source: str = ""  # 'l1_cache', 'l2_cache', 'library', 'pattern_match', 'llm_pipeline'

    def is_instant(self) -> bool:
        return self.path == RoutePath.INSTANT

    def is_fast(self) -> bool:
        return self.path == RoutePath.FAST

    def needs_llm(self) -> bool:
        return self.path == RoutePath.FULL


@dataclass
class RouterStats:
    """Statistics for router performance."""
    total_requests: int = 0
    instant_hits: int = 0
    fast_hits: int = 0
    full_pipeline: int = 0
    avg_instant_ms: float = 0.0
    avg_fast_ms: float = 0.0
    avg_full_ms: float = 0.0
    cache_hit_rate: float = 0.0


class SmartRouter:
    """
    Smart routing system for AlgoInsight.

    Routes requests through three paths:
    1. INSTANT (<100ms): Exact cache hit or algorithm library match
    2. FAST (<500ms): Pattern match + template customization
    3. FULL (20-60s): Full LLM pipeline for novel problems

    Flow:
    1. Check L1 cache (exact match)
    2. Check algorithm library (pattern match)
    3. Check L2 cache (normalized match)
    4. Fall back to LLM pipeline
    """

    def __init__(
        self,
        cache_manager: CacheManager = None,
        pattern_matcher: PatternMatcher = None,
        algorithm_library: AlgorithmLibrary = None
    ):
        """Initialize router with dependencies."""
        self._cache = cache_manager or get_cache_manager()
        self._matcher = pattern_matcher or get_pattern_matcher()
        self._library = algorithm_library or get_algorithm_library()
        self._template_engine = TemplateEngine()
        self._stats = RouterStats()

        logger.info("SmartRouter initialized")

    async def route(
        self,
        problem_text: str,
        context_toggles: List[str] = None,
        user_inputs: Optional[Dict] = None
    ) -> RouteResult:
        """
        Route a request through the optimal path.

        Args:
            problem_text: User's problem description
            context_toggles: Selected context options
            user_inputs: Any user-provided input data

        Returns:
            RouteResult with path type and data (if found)
        """
        start_time = time.time()
        context_toggles = context_toggles or []

        self._stats.total_requests += 1

        # Try all fast paths in parallel
        l1_task = asyncio.create_task(self._check_l1_cache(problem_text, context_toggles))
        pattern_task = asyncio.create_task(self._check_pattern_match(problem_text))

        # Wait for both
        l1_result, pattern_result = await asyncio.gather(l1_task, pattern_task)

        elapsed_ms = (time.time() - start_time) * 1000

        # Priority 1: L1 exact cache hit
        if l1_result:
            self._stats.instant_hits += 1
            self._update_avg_timing('instant', elapsed_ms)
            logger.info(f"INSTANT path: L1 cache hit in {elapsed_ms:.1f}ms")
            return RouteResult(
                path=RoutePath.INSTANT,
                data=l1_result,
                cache_key=CacheKeys.l1_exact_match(problem_text, context_toggles),
                timing_ms=elapsed_ms,
                source='l1_cache',
                confidence=1.0
            )

        # Priority 2: Algorithm library match
        if pattern_result:
            algo_id, confidence, trace = pattern_result

            if trace:
                # Customize with user inputs if provided
                if user_inputs:
                    trace = self._template_engine.customize_trace(trace, user_inputs, problem_text)

                elapsed_ms = (time.time() - start_time) * 1000
                self._stats.instant_hits += 1
                self._update_avg_timing('instant', elapsed_ms)

                logger.info(f"INSTANT path: Library match '{algo_id}' (confidence: {confidence:.2f}) in {elapsed_ms:.1f}ms")
                return RouteResult(
                    path=RoutePath.INSTANT,
                    data=trace,
                    algorithm_id=algo_id,
                    confidence=confidence,
                    timing_ms=elapsed_ms,
                    source='library'
                )

            # Pattern matched but no pre-computed trace - FAST path
            elapsed_ms = (time.time() - start_time) * 1000
            self._stats.fast_hits += 1
            self._update_avg_timing('fast', elapsed_ms)

            logger.info(f"FAST path: Pattern matched '{algo_id}' but no template in {elapsed_ms:.1f}ms")
            return RouteResult(
                path=RoutePath.FAST,
                algorithm_id=algo_id,
                confidence=confidence,
                timing_ms=elapsed_ms,
                source='pattern_match'
            )

        # Priority 3: Full LLM pipeline needed
        elapsed_ms = (time.time() - start_time) * 1000
        self._stats.full_pipeline += 1

        logger.info(f"FULL path: No cache/pattern match in {elapsed_ms:.1f}ms - LLM pipeline required")
        return RouteResult(
            path=RoutePath.FULL,
            timing_ms=elapsed_ms,
            source='llm_pipeline'
        )

    async def _check_l1_cache(
        self,
        problem_text: str,
        context_toggles: List[str]
    ) -> Optional[Dict]:
        """Check L1 exact match cache."""
        try:
            return await self._cache.get_exact_trace(problem_text, context_toggles)
        except Exception as e:
            logger.error(f"L1 cache check failed: {e}")
            return None

    async def _check_pattern_match(
        self,
        problem_text: str
    ) -> Optional[Tuple[str, float, Optional[Dict]]]:
        """
        Check if problem matches a known algorithm pattern.

        Only returns matches with HIGH confidence (>= 0.7) to avoid
        incorrect algorithm identification.

        Returns:
            (algorithm_id, confidence, trace_data) or None
        """
        try:
            # Use HIGH confidence threshold to avoid false positives
            match = self._matcher.match(problem_text, min_confidence=0.7)
            if not match:
                return None

            # Only use INSTANT path if confidence is very high (>= 0.8)
            # and we have a pre-computed trace
            trace = None
            if match.confidence >= 0.8:
                trace = self._library.get_full_trace(match.algorithm_id)

            # If confidence is between 0.7-0.8, don't return trace
            # This prevents returning incorrect pre-computed results
            if not trace:
                logger.info(f"Pattern match '{match.algorithm_id}' with confidence {match.confidence:.2f} "
                           f"- not high enough for INSTANT path, will use FULL pipeline")
                return None

            return (match.algorithm_id, match.confidence, trace)

        except Exception as e:
            logger.error(f"Pattern match failed: {e}")
            return None

    async def store_result(
        self,
        problem_text: str,
        context_toggles: List[str],
        trace_data: Dict,
        algorithm_id: Optional[str] = None
    ) -> None:
        """
        Store successful result in cache for future instant access.

        Args:
            problem_text: Original problem text
            context_toggles: Context options
            trace_data: Generated trace data
            algorithm_id: Optional algorithm identifier
        """
        try:
            # Store in L1 cache
            await self._cache.store_exact_trace(problem_text, context_toggles, trace_data)

            # If algorithm identified, also update L3 cache
            if algorithm_id:
                size_category = CacheKeys.get_input_size_category(
                    trace_data.get('frames', [{}])[0].get('state', {}).get('data', {})
                )
                await self._cache.store_algorithm_template(algorithm_id, size_category, trace_data)

            logger.debug(f"Stored result in cache (algo: {algorithm_id})")

        except Exception as e:
            logger.error(f"Failed to store result in cache: {e}")

    async def warm_up(self) -> Dict[str, int]:
        """
        Warm up caches with pre-computed algorithms.

        Returns:
            Statistics about loaded entries
        """
        # Load algorithm library
        algo_count = self._library.load()

        # Warm cache from library
        cache_count = await self._cache.warm_cache()

        logger.info(f"Router warm-up complete: {algo_count} algorithms, {cache_count} cache entries")

        return {
            'algorithms_loaded': algo_count,
            'cache_entries': cache_count
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        total = self._stats.total_requests or 1  # Avoid division by zero

        return {
            'total_requests': self._stats.total_requests,
            'instant_hits': self._stats.instant_hits,
            'fast_hits': self._stats.fast_hits,
            'full_pipeline': self._stats.full_pipeline,
            'instant_rate': round(self._stats.instant_hits / total * 100, 2),
            'fast_rate': round(self._stats.fast_hits / total * 100, 2),
            'full_rate': round(self._stats.full_pipeline / total * 100, 2),
            'avg_instant_ms': round(self._stats.avg_instant_ms, 2),
            'avg_fast_ms': round(self._stats.avg_fast_ms, 2),
            'cache_stats': self._cache.get_stats(),
            'library_stats': self._library.get_stats()
        }

    def _update_avg_timing(self, path_type: str, ms: float) -> None:
        """Update average timing statistics."""
        if path_type == 'instant':
            n = self._stats.instant_hits
            self._stats.avg_instant_ms = (
                (self._stats.avg_instant_ms * (n - 1) + ms) / n if n > 0 else ms
            )
        elif path_type == 'fast':
            n = self._stats.fast_hits
            self._stats.avg_fast_ms = (
                (self._stats.avg_fast_ms * (n - 1) + ms) / n if n > 0 else ms
            )

    def get_available_algorithms(self) -> List[str]:
        """Get list of algorithms with instant response."""
        return self._library.list_algorithms()

    def get_algorithm_info(self, algorithm_id: str) -> Optional[Dict]:
        """Get information about a specific algorithm."""
        algo = self._library.get(algorithm_id)
        if not algo:
            return None

        return {
            'id': algo.algorithm_id,
            'name': algo.algorithm_name,
            'category': algo.category,
            'complexity': algo.complexity,
            'strategy': algo.strategy,
            'has_precomputed': bool(algo.templates)
        }


def get_smart_router() -> SmartRouter:
    """Get singleton SmartRouter instance."""
    global _smart_router_instance
    if _smart_router_instance is None:
        _smart_router_instance = SmartRouter()
    return _smart_router_instance


async def initialize_router() -> SmartRouter:
    """Initialize and warm up the router."""
    router = get_smart_router()
    await router.warm_up()
    return router
