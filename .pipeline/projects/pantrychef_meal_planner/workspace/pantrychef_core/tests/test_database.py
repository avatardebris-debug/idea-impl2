"""Tests for Database layer."""

import os
import tempfile
from pathlib import Path

import pytest

from pantrychef_core.database import Database


class TestDatabaseInit:
    def test_default_db_path(self):
        """When no db_path is given, should use default DB_NAME."""
        db = Database()
        assert db.db_path == Path(Database.DB_NAME)

    def test_custom_db_path(self):
        """When db_path is given, should use that path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "custom.db")
            db = Database(db_path=path)
            assert db.db_path == Path(path)

    def test_default_db_path_is_none_branch(self):
        """Explicitly test the else branch of __init__ (db_path=None)."""
        db = Database(db_path=None)
        assert db.db_path == Path(Database.DB_NAME)


class TestDatabaseInitDb:
    def test_init_creates_tables(self):
        """init_db should create all expected tables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.db")
            db = Database(db_path=path)
            db.init_db()
            conn = db._get_or_create_conn()
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {t[0] for t in tables}
            assert "pantry_items" in table_names
            assert "recipes" in table_names
            assert "recipe_ingredients" in table_names
            assert "meal_plans" in table_names
            assert "shopping_items" in table_names

    def test_init_db_is_idempotent(self):
        """Calling init_db multiple times should not raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.db")
            db = Database(db_path=path)
            db.init_db()
            db.init_db()  # Should not raise

    def test_init_db_creates_tables_if_not_exist(self):
        """Tables should be created only if they don't exist (IF NOT EXISTS)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.db")
            db = Database(db_path=path)
            db.init_db()
            conn = db._get_or_create_conn()
            # Verify pantry_items table has expected columns
            cols = conn.execute("PRAGMA table_info(pantry_items)").fetchall()
            col_names = {c[1] for c in cols}
            assert "id" in col_names
            assert "name" in col_names
            assert "quantity" in col_names
            assert "unit" in col_names
            assert "category" in col_names
            assert "expiry_date" in col_names


class TestDatabaseGetConnection:
    def test_get_connection_returns_context_manager(self):
        """get_connection should return a context manager yielding a connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.db")
            db = Database(db_path=path)
            db.init_db()
            with db.get_connection() as conn:
                assert conn is not None
                # Should be able to execute queries
                result = conn.execute("SELECT 1").fetchone()
                assert result == (1,)

    def test_connection_is_persistent(self):
        """Multiple get_connection calls should return the same connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.db")
            db = Database(db_path=path)
            db.init_db()
            conn1 = db._get_or_create_conn()
            conn2 = db._get_or_create_conn()
            assert conn1 is conn2

    def test_get_connection_with_no_init(self):
        """get_connection should work even if init_db hasn't been called."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.db")
            db = Database(db_path=path)
            with db.get_connection() as conn:
                result = conn.execute("SELECT 1").fetchone()
                assert result == (1,)


class TestDatabasePersistence:
    def test_data_persists_across_context_manager_exits(self):
        """Data inserted in one context should be visible in another."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.db")
            db = Database(db_path=path)
            db.init_db()
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO pantry_items (name, quantity, unit, category) VALUES (?, ?, ?, ?)",
                    ("TestItem", 1.0, "kg", "test"),
                )
                conn.commit()
            with db.get_connection() as conn:
                row = conn.execute("SELECT name FROM pantry_items").fetchone()
                assert row == ("TestItem",)
