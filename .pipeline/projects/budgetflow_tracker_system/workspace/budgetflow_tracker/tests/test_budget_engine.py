"""Tests for the budget engine."""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import Database, reset_database
from src.budget.engine import BudgetEngine, BudgetSummary


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
def budget_engine(db_path):
    """Create a fresh budget engine with seeded database."""
    reset_database()
    db = Database(db_path)
    db.init_schema()
    db.seed_default_data()
    engine = BudgetEngine(db)
    yield engine
    db.close()


class TestBudgetEngineCreateBudget:
    """Test budget creation."""

    def test_create_budget(self, budget_engine):
        """Test creating a budget."""
        budget_id = budget_engine.create_budget("Food & Drink", 500.0, "monthly")
        assert budget_id > 0

    def test_create_budget_with_start_date(self, budget_engine):
        """Test creating a budget with custom start date."""
        budget_id = budget_engine.create_budget(
            "Food & Drink", 500.0, "monthly", "2024-01-01"
        )
        assert budget_id > 0

    def test_create_budget_with_rollover(self, budget_engine):
        """Test creating a budget with rollover."""
        budget_id = budget_engine.create_budget(
            "Food & Drink", 500.0, "monthly", rollover=True
        )
        assert budget_id > 0

    def test_create_budget_for_unknown_category(self, budget_engine):
        """Test creating a budget for unknown category."""
        with pytest.raises(ValueError, match="Category 'Unknown Category' not found"):
            budget_engine.create_budget("Unknown Category", 500.0)

    def test_create_weekly_budget(self, budget_engine):
        """Test creating a weekly budget."""
        budget_id = budget_engine.create_budget("Food & Drink", 100.0, "weekly")
        assert budget_id > 0


class TestBudgetEngineGetBudget:
    """Test getting budgets."""

    def test_get_budget(self, budget_engine):
        """Test getting a budget."""
        budget_engine.create_budget("Food & Drink", 500.0)
        budget = budget_engine.get_budget("Food & Drink")
        assert budget is not None
        assert budget["category_name"] == "Food & Drink"
        assert budget["amount"] == 500.0

    def test_get_budget_not_found(self, budget_engine):
        """Test getting a non-existent budget."""
        budget = budget_engine.get_budget("Nonexistent Category")
        assert budget is None


class TestBudgetEngineGetBudgetSummary:
    """Test getting budget summaries."""

    def test_get_budget_summary(self, budget_engine):
        """Test getting a budget summary."""
        budget_engine.create_budget("Food & Drink", 500.0)
        summary = budget_engine.get_budget_summary("Food & Drink")
        assert summary is not None
        assert summary.category_name == "Food & Drink"
        assert summary.budget_amount == 500.0
        assert isinstance(summary.spent, float)
        assert isinstance(summary.remaining, float)
        assert isinstance(summary.percentage_used, float)
        assert summary.period == "monthly"

    def test_get_budget_summary_not_found(self, budget_engine):
        """Test getting a budget summary for non-existent budget."""
        summary = budget_engine.get_budget_summary("Nonexistent Category")
        assert summary is None

    def test_get_budget_summary_with_transactions(self, budget_engine):
        """Test getting a budget summary with transactions."""
        budget_engine.create_budget("Food & Drink", 500.0)
        budget_engine.db.execute(
            """INSERT INTO transactions 
               (date, description, amount, transaction_type, account_id, category_name)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("2024-01-15", "Grocery Store", -50.0, "debit", 1, "Food & Drink"),
        )
        summary = budget_engine.get_budget_summary("Food & Drink")
        assert summary.spent == 50.0
        assert summary.remaining == 450.0
        assert summary.percentage_used == 10.0


class TestBudgetEngineGetAllBudgets:
    """Test getting all budgets."""

    def test_get_all_budgets(self, budget_engine):
        """Test getting all budgets."""
        budget_engine.create_budget("Food & Drink", 500.0)
        budget_engine.create_budget("Transportation", 200.0)
        budgets = budget_engine.get_all_budgets()
        assert len(budgets) == 2
        assert all(isinstance(b, BudgetSummary) for b in budgets)


class TestBudgetEngineUpdateBudget:
    """Test updating budgets."""

    def test_update_budget(self, budget_engine):
        """Test updating a budget."""
        budget_engine.create_budget("Food & Drink", 500.0)
        result = budget_engine.update_budget("Food & Drink", 600.0)
        assert result is True
        budget = budget_engine.get_budget("Food & Drink")
        assert budget["amount"] == 600.0

    def test_update_budget_not_found(self, budget_engine):
        """Test updating a non-existent budget."""
        result = budget_engine.update_budget("Nonexistent Category", 600.0)
        assert result is False


class TestBudgetEngineDeactivateBudget:
    """Test deactivating budgets."""

    def test_deactivate_budget(self, budget_engine):
        """Test deactivating a budget."""
        budget_engine.create_budget("Food & Drink", 500.0)
        result = budget_engine.deactivate_budget("Food & Drink")
        assert result is True
        budget = budget_engine.get_budget("Food & Drink")
        assert budget is None

    def test_deactivate_budget_not_found(self, budget_engine):
        """Test deactivating a non-existent budget."""
        result = budget_engine.deactivate_budget("Nonexistent Category")
        assert result is False


class TestBudgetEnginePeriodCalculation:
    """Test period calculation logic."""

    def test_monthly_period_start(self, budget_engine):
        """Test monthly period start calculation."""
        # This tests the internal _get_period_start method
        period_start = budget_engine._get_period_start("2024-01-15", "monthly")
        # Should return the start of the current month
        assert period_start is not None

    def test_weekly_period_start(self, budget_engine):
        """Test weekly period start calculation."""
        period_start = budget_engine._get_period_start("2024-01-15", "weekly")
        # Should return the Monday of the current week
        assert period_start is not None
