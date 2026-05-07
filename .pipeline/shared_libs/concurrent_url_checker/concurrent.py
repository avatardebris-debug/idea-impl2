"""Concurrent URL checking using a thread pool."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from .checker import URLChecker


def check_urls_concurrent(
    urls: List[str],
    max_workers: int = 5,
    timeout: int = 10,
) -> List[Dict]:
    """Check multiple URLs concurrently.

    Args:
        urls: List of URL strings to check.
        max_workers: Maximum number of concurrent threads (default 5).
        timeout: Per-request timeout in seconds (default 10).

    Returns:
        A list of result dicts (same format as URLChecker.check),
        ordered by the original *urls* list.
    """
    results: Dict[int, Dict] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(URLChecker(timeout=timeout).check, url): idx
            for idx, url in enumerate(urls)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except Exception:
                # Should not happen because URLChecker.check handles exceptions,
                # but guard anyway.
                results[idx] = {
                    "url": urls[idx],
                    "status_code": None,
                    "response_time_ms": None,
                    "is_up": False,
                }

    # Return in original order
    return [results[i] for i in range(len(urls))]
