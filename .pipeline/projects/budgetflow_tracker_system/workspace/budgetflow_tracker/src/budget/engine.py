"""Budget engine for BudgetFlow Tracker."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from src.core.database import Database

logger = logging.getLogger(__name__)


@dataclass
class BudgetSummary:
    """Summary of a budget's status."""
    category_name: str
    budget_amount: float
    spent: float
    remaining: float
    percentage_used: float
    period: str
    start_date: str
    rollover_amount: float = 0.0


class BudgetEngine:
    """Manage budgets and track spending against them."""

    def __init__(self, db: Database):
        self.db = db

    def create_budget(
        self,
        category_name: str,
        amount: float,
        period: str = "monthly",
        start_date: Optional[str] = None,
        rollover: bool = False,
    ) -> int:
        """Create a new budget.

        Args:
            category_name: Category to budget for.
            amount: Budget amount.
            period: Budget period ('monthly' or 'weekly').
            start_date: Start date (YYYY-MM-DD). Defaults to today.
            rollover: Whether unused amounts roll over.

        Returns:
            ID of the created budget.
        """
        if start_date is None:
            start_date = date.today().isoformat()

        # Get category ID
        cat = self.db.fetchone(
            "SELECT id FROM categories WHERE name = ?", (category_name,)
        )
        if not cat:
            raise ValueError(f"Category '{category_name}' not found")

        self.db.execute(
            """INSERT INTO budgets
               (category_id, category_name, amount, period, start_date, is_active, rollover)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (cat["id"], category_name, amount, period, start_date, 1 if rollover else 0),
        )
        budget_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        logger.info("Created budget %d: $%.2f/%s for '%s'", budget_id, amount, period, category_name)
        return budget_id

    def get_budget(self, category_name: str) -> Optional[dict]:
        """Get an active budget for a category.

        Args:
            category_name: Category name.

        Returns:
            Budget dict or None.
        """
        budget = self.db.fetchone(
            """SELECT * FROM budgets
               WHERE category_name = ? AND is_active = 1
               ORDER BY start_date DESC LIMIT 1""",
            (category_name,),
        )
        return dict(budget) if budget else None

    def get_budget_summary(self, category_name: str) -> Optional[BudgetSummary]:
        """Get a budget summary with spending info.

        Args:
            category_name: Category name.

        Returns:
            BudgetSummary or None.
        """
        budget = self.get_budget(category_name)
        if not budget:
            return None

        # Calculate spending for the current period
        spent = self._calculate_spending(category_name, budget["start_date"], budget["period"])

        remaining = budget["amount"] - spent
        percentage_used = (spent / budget["amount"] * 100) if budget["amount"] > 0 else 0

        # Calculate rollover
        rollover_amount = 0.0
        if budget["rollover"]:
            rollover_amount = self._calculate_rollover(category_name, budget["start_date"], budget["period"])

        return BudgetSummary(
            category_name=category_name,
            budget_amount=budget["amount"],
            spent=spent,
            remaining=remaining,
            percentage_used=percentage_used,
            period=budget["period"],
            start_date=budget["start_date"],
            rollover_amount=rollover_amount,
        )

    def get_all_budgets(self) -> list[BudgetSummary]:
        """Get summaries for all active budgets.

        Returns:
            List of BudgetSummary objects.
        """
        budgets = self.db.fetchall(
            """SELECT DISTINCT category_name FROM budgets WHERE is_active = 1"""
        )
        return [
            self.get_budget_summary(b["category_name"])
            for b in budgets
            if self.get_budget_summary(b["category_name"])
        ]

    def update_budget(self, category_name: str, amount: float) -> bool:
        """Update a budget amount.

        Args:
            category_name: Category name.
            amount: New budget amount.

        Returns:
            True if updated, False if no budget found.
        """
        budget = self.get_budget(category_name)
        if not budget:
            return False

        self.db.execute(
            "UPDATE budgets SET amount = ? WHERE id = ?",
            (amount, budget["id"]),
        )
        logger.info("Updated budget for '%s' to $%.2f", category_name, amount)
        return True

    def deactivate_budget(self, category_name: str) -> bool:
        """Deactivate a budget.

        Args:
            category_name: Category name.

        Returns:
            True if deactivated, False if no budget found.
        """
        budget = self.get_budget(category_name)
        if not budget:
            return False

        self.db.execute(
            "UPDATE budgets SET is_active = 0 WHERE id = ?",
            (budget["id"],),
        )
        logger.info("Deactivated budget for '%s'", category_name)
        return True

    def _calculate_spending(self, category_name: str, start_date: str, period: str) -> float:
        """Calculate total spending for a category in the current period.

        Args:
            category_name: Category name.
            start_date: Budget start date.
            period: Budget period.

        Returns:
            Total spending amount.
        """
        # Determine period start date
        period_start = self._get_period_start(start_date, period)

        query = """
            SELECT COALESCE(SUM(ABS(amount)), 0) as total
            FROM transactions
            WHERE category_name = ?
              AND date >= ?
              AND date <= ?
              AND transaction_type = 'debit'
        """
        period_end = self._get_period_end(start_date, period)

        result = self.db.fetchone(
            query,
            (category_name, period_start, period_end),
        )
        return float(result["total"]) if result else 0.0

    def _calculate_rollover(self, category_name: str, start_date: str, period: str) -> float:
        """Calculate rollover amount from previous period.

        Args:
            category_name: Category name.
            start_date: Budget start date.
            period: Budget period.

        Returns:
            Rollover amount.
        """
        # Get previous period's budget
        prev_start = self._get_previous_period_start(start_date, period)
        prev_budget = self.db.fetchone(
            """SELECT amount FROM budgets
               WHERE category_name = ? AND is_active = 1
               ORDER BY start_date DESC LIMIT 1""",
            (category_name,),
        )
        if not prev_budget:
            return 0.0

        prev_spent = self._calculate_spending(category_name, prev_start, period)
        return max(0, prev_budget["amount"] - prev_spent)

    def _get_period_start(self, start_date: str, period: str) -> str:
        """Get the effective start date for the current period."""
        budget_start = date.fromisoformat(start_date)
        today = date.today()

        if period == "monthly":
            # Find the most recent month start on or before today
            if today.month == budget_start.month and today.year == budget_start.year:
                return start_date
            # Go back to the last month start
            year = today.year
            month = today.month
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1
            return date(year, month, 1).isoformat()
        else:  # weekly
            # Find the most recent week start (Monday)
            days_since_monday = today.weekday()
            week_start = today.replace(day=today.day - days_since_monday)
            return week_start.isoformat()

    def _get_period_end(self, start_date: str, period: str) -> str:
        """Get the effective end date for the current period."""
        budget_start = date.fromisoformat(start_date)
        today = date.today()

        if period == "monthly":
            # End of current month
            if today.month == 12:
                return date(today.year, 12, 31).isoformat()
            else:
                return date(today.year, today.month + 1, 1).replace(day=1) - __import__('datetime').timedelta(days=1)
        else:  # weekly
            days_until_sunday = 6 - today.weekday()
            week_end = today + __import__('datetime').timedelta(days=days_until_sunday)
            return week_end.isoformat()

    def _get_previous_period_start(self, start_date: str, period: str) -> str:
        """Get the start date of the previous period."""
        budget_start = date.fromisoformat(start_date)

        if period == "monthly":
            if budget_start.month == 1:
                return date(budget_start.year - 1, 12, 1).isoformat()
            else:
                return date(budget_start.year, budget_start.month - 1, 1).isoformat()
        else:  # weekly
            prev_monday = budget_start - __import__('datetime').timedelta(weeks=1)
            return prev_monday.isoformat()
