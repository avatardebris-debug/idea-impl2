"""SQLite database engine with migration system for BudgetFlow Tracker."""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "budgetflow_tracker.db")


class DatabaseError(Exception):
    """Raised when a database operation fails."""
    pass


class Database:
    """SQLite database engine with WAL mode and migration support."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_db_dir()
        self._connection: sqlite3.Connection | None = None

    def _ensure_db_dir(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                timeout=30,
                isolation_level=None,  # Autocommit mode
            )
            self._connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._connection.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys=ON")
            # Increase page size for performance
            self._connection.execute("PRAGMA page_size=4096")
            # Enable WAL checkpoint auto
            self._connection.execute("PRAGMA wal_autocheckpoint=1000")
            logger.info("Database connection opened: %s", self.db_path)
        return self._connection

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager for database cursor operations."""
        conn = self.connection
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}") from e
        finally:
            cursor.close()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL statement and return the cursor."""
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        self.connection.commit()
        return cursor

    def executemany(self, sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        cursor = self.connection.cursor()
        cursor.executemany(sql, params_list)
        self.connection.commit()
        return cursor

    def fetchone(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        """Execute a query and return one row."""
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        cursor.close()
        return row

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Execute a query and return all rows."""
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def init_schema(self):
        """Initialize the database schema with all tables and indexes."""
        self._create_tables()
        self._create_indexes()
        logger.info("Database schema initialized")

    def _create_tables(self):
        """Create all database tables."""
        self.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL DEFAULT 'checking',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                is_income INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                parent_id INTEGER,
                FOREIGN KEY (parent_id) REFERENCES categories(id)
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL DEFAULT 'debit',
                category_id INTEGER,
                category_name TEXT,
                account_id INTEGER,
                merchant TEXT,
                confidence REAL,
                is_reconciled INTEGER NOT NULL DEFAULT 0,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                category_name TEXT NOT NULL,
                amount REAL NOT NULL,
                period TEXT NOT NULL CHECK (period IN ('monthly', 'weekly')),
                start_date TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                rollover INTEGER NOT NULL DEFAULT 0,
                rollover_amount REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS transaction_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                pattern TEXT NOT NULL,
                pattern_type TEXT NOT NULL DEFAULT 'contains' CHECK (pattern_type IN ('contains', 'regex', 'exact')),
                category_id INTEGER NOT NULL,
                category_name TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                confidence REAL NOT NULL DEFAULT 0.8,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

    def _create_indexes(self):
        """Create indexes for performance."""
        self.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON transactions(merchant)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_budgets_category ON budgets(category_id)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(period)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_budgets_active ON budgets(is_active)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_rules_active ON transaction_rules(is_active)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_rules_priority ON transaction_rules(priority)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active)")

    def seed_default_data(self):
        """Seed the database with default categories and rules."""
        # Check if already seeded
        count = self.fetchone("SELECT COUNT(*) FROM categories")
        if count and count[0] > 0:
            logger.info("Database already has data, skipping seed")
            return

        # Default categories
        default_categories = [
            ("Food & Drink", "Groceries, restaurants, dining out", 0),
            ("Transportation", "Gas, transit, rideshare, parking", 0),
            ("Shopping", "Retail purchases, online shopping", 0),
            ("Entertainment", "Movies, streaming, events, hobbies", 0),
            ("Bills & Utilities", "Electric, water, internet, phone bills", 0),
            ("Healthcare", "Medical expenses, prescriptions, insurance", 0),
            ("Income", "Salary, freelance, investment income", 1),
            ("Other", "Miscellaneous transactions", 0),
        ]

        self.executemany(
            "INSERT INTO categories (name, description, is_income) VALUES (?, ?, ?)",
            [(name, desc, inc) for name, desc, inc in default_categories]
        )

        # Get category IDs
        cat_map = {}
        for name, _, _ in default_categories:
            row = self.fetchone("SELECT id FROM categories WHERE name = ?", (name,))
            cat_map[name] = row["id"]

        # Default categorization rules (20+)
        default_rules = [
            # Food & Drink rules
            ("Grocery Store Match", "Any grocery store", "grocery", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.9),
            ("Whole Foods", "Whole Foods Market", "whole foods", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.95),
            ("Trader Joe's", "Trader Joe's", "trader joe", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.95),
            ("Walmart Grocery", "Walmart grocery", "walmart grocery", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.9),
            ("Safeway", "Safeway grocery", "safeway", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.95),
            ("Kroger", "Kroger grocery", "kroger", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.95),
            ("Restaurant General", "Restaurant transactions", "restaurant", "contains", cat_map["Food & Drink"], "Food & Drink", 5, 0.7),
            ("Starbucks", "Starbucks coffee", "starbucks", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.95),
            ("McDonald's", "McDonald's", "mcdonald", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.95),
            ("Subway", "Subway sandwich shop", "subway", "contains", cat_map["Food & Drink"], "Food & Drink", 10, 0.95),
            # Transportation rules
            ("Gas Station", "Gas station transactions", "gas station", "contains", cat_map["Transportation"], "Transportation", 5, 0.7),
            ("Shell Gas", "Shell gas station", "shell", "contains", cat_map["Transportation"], "Transportation", 10, 0.9),
            ("Uber", "Uber rides", "uber", "contains", cat_map["Transportation"], "Transportation", 10, 0.95),
            ("Lyft", "Lyft rides", "lyft", "contains", cat_map["Transportation"], "Transportation", 10, 0.95),
            ("Transit", "Public transit", "transit", "contains", cat_map["Transportation"], "Transportation", 10, 0.9),
            ("MTA", "MTA subway/bus", "mta", "contains", cat_map["Transportation"], "Transportation", 10, 0.95),
            # Shopping rules
            ("Amazon", "Amazon purchases", "amazon", "contains", cat_map["Shopping"], "Shopping", 10, 0.95),
            ("Target", "Target store", "target", "contains", cat_map["Shopping"], "Shopping", 10, 0.95),
            ("Walmart", "Walmart store", "walmart", "contains", cat_map["Shopping"], "Shopping", 10, 0.95),
            ("Best Buy", "Best Buy electronics", "best buy", "contains", cat_map["Shopping"], "Shopping", 10, 0.95),
            # Bills & Utilities rules
            ("Electric Company", "Electric bill", "electric", "contains", cat_map["Bills & Utilities"], "Bills & Utilities", 5, 0.7),
            ("Water Company", "Water bill", "water", "contains", cat_map["Bills & Utilities"], "Bills & Utilities", 5, 0.7),
            ("Internet Provider", "Internet bill", "internet", "contains", cat_map["Bills & Utilities"], "Bills & Utilities", 5, 0.7),
            ("Phone Company", "Phone bill", "phone", "contains", cat_map["Bills & Utilities"], "Bills & Utilities", 5, 0.7),
            ("Netflix", "Netflix subscription", "netflix", "contains", cat_map["Bills & Utilities"], "Bills & Utilities", 10, 0.95),
            ("Spotify", "Spotify subscription", "spotify", "contains", cat_map["Bills & Utilities"], "Bills & Utilities", 10, 0.95),
            ("Insurance Payment", "Insurance premium", "insurance", "contains", cat_map["Bills & Utilities"], "Bills & Utilities", 5, 0.7),
            # Healthcare rules
            ("CVS Pharmacy", "CVS pharmacy", "cvs pharmacy", "contains", cat_map["Healthcare"], "Healthcare", 10, 0.95),
            ("Walgreens", "Walgreens pharmacy", "walgreens", "contains", cat_map["Healthcare"], "Healthcare", 10, 0.95),
            ("Hospital", "Hospital expenses", "hospital", "contains", cat_map["Healthcare"], "Healthcare", 10, 0.9),
            ("Doctor Office", "Doctor/medical office", "doctor", "contains", cat_map["Healthcare"], "Healthcare", 10, 0.9),
            # Income rules
            ("Direct Deposit", "Direct deposit income", "direct deposit", "contains", cat_map["Income"], "Income", 10, 0.95),
            ("Payroll", "Payroll income", "payroll", "contains", cat_map["Income"], "Income", 10, 0.95),
            ("Freelance Payment", "Freelance income", "freelance", "contains", cat_map["Income"], "Income", 10, 0.9),
            ("Refund", "Refund income", "refund", "contains", cat_map["Income"], "Income", 5, 0.7),
            ("Interest Income", "Interest earnings", "interest", "contains", cat_map["Income"], "Income", 5, 0.7),
            ("Dividend", "Dividend income", "dividend", "contains", cat_map["Income"], "Income", 5, 0.7),
            ("Transfer In", "Transfer in income", "transfer in", "contains", cat_map["Income"], "Income", 5, 0.6),
        ]

        self.executemany(
            """INSERT INTO transaction_rules
               (name, description, pattern, pattern_type, category_id, category_name, priority, is_active, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
            [(name, desc, pat, ptype, cat_id, cat_name, pri, conf)
             for name, desc, pat, ptype, cat_id, cat_name, pri, conf in default_rules]
        )

        logger.info("Seeded %d categories and %d rules", len(default_categories), len(default_rules))


# Module-level singleton
_db_instance: Database | None = None


def get_database(db_path: str | None = None) -> Database:
    """Get or create the database singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
        _db_instance.init_schema()
        _db_instance.seed_default_data()
    return _db_instance


def reset_database(db_path: str | None = None):
    """Reset the database (for testing)."""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None
    if db_path and os.path.exists(db_path):
        os.remove(db_path)
