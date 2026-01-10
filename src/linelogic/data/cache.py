"""
SQLite-backed cache for API responses.

Caches responses to minimize API calls and costs.
"""

import hashlib
import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from tempfile import gettempdir

from linelogic.config.settings import settings

logger = logging.getLogger("linelogic.cache")


class Cache:
    """
    Simple SQLite-backed cache with TTL support.

    Cache key format: {provider}:{endpoint}:{params_hash}
    """

    def __init__(self, db_path: str | None = None, default_ttl: int = 86400):
        """
        Initialize cache.

        Args:
            db_path: Path to cache SQLite database
            default_ttl: Default TTL in seconds (default: 24 hours)
        """
        # Use configured cache path by default; fall back to a temp-backed DB for tests
        if db_path is None:
            configured_path = settings.cache_db_path or ""
            if configured_path:
                db_path = configured_path
            else:
                db_path = str(
                    Path(gettempdir()) / f"linelogic-cache-{uuid.uuid4().hex}.db"
                )

        self.db_path = db_path
        self.default_ttl = default_ttl

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Create cache table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                fetched_at REAL NOT NULL,
                ttl_seconds INTEGER NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

    def _make_key(self, provider: str, endpoint: str, params: dict) -> str:
        """
        Generate cache key from provider, endpoint, and params.

        Args:
            provider: Provider name (e.g., "balldontlie")
            endpoint: Endpoint name (e.g., "players")
            params: Query parameters dict

        Returns:
            Cache key string
        """
        # Sort params for consistent hashing
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

        return f"{provider}:{endpoint}:{params_hash}"

    def get(
        self, provider: str, endpoint: str, params: dict | None = None
    ) -> dict | None:
        """
        Get cached response.

        Args:
            provider: Provider name
            endpoint: Endpoint name
            params: Query parameters dict (default: {})

        Returns:
            Cached response dict or None if not found or expired
        """
        if params is None:
            params = {}

        key = self._make_key(provider, endpoint, params)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT value, fetched_at, ttl_seconds FROM cache WHERE key = ?",
            (key,),
        )

        row = cursor.fetchone()
        conn.close()

        if row is None:
            logger.debug(f"Cache MISS: {provider}/{endpoint}")
            return None

        value_str, fetched_at, ttl_seconds = row

        # Check if expired
        if time.time() - fetched_at > ttl_seconds:
            # Expired, delete and return None
            logger.debug(f"Cache EXPIRED: {provider}/{endpoint}")
            self.delete(provider, endpoint, params)
            return None

        logger.debug(f"Cache HIT: {provider}/{endpoint}")
        return json.loads(value_str)

    def set(
        self,
        provider: str,
        endpoint: str,
        params: dict | None,
        value: dict,
        ttl: int | None = None,
    ) -> None:
        """
        Store response in cache.

        Args:
            provider: Provider name
            endpoint: Endpoint name
            params: Query parameters dict (default: {})
            value: Response dict to cache
            ttl: TTL in seconds (default: use default_ttl)
        """
        if params is None:
            params = {}

        if ttl is None:
            ttl = self.default_ttl

        key = self._make_key(provider, endpoint, params)
        value_str = json.dumps(value)
        fetched_at = time.time()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO cache (key, value, fetched_at, ttl_seconds)
            VALUES (?, ?, ?, ?)
            """,
            (key, value_str, fetched_at, ttl),
        )

        conn.commit()
        conn.close()

    def delete(self, provider: str, endpoint: str, params: dict | None = None) -> None:
        """
        Delete cached response.

        Args:
            provider: Provider name
            endpoint: Endpoint name
            params: Query parameters dict (default: {})
        """
        if params is None:
            params = {}

        key = self._make_key(provider, endpoint, params)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))

        conn.commit()
        conn.close()

    def clear(self) -> None:
        """Clear all cached responses."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM cache")

        conn.commit()
        conn.close()

    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.

        Returns:
            Number of entries deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = time.time()

        cursor.execute(
            "DELETE FROM cache WHERE fetched_at + ttl_seconds < ?",
            (current_time,),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted
