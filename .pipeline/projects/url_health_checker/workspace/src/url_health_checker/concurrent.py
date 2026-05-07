"""Concurrent URL checking using a thread pool."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from .checker import URLChecker


def check_urls_concurrent(
    urls: List[str],
    max_workers: int = 5,
    timeout: int = 10,
    max_attempts: int = 1,
    retry_delay: float = 1.0,
    rate_limit: Optional[float] = None,
    logger: Optional[logging.Logger] = None,
) -> List[Dict]:
    """Check multiple URLs concurrently.

    Args:
        urls: List of URL strings to check.
        max_workers: Maximum number of concurrent threads (default 5).
        timeout: Per-request timeout in seconds (default 10).
        max_attempts: Max retry attempts per URL (default 1).
        retry_delay: Seconds between retry attempts (default 1.0).
        rate_limit: Max requests per second (None = unlimited).
        logger: Optional logger for structured logging.

    Returns:
        A list of result dicts (same format as URLChecker.check),
        ordered by the original *urls* list.
    """
    results: Dict[int, Dict] = {}

    # Rate limiter: track submission timestamps
    last_submission_time = 0.0
    min_interval = 1.0 / rate_limit if rate_limit and rate_limit > 0 else 0.0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Build a mapping from future -> index
        future_to_idx = {}
        for idx, url in enumerate(urls):
            # Apply rate limiting before submission
            if min_interval > 0:
                elapsed = time.time() - last_submission_time
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
            last_submission_time = time.time()

            checker = URLChecker(
                timeout=timeout,
                max_attempts=max_attempts,
                retry_delay=retry_delay,
                logger=logger,
            )
            future = executor.submit(checker.check, url)
            future_to_idx[future] = idx

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception:
                results[idx] = {
                    "url": urls[idx],
                    "status_code": None,
                    "response_time_ms": None,
                    "is_up": False,
                }

    # Return in original order
    return [results[i] for i in range(len(urls))]
