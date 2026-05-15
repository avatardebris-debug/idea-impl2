"""SQLite database layer for PantryChef Core."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    """SQLite database helper with schema-on-first-write.

    Connections are opened on-demand and closed after each context manager
    exit so that temporary files can be deleted on Windows without hitting
    a PermissionError from an open file handle.
    """

    DB_NAME = "pantrychef.db"

    def __init__(self, db_path: str | None = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(self.DB_NAME)
        # Persistent connection used only for in-memory DBs or when explicitly
        # held via __enter__/__exit__.  File-backed DBs use short-lived
        # connections inside get_connection() by default.
        self._conn: sqlite3.Connection | None = None

    def _get_or_create_conn(self) -> sqlite3.Connection:
        """Return a persistent connection (reuse the same object)."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
        return self._conn

    def init_db(self) -> None:
        """Create all tables if they don't exist."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pantry_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    category TEXT NOT NULL,
                    expiry_date TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    servings INTEGER NOT NULL,
                    prep_time INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recipe_ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meal_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    meal_type TEXT NOT NULL,
                    recipe_id INTEGER NOT NULL,
                    recipe_name TEXT NOT NULL,
                    servings INTEGER NOT NULL,
                    score REAL NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS shopping_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    source_recipe_ids TEXT NOT NULL
                )
            """)
            conn.commit()

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Open a connection, yield it, then close it.

        Using short-lived connections ensures the file handle is released
        immediately, which is required for Windows temp-dir cleanup.

        For in-memory databases, reuse the persistent ``_conn`` so that
        data is not lost between calls.
        """
        if str(self.db_path) == ":memory:":
            # In-memory: must reuse the same connection
            conn = self._get_or_create_conn()
            yield conn
        else:
            conn = sqlite3.connect(str(self.db_path))
            try:
                yield conn
            finally:
                conn.close()

    def close(self) -> None:
        """Close any persistent connection held by this instance."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
