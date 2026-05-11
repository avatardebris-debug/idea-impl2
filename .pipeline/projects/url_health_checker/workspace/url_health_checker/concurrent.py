"""Concurrent URL checking with ThreadPoolExecutor."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from url_health_checker.checker import check_url


def check_urls_concurrently(
    urls: list[str],
    timeout: float = 5.0,
    max_workers: int = 4,
) -> list[dict]:
    """Check a list of URLs concurrently.

    Results are returned in the **same order** as the input *urls*.

    Args:
        urls: List of URLs to check.
        timeout: Timeout per request in seconds.
        max_workers: Maximum number of concurrent workers.

    Returns:
        List of result dicts, ordered to match the input *urls*.
    """
    results: list[dict | None] = [None] * len(urls)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(check_url, url, timeout): idx
            for idx, url in enumerate(urls)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            results[idx] = future.result()

    return results  # type: ignore[return-value]
