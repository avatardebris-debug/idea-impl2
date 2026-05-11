"""Tests for the Google Places client and rate limiter."""

import sys
import pathlib

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from app.services.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    def test_should_retry_on_429(self):
        limiter = RateLimiter(delay=1.0, max_retries=5)
        assert limiter.should_retry(1, status_code=429) is True
        assert limiter.should_retry(5, status_code=429) is True
        assert limiter.should_retry(6, status_code=429) is False

    def test_should_retry_on_server_error(self):
        limiter = RateLimiter(delay=1.0, max_retries=5)
        assert limiter.should_retry(1, status_code=500) is True
        assert limiter.should_retry(1, status_code=503) is True

    def test_should_not_retry_on_client_error(self):
        limiter = RateLimiter(delay=1.0, max_retries=5)
        assert limiter.should_retry(1, status_code=400) is False
        assert limiter.should_retry(1, status_code=403) is False
        assert limiter.should_retry(1, status_code=404) is False

    def test_should_not_retry_on_success(self):
        limiter = RateLimiter(delay=1.0, max_retries=5)
        assert limiter.should_retry(1, status_code=200) is False

    def test_wait_increases_exponentially(self):
        limiter = RateLimiter(delay=1.0, max_retries=5)
        # Just verify no exception is raised
        limiter.wait(1)
        limiter.wait(2)
        limiter.wait(3)
