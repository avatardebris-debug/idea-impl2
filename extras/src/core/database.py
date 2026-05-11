"""Database module for BudgetFlow Tracker."""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Optional

from src.core.default_categories import DEFAULT_CATEGORIES

logger = logging.getLogger(__name__)


class Database:
    """SQLite database wrapper for BudgetFlow Tracker."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Establish database connection."""
        if self._connection is None:
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            logger.info("Connected to database: %s", self.db_path)
        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        conn = self.connect()
        conn.execute("BEGIN TRANSACTION")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor."""
        conn = self.connect()
        return conn.execute(query, params)

    def fetchone(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Execute query and return first result."""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        """Execute query and return all results."""
        cursor = self.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def init_schema(self) -> None:
        """Initialize database schema."""
        conn = self.connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_income BOOLEAN DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                category_name TEXT,
                amount REAL NOT NULL,
                period TEXT DEFAULT 'monthly',
                start_date TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                rollover BOOLEAN DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                category_name TEXT,
                merchant TEXT,
                FOREIGN KEY (category_name) REFERENCES categories(name)
            );

            CREATE TABLE IF NOT EXISTS categorization_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                keywords TEXT NOT NULL,
                category_name TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                confidence REAL DEFAULT 0.8,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (category_name) REFERENCES categories(name)
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
            CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_name);
            CREATE INDEX IF NOT EXISTS idx_budgets_category ON budgets(category_name);
        """)
        logger.info("Database schema initialized")

    def seed_default_data(self) -> None:
        """Seed database with default categories."""
        existing = self.fetchall("SELECT name FROM categories")
        existing_names = {row["name"] for row in existing}

        for cat in DEFAULT_CATEGORIES:
            if cat["name"] not in existing_names:
                self.execute(
                    """INSERT INTO categories (name, description, is_income)
                       VALUES (?, ?, ?)""",
                    (cat["name"], cat["description"], 1 if cat["is_income"] else 0),
                )
                logger.info("Seeded category: %s", cat["name"])

        # Seed default categorization rules
        default_rules = [
            ("Groceries", "grocery, supermarket, food market, whole foods, trader joe", "Food & Drink", 8, 0.9),
            ("Restaurant", "restaurant, cafe, coffee, starbucks, mcdonalds, pizza, dining", "Food & Drink", 8, 0.85),
            ("Gas Station", "gas, fuel, shell, chevron, bp, exxon", "Transportation", 8, 0.9),
            ("Uber/Lyft", "uber, lyft, rideshare, grab, diDi", "Transportation", 8, 0.9),
            ("Rent", "rent, mortgage, property, housing", "Housing", 9, 0.95),
            ("Electric", "electric, power, utility, energy bill", "Housing", 7, 0.8),
            ("Netflix", "netflix, spotify, subscription, streaming", "Entertainment", 8, 0.85),
            ("Amazon", "amazon, online, shopping, purchase", "Shopping", 7, 0.7),
            ("Payroll", "payroll, salary, direct deposit, wages", "Salary", 9, 0.95),
            ("Freelance", "freelance, contract, invoice, payment", "Freelance", 8, 0.85),
        ]

        existing_rules = self.fetchall("SELECT name FROM categorization_rules")
        existing_rule_names = {row["name"] for row in existing_rules}

        for rule in default_rules:
            if rule[0] not in existing_rule_names:
                self.execute(
                    """INSERT INTO categorization_rules
                       (name, keywords, category_name, priority, confidence)
                       VALUES (?, ?, ?, ?, ?)""",
                    rule,
                )
                logger.info("Seeded rule: %s", rule[0])

        logger.info("Default data seeded")


# Singleton database instance
_db_instance: Optional[Database] = None


def get_database(db_path: str) -> Database:
    """Get or create database singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance


def reset_database() -> None:
    """Reset the database singleton."""
    global _db_instance
    if _db_instance:
        _db_instance.close()
    _db_instance = None
