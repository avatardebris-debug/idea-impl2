"""Tests for the database module."""

import os
import tempfile
import unittest

from src.core.database import Database, DatabaseError, get_database, reset_database


class TestDatabase(unittest.TestCase):
    """Test suite for the Database class."""

    def setUp(self):
        """Set up a temporary database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        self.db = Database(self.temp_db_path)
        self.db.init_schema()

    def tearDown(self):
        """Clean up the temporary database."""
        self.db.close()
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    # --- Connection Tests ---

    def test_connection_opened(self):
        """Test that a connection is opened on first access."""
        conn = self.db.connection
        self.assertIsNotNone(conn)

    def test_connection_closed(self):
        """Test that close() works."""
        self.db.connection  # Open connection
        self.db.close()
        # After close, connection should be None
        self.assertIsNone(self.db._connection)

    def test_wal_mode_enabled(self):
        """Test that WAL journal mode is enabled."""
        row = self.db.fetchone("PRAGMA journal_mode")
        self.assertEqual(row["journal_mode"], "wal")

    def test_foreign_keys_enabled(self):
        """Test that foreign keys are enabled."""
        row = self.db.fetchone("PRAGMA foreign_keys")
        self.assertEqual(row["foreign_keys"], 1)

    # --- Schema Tests ---

    def test_tables_created(self):
        """Test that all tables are created."""
        tables = [
            "accounts", "categories", "transactions", "budgets", "transaction_rules"
        ]
        for table in tables:
            row = self.db.fetchone(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            self.assertIsNotNone(row, f"Table '{table}' not found")

    def test_indexes_created(self):
        """Test that indexes are created."""
        indexes = self.db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        index_names = [idx["name"] for idx in indexes]
        # Check for at least some indexes
        self.assertTrue(len(index_names) > 0, "No indexes found")

    def test_accounts_table_schema(self):
        """Test accounts table schema."""
        self.db.execute("INSERT INTO accounts (name, account_type) VALUES ('Test', 'checking')")
        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("Test",))
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Test")
        self.assertEqual(row["account_type"], "checking")
        self.assertEqual(row["is_active"], 1)

    def test_categories_table_schema(self):
        """Test categories table schema."""
        self.db.execute(
            "INSERT INTO categories (name, description, is_income) VALUES ('Test', 'A test category', 0)"
        )
        row = self.db.fetchone("SELECT * FROM categories WHERE name = ?", ("Test",))
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Test")
        self.assertEqual(row["is_income"], 0)

    def test_transactions_table_schema(self):
        """Test transactions table schema."""
        self.db.execute(
            """INSERT INTO transactions (date, description, amount, transaction_type, account_id)
               VALUES ('2024-01-01', 'Test transaction', 100.0, 'debit', 1)"""
        )
        row = self.db.fetchone("SELECT * FROM transactions WHERE description = ?", ("Test transaction",))
        self.assertIsNotNone(row)
        self.assertEqual(row["amount"], 100.0)
        self.assertEqual(row["transaction_type"], "debit")

    def test_budgets_table_schema(self):
        """Test budgets table schema."""
        self.db.execute(
            "INSERT INTO categories (name) VALUES ('TestCat')"
        )
        cat_id = self.db.fetchone("SELECT id FROM categories WHERE name = ?", ("TestCat",))["id"]
        self.db.execute(
            """INSERT INTO budgets (category_id, category_name, amount, period, start_date)
               VALUES (?, 'TestCat', 500.0, 'monthly', '2024-01-01')""",
            (cat_id,),
        )
        row = self.db.fetchone("SELECT * FROM budgets WHERE category_name = ?", ("TestCat",))
        self.assertIsNotNone(row)
        self.assertEqual(row["amount"], 500.0)
        self.assertEqual(row["period"], "monthly")

    def test_transaction_rules_table_schema(self):
        """Test transaction_rules table schema."""
        self.db.execute(
            "INSERT INTO categories (name) VALUES ('TestCat')"
        )
        cat_id = self.db.fetchone("SELECT id FROM categories WHERE name = ?", ("TestCat",))["id"]
        self.db.execute(
            """INSERT INTO transaction_rules (name, pattern, pattern_type, category_id, category_name, priority, confidence)
               VALUES ('TestRule', 'test', 'contains', ?, 'TestCat', 10, 0.9)""",
            (cat_id,),
        )
        row = self.db.fetchone("SELECT * FROM transaction_rules WHERE name = ?", ("TestRule",))
        self.assertIsNotNone(row)
        self.assertEqual(row["pattern"], "test")
        self.assertEqual(row["priority"], 10)

    # --- CRUD Tests ---

    def test_fetchone_returns_none_for_missing(self):
        """Test that fetchone returns None for missing rows."""
        result = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("NonExistent",))
        self.assertIsNone(result)

    def test_fetchall_returns_empty_list(self):
        """Test that fetchall returns empty list for no results."""
        result = self.db.fetchall("SELECT * FROM accounts")
        self.assertEqual(result, [])

    def test_execute_returns_cursor(self):
        """Test that execute returns a cursor."""
        cursor = self.db.execute("SELECT 1")
        self.assertIsNotNone(cursor)

    def test_insert_and_select_account(self):
        """Test inserting and selecting an account."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES ('Test Account', 'checking')"
        )
        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("Test Account",))
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Test Account")

    def test_insert_and_select_category(self):
        """Test inserting and selecting a category."""
        self.db.execute(
            "INSERT INTO categories (name, description, is_income) VALUES ('Test', 'Desc', 0)"
        )
        row = self.db.fetchone("SELECT * FROM categories WHERE name = ?", ("Test",))
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Test")

    def test_insert_and_select_transaction(self):
        """Test inserting and selecting a transaction."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES ('Test', 'checking')"
        )
        account_id = self.db.fetchone("SELECT id FROM accounts WHERE name = ?", ("Test",))["id"]
        self.db.execute(
            """INSERT INTO transactions (date, description, amount, transaction_type, account_id)
               VALUES ('2024-01-01', 'Test', 100.0, 'debit', ?)""",
            (account_id,),
        )
        row = self.db.fetchone("SELECT * FROM transactions WHERE description = ?", ("Test",))
        self.assertIsNotNone(row)
        self.assertEqual(row["amount"], 100.0)

    def test_update_account(self):
        """Test updating an account."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES ('Old Name', 'checking')"
        )
        self.db.execute(
            "UPDATE accounts SET name = 'New Name' WHERE name = 'Old Name'"
        )
        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("New Name",))
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "New Name")

    def test_delete_account(self):
        """Test deleting an account."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES ('ToDelete', 'checking')"
        )
        self.db.execute("DELETE FROM accounts WHERE name = 'ToDelete'")
        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("ToDelete",))
        self.assertIsNone(row)

    # --- Foreign Key Tests ---

    def test_foreign_key_violation_raises_error(self):
        """Test that foreign key violations raise DatabaseError."""
        # Try to insert a transaction with non-existent account
        with self.assertRaises(DatabaseError):
            self.db.execute(
                """INSERT INTO transactions (date, description, amount, transaction_type, account_id)
                   VALUES ('2024-01-01', 'Test', 100.0, 'debit', 999999)"""
            )

    # --- Configuration Tests ---

    def test_get_config_default(self):
        """Test getting a config value with default."""
        result = self.db.get_config("nonexistent_key", "default_value")
        self.assertEqual(result, "default_value")

    def test_set_and_get_config(self):
        """Test setting and getting a config value."""
        self.db.set_config("test_key", "test_value")
        result = self.db.get_config("test_key")
        self.assertEqual(result, "test_value")

    def test_set_config_overwrites(self):
        """Test that set_config overwrites existing values."""
        self.db.set_config("test_key", "value1")
        self.db.set_config("test_key", "value2")
        result = self.db.get_config("test_key")
        self.assertEqual(result, "value2")

    # --- Initialization Tests ---

    def test_init_schema_creates_tables(self):
        """Test that init_schema creates all tables."""
        # Close and reopen to simulate fresh database
        self.db.close()
        db2 = Database(self.temp_db_path)
        db2.init_schema()
        tables = [t["name"] for t in db2.fetchall("SELECT name FROM sqlite_master WHERE type='table'")]
        self.assertIn("accounts", tables)
        self.assertIn("categories", tables)
        self.assertIn("transactions", tables)
        self.assertIn("budgets", tables)
        self.assertIn("transaction_rules", tables)

    def test_init_schema_with_defaults(self):
        """Test that init_schema with defaults populates data."""
        self.db.close()
        db2 = Database(self.temp_db_path)
        db2.init_schema(with_defaults=True)
        categories = db2.fetchall("SELECT name FROM categories")
        category_names = [c["name"] for c in categories]
        self.assertIn("Food & Drink", category_names)
        self.assertIn("Income", category_names)

    def test_init_schema_without_defaults(self):
        """Test that init_schema without defaults doesn't populate data."""
        self.db.close()
        db2 = Database(self.temp_db_path)
        db2.init_schema(with_defaults=False)
        categories = db2.fetchall("SELECT name FROM categories")
        self.assertEqual(len(categories), 0)

    # --- Helper Method Tests ---

    def test_fetchone_with_tuple_params(self):
        """Test fetchone with tuple parameters."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Tuple Test", "checking"),
        )
        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("Tuple Test",))
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Tuple Test")

    def test_fetchone_with_list_params(self):
        """Test fetchone with list parameters."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ["List Test", "checking"],
        )
        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ["List Test"])
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "List Test")

    def test_fetchall_with_params(self):
        """Test fetchall with parameters."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Test A", "checking"),
        )
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Test B", "savings"),
        )
        rows = self.db.fetchall(
            "SELECT * FROM accounts WHERE account_type = ?",
            ("checking",),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Test A")

    # --- Error Handling Tests ---

    def test_execute_with_invalid_sql(self):
        """Test that execute raises DatabaseError for invalid SQL."""
        with self.assertRaises(DatabaseError):
            self.db.execute("INVALID SQL STATEMENT")

    def test_fetchone_with_invalid_sql(self):
        """Test that fetchone raises DatabaseError for invalid SQL."""
        with self.assertRaises(DatabaseError):
            self.db.fetchone("INVALID SQL")

    def test_fetchall_with_invalid_sql(self):
        """Test that fetchall raises DatabaseError for invalid SQL."""
        with self.assertRaises(DatabaseError):
            self.db.fetchall("INVALID SQL")

    def test_get_config_with_invalid_sql(self):
        """Test that get_config raises DatabaseError for invalid SQL."""
        with self.assertRaises(DatabaseError):
            self.db.get_config("invalid_key")

    def test_set_config_with_invalid_sql(self):
        """Test that set_config raises DatabaseError for invalid SQL."""
        with self.assertRaises(DatabaseError):
            self.db.set_config("invalid_key", "value")

    # --- Edge Cases ---

    def test_empty_database(self):
        """Test operations on an empty database."""
        accounts = self.db.fetchall("SELECT * FROM accounts")
        self.assertEqual(accounts, [])

        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("Empty",))
        self.assertIsNone(row)

    def test_special_characters_in_data(self):
        """Test handling of special characters."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Test 'quotes' & \"double\"", "checking"),
        )
        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("Test 'quotes' & \"double\"",))
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Test 'quotes' & \"double\"")

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("测试账户", "checking"),
        )
        row = self.db.fetchone("SELECT * FROM accounts WHERE name = ?", ("测试账户",))
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "测试账户")

    def test_large_amount(self):
        """Test handling of large amounts."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Big Account", "checking"),
        )
        account_id = self.db.fetchone("SELECT id FROM accounts WHERE name = ?", ("Big Account",))["id"]
        self.db.execute(
            """INSERT INTO transactions (date, description, amount, transaction_type, account_id)
               VALUES ('2024-01-01', 'Large', 999999999.99, 'debit', ?)""",
            (account_id,),
        )
        row = self.db.fetchone("SELECT * FROM transactions WHERE description = ?", ("Large",))
        self.assertIsNotNone(row)
        self.assertEqual(row["amount"], 999999999.99)

    def test_zero_amount(self):
        """Test handling of zero amounts."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Zero Account", "checking"),
        )
        account_id = self.db.fetchone("SELECT id FROM accounts WHERE name = ?", ("Zero Account",))["id"]
        self.db.execute(
            """INSERT INTO transactions (date, description, amount, transaction_type, account_id)
               VALUES ('2024-01-01', 'Zero', 0.0, 'debit', ?)""",
            (account_id,),
        )
        row = self.db.fetchone("SELECT * FROM transactions WHERE description = ?", ("Zero",))
        self.assertIsNotNone(row)
        self.assertEqual(row["amount"], 0.0)

    def test_negative_amount(self):
        """Test handling of negative amounts."""
        self.db.execute(
            "INSERT INTO accounts (name, account_type) VALUES (?, ?)",
            ("Negative Account", "checking"),
        )
        account_id = self.db.fetchone("SELECT id FROM accounts WHERE name = ?", ("Negative Account",))["id"]
        self.db.execute(
            """INSERT INTO transactions (date, description, amount, transaction_type, account_id)
               VALUES ('2024-01-01', 'Negative', -100.0, 'credit', ?)""",
            (account_id,),
        )
        row = self.db.fetchone("SELECT * FROM transactions WHERE description = ?", ("Negative",))
        self.assertIsNotNone(row)
        self.assertEqual(row["amount"], -100.0)

    # --- get_database and reset_database Tests ---

    def test_get_database_creates_new_instance(self):
        """Test that get_database creates a new instance."""
        db1 = get_database(self.temp_db_path)
        db2 = get_database(self.temp_db_path)
        # They should be different instances
        self.assertIsNot(db1, db2)
        db1.close()
        db2.close()

    def test_reset_database_removes_file(self):
        """Test that reset_database removes the database file."""
        # Create and initialize
        db = get_database(self.temp_db_path)
        db.init_schema()
        db.close()

        # Reset
        reset_database(self.temp_db_path)
        self.assertFalse(os.path.exists(self.temp_db_path))

    def test_reset_database_creates_fresh_schema(self):
        """Test that reset_database creates a fresh schema."""
        # Create and initialize with data
        db = get_database(self.temp_db_path)
        db.init_schema(with_defaults=True)
        db.execute("INSERT INTO accounts (name, account_type) VALUES ('Test', 'checking')")
        db.close()

        # Reset
        reset_database(self.temp_db_path)

        # Reopen and check
        db2 = get_database(self.temp_db_path)
        db2.init_schema()
        accounts = db2.fetchall("SELECT * FROM accounts")
        self.assertEqual(len(accounts), 0)
        db2.close()


class TestDatabaseError(unittest.TestCase):
    """Test suite for DatabaseError."""

    def test_error_message(self):
        """Test that error message is set correctly."""
        error = DatabaseError("Test error")
        self.assertEqual(str(error), "Test error")

    def test_error_is_exception(self):
        """Test that DatabaseError is an Exception."""
        error = DatabaseError("Test error")
        self.assertIsInstance(error, Exception)


if __name__ == "__main__":
    unittest.main()
