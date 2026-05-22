"""Retry utilities for the invoice processor."""

import time
import logging
from typing import Callable, TypeVar

logger = logging.getLogger("invoice_processor.retry")

T = TypeVar("T")


def retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay: float = 0.5,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs,
) -> T:
    """Retry *func* up to *max_attempts* times, waiting *delay* seconds between tries.

    Args:
        func: The callable to retry.
        max_attempts: Maximum number of attempts.
        delay: Seconds to wait between retries.
        exceptions: Tuple of exception types that trigger a retry.
        *args, **kwargs: Arguments passed to *func*.

    Returns:
        The result of *func* on success.

    Raises:
        The last exception if all attempts fail.
    """
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as exc:
            last_exc = exc
            if attempt < max_attempts:
                logger.warning(
                    "Attempt %d/%d failed for %s: %s. Retrying in %.1fs...",
                    attempt,
                    max_attempts,
                    func.__name__,
                    exc,
                    delay,
                )
                time.sleep(delay)
    raise last_exc  # type: ignore[misc]
