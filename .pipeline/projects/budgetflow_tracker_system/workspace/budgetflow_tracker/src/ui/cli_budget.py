"""CLI budget management for BudgetFlow Tracker."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from src.core.database import Database
from src.budget.engine import BudgetEngine

logger = logging.getLogger(__name__)


class BudgetCLI:
    """CLI interface for budget management."""

    def __init__(self, db: Database):
        self.db = db
        self.budget_engine = BudgetEngine(db)

    def add_budget(
        self,
        category_name: str,
        amount: float,
        period: str = "monthly",
        start_date: Optional[str] = None,
        rollover: bool = False,
    ) -> str:
        """Add a new budget.

        Args:
            category_name: Category to budget for.
            amount: Budget amount.
            period: Budget period ('monthly' or 'weekly').
            start_date: Start date (YYYY-MM-DD). Defaults to today.
            rollover: Whether unused amounts roll over.

        Returns:
            Status message.
        """
        # Validate category exists
        cat = self.db.fetchone(
            "SELECT id FROM categories WHERE name = ?", (category_name,)
        )
        if not cat:
            return f"Error: Category '{category_name}' not found. Use 'category add' first."

        try:
            budget_id = self.budget_engine.create_budget(
                category_name=category_name,
                amount=amount,
                period=period,
                start_date=start_date,
                rollover=rollover,
            )
            return f"Budget created: ${amount:.2f}/{period} for '{category_name}' (ID: {budget_id})"
        except Exception as e:
            return f"Error creating budget: {str(e)}"

    def update_budget(self, category_name: str, amount: float) -> str:
        """Update a budget amount.

        Args:
            category_name: Category name.
            amount: New budget amount.

        Returns:
            Status message.
        """
        if self.budget_engine.update_budget(category_name, amount):
            return f"Budget updated: ${amount:.2f}/month for '{category_name}'"
        return f"Error: No active budget found for '{category_name}'"

    def deactivate_budget(self, category_name: str) -> str:
        """Deactivate a budget.

        Args:
            category_name: Category name.

        Returns:
            Status message.
        """
        if self.budget_engine.deactivate_budget(category_name):
            return f"Budget deactivated for '{category_name}'"
        return f"Error: No active budget found for '{category_name}'"

    def show_budgets(self) -> str:
        """Show all budget statuses.

        Returns:
            Formatted budgets string.
        """
        from src.ui.cli_dashboard import DashboardCLI
        dashboard = DashboardCLI(self.db)
        return dashboard.show_budgets()

    def show_summary(self, category_name: str) -> str:
        """Show summary for a specific budget.

        Args:
            category_name: Category name.

        Returns:
            Formatted summary string.
        """
        summary = self.budget_engine.get_budget_summary(category_name)
        if not summary:
            return f"No active budget found for '{category_name}'"

        lines = [
            "=" * 50,
            f"  Budget Summary: {summary.category_name}",
            "=" * 50,
            f"  Period: {summary.period}",
            f"  Start Date: {summary.start_date}",
            f"  Budget Amount: ${summary.budget_amount:.2f}",
            f"  Spent: ${summary.spent:.2f}",
            f"  Remaining: ${summary.remaining:.2f}",
            f"  Percentage Used: {summary.percentage_used:.1f}%",
            f"  Rollover: ${summary.rollover_amount:.2f}",
            "=" * 50,
        ]

        if summary.percentage_used > 100:
            lines.append("  ⚠️  WARNING: Budget exceeded!")
        elif summary.percentage_used > 80:
            lines.append("  ⚠️  WARNING: Budget nearly exceeded!")

        lines.append("")
        return "\n".join(lines)
