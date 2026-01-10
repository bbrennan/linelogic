"""
Tests for rate limiter functionality.
"""

import time

import pytest

from linelogic.data.rate_limit import RateLimiter


class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_rate_limiter_single_request(self):
        limiter = RateLimiter(requests_per_minute=60)  # 1 per second
        assert limiter.acquire(blocking=False) is True

    def test_rate_limiter_multiple_requests(self):
        limiter = RateLimiter(requests_per_minute=60)  # 1 per second

        # First request should succeed
        assert limiter.acquire(blocking=False) is True

        # Immediate second request should fail (no token)
        assert limiter.acquire(blocking=False) is False

        # Wait for token refill
        time.sleep(1.1)

        # Should succeed after refill
        assert limiter.acquire(blocking=False) is True

    def test_rate_limiter_blocking(self):
        limiter = RateLimiter(requests_per_minute=60)  # 1 per second

        # First request
        limiter.acquire(blocking=True)

        # Second request should block until token available
        start = time.time()
        limiter.acquire(blocking=True)
        elapsed = time.time() - start

        # Should have waited ~1 second
        assert elapsed >= 0.9  # Allow some margin

    def test_rate_limiter_burst(self):
        limiter = RateLimiter(requests_per_minute=120)  # 2 per second

        # Should allow 2 requests immediately
        assert limiter.acquire(blocking=False) is True
        assert limiter.acquire(blocking=False) is True

        # Third should fail
        assert limiter.acquire(blocking=False) is False

    def test_rate_limiter_get_available_tokens(self):
        limiter = RateLimiter(requests_per_minute=60)

        # Initially should have full tokens
        assert limiter.get_available_tokens() == pytest.approx(60.0, abs=0.1)

        # After one request
        limiter.acquire(blocking=False)
        assert limiter.get_available_tokens() == pytest.approx(59.0, abs=0.1)

    def test_rate_limiter_reset(self):
        limiter = RateLimiter(requests_per_minute=60)

        # Consume all tokens
        limiter.acquire(blocking=False)
        for _ in range(60):
            limiter.acquire(blocking=False)

        # Should be depleted
        assert limiter.get_available_tokens() < 1.0

        # Reset
        limiter.reset()

        # Should be full again
        assert limiter.get_available_tokens() == pytest.approx(60.0, abs=0.1)
