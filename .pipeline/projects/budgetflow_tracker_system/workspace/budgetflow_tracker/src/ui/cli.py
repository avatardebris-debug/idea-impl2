"""CLI interface for BudgetFlow Tracker."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from typing import Optional

from src.core.database import Database, get_database, reset_database
from src.core.config import Config
from src.categorize.rule_engine import Categorizer
import importlib
csv_parser = importlib.import_module("src.import.csv_parser")
from src.budget.engine import BudgetEngine
from src.ui.cli_dashboard import DashboardCLI
from src.ui.cli_budget import BudgetCLI
from src.reports.summary import ReportGenerator

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="budgetflow",
        description="BudgetFlow Tracker - Personal budget management CLI",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--db", type=str, help="Database path (default: ~/.budgetflow/budget.db)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Show financial dashboard")
    dash_parser.add_argument("--days", type=int, default=30, help="Days to look back")

    # Transactions
    txn_parser = subparsers.add_parser("transactions", help="Manage transactions")
    txn_sub = txn_parser.add_subparsers(dest="subcommand")

    add_txn = txn_sub.add_parser("add", help="Add a transaction")
    add_txn.add_argument("description", type=str, help="Transaction description")
    add_txn.add_argument("amount", type=float, help="Transaction amount (negative for expense)")
    add_txn.add_argument("--date", type=str, default=date.today().isoformat(), help="Date (YYYY-MM-DD)")
    add_txn.add_argument("--category", type=str, help="Category name")
    add_txn.add_argument("--account", type=str, help="Account name")

    list_txn = txn_sub.add_parser("list", help="List transactions")
    list_txn.add_argument("--days", type=int, default=7, help="Days to look back")
    list_txn.add_argument("--limit", type=int, default=20, help="Max transactions to show")

    # Import
    import_parser = subparsers.add_parser("import", help="Import bank statements")
    import_parser.add_argument("file", type=str, help="CSV file path")
    import_parser.add_argument("--account", type=str, help="Account to import to")
    import_parser.add_argument("--dry-run", action="store_true", help="Preview without importing")

    # Budget
    budget_parser = subparsers.add_parser("budget", help="Manage budgets")
    budget_sub = budget_parser.add_subparsers(dest="subcommand")

    add_budget = budget_sub.add_parser("add", help="Add a budget")
    add_budget.add_argument("category", type=str, help="Category name")
    add_budget.add_argument("amount", type=float, help="Budget amount")
    add_budget.add_argument("--period", type=str, default="monthly", choices=["monthly", "weekly"])
    add_budget.add_argument("--rollover", action="store_true", help="Enable rollover")

    update_budget = budget_sub.add_parser("update", help="Update a budget")
    update_budget.add_argument("category", type=str, help="Category name")
    update_budget.add_argument("amount", type=float, help="New budget amount")

    show_budget = budget_sub.add_parser("show", help="Show budget status")
    show_budget.add_argument("category", type=str, help="Category name")

    # Categories
    cat_parser = subparsers.add_parser("categories", help="Manage categories")
    cat_sub = cat_parser.add_subparsers(dest="subcommand")

    list_cats = cat_sub.add_parser("list", help="List categories")

    # Reports
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_parser.add_argument("type", type=str, choices=["summary", "category", "trend"], help="Report type")
    report_parser.add_argument("--days", type=int, default=30, help="Days to look back")

    # Rules
    rule_parser = subparsers.add_parser("rules", help="Manage categorization rules")
    rule_sub = rule_parser.add_subparsers(dest="subcommand")

    list_rules = rule_sub.add_parser("list", help="List all rules")

    add_rule = rule_sub.add_parser("add", help="Add a rule")
    add_rule.add_argument("name", type=str, help="Rule name")
    add_rule.add_argument("keywords", type=str, help="Comma-separated keywords")
    add_rule.add_argument("category", type=str, help="Category name")
    add_rule.add_argument("--priority", type=int, default=5, help="Rule priority")
    add_rule.add_argument("--confidence", type=float, default=0.8, help="Confidence score")

    remove_rule = rule_sub.add_parser("remove", help="Remove a rule")
    remove_rule.add_argument("name", type=str, help="Rule name")

    return parser


def get_db_path(args) -> str:
    """Get database path from args or config."""
    if args.db:
        return args.db
    config = Config()
    return config.get("database.path", "~/.budgetflow/budget.db")


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    # Initialize database
    reset_database()
    db_path = get_db_path(args)
    db = get_database(db_path)
    db.init_schema()
    db.seed_default_data()

    categorizer = Categorizer(db)
    csv_parser = csv_parser.CSVParser(db)
    budget_engine = BudgetEngine(db)
    dashboard = DashboardCLI(db)
    budget_cli = BudgetCLI(db)
    report_gen = ReportGenerator(db)

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "dashboard":
            print(dashboard.show_overview(days=args.days))

        elif args.command == "transactions":
            if args.subcommand == "add":
                # Auto-categorize if no category given
                category = args.category
                if not category:
                    result = categorizer.categorize(args.description, args.amount)
                    category = result.category_name
                    print(f"Auto-categorized as: {category}")

                db.execute(
                    """INSERT INTO transactions
                       (date, description, amount, transaction_type, category_name, merchant)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        args.date,
                        args.description,
                        args.amount,
                        "credit" if args.amount > 0 else "debit",
                        category,
                        args.description,
                    ),
                )
                print(f"Transaction added: {args.description} - ${abs(args.amount):.2f}")

            elif args.subcommand == "list":
                print(dashboard.show_transactions(days=args.days, limit=args.limit))

        elif args.command == "import":
            with open(args.file, "r") as f:
                csv_content = f.read()

            bank_format = csv_parser.detect_format(csv_content)
            print(f"Detected format: {bank_format.name}")

            transactions = csv_parser.parse(csv_content, bank_format)
            errors = csv_parser.validate_transactions(transactions)

            if errors:
                print(f"\nValidation errors ({len(errors)}):")
                for err in errors:
                    print(f"  Row {err['row']}: {err['field']} - {err['message']}")

            print(f"\nParsed {len(transactions)} transactions")

            if not args.dry_run:
                db.execute("BEGIN TRANSACTION")
                try:
                    for txn in transactions:
                        db.execute(
                            """INSERT INTO transactions
                               (date, description, amount, transaction_type, category_name, merchant)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                txn.date.isoformat(),
                                txn.description,
                                txn.amount,
                                "credit" if txn.amount > 0 else "debit",
                                txn.description,
                                txn.description,
                            ),
                        )
                    db.execute("COMMIT")
                    print(f"Imported {len(transactions)} transactions successfully")
                except Exception as e:
                    db.execute("ROLLBACK")
                    print(f"Import failed: {str(e)}")
                    return 1

        elif args.command == "budget":
            if args.subcommand == "add":
                print(budget_cli.add_budget(
                    category_name=args.category,
                    amount=args.amount,
                    period=args.period,
                    rollover=args.rollover,
                ))
            elif args.subcommand == "update":
                print(budget_cli.update_budget(args.category, args.amount))
            elif args.subcommand == "show":
                print(budget_cli.show_summary(args.category))

        elif args.command == "categories":
            if args.subcommand == "list":
                print(dashboard.show_categories())

        elif args.command == "report":
            if args.type == "summary":
                print(report_gen.generate_summary(days=args.days))
            elif args.type == "category":
                print(report_gen.generate_category_report(days=args.days))
            elif args.type == "trend":
                print(report_gen.generate_trend_report(days=args.days))

        elif args.command == "rules":
            if args.subcommand == "list":
                rules = categorizer.get_all_rules()
                print(f"  {'Name':<20} {'Keywords':<30} {'Category':<20} {'Priority':>8}")
                print("  " + "-" * 78)
                for rule in rules:
                    print(
                        f"  {rule['name']:<20} {rule['keywords']:<30} "
                        f"{rule['category_name']:<20} {rule['priority']:>8}"
                    )
            elif args.subcommand == "add":
                keywords = [k.strip() for k in args.keywords.split(",")]
                categorizer.add_rule(
                    name=args.name,
                    keywords=keywords,
                    category_name=args.category,
                    priority=args.priority,
                    confidence=args.confidence,
                )
                print(f"Rule added: {args.name}")
            elif args.subcommand == "remove":
                categorizer.remove_rule(args.name)
                print(f"Rule removed: {args.name}")

        else:
            parser.print_help()

    except Exception as e:
        logger.exception("Error: %s", str(e))
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
