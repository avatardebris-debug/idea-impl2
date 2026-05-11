"""Tests for BudgetFlow Tracker core modules."""

import os
import sys
import tempfile
import unittest
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import Database, get_database, reset_database
from src.core.config import AppConfig, get_config, update_config
from src.core.default_categories import DEFAULT_CATEGORIES
from src.categorize.rule_engine import Categorizer, CategorizationResult
from src.budget.engine import BudgetEngine, BudgetSummary
from src.import.csv_parser import CSVParser, ParsedTransaction
from src.reports.generator import ReportGenerator
from src.ui.cli_dashboard import CLIDashboard


class TestDatabase(unittest.TestCase):
    """Test database module."""

    def setUp(self):
        """Set up test fixtures."""
        reset_database()
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
        self.db.init_schema()

    def tearDown(self):
        """Tear down test fixtures."""
        self.db.close()
        os.unlink(self.temp_db.name)
        reset_database()

    def test_init_schema(self):
        """Test schema initialization."""
        self.db.init_schema()
        tables = self.db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t['name'] for t in tables]
        self.assertIn('transactions', table_names)
        self.assertIn('budgets', table_names)
        self.assertIn('categories', table_names)

    def test_insert_and_fetch_transactions(self):
        """Test inserting and fetching transactions."""
        self.db.execute(
            """INSERT INTO transactions
               (date, description, amount, transaction_type, category_name)
               VALUES (?, ?, ?, ?, ?)""",
            ("2024-01-01", "Test transaction", -50.0, "expense", "Food"),
        )

        result = self.db.fetchone(
            "SELECT * FROM transactions WHERE date = ?",
            ("2024-01-01",),
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['description'], "Test transaction")
        self.assertEqual(result['amount'], -50.0)

    def test_fetch_all_transactions(self):
        """Test fetching all transactions."""
        self.db.execute(
            """INSERT INTO transactions
               (date, description, amount, transaction_type, category_name)
               VALUES (?, ?, ?, ?, ?)""",
            ("2024-01-01", "Transaction 1", -50.0, "expense", "Food"),
        )
        self.db.execute(
            """INSERT INTO transactions
               (date, description, amount, transaction_type, category_name)
               VALUES (?, ?, ?, ?, ?)""",
            ("2024-01-02", "Transaction 2", 1000.0, "income", "Salary"),
        )

        results = self.db.fetchall("SELECT * FROM transactions")
        self.assertEqual(len(results), 2)

    def test_delete_transaction(self):
        """Test deleting a transaction."""
        self.db.execute(
            """INSERT INTO transactions
               (date, description, amount, transaction_type, category_name)
               VALUES (?, ?, ?, ?, ?)""",
            ("2024-01-01", "Test transaction", -50.0, "expense", "Food"),
        )

        self.db.execute("DELETE FROM transactions WHERE date = ?", ("2024-01-01",))
        result = self.db.fetchone("SELECT * FROM transactions WHERE date = ?", ("2024-01-01",))
        self.assertIsNone(result)


class TestConfig(unittest.TestCase):
    """Test configuration module."""

    def test_default_config(self):
        """Test default configuration values."""
        config = get_config()
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.budget_warning_threshold, 0.8)
        self.assertEqual(config.budget_alert_threshold, 1.0)
        self.assertEqual(config.default_currency, "USD")

    def test_update_config(self):
        """Test updating configuration."""
        update_config(budget_warning_threshold=0.9)
        config = get_config()
        self.assertEqual(config.budget_warning_threshold, 0.9)


class TestDefaultCategories(unittest.TestCase):
    """Test default categories."""

    def test_default_categories(self):
        """Test default categories are defined."""
        self.assertIn("Food", DEFAULT_CATEGORIES)
        self.assertIn("Transportation", DEFAULT_CATEGORIES)
        self.assertIn("Housing", DEFAULT_CATEGORIES)
        self.assertIn("Entertainment", DEFAULT_CATEGORIES)
        self.assertIn("Utilities", DEFAULT_CATEGORIES)
        self.assertIn("Healthcare", DEFAULT_CATEGORIES)
        self.assertIn("Shopping", DEFAULT_CATEGORIES)
        self.assertIn("Dining", DEFAULT_CATEGORIES)
        self.assertIn("Groceries", DEFAULT_CATEGORIES)
        self.assertIn("Gas", DEFAULT_CATEGORIES)
        self.assertIn("Salary", DEFAULT_CATEGORIES)
        self.assertIn("Freelance", DEFAULT_CATEGORIES)
        self.assertIn("Investment", DEFAULT_CATEGORIES)
        self.assertIn("Gift", DEFAULT_CATEGORIES)
        self.assertIn("Refund", DEFAULT_CATEGORIES)
        self.assertIn("Other", DEFAULT_CATEGORIES)


class TestCategorizer(unittest.TestCase):
    """Test categorizer module."""

    def setUp(self):
        """Set up test fixtures."""
        reset_database()
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
        self.db.init_schema()
        self.categorizer = Categorizer(self.db)

    def tearDown(self):
        """Tear down test fixtures."""
        self.db.close()
        os.unlink(self.temp_db.name)
        reset_database()

    def test_categorize_food(self):
        """Test categorizing food-related transactions."""
        result = self.categorizer.categorize("Starbucks Coffee", -5.50)
        self.assertEqual(result.category_name, "Food")
        self.assertGreater(result.confidence, 0.5)

    def test_categorize_transportation(self):
        """Test categorizing transportation-related transactions."""
        result = self.categorizer.categorize("Shell Gas Station", -45.00)
        self.assertEqual(result.category_name, "Transportation")
        self.assertGreater(result.confidence, 0.5)

    def test_categorize_salary(self):
        """Test categorizing salary transactions."""
        result = self.categorizer.categorize("Direct Deposit - Employer", 3000.00)
        self.assertEqual(result.category_name, "Salary")
        self.assertGreater(result.confidence, 0.5)

    def test_categorize_unknown(self):
        """Test categorizing unknown transactions."""
        result = self.categorizer.categorize("Random Transaction", -10.00)
        self.assertEqual(result.category_name, "Other")
        self.assertGreater(result.confidence, 0.0)


class TestBudgetEngine(unittest.TestCase):
    """Test budget engine module."""

    def setUp(self):
        """Set up test fixtures."""
        reset_database()
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
        self.db.init_schema()
        self.budget_engine = BudgetEngine(self.db)

    def tearDown(self):
        """Tear down test fixtures."""
        self.db.close()
        os.unlink(self.temp_db.name)
        reset_database()

    def test_create_budget(self):
        """Test creating a budget."""
        budget_id = self.budget_engine.create_budget("Food", 500.0, "monthly")
        self.assertGreater(budget_id, 0)

        budget = self.db.fetchone(
            "SELECT * FROM budgets WHERE id = ?",
            (budget_id,),
        )
        self.assertIsNotNone(budget)
        self.assertEqual(budget['category_name'], "Food")
        self.assertEqual(budget['amount'], 500.0)

    def test_update_budget(self):
        """Test updating a budget."""
        budget_id = self.budget_engine.create_budget("Food", 500.0, "monthly")
        result = self.budget_engine.update_budget("Food", 600.0)
        self.assertTrue(result)

        budget = self.db.fetchone(
            "SELECT * FROM budgets WHERE id = ?",
            (budget_id,),
        )
        self.assertEqual(budget['amount'], 600.0)

    def test_get_budget_summary(self):
        """Test getting budget summary."""
        budget_id = self.budget_engine.create_budget("Food", 500.0, "monthly")
        summary = self.budget_engine.get_budget_summary("Food")
        self.assertIsNotNone(summary)
        self.assertEqual(summary.category_name, "Food")
        self.assertEqual(summary.budget_amount, 500.0)


class TestCSVParser(unittest.TestCase):
    """Test CSV parser module."""

    def setUp(self):
        """Set up test fixtures."""
        reset_database()
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
        self.db.init_schema()
        self.csv_parser = CSVParser(self.db)

    def tearDown(self):
        """Tear down test fixtures."""
        self.db.close()
        os.unlink(self.temp_db.name)
        reset_database()

    def test_detect_format(self):
        """Test detecting CSV format."""
        csv_content = "Date,Description,Amount\n2024-01-01,Test,100.00"
        fmt = self.csv_parser.detect_format(csv_content)
        self.assertEqual(fmt.date_column, "Date")
        self.assertEqual(fmt.description_column, "Description")
        self.assertEqual(fmt.amount_column, "Amount")

    def test_parse_transactions(self):
        """Test parsing transactions from CSV."""
        csv_content = "Date,Description,Amount\n2024-01-01,Test Transaction,-50.00"
        transactions = self.csv_parser.parse(csv_content)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].date, date(2024, 1, 1))
        self.assertEqual(transactions[0].description, "Test Transaction")
        self.assertEqual(transactions[0].amount, -50.0)

    def test_import_transactions(self):
        """Test importing transactions from CSV."""
        csv_content = "Date,Description,Amount\n2024-01-01,Test Transaction,-50.00"
        result = self.csv_parser.import_transactions(csv_content)
        self.assertEqual(result['imported'], 1)
        self.assertEqual(result['errors'], 0)


class TestReportGenerator(unittest.TestCase):
    """Test report generator module."""

    def setUp(self):
        """Set up test fixtures."""
        reset_database()
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
        self.db.init_schema()
        self.report_gen = ReportGenerator(self.db)

    def tearDown(self):
        """Tear down test fixtures."""
        self.db.close()
        os.unlink(self.temp_db.name)
        reset_database()

    def test_generate_summary(self):
        """Test generating summary report."""
        self.db.execute(
            """INSERT INTO transactions
               (date, description, amount, transaction_type, category_name)
               VALUES (?, ?, ?, ?, ?)""",
            (date.today().isoformat(), "Test", -50.0, "expense", "Food"),
        )

        report = self.report_gen.generate_summary()
        self.assertIn("OVERALL SUMMARY", report)
        self.assertIn("EXPENSES BY CATEGORY", report)

    def test_generate_budget_report(self):
        """Test generating budget report."""
        budget_engine = BudgetEngine(self.db)
        budget_engine.create_budget("Food", 500.0, "monthly")

        report = self.report_gen.generate_budget_report()
        self.assertIn("BUDGET STATUS REPORT", report)
        self.assertIn("Food", report)

    def test_generate_export_csv(self):
        """Test generating CSV export."""
        self.db.execute(
            """INSERT INTO transactions
               (date, description, amount, transaction_type, category_name)
               VALUES (?, ?, ?, ?, ?)""",
            (date.today().isoformat(), "Test", -50.0, "expense", "Food"),
        )

        csv_export = self.report_gen.generate_export_csv()
        self.assertIn("Date,Description,Amount,Category,Type", csv_export)
        self.assertIn("Test", csv_export)


class TestCLIDashboard(unittest.TestCase):
    """Test CLI dashboard module."""

    def setUp(self):
        """Set up test fixtures."""
        reset_database()
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db = Database(self.temp_db.name)
        self.db.init_schema()
        self.dashboard = CLIDashboard(self.db)

    def tearDown(self):
        """Tear down test fixtures."""
        self.db.close()
        os.unlink(self.temp_db.name)
        reset_database()

    def test_add_transaction(self):
        """Test adding a transaction via dashboard."""
        self.dashboard.add_transaction("Test Transaction", -50.0)
        result = self.db.fetchone(
            "SELECT * FROM transactions WHERE description = ?",
            ("Test Transaction",),
        )
        self.assertIsNotNone(result)

    def test_add_budget(self):
        """Test adding a budget via dashboard."""
        self.dashboard.add_budget("Food", 500.0)
        result = self.db.fetchone(
            "SELECT * FROM budgets WHERE category_name = ?",
            ("Food",),
        )
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
