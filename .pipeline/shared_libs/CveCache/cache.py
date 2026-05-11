"""SQLite-based CVE cache with TTL expiration."""
import json
import os
import sqlite3
import time
from typing import Any


class CveCache:
    """TTL-based SQLite cache for CVE query results."""

    def __init__(self, db_path: str, ttl: int = 3600):
        """
        Args:
            db_path: Path to the SQLite database file.
            ttl: Time-to-live in seconds (default 1 hour).
        """
        self.db_path = db_path
        self.ttl = ttl
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cve_cache (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            conn.commit()

    def get(self, key: str) -> Any | None:
        """Return cached data if present and not expired, else None."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data, expires_at FROM cve_cache WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        data, expires_at = row
        if time.time() < expires_at:
            return json.loads(data)
        return None

    def set(self, key: str, data: Any):
        """Store data with current time + TTL."""
        expires_at = time.time() + self.ttl
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cve_cache (key, data, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(data), expires_at),
            )
            conn.commit()

    def invalidate(self, key: str):
        """Remove a specific cache entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cve_cache WHERE key = ?", (key,))
            conn.commit()
