"""CLI dashboard for BudgetFlow Tracker."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from src.core.database import Database
from src.categorize.rule_engine import Categorizer
from src.budget.engine import BudgetEngine

logger = logging.getLogger(__name__)


class DashboardCLI:
    """CLI interface for the budget dashboard."""

    def __init__(self, db: Database):
        self.db = db
        self.categorizer = Categorizer(db)
        self.budget_engine = BudgetEngine(db)

    def show_overview(self, days: int = 30) -> str:
        """Show a financial overview for the given number of days.

        Args:
            days: Number of days to look back.

        Returns:
            Formatted overview string.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get totals
        totals = self.db.fetchone(
            """
            SELECT
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE date >= ? AND date <= ?
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        income = totals["income"] or 0
        expenses = totals["expenses"] or 0
        count = totals["transaction_count"] or 0
        net = income - expenses

        lines = [
            "=" * 50,
            f"  BudgetFlow Dashboard ({start_date} to {end_date})",
            "=" * 50,
            f"  Income:      ${income:>10.2f}",
            f"  Expenses:    ${expenses:>10.2f}",
            f"  Net:         ${net:>10.2f}",
            f"  Transactions: {count:>9}",
            "=" * 50,
        ]

        # Spending by category
        category_spending = self.db.fetchall(
            """
            SELECT category_name, SUM(ABS(amount)) as total
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY category_name
            ORDER BY total DESC
            LIMIT 5
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        if category_spending:
            lines.append("")
            lines.append("  Top Spending Categories:")
            lines.append("  " + "-" * 40)
            for row in category_spending:
                bar = "█" * int(row["total"] / 10) if row["total"] > 0 else ""
                lines.append(f"    {row['category_name']:<20} ${row['total']:>8.2f} {bar}")

        # Budget status
        budgets = self.budget_engine.get_all_budgets()
        if budgets:
            lines.append("")
            lines.append("  Budget Status:")
            lines.append("  " + "-" * 40)
            for b in budgets:
                pct = min(b.percentage_used, 100)
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                status = "⚠️ OVER" if b.percentage_used > 100 else "✅"
                lines.append(
                    f"    {b.category_name:<20} ${b.spent:>8.2f}/${b.budget_amount:>8.2f} {pct:>5.1f}% {bar} {status}"
                )

        lines.append("")
        return "\n".join(lines)

    def show_transactions(self, days: int = 7, limit: int = 20) -> str:
        """Show recent transactions.

        Args:
            days: Number of days to look back.
            limit: Maximum number of transactions to show.

        Returns:
            Formatted transactions string.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        transactions = self.db.fetchall(
            """
            SELECT date, description, amount, category_name, merchant
            FROM transactions
            WHERE date >= ? AND date <= ?
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            (start_date.isoformat(), end_date.isoformat(), limit),
        )

        lines = [
            "=" * 60,
            f"  Recent Transactions (last {days} days)",
            "=" * 60,
            f"  {'Date':<12} {'Category':<20} {'Description':<20} {'Amount':>10}",
            "  " + "-" * 58,
        ]

        for txn in transactions:
            amount_str = f"+${txn['amount']:.2f}" if txn["amount"] > 0 else f"-${abs(txn['amount']):.2f}"
            lines.append(
                f"  {txn['date']:<12} {txn['category_name'] or 'Uncategorized':<20} "
                f"{txn['description'][:18]:<20} {amount_str:>10}"
            )

        lines.append("")
        return "\n".join(lines)

    def show_budgets(self) -> str:
        """Show all budget statuses.

        Returns:
            Formatted budgets string.
        """
        budgets = self.budget_engine.get_all_budgets()

        if not budgets:
            return "  No active budgets. Use 'budget add' to create one."

        lines = [
            "=" * 60,
            "  Budget Status",
            "=" * 60,
            f"  {'Category':<20} {'Spent':>10} {'Budget':>10} {'Remaining':>10} {'% Used':>8}",
            "  " + "-" * 58,
        ]

        for b in budgets:
            remaining = b.remaining
            remaining_str = f"${remaining:.2f}"
            if remaining < 0:
                remaining_str = f"-${abs(remaining):.2f} ⚠️"
            lines.append(
                f"  {b.category_name:<20} ${b.spent:>9.2f} ${b.budget_amount:>9.2f} "
                f"{remaining_str:>10} {b.percentage_used:>7.1f}%"
            )

        lines.append("")
        return "\n".join(lines)

    def show_categories(self) -> str:
        """Show all categories.

        Returns:
            Formatted categories string.
        """
        categories = self.db.fetchall(
            """
            SELECT name, description, is_income, COUNT(t.id) as txn_count
            FROM categories
            LEFT JOIN transactions t ON categories.name = t.category_name
            GROUP BY categories.id
            ORDER BY is_income DESC, name ASC
            """
        )

        lines = [
            "=" * 50,
            "  Categories",
            "=" * 50,
            f"  {'Name':<20} {'Type':<8} {'Transactions':>12}",
            "  " + "-" * 38,
        ]

        for cat in categories:
            cat_type = "Income" if cat["is_income"] else "Expense"
            lines.append(
                f"  {cat['name']:<20} {cat_type:<8} {cat['txn_count']:>12}"
            )

        lines.append("")
        return "\n".join(lines)
