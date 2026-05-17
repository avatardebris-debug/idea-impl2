"""Rate limiter with exponential backoff for API connectors."""

from __future__ import annotations

import logging
import time
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with exponential backoff for API endpoints.

    Attributes:
        limits: Dict of endpoint -> max requests per window.
        window_seconds: Time window in seconds for rate limiting.
        max_retries: Maximum number of retries on rate limit errors.
        base_delay: Base delay in seconds for exponential backoff.
        _request_counts: Dict of endpoint -> list of request timestamps.
        _lock: Threading lock for thread safety.
    """

    def __init__(
        self,
        limits: Optional[Dict[str, int]] = None,
        window_seconds: float = 60.0,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        self.limits = limits or {
            "products": 10,
            "inventory": 5,
            "orders": 5,
            "ads": 3,
            "analytics": 5,
        }
        self.window_seconds = window_seconds
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._request_counts: Dict[str, list] = {
            endpoint: [] for endpoint in self.limits
        }
        self._lock = threading.Lock()

    def _cleanup_old_requests(self, endpoint: str, now: float) -> None:
        """Remove requests outside the current window."""
        if endpoint not in self._request_counts:
            self._request_counts[endpoint] = []
        cutoff = now - self.window_seconds
        self._request_counts[endpoint] = [
            t for t in self._request_counts[endpoint] if t > cutoff
        ]

    def wait_if_needed(self, endpoint: str) -> float:
        """Wait if the rate limit for an endpoint is exceeded.

        Args:
            endpoint: The API endpoint being accessed.

        Returns:
            Delay in seconds before the request can be made.
        """
        with self._lock:
            now = time.time()
            self._cleanup_old_requests(endpoint, now)

            max_requests = self.limits.get(endpoint, 10)
            current_count = len(self._request_counts[endpoint])

            if current_count >= max_requests:
                # Calculate how long to wait
                oldest_request = self._request_counts[endpoint][0]
                wait_time = self.window_seconds - (now - oldest_request)
                if wait_time > 0:
                    logger.debug(
                        f"Rate limit hit for {endpoint}. Waiting {wait_time:.2f}s"
                    )
                    return wait_time
            return 0.0

    def record_request(self, endpoint: str) -> None:
        """Record a request to an endpoint."""
        with self._lock:
            now = time.time()
            self._cleanup_old_requests(endpoint, now)
            self._request_counts[endpoint].append(now)

    def get_remaining(self, endpoint: str) -> int:
        """Get remaining requests for an endpoint in the current window.

        Args:
            endpoint: The API endpoint.

        Returns:
            Number of remaining requests allowed.
        """
        with self._lock:
            now = time.time()
            self._cleanup_old_requests(endpoint, now)
            max_requests = self.limits.get(endpoint, 10)
            current_count = len(self._request_counts[endpoint])
            return max(0, max_requests - current_count)

    def reset(self) -> None:
        """Reset all request counts."""
        with self._lock:
            for endpoint in self._request_counts:
                self._request_counts[endpoint] = []
