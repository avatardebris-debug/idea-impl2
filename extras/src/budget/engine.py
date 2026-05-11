"""Budget engine for BudgetFlow Tracker."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from src.core.database import Database

logger = logging.getLogger(__name__)


@dataclass
class BudgetSummary:
    """Summary of a budget's status."""
    category_name: str
    period: str
    start_date: str
    budget_amount: float
    spent: float
    remaining: float
    percentage_used: float
    rollover_amount: float = 0.0


class BudgetEngine:
    """Engine for managing budgets."""

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
            Budget ID.
        """
        if start_date is None:
            start_date = date.today().isoformat()

        # Deactivate any existing budget for this category
        self.db.execute(
            "UPDATE budgets SET is_active = 0 WHERE category_name = ? AND is_active = 1",
            (category_name,),
        )

        cursor = self.db.execute(
            """INSERT INTO budgets (category_name, amount, period, start_date, rollover)
               VALUES (?, ?, ?, ?, ?)""",
            (category_name, amount, period, start_date, 1 if rollover else 0),
        )
        budget_id = cursor.lastrowid
        logger.info("Created budget %d for %s: $%.2f/%s", budget_id, category_name, amount, period)
        return budget_id

    def update_budget(self, category_name: str, amount: float) -> bool:
        """Update a budget amount.

        Args:
            category_name: Category name.
            amount: New budget amount.

        Returns:
            True if updated, False if no active budget found.
        """
        result = self.db.execute(
            """UPDATE budgets SET amount = ? WHERE category_name = ? AND is_active = 1""",
            (amount, category_name),
        )
        if result.rowcount > 0:
            logger.info("Updated budget for %s to $%.2f", category_name, amount)
            return True
        return False

    def deactivate_budget(self, category_name: str) -> bool:
        """Deactivate a budget.

        Args:
            category_name: Category name.

        Returns:
            True if deactivated, False if no active budget found.
        """
        result = self.db.execute(
            "UPDATE budgets SET is_active = 0 WHERE category_name = ? AND is_active = 1",
            (category_name,),
        )
        if result.rowcount > 0:
            logger.info("Deactivated budget for %s", category_name)
            return True
        return False

    def get_all_budgets(self) -> list[BudgetSummary]:
        """Get all active budgets with their current status.

        Returns:
            List of BudgetSummary objects.
        """
        budgets = self.db.fetchall(
            """SELECT b.id, b.category_name, b.amount as budget_amount,
                      b.period, b.start_date, b.rollover
               FROM budgets b
               WHERE b.is_active = 1"""
        )

        summaries = []
        for b in budgets:
            summary = self.get_budget_summary(b["category_name"])
            if summary:
                summaries.append(summary)

        return summaries

    def get_budget_summary(self, category_name: str) -> Optional[BudgetSummary]:
        """Get summary for a specific budget.

        Args:
            category_name: Category name.

        Returns:
            BudgetSummary or None if no active budget.
        """
        budget = self.db.fetchone(
            """SELECT id, category_name, amount as budget_amount,
                      period, start_date, rollover
               FROM budgets
               WHERE category_name = ? AND is_active = 1""",
            (category_name,),
        )

        if not budget:
            return None

        # Calculate spent amount for current period
        spent = self._calculate_spent(category_name, budget["start_date"], budget["period"])

        # Calculate rollover amount
        rollover_amount = 0.0
        if budget["rollover"]:
            rollover_amount = self._calculate_rollover(category_name)

        budget_amount = budget["budget_amount"]
        remaining = budget_amount - spent + rollover_amount
        percentage_used = (spent / budget_amount * 100) if budget_amount > 0 else 0

        return BudgetSummary(
            category_name=budget["category_name"],
            period=budget["period"],
            start_date=budget["start_date"],
            budget_amount=budget_amount,
            spent=spent,
            remaining=remaining,
            percentage_used=percentage_used,
            rollover_amount=rollover_amount,
        )

    def _calculate_spent(self, category_name: str, start_date: str, period: str) -> float:
        """Calculate total spent for a category in the current period."""
        start = date.fromisoformat(start_date)

        if period == "monthly":
            # Calculate end of current month
            if start.month == 12:
                end = date(start.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(start.year, start.month + 1, 1) - timedelta(days=1)
        else:  # weekly
            end = start + timedelta(weeks=1)

        spent = self.db.fetchone(
            """SELECT COALESCE(SUM(ABS(amount)), 0) as total
               FROM transactions
               WHERE category_name = ?
               AND date >= ?
               AND date <= ?
               AND transaction_type = 'expense'""",
            (category_name, start.isoformat(), end.isoformat()),
        )

        return spent["total"] if spent else 0.0

    def _calculate_rollover(self, category_name: str) -> float:
        """Calculate rollover amount from previous period."""
        # Get the last completed period's budget
        last_budget = self.db.fetchone(
            """SELECT amount as budget_amount, start_date
               FROM budgets
               WHERE category_name = ? AND is_active = 0
               ORDER BY start_date DESC
               LIMIT 1""",
            (category_name,),
        )

        if not last_budget:
            return 0.0

        # Calculate what was spent in the last period
        spent = self.db.fetchone(
            """SELECT COALESCE(SUM(ABS(amount)), 0) as total
               FROM transactions
               WHERE category_name = ?
               AND date >= ?
               AND date < (
                   SELECT start_date FROM budgets
                   WHERE category_name = ? AND is_active = 1
                   ORDER BY start_date ASC
                   LIMIT 1
               )
               AND transaction_type = 'expense'""",
            (category_name, last_budget["start_date"], category_name),
        )

        if not spent:
            return 0.0

        return max(0, last_budget["budget_amount"] - spent["total"])

    def get_budget_alerts(self) -> list[dict]:
        """Get budget alerts for budgets that are over threshold.

        Returns:
            List of alert dictionaries.
        """
        from src.core.config import get_config
        config = get_config()

        budgets = self.get_all_budgets()
        alerts = []

        for budget in budgets:
            if budget.percentage_used >= config.budget_alert_threshold * 100:
                alerts.append({
                    "type": "critical",
                    "category_name": budget.category_name,
                    "percentage": budget.percentage_used,
                    "remaining": budget.remaining,
                    "message": f"Budget exceeded for {budget.category_name}!",
                })
            elif budget.percentage_used >= config.budget_warning_threshold * 100:
                alerts.append({
                    "type": "warning",
                    "category_name": budget.category_name,
                    "percentage": budget.percentage_used,
                    "remaining": budget.remaining,
                    "message": f"Approaching budget limit for {budget.category_name}",
                })

        return alerts
