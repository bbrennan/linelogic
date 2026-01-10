"""
Tests for cache functionality.
"""

import tempfile
import time
from pathlib import Path

import pytest

from linelogic.data.cache import Cache


@pytest.fixture
def temp_cache():
    """Create a temporary cache for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "test_cache.db"
        yield Cache(str(cache_path), default_ttl=2)


class TestCache:
    """Test cache functionality."""

    def test_cache_set_and_get(self, temp_cache):
        # Set a value
        temp_cache.set(
            "test_provider", "test_endpoint", {"param": "value"}, {"data": "result"}
        )

        # Get the value
        result = temp_cache.get("test_provider", "test_endpoint", {"param": "value"})
        assert result == {"data": "result"}

    def test_cache_miss(self, temp_cache):
        result = temp_cache.get("test_provider", "nonexistent", {})
        assert result is None

    def test_cache_ttl_expiration(self, temp_cache):
        # Set with 1 second TTL
        temp_cache.set("test_provider", "test_endpoint", {}, {"data": "result"}, ttl=1)

        # Should be cached immediately
        result = temp_cache.get("test_provider", "test_endpoint", {})
        assert result == {"data": "result"}

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        result = temp_cache.get("test_provider", "test_endpoint", {})
        assert result is None

    def test_cache_different_params(self, temp_cache):
        # Set two different values with different params
        temp_cache.set("provider", "endpoint", {"param": "a"}, {"data": "a"})
        temp_cache.set("provider", "endpoint", {"param": "b"}, {"data": "b"})

        # Both should be cached separately
        assert temp_cache.get("provider", "endpoint", {"param": "a"}) == {"data": "a"}
        assert temp_cache.get("provider", "endpoint", {"param": "b"}) == {"data": "b"}

    def test_cache_delete(self, temp_cache):
        temp_cache.set("provider", "endpoint", {}, {"data": "result"})
        assert temp_cache.get("provider", "endpoint", {}) == {"data": "result"}

        temp_cache.delete("provider", "endpoint", {})
        assert temp_cache.get("provider", "endpoint", {}) is None

    def test_cache_clear(self, temp_cache):
        temp_cache.set("provider1", "endpoint1", {}, {"data": "1"})
        temp_cache.set("provider2", "endpoint2", {}, {"data": "2"})

        temp_cache.clear()

        assert temp_cache.get("provider1", "endpoint1", {}) is None
        assert temp_cache.get("provider2", "endpoint2", {}) is None

    def test_cache_cleanup_expired(self, temp_cache):
        # Set with short TTL
        temp_cache.set("provider", "endpoint1", {}, {"data": "1"}, ttl=1)
        temp_cache.set("provider", "endpoint2", {}, {"data": "2"}, ttl=100)

        # Wait for first to expire
        time.sleep(1.5)

        # Cleanup
        deleted = temp_cache.cleanup_expired()
        assert deleted == 1

        # Only the second should remain
        assert temp_cache.get("provider", "endpoint1", {}) is None
        assert temp_cache.get("provider", "endpoint2", {}) == {"data": "2"}
