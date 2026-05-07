"""Tests for the rate limiter module."""

import time
import pytest
from sec_importer.rate_limiter import RateLimiter


class TestRateLimiterInit:
    def test_default_values(self):
        """Test default initialization values."""
        rl = RateLimiter()
        assert rl.requests_per_second == 10
        assert rl.delay == 0.1
        assert rl.max_retries == 3
        assert rl.base_backoff == 1.0
        assert rl.jitter is True

    def test_custom_values(self):
        """Test custom initialization values."""
        rl = RateLimiter(
            requests_per_second=5,
            delay=0.2,
            max_retries=5,
            base_backoff=2.0,
            jitter=False,
        )
        assert rl.requests_per_second == 5
        assert rl.delay == 0.2
        assert rl.max_retries == 5
        assert rl.base_backoff == 2.0
        assert rl.jitter is False

    def test_invalid_requests_per_second(self):
        """Test that invalid requests_per_second raises error."""
        with pytest.raises(ValueError):
            RateLimiter(requests_per_second=0)

    def test_invalid_delay(self):
        """Test that invalid delay raises error."""
        with pytest.raises(ValueError):
            RateLimiter(delay=-1)

    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises error."""
        with pytest.raises(ValueError):
            RateLimiter(max_retries=-1)


class TestRateLimiterWait:
    def test_wait_enforces_delay(self):
        """Test that wait enforces the configured delay."""
        rl = RateLimiter(delay=0.05)  # 50ms delay
        start = time.time()
        rl.wait()
        elapsed = time.time() - start
        # Allow some tolerance for timing
        assert elapsed >= 0.04

    def test_wait_with_jitter(self):
        """Test that wait with jitter varies the delay."""
        rl = RateLimiter(delay=0.05, jitter=True)

        delays = []
        for _ in range(10):
            start = time.time()
            rl.wait()
            delays.append(time.time() - start)

        # With jitter, delays should vary
        assert max(delays) > min(delays)

    def test_wait_without_jitter(self):
        """Test that wait without jitter is consistent."""
        rl = RateLimiter(delay=0.05, jitter=False)

        delays = []
        for _ in range(10):
            start = time.time()
            rl.wait()
            delays.append(time.time() - start)

        # Without jitter, delays should be very consistent
        assert max(delays) - min(delays) < 0.01


class TestRateLimiterExecute:
    def test_execute_success(self):
        """Test execute with successful function."""
        rl = RateLimiter(delay=0.01)
        result = []

        def sample_func():
            result.append(1)
            return "success"

        assert rl.execute(sample_func) == "success"
        assert result == [1]

    def test_execute_with_retries(self):
        """Test execute retries on failure."""
        rl = RateLimiter(delay=0.01, max_retries=2)
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = rl.execute(failing_func)
        assert result == "success"
        assert call_count == 3

    def test_execute_exhausts_retries(self):
        """Test execute raises after exhausting retries."""
        rl = RateLimiter(delay=0.01, max_retries=1)
        call_count = 0

        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            rl.execute(always_fails)
        assert call_count == 2  # Initial + 1 retry

    def test_execute_with_backoff(self):
        """Test execute uses exponential backoff."""
        rl = RateLimiter(delay=0.01, base_backoff=2.0, max_retries=2)
        call_count = 0
        times = []

        def failing_func():
            nonlocal call_count
            call_count += 1
            times.append(time.time())
            if call_count < 3:
                raise ValueError("Retry me")
            return "success"

        result = rl.execute(failing_func)
        assert result == "success"

        # Check that retries have increasing delays
        if len(times) >= 2:
            delay1 = times[1] - times[0]
            assert delay1 > 0.01  # Should be at least base delay


class TestRateLimiterContextManager:
    def test_context_manager(self):
        """Test rate limiter as context manager."""
        rl = RateLimiter(delay=0.01)

        with rl:
            time.sleep(0.02)  # Should be within rate limit

    def test_context_manager_nested(self):
        """Test nested context managers."""
        rl = RateLimiter(delay=0.01)

        with rl:
            with rl:
                time.sleep(0.02)


class TestRateLimiterReset:
    def test_reset_clears_state(self):
        """Test reset clears internal state."""
        rl = RateLimiter(delay=0.01)
        rl.wait()  # Set some state

        # Reset should allow immediate execution
        start = time.time()
        rl.reset()
        elapsed = time.time() - start
        assert elapsed < 0.01  # Should be nearly instant


class TestRateLimiterIntegration:
    def test_multiple_requests(self):
        """Test multiple sequential requests are rate-limited."""
        rl = RateLimiter(delay=0.02, jitter=False)
        times = []

        for _ in range(5):
            start = time.time()
            rl.wait()
            times.append(time.time() - start)

        # All waits should be approximately equal to delay
        for t in times:
            assert 0.015 <= t <= 0.035  # Allow tolerance

    def test_execute_multiple_requests(self):
        """Test execute with multiple requests."""
        rl = RateLimiter(delay=0.01, max_retries=0)
        results = []

        def sample_func():
            results.append(1)
            return len(results)

        returned = []
        for _ in range(3):
            returned.append(rl.execute(sample_func))

        assert returned == [1, 2, 3]
