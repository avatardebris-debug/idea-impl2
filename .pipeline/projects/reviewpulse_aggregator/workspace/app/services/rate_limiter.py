"""Rate limiter for external API calls."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket rate limiter for API calls.

    Args:
        delay: Minimum seconds between requests.
        max_retries: Maximum number of retry attempts on rate-limit (429) or server errors.
    """

    def __init__(self, delay: float = 1.0, max_retries: int = 5) -> None:
        self.delay = delay
        self.max_retries = max_retries
        self._last_request_time: float = 0.0

    def should_retry(self, retry_count: int, status_code: int) -> bool:
        """Return True if the retry count and status code warrant a retry."""
        if retry_count > self.max_retries:
            return False
        return status_code in (429, 500, 502, 503, 504)

    def wait(self, retry_count: int = 0) -> None:
        """Wait until enough time has passed since the last request.
        
        Args:
            retry_count: Current retry count for exponential backoff.
        """
        elapsed = time.monotonic() - self._last_request_time
        wait_time = self.delay * (2 ** retry_count)
        if elapsed < wait_time:
            sleep_time = wait_time - elapsed
            try:
                loop = asyncio.get_running_loop()
                loop.run_until_complete(asyncio.sleep(sleep_time))
            except RuntimeError:
                time.sleep(sleep_time)
        self._last_request_time = time.monotonic()

    async def async_wait(self) -> None:
        """Async version of wait for use in async contexts."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            await asyncio.sleep(sleep_time)
        self._last_request_time = time.monotonic()
