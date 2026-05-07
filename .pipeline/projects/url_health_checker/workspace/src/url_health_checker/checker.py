"""Core URLChecker class that sends HEAD requests and reports health status."""

import logging
import time
from typing import Dict, Optional

import requests


class URLChecker:
    """Check the health of a single URL via HEAD request.

    Attributes:
        timeout: Request timeout in seconds (default 10).
        max_attempts: Maximum number of attempts per URL (default 1).
        retry_delay: Seconds to wait between retry attempts (default 1).
        logger: Optional logger instance for structured logging.
    """

    def __init__(
        self,
        timeout: int = 10,
        max_attempts: int = 1,
        retry_delay: float = 1.0,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.retry_delay = retry_delay
        self.logger = logger

    def check(self, url: str) -> Dict:
        """Send a HEAD request to *url* and return a result dict.

        Retries up to *max_attempts* times on ConnectionError or Timeout.

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

        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                session = requests.Session()
                session.headers.update({"User-Agent": "URLHealthChecker/0.1.0"})
                start = time.time()
                response = session.head(url, timeout=self.timeout, allow_redirects=True)
                elapsed_ms = response.elapsed.total_seconds() * 1000
                result["status_code"] = response.status_code
                result["response_time_ms"] = round(elapsed_ms, 2)
                result["is_up"] = 200 <= response.status_code < 300

                # Log success
                if self.logger:
                    from .logging_config import log_check_result
                    log_check_result(
                        self.logger,
                        url,
                        result["status_code"],
                        result["response_time_ms"],
                        result["is_up"],
                        level="INFO",
                    )

                return result

            except requests.exceptions.Timeout as exc:
                last_exception = exc
                if self.logger:
                    from .logging_config import log_error
                    log_error(self.logger, url, exc)
            except requests.exceptions.ConnectionError as exc:
                last_exception = exc
                if self.logger:
                    from .logging_config import log_error
                    log_error(self.logger, url, exc)
            except requests.exceptions.RequestException as exc:
                last_exception = exc
                if self.logger:
                    from .logging_config import log_error
                    log_error(self.logger, url, exc)
            except Exception as exc:
                last_exception = exc
                if self.logger:
                    from .logging_config import log_error
                    log_error(self.logger, url, exc)

            # Retry if attempts remain
            if attempt < self.max_attempts:
                time.sleep(self.retry_delay)

        # All attempts exhausted
        if self.logger:
            from .logging_config import log_check_result
            log_check_result(
                self.logger,
                url,
                result["status_code"],
                result["response_time_ms"],
                result["is_up"],
                level="ERROR",
            )

        return result
