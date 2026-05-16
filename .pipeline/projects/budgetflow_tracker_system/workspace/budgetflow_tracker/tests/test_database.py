"""Tests for the database module."""

import os
import sys
import tempfile
import pytest

# Add workspace to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import Database, get_database, reset_database


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    # WAL mode creates -wal and -shm sidecar files; remove them all
    for suffix in ('', '-wal', '-shm'):
        p = path + suffix
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass  # best-effort on Windows


@pytest.fixture
def db(temp_db_path):
    """Create a fresh database instance."""
    instance = Database(temp_db_path)
    instance.init_schema()
    yield instance
    instance.close()  # ensure connection is released before temp file cleanup


class TestDatabaseSchema:
    """Test database schema creation."""

    def test_tables_created(self, db):
        """Test that all expected tables are created."""
        tables = db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [t['name'] for t in tables]
        assert 'accounts' in table_names
        assert 'categories' in table_names
        assert 'transactions' in table_names
        assert 'budgets' in table_names
        assert 'transaction_rules' in table_names

    def test_indexes_created(self, db):
        """Test that indexes are created."""
        indexes = db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        index_names = [i['name'] for i in indexes]
        assert 'idx_transactions_date' in index_names
        assert 'idx_transactions_category' in index_names
        assert 'idx_budgets_category' in index_names

    def test_foreign_keys_enabled(self, db):
        """Test that foreign keys are enabled."""
        result = db.fetchone("PRAGMA foreign_keys")
        assert result[0] == 1


class TestDatabaseCRUD:
    """Test database CRUD operations."""

    def test_insert_account(self, db):
        """Test inserting an account."""
        db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Checking", "checking")
        )
        row = db.fetchone("SELECT * FROM accounts WHERE name = ?", ("Checking",))
        assert row is not None
        assert row['name'] == 'Checking'
        assert row['account_type'] == 'checking'

    def test_insert_category(self, db):
        """Test inserting a category."""
        db.execute(
            "INSERT INTO categories (name, description, is_income) VALUES (?, ?, ?)",
            ("Test Category", "A test", 0)
        )
        row = db.fetchone("SELECT * FROM categories WHERE name = ?", ("Test Category",))
        assert row is not None
        assert row['name'] == 'Test Category'
        assert row['is_income'] == 0

    def test_insert_transaction(self, db):
        """Test inserting a transaction."""
        # Insert account first
        db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Checking", "checking")
        )
        account_id = db.fetchone("SELECT id FROM accounts WHERE name = ?", ("Checking",))['id']

        db.execute(
            """INSERT INTO transactions 
               (date, description, amount, transaction_type, account_id, merchant)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("2024-01-15", "Grocery Store", -50.0, "debit", account_id, "Grocery Store")
        )
        row = db.fetchone("SELECT * FROM transactions WHERE description = ?", ("Grocery Store",))
        assert row is not None
        assert row['amount'] == -50.0
        assert row['merchant'] == "Grocery Store"

    def test_insert_budget(self, db):
        """Test inserting a budget."""
        db.execute(
            "INSERT INTO categories (name, description, is_income) VALUES (?, ?, ?)",
            ("Food & Drink", "Groceries", 0)
        )
        cat_id = db.fetchone("SELECT id FROM categories WHERE name = ?", ("Food & Drink",))['id']

        db.execute(
            """INSERT INTO budgets (category_id, category_name, amount, period, start_date)
               VALUES (?, ?, ?, ?, ?)""",
            (cat_id, "Food & Drink", 500.0, "monthly", "2024-01-01")
        )
        row = db.fetchone("SELECT * FROM budgets WHERE category_name = ?", ("Food & Drink",))
        assert row is not None
        assert row['amount'] == 500.0
        assert row['period'] == 'monthly'


class TestDatabaseSeeding:
    """Test database seeding."""

    def test_seed_default_data(self, temp_db_path):
        """Test that seeding creates default categories and rules."""
        db = Database(temp_db_path)
        db.init_schema()
        db.seed_default_data()

        categories = db.fetchall("SELECT name FROM categories ORDER BY name")
        assert len(categories) == 8
        category_names = [c['name'] for c in categories]
        assert 'Food & Drink' in category_names
        assert 'Income' in category_names
        assert 'Other' in category_names

        rules = db.fetchall("SELECT name FROM transaction_rules")
        assert len(rules) >= 30  # Should have 30+ rules

    def test_seed_is_idempotent(self, temp_db_path):
        """Test that seeding twice doesn't duplicate data."""
        db = Database(temp_db_path)
        db.init_schema()
        db.seed_default_data()
        db.seed_default_data()  # Second call should be a no-op

        count = db.fetchone("SELECT COUNT(*) FROM categories")
        assert count[0] == 8  # Still 8, not 16


class TestDatabaseSingleton:
    """Test database singleton pattern."""

    def test_get_database_creates_singleton(self, temp_db_path):
        """Test that get_database returns the same instance."""
        reset_database()
        db1 = get_database(temp_db_path)
        db2 = get_database(temp_db_path)
        assert db1 is db2

    def test_reset_database(self, temp_db_path):
        """Test that reset_database works."""
        reset_database()
        db1 = get_database(temp_db_path)
        reset_database()
        db2 = get_database(temp_db_path)
        assert db1 is not db2


class TestDatabaseWAL:
    """Test WAL mode configuration."""

    def test_wal_mode_enabled(self, db):
        """Test that WAL journal mode is enabled."""
        result = db.fetchone("PRAGMA journal_mode")
        assert result[0] == 'wal'
