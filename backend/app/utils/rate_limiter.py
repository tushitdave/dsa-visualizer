"""
Simple in-memory rate limiter for API endpoints.

Provides protection against:
- Brute force attacks
- API abuse
- DoS attempts

Uses a sliding window algorithm with thread-safe operations.
"""

import time
import threading
from typing import Dict, Tuple
from collections import defaultdict
import os

from app.utils.logger import get_logger

logger = get_logger("rate_limiter")


class RateLimiter:
    """
    Thread-safe sliding window rate limiter.

    Tracks requests per IP address within a time window.
    """

    def __init__(self):
        # Default limits (can be overridden via environment)
        self.default_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.analyze_limit = int(os.getenv("ANALYZE_RATE_LIMIT_PER_MINUTE", "10"))

        # Storage: {ip: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.RLock()

        # Cleanup old entries periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # seconds

        logger.info(f"Rate limiter initialized: default={self.default_limit}/min, analyze={self.analyze_limit}/min")

    def _cleanup_old_entries(self, now: float):
        """Remove entries older than 1 minute."""
        cutoff = now - 60
        with self._lock:
            for ip in list(self._requests.keys()):
                self._requests[ip] = [
                    (ts, endpoint) for ts, endpoint in self._requests[ip]
                    if ts > cutoff
                ]
                if not self._requests[ip]:
                    del self._requests[ip]

    def is_allowed(self, ip: str, endpoint: str = "default") -> Tuple[bool, int, int]:
        """
        Check if a request from this IP is allowed.

        Args:
            ip: Client IP address
            endpoint: Endpoint category ('analyze', 'learn', or 'default')

        Returns:
            Tuple of (allowed: bool, current_count: int, limit: int)
        """
        now = time.time()

        # Periodic cleanup
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_old_entries(now)
            self._last_cleanup = now

        # Determine limit based on endpoint
        if endpoint in ('analyze', 'learn'):
            limit = self.analyze_limit
        else:
            limit = self.default_limit

        cutoff = now - 60  # 1 minute window

        with self._lock:
            # Count recent requests for this IP and endpoint category
            recent = [
                ts for ts, ep in self._requests[ip]
                if ts > cutoff and (ep == endpoint or endpoint == 'default')
            ]
            current_count = len(recent)

            if current_count >= limit:
                logger.warning(f"Rate limit exceeded for IP {ip[:16]}... on {endpoint} ({current_count}/{limit})")
                return False, current_count, limit

            # Record this request
            self._requests[ip].append((now, endpoint))
            return True, current_count + 1, limit

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        with self._lock:
            total_ips = len(self._requests)
            total_requests = sum(len(reqs) for reqs in self._requests.values())
            return {
                "active_ips": total_ips,
                "tracked_requests": total_requests,
                "default_limit": self.default_limit,
                "analyze_limit": self.analyze_limit
            }


# Singleton instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get the singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
