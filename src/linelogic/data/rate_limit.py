"""
Rate limiter using token bucket algorithm.

Prevents exceeding API rate limits.
"""

import time
from threading import Lock


class RateLimiter:
    """
    Token bucket rate limiter.

    Tokens are added at a fixed rate. Each request consumes one token.
    If no tokens are available, request is blocked until token is available.
    """

    def __init__(self, requests_per_minute: int):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens = float(requests_per_minute)
        self.max_tokens = float(requests_per_minute)
        self.last_update = time.time()
        self.lock = Lock()

        # Calculate token refill rate (tokens per second)
        self.refill_rate = requests_per_minute / 60.0

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_update = now

    def acquire(self, blocking: bool = True) -> bool:
        """
        Acquire a token (consume one request).

        Args:
            blocking: If True, block until token available. If False, return immediately.

        Returns:
            True if token acquired, False if not available (only when blocking=False)
        """
        with self.lock:
            self._refill_tokens()

            if self.tokens >= 1:
                self.tokens -= 1
                return True

            if not blocking:
                return False

            # Calculate wait time until next token is available
            wait_time = (1 - self.tokens) / self.refill_rate
            time.sleep(wait_time)

            # Try again after waiting
            self._refill_tokens()
            if self.tokens >= 1:
                self.tokens -= 1
                return True

            # Should never reach here, but handle edge case
            return False

    def get_available_tokens(self) -> float:
        """
        Get current number of available tokens.

        Returns:
            Number of tokens available (may be fractional)
        """
        with self.lock:
            self._refill_tokens()
            return self.tokens

    def reset(self) -> None:
        """Reset rate limiter to full capacity."""
        with self.lock:
            self.tokens = self.max_tokens
            self.last_update = time.time()
