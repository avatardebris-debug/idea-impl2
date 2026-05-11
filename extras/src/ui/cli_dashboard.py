"""CLI dashboard for BudgetFlow Tracker."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from src.core.database import Database
from src.categorize.rule_engine import Categorizer
from src.budget.engine import BudgetEngine

logger = logging.getLogger(__name__)


class CLIDashboard:
    """Command-line dashboard for BudgetFlow Tracker."""

    def __init__(self, db: Database):
        self.db = db
        self.categorizer = Categorizer(db)
        self.budget_engine = BudgetEngine(db)

    def display_summary(self) -> None:
        """Display financial summary."""
        print("\n" + "=" * 50)
        print("       BUDGETFLOW TRACKER - SUMMARY")
        print("=" * 50)

        # Get current month stats
        today = date.today()
        start_of_month = date(today.year, today.month, 1)

        income = self.db.fetchone(
            """SELECT COALESCE(SUM(amount), 0) as total
               FROM transactions
               WHERE date >= ?
               AND transaction_type = 'income'""",
            (start_of_month.isoformat(),),
        )

        expenses = self.db.fetchone(
            """SELECT COALESCE(SUM(ABS(amount)), 0) as total
               FROM transactions
               WHERE date >= ?
               AND transaction_type = 'expense'""",
            (start_of_month.isoformat(),),
        )

        print(f"\n📊 Current Month ({today.strftime('%B %Y')}):")
        print(f"   Income:   ${income['total']:>10,.2f}")
        print(f"   Expenses: ${expenses['total']:>10,.2f}")
        print(f"   Net:      ${income['total'] - expenses['total']:>10,.2f}")

        # Budget status
        budgets = self.budget_engine.get_all_budgets()
        if budgets:
            print("\n💰 Budget Status:")
            for budget in budgets:
                status = "✅" if budget.percentage_used < 80 else "⚠️" if budget.percentage_used < 100 else "❌"
                print(f"   {status} {budget.category_name}: ${budget.spent:.2f} / ${budget.budget_amount:.2f} ({budget.percentage_used:.1f}%)")

        print("\n" + "=" * 50)

    def display_recent_transactions(self, limit: int = 10) -> None:
        """Display recent transactions."""
        print("\n" + "=" * 50)
        print("       RECENT TRANSACTIONS")
        print("=" * 50)

        transactions = self.db.fetchall(
            """SELECT date, description, amount, category_name
               FROM transactions
               ORDER BY date DESC
               LIMIT ?""",
            (limit,),
        )

        if not transactions:
            print("   No transactions found.")
            return

        print(f"\n   {'Date':<12} {'Description':<25} {'Amount':>10}")
        print("   " + "-" * 47)

        for t in transactions:
            amount_str = f"${abs(t['amount']):,.2f}"
            if t['amount'] < 0:
                amount_str = f"-{amount_str}"
            else:
                amount_str = f"+{amount_str}"

            print(f"   {t['date']:<12} {t['description']:<25} {amount_str:>10}")

        print("\n" + "=" * 50)

    def display_budget_alerts(self) -> None:
        """Display budget alerts."""
        alerts = self.budget_engine.get_budget_alerts()

        if not alerts:
            print("\n✅ No budget alerts.")
            return

        print("\n" + "=" * 50)
        print("       BUDGET ALERTS")
        print("=" * 50)

        for alert in alerts:
            icon = "🚨" if alert['type'] == 'critical' else "⚠️"
            print(f"\n   {icon} {alert['message']}")
            print(f"      Remaining: ${alert['remaining']:.2f}")

        print("\n" + "=" * 50)

    def add_transaction(self, description: str, amount: float, date_str: Optional[str] = None) -> None:
        """Add a new transaction."""
        if date_str is None:
            date_str = date.today().isoformat()

        # Auto-categorize
        result = self.categorizer.categorize(description, amount)

        transaction_type = "expense" if amount < 0 else "income"

        self.db.execute(
            """INSERT INTO transactions
               (date, description, amount, transaction_type, category_name)
               VALUES (?, ?, ?, ?, ?)""",
            (date_str, description, amount, transaction_type, result.category_name),
        )

        print(f"\n✅ Transaction added:")
        print(f"   Date: {date_str}")
        print(f"   Description: {description}")
        print(f"   Amount: ${abs(amount):,.2f}")
        print(f"   Category: {result.category_name} (confidence: {result.confidence:.2f})")

    def add_budget(self, category_name: str, amount: float, period: str = "monthly") -> None:
        """Add a new budget."""
        budget_id = self.budget_engine.create_budget(category_name, amount, period)
        print(f"\n✅ Budget created:")
        print(f"   Category: {category_name}")
        print(f"   Amount: ${amount:,.2f}/{period}")
        print(f"   Budget ID: {budget_id}")

    def show_help(self) -> None:
        """Display help information."""
        print("\n" + "=" * 50)
        print("       BUDGETFLOW TRACKER - HELP")
        print("=" * 50)

        print("\n📋 Commands:")
        print("   summary          - Show financial summary")
        print("   transactions     - Show recent transactions")
        print("   alerts           - Show budget alerts")
        print("   add <desc> <amt> - Add transaction")
        print("   budget <cat> <amt> - Add budget")
        print("   help             - Show this help")
        print("   quit             - Exit application")

        print("\n💡 Tips:")
        print("   - Use 'summary' to see your financial overview")
        print("   - Use 'alerts' to check for budget warnings")
        print("   - Transactions are auto-categorized when added")

        print("\n" + "=" * 50)
