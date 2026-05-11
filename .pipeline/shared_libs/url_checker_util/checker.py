"""Core URL checking logic."""

import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_url(url, timeout=10):
    """Check a single URL via HEAD request.

    Args:
        url: The URL to check.
        timeout: Request timeout in seconds (default: 10).

    Returns:
        dict with keys: url, status_code, response_time_ms, is_up
    """
    result = {
        "url": url,
        "status_code": None,
        "response_time_ms": None,
        "is_up": False,
    }
    try:
        start = time.time()
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        elapsed_ms = (time.time() - start) * 1000
        result["status_code"] = response.status_code
        result["response_time_ms"] = round(elapsed_ms, 2)
        result["is_up"] = 200 <= response.status_code < 400
    except requests.exceptions.Timeout:
        result["is_up"] = False
        result["status_code"] = None
        result["response_time_ms"] = None
    except requests.exceptions.ConnectionError:
        result["is_up"] = False
        result["status_code"] = None
        result["response_time_ms"] = None
    except Exception:
        result["is_up"] = False
        result["status_code"] = None
        result["response_time_ms"] = None
    return result


def check_urls(urls, timeout=10, max_workers=10):
    """Check multiple URLs concurrently.

    Args:
        urls: List of URL strings.
        timeout: Timeout per request in seconds.
        max_workers: Max concurrent threads.

    Returns:
        List of result dicts from check_url.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(check_url, url, timeout): url for url in urls
        }
        for future in as_completed(future_to_url):
            results.append(future.result())
    # Return results in the same order as input
    url_index = {url: i for i, url in enumerate(urls)}
    results.sort(key=lambda r: url_index[r["url"]])
    return results
