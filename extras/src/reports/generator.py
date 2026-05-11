"""Report generation for BudgetFlow Tracker."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from src.core.database import Database

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate financial reports."""

    def __init__(self, db: Database):
        self.db = db

    def generate_summary(self, days: int = 30) -> str:
        """Generate a financial summary report.

        Args:
            days: Number of days to look back.

        Returns:
            Formatted summary report string.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Overall totals
        totals = self.db.fetchone(
            """
            SELECT
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_expenses,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE date >= ? AND date <= ?
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        # Category breakdown
        categories = self.db.fetchall(
            """
            SELECT category_name,
                   SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_expenses,
                   COUNT(*) as transaction_count
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY category_name
            ORDER BY total_expenses DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        # Top merchants
        merchants = self.db.fetchall(
            """
            SELECT description,
                   SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_spent,
                   COUNT(*) as transaction_count
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY description
            ORDER BY total_spent DESC
            LIMIT 10
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        # Build report
        report = []
        report.append("=" * 60)
        report.append(f"  BUDGETFLOW REPORT ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
        report.append("=" * 60)
        report.append("")
        report.append("OVERALL SUMMARY")
        report.append("-" * 40)
        report.append(f"  Total Income:   ${totals['total_income']:>10,.2f}")
        report.append(f"  Total Expenses: ${totals['total_expenses']:>10,.2f}")
        report.append(f"  Net Savings:    ${totals['total_income'] - totals['total_expenses']:>10,.2f}")
        report.append(f"  Transactions:   {totals['transaction_count']:>10}")
        report.append("")

        if categories:
            report.append("EXPENSES BY CATEGORY")
            report.append("-" * 40)
            for cat in categories:
                report.append(f"  {cat['category_name']:<25} ${cat['total_expenses']:>10,.2f} ({cat['transaction_count']} txns)")
            report.append("")

        if merchants:
            report.append("TOP MERCHANTS")
            report.append("-" * 40)
            for merch in merchants:
                report.append(f"  {merch['description']:<25} ${merch['total_spent']:>10,.2f} ({merch['transaction_count']} txns)")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def generate_budget_report(self) -> str:
        """Generate a budget status report.

        Returns:
            Formatted budget report string.
        """
        from src.budget.engine import BudgetEngine
        budget_engine = BudgetEngine(self.db)
        budgets = budget_engine.get_all_budgets()

        report = []
        report.append("=" * 60)
        report.append("  BUDGET STATUS REPORT")
        report.append("=" * 60)
        report.append("")

        if not budgets:
            report.append("  No active budgets found.")
            report.append("")
            report.append("  To create a budget, use the 'budget' command.")
            report.append("=" * 60)
            return "\n".join(report)

        for budget in budgets:
            status_icon = "✅" if budget.percentage_used < 80 else "⚠️" if budget.percentage_used < 100 else "❌"
            report.append(f"  {status_icon} {budget.category_name}")
            report.append(f"     Budget: ${budget.budget_amount:,.2f}/{budget.period}")
            report.append(f"     Spent:  ${budget.spent:,.2f} ({budget.percentage_used:.1f}%)")
            report.append(f"     Remaining: ${budget.remaining:,.2f}")
            if budget.rollover_amount > 0:
                report.append(f"     Rollover: ${budget.rollover_amount:,.2f}")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def generate_export_csv(self, days: int = 30) -> str:
        """Generate CSV export of transactions.

        Args:
            days: Number of days to include.

        Returns:
            CSV formatted string.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        transactions = self.db.fetchall(
            """SELECT date, description, amount, category_name, transaction_type
               FROM transactions
               WHERE date >= ? AND date <= ?
               ORDER BY date ASC""",
            (start_date.isoformat(), end_date.isoformat()),
        )

        # CSV header
        csv_lines = ["Date,Description,Amount,Category,Type"]

        for t in transactions:
            # Escape description if it contains commas
            desc = t['description'].replace('"', '""')
            if ',' in desc:
                desc = f'"{desc}"'

            csv_lines.append(f"{t['date']},{desc},{t['amount']},{t['category_name']},{t['transaction_type']}")

        return "\n".join(csv_lines)
