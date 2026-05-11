"""URL checker module — sends HEAD requests and checks URL health."""

import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


def check_url(url: str, timeout: float = 5.0) -> dict[str, Any]:
    """Send a HEAD request to *url* and return its health status.

    Args:
        url: The URL to check.
        timeout: Timeout in seconds for the request.

    Returns:
        A dict with keys:
            - url (str): the URL that was checked.
            - status_code (int | None): HTTP status code, or None on error.
            - response_time_ms (float | None): response time in ms, or None.
            - up (bool): True if status is 2xx or 3xx, False otherwise.
    """
    result: dict[str, Any] = {
        "url": url,
        "status_code": None,
        "response_time_ms": None,
        "up": False,
    }

    try:
        start = time.monotonic()
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        elapsed_ms = (time.monotonic() - start) * 1000

        result["status_code"] = resp.status_code
        result["response_time_ms"] = round(elapsed_ms, 2)
        result["up"] = 200 <= resp.status_code < 400

    except requests.exceptions.Timeout:
        result["up"] = False
    except requests.exceptions.ConnectionError:
        result["up"] = False
    except Exception:
        result["up"] = False

    return result


def check_urls(
    urls: list[str],
    timeout: float = 5.0,
    max_workers: int = 10,
) -> list[dict[str, Any]]:
    """Check multiple URLs concurrently using a thread pool.

    Args:
        urls: List of URLs to check.
        timeout: Timeout per URL in seconds.
        max_workers: Maximum concurrent threads.

    Returns:
        List of result dicts (same shape as returned by check_url).
    """
    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(check_url, url, timeout): url
            for url in urls
        }
        for future in as_completed(future_to_url):
            results.append(future.result())

    # Preserve original order
    url_order = {url: i for i, url in enumerate(urls)}
    results.sort(key=lambda r: url_order.get(r["url"], 0))

    return results
