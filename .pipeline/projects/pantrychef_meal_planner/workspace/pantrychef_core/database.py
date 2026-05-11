"""Database module with SQLite connection management."""

import sqlite3
from contextlib import contextmanager
from typing import Optional


class Database:
    """Manages SQLite connections with context manager support."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection. For in-memory databases, reuse the connection."""
        if self.db_path == ":memory:" and self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        elif self._conn is not None:
            return self._conn
        else:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    @contextmanager
    def get_connection_ctx(self):
        """Context manager for database connections."""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            pass  # Don't close — the connection is managed by the Database instance

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
