"""Tests for the report generator."""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import Database, reset_database
from src.reports.summary import ReportGenerator


@pytest.fixture
def db_path():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    for suffix in ('', '-wal', '-shm'):
        p = path + suffix
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass


@pytest.fixture
def report_generator(db_path):
    """Create a fresh report generator with seeded database."""
    reset_database()
    db = Database(db_path)
    db.init_schema()
    db.seed_default_data()
    generator = ReportGenerator(db)
    yield generator
    db.close()


class TestReportGeneratorInit:
    """Test report generator initialization."""

    def test_init(self, report_generator):
        """Test report generator initialization."""
        assert report_generator is not None
        assert hasattr(report_generator, 'db')


class TestReportGeneratorGenerateSummary:
    """Test summary report generation."""

    def test_generate_summary(self, report_generator):
        """Test generating a summary report."""
        report = report_generator.generate_summary(30)
        assert isinstance(report, str)
        assert "Financial Summary Report" in report
        assert "Total Income" in report
        assert "Total Expenses" in report
        assert "Net Flow" in report
        assert "Transactions" in report

    def test_generate_summary_with_transactions(self, report_generator):
        """Test generating a summary report with transactions."""
        report_generator.db.execute(
            """INSERT INTO transactions 
               (date, description, amount, transaction_type, account_id, category_name)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("2024-01-15", "Grocery Store", -50.0, "debit", 1, "Food & Drink"),
        )
        report_generator.db.execute(
            """INSERT INTO transactions 
               (date, description, amount, transaction_type, account_id, category_name)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("2024-01-16", "Salary", 2000.0, "credit", 1, "Income"),
        )
        report = report_generator.generate_summary(30)
        assert "Grocery Store" not in report  # Summary doesn't include individual transactions
        assert "Total Income" in report
        assert "Total Expenses" in report

    def test_generate_summary_custom_days(self, report_generator):
        """Test generating a summary report with custom days."""
        report = report_generator.generate_summary(7)
        assert "7 days" in report

    def test_generate_summary_empty(self, report_generator):
        """Test generating a summary report with no transactions."""
        # Clear all transactions
        report_generator.db.execute("DELETE FROM transactions")
        report = report_generator.generate_summary(30)
        assert "Financial Summary Report" in report
        assert "$0.00" in report


class TestReportGeneratorGenerateCategoryReport:
    """Test category report generation."""

    def test_generate_category_report(self, report_generator):
        """Test generating a category report."""
        report = report_generator.generate_category_report(30)
        assert isinstance(report, str)
        assert "Category Spending Report" in report
        assert "Category" in report
        assert "Income" in report
        assert "Expenses" in report

    def test_generate_category_report_with_transactions(self, report_generator):
        """Test generating a category report with transactions."""
        report_generator.db.execute(
            """INSERT INTO transactions 
               (date, description, amount, transaction_type, account_id, category_name)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("2024-01-15", "Grocery Store", -50.0, "debit", 1, "Food & Drink"),
        )
        report_generator.db.execute(
            """INSERT INTO transactions 
               (date, description, amount, transaction_type, account_id, category_name)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("2024-01-16", "Bus Pass", -30.0, "debit", 1, "Transportation"),
        )
        report = report_generator.generate_category_report(30)
        assert "Food & Drink" in report
        assert "Transportation" in report

    def test_generate_category_report_empty(self, report_generator):
        """Test generating a category report with no transactions."""
        report_generator.db.execute("DELETE FROM transactions")
        report = report_generator.generate_category_report(30)
        assert "Category Spending Report" in report


class TestReportGeneratorGenerateTrendReport:
    """Test trend report generation."""

    def test_generate_trend_report(self, report_generator):
        """Test generating a trend report."""
        report = report_generator.generate_trend_report(30)
        assert isinstance(report, str)
        assert "Spending Trend Report" in report
        assert "Date" in report
        assert "Income" in report
        assert "Expenses" in report
        assert "Net" in report

    def test_generate_trend_report_with_transactions(self, report_generator):
        """Test generating a trend report with transactions."""
        report_generator.db.execute(
            """INSERT INTO transactions 
               (date, description, amount, transaction_type, account_id, category_name)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("2024-01-15", "Grocery Store", -50.0, "debit", 1, "Food & Drink"),
        )
        report = report_generator.generate_trend_report(30)
        assert "Weekly Summary" in report

    def test_generate_trend_report_empty(self, report_generator):
        """Test generating a trend report with no transactions."""
        report_generator.db.execute("DELETE FROM transactions")
        report = report_generator.generate_trend_report(30)
        assert "Spending Trend Report" in report
