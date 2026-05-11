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
                COUNT(*) as total_transactions
            FROM transactions
            WHERE date >= ? AND date <= ?
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        income = totals["total_income"] or 0
        expenses = totals["total_expenses"] or 0
        net = income - expenses
        count = totals["total_transactions"] or 0

        # Average daily spending
        avg_daily = expenses / days if days > 0 and expenses > 0 else 0

        # Top spending categories
        top_categories = self.db.fetchall(
            """
            SELECT category_name, SUM(ABS(amount)) as total, COUNT(*) as count
            FROM transactions
            WHERE date >= ? AND date <= ? AND amount < 0
            GROUP BY category_name
            ORDER BY total DESC
            LIMIT 10
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        # Monthly comparison (previous period)
        prev_start = start_date - timedelta(days=days)
        prev_totals = self.db.fetchone(
            """
            SELECT
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_expenses
            FROM transactions
            WHERE date >= ? AND date <= ?
            """,
            (prev_start.isoformat(), start_date.isoformat() if start_date > prev_start else prev_start.isoformat()),
        )

        lines = [
            "=" * 60,
            "  Financial Summary Report",
            "=" * 60,
            f"  Period: {start_date} to {end_date} ({days} days)",
            "=" * 60,
            "",
            "  Overall Financials:",
            f"    Total Income:    ${income:>12.2f}",
            f"    Total Expenses:  ${expenses:>12.2f}",
            f"    Net Flow:        ${net:>12.2f}",
            f"    Transactions:    {count:>12}",
            f"    Avg Daily Spend: ${avg_daily:>12.2f}",
            "",
        ]

        if top_categories:
            lines.append("  Top Spending Categories:")
            lines.append("  " + "-" * 40)
            for i, cat in enumerate(top_categories, 1):
                pct = (cat["total"] / expenses * 100) if expenses > 0 else 0
                lines.append(
                    f"    {i:>2}. {cat['category_name']:<20} ${cat['total']:>10.2f} ({pct:.1f}%)"
                )

        lines.append("")
        return "\n".join(lines)

    def generate_category_report(self, days: int = 30) -> str:
        """Generate a category-wise spending report.

        Args:
            days: Number of days to look back.

        Returns:
            Formatted category report string.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        categories = self.db.fetchall(
            """
            SELECT category_name,
                   SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                   SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses,
                   COUNT(*) as count
            FROM transactions
            WHERE date >= ? AND date <= ?
            GROUP BY category_name
            ORDER BY expenses DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        lines = [
            "=" * 60,
            "  Category Spending Report",
            "=" * 60,
            f"  Period: {start_date} to {end_date} ({days} days)",
            "=" * 60,
            f"  {'Category':<25} {'Income':>12} {'Expenses':>12} {'Net':>12} {'Count':>8}",
            "  " + "-" * 68,
        ]

        for cat in categories:
            net = cat["income"] - cat["expenses"]
            lines.append(
                f"  {cat['category_name'] or 'Uncategorized':<25} "
                f"${cat['income']:>11.2f} ${cat['expenses']:>11.2f} "
                f"${net:>11.2f} {cat['count']:>8}"
            )

        lines.append("")
        return "\n".join(lines)

    def generate_trend_report(self, days: int = 30) -> str:
        """Generate a spending trend report.

        Args:
            days: Number of days to look back.

        Returns:
            Formatted trend report string.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Daily spending trend
        daily_spending = self.db.fetchall(
            """
            SELECT date,
                   SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as daily_expenses,
                   SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as daily_income
            FROM transactions
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date ASC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        lines = [
            "=" * 60,
            "  Spending Trend Report",
            "=" * 60,
            f"  Period: {start_date} to {end_date} ({days} days)",
            "=" * 60,
            f"  {'Date':<12} {'Income':>12} {'Expenses':>12} {'Net':>12}",
            "  " + "-" * 48,
        ]

        for day in daily_spending:
            net = day["daily_income"] - day["daily_expenses"]
            lines.append(
                f"  {day['date']:<12} "
                f"${day['daily_income']:>11.2f} ${day['daily_expenses']:>11.2f} "
                f"${net:>11.2f}"
            )

        # Weekly summary
        lines.append("")
        lines.append("  Weekly Summary:")
        lines.append("  " + "-" * 40)

        weeks = self.db.fetchall(
            """
            SELECT
                MIN(date) as week_start,
                MAX(date) as week_end,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses
            FROM transactions
            WHERE date >= ? AND date <= ?
            GROUP BY strftime('%W', date)
            ORDER BY week_start ASC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        for week in weeks:
            lines.append(
                f"    {week['week_start']} to {week['week_end']}: "
                f"Income ${week['income']:.2f}, Expenses ${week['expenses']:.2f}"
            )

        lines.append("")
        return "\n".join(lines)
