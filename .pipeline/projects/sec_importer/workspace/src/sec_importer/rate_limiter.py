"""Rate limiter for SEC API requests.

Implements a token-bucket algorithm with configurable rate and exponential
backoff for transient errors.
"""

import time
import random
from typing import Optional, Callable, Any


class RateLimiter:
    """Token-bucket rate limiter with exponential backoff support.

    Attributes:
        requests_per_second: Maximum requests allowed per second.
        delay: Fixed delay between requests (fallback).
        max_retries: Maximum number of retries for transient errors.
        base_backoff: Base backoff time in seconds.
        jitter: Whether to add jitter to backoff times.
    """

    def __init__(self, requests_per_second: int = 10,
                 delay: float = 0.1,
                 max_retries: int = 3,
                 base_backoff: float = 1.0,
                 jitter: bool = True):
        """Initialize rate limiter.

        Args:
            requests_per_second: Target request rate.
            delay: Minimum delay between requests in seconds.
            max_retries: Max retries for transient errors.
            base_backoff: Base backoff time for exponential backoff.
            jitter: Add random jitter to backoff to avoid thundering herd.

        Raises:
            ValueError: If requests_per_second <= 0, delay < 0, or max_retries < 0.
        """
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if delay < 0:
            raise ValueError("delay must be non-negative")
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        self.requests_per_second = requests_per_second
        self.delay = delay
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.jitter = jitter

        # Token bucket state
        self._tokens: float = requests_per_second
        self._last_refill: float = time.monotonic()
        self._lock = False  # Simple lock to prevent concurrent refills
        self._last_wait_time: Optional[float] = None

    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self.requests_per_second,
            self._tokens + elapsed * self.requests_per_second,
        )
        self._last_refill = now

    def acquire(self) -> float:
        """Acquire a token, waiting if necessary.

        Returns:
            Time waited in seconds.
        """
        waited = 0.0
        while True:
            self._refill_tokens()

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return waited

            # Calculate wait time for next token
            wait_time = (1.0 - self._tokens) / self.requests_per_second
            time.sleep(wait_time)
            waited += wait_time

    def wait(self):
        """Wait for rate limit without returning wait time.
        
        Enforces the configured delay between calls.
        """
        if self._last_wait_time is None:
            # First call: always sleep the full delay
            if self.delay > 0:
                if self.jitter:
                    time.sleep(self.delay * (0.5 + random.random()))
                else:
                    time.sleep(self.delay)
            self._last_wait_time = time.monotonic()
            return

        elapsed = time.monotonic() - self._last_wait_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            if self.jitter:
                sleep_time *= (0.5 + random.random())
            time.sleep(sleep_time)
        self._last_wait_time = time.monotonic()

    def wait_between(self, last_request_time: float):
        """Wait if needed based on last request time.

        Args:
            last_request_time: Timestamp of the last request.
        """
        elapsed = time.monotonic() - last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with rate limiting and exponential backoff.

        Args:
            func: Callable to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            Result of func.

        Raises:
            Exception: If all retries are exhausted.
        """
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                self.wait()
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    backoff = self.base_backoff * (2 ** attempt)
                    if self.jitter:
                        backoff *= (0.5 + random.random())
                    time.sleep(backoff)
        raise last_error

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with rate limiting and exponential backoff.

        Alias for execute().

        Args:
            func: Callable to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            Result of func.

        Raises:
            Exception: If all retries are exhausted.
        """
        return self.execute(func, *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def reset(self):
        """Reset the token bucket to full."""
        self._tokens = self.requests_per_second
        self._last_refill = time.monotonic()

    @property
    def available_tokens(self) -> float:
        """Get current available tokens (without consuming)."""
        self._refill_tokens()
        return self._tokens
