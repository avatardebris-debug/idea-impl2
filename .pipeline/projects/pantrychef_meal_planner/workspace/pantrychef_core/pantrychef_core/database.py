"""SQLite database layer for PantryChef Core."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    """SQLite database helper with schema-on-first-write."""

    DB_NAME = "pantrychef.db"

    def __init__(self, db_path: str | None = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(self.DB_NAME)
        self._conn: sqlite3.Connection | None = None

    def _get_or_create_conn(self) -> sqlite3.Connection:
        """Return a persistent connection (reuse for in-memory)."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
        return self._conn

    def init_db(self) -> None:
        """Create all tables if they don't exist."""
        conn = self._get_or_create_conn()
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
        """Return a live connection as a context manager."""
        conn = self._get_or_create_conn()
        try:
            yield conn
        finally:
            pass  # Don't close the persistent connection
