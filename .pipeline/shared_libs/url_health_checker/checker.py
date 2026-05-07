"""Core URLChecker class that sends HEAD requests and reports health status."""

import requests
from typing import Dict, Optional


class URLChecker:
    """Check the health of a single URL via HEAD request.

    Attributes:
        timeout: Request timeout in seconds (default 10).
    """

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def check(self, url: str) -> Dict:
        """Send a HEAD request to *url* and return a result dict.

        The returned dict always has keys:
            - url (str)
            - status_code (int | None)
            - response_time_ms (float | None)
            - is_up (bool)

        A URL is considered "up" when the response status code is in the
        2xx range.  Connection errors, timeouts, and other exceptions
        result in ``status_code=None``, ``response_time_ms=None``, and
        ``is_up=False``.
        """
        result: Dict = {
            "url": url,
            "status_code": None,
            "response_time_ms": None,
            "is_up": False,
        }

        try:
            session = requests.Session()
            session.headers.update({"User-Agent": "URLHealthChecker/0.1.0"})
            response = session.head(url, timeout=self.timeout, allow_redirects=True)
            elapsed_ms = response.elapsed.total_seconds() * 1000 if response.elapsed else None
            result["status_code"] = response.status_code
            result["response_time_ms"] = round(elapsed_ms, 2) if elapsed_ms is not None else None
            result["is_up"] = 200 <= response.status_code < 300
        except requests.exceptions.Timeout:
            result["is_up"] = False
        except requests.exceptions.ConnectionError:
            result["is_up"] = False
        except requests.exceptions.RequestException:
            result["is_up"] = False
        except Exception:
            result["is_up"] = False

        return result
