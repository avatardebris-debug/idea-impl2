"""Main entry point for BudgetFlow Tracker CLI."""

from __future__ import annotations

import argparse
import logging
import sys

from src.core.database import Database, get_database, reset_database
from src.core.config import get_config
from src.ui.cli_dashboard import CLIDashboard
from src.reports.generator import ReportGenerator


def setup_logging() -> None:
    """Configure logging."""
    config = get_config()
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    if config.log_file:
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(config.log_file),
            ],
        )


def main() -> None:
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="BudgetFlow Tracker - Personal budget management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add "Grocery shopping" -45.50
  %(prog)s budget "Groceries" 500 monthly
  %(prog)s summary
  %(prog)s report
  %(prog)s reset  # Reset database
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add transaction
    add_parser = subparsers.add_parser("add", help="Add a transaction")
    add_parser.add_argument("description", type=str, help="Transaction description")
    add_parser.add_argument("amount", type=float, help="Transaction amount (negative for expenses)")
    add_parser.add_argument("--date", type=str, help="Transaction date (YYYY-MM-DD)")

    # Add budget
    budget_parser = subparsers.add_parser("budget", help="Add a budget")
    budget_parser.add_argument("category", type=str, help="Category name")
    budget_parser.add_argument("amount", type=float, help="Budget amount")
    budget_parser.add_argument("--period", type=str, default="monthly", choices=["monthly", "weekly"], help="Budget period")

    # Summary
    subparsers.add_parser("summary", help="Show financial summary")

    # Report
    subparsers.add_parser("report", help="Generate report")

    # Reset
    subparsers.add_parser("reset", help="Reset database")

    args = parser.parse_args()

    # Handle reset
    if args.command == "reset":
        reset_database()
        logger.info("Database reset successfully")
        print("✅ Database reset successfully")
        return

    # Initialize database
    db = get_database()

    # Initialize dashboard
    dashboard = CLIDashboard(db)
    report_gen = ReportGenerator(db)

    # Handle commands
    if args.command == "add":
        dashboard.add_transaction(args.description, args.amount, args.date)
    elif args.command == "budget":
        dashboard.add_budget(args.category, args.amount, args.period)
    elif args.command == "summary":
        dashboard.display_summary()
    elif args.command == "report":
        print(report_gen.generate_summary())
        print("\n" + report_gen.generate_budget_report())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
