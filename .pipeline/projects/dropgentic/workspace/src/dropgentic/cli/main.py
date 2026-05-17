"""CLI entry point for DropGentic.

Provides commands for:
- planning: Generate sourcing plans from products and suppliers
- config: Manage configuration
- validate: Validate product/supplier data
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from dropgentic.config.settings import Settings
from dropgentic.planner.engine import PlannerEngine
from dropgentic.models.product import Product
from dropgentic.models.supplier import Supplier
from dropgentic.models.margin import MarginCalculator


def _load_products(path: str) -> list:
    """Load products from a JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("products", [data])
    return [Product.from_dict(p) for p in data]


def _load_suppliers(path: str) -> list:
    """Load suppliers from a JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("suppliers", [data])
    return [Supplier.from_dict(s) for s in data]


def _format_table(recommendations: list) -> str:
    """Format recommendations as a table."""
    if not recommendations:
        return "No recommendations found."

    # Column headers
    headers = ["Rank", "Product", "Supplier", "Net Margin %", "Gross Margin %", "Action"]
    col_widths = [max(len(h), 6) for h in headers]

    rows = []
    for r in recommendations:
        rows.append([
            str(r.rank),
            r.product_title[:20],
            r.supplier_name[:20],
            f"{r.margin_result.net_margin_pct:.1f}%",
            f"{r.margin_result.gross_margin_pct:.1f}%",
            r.margin_result.recommended_action.split(" — ")[0],
        ])

    # Calculate column widths
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    # Format table
    def format_row(cells: list) -> str:
        return " | ".join(f"{c:<{col_widths[i]}}" for i, c in enumerate(cells))

    lines = [format_row(headers), "-" * (sum(col_widths) + len(col_widths) * 3 - 1)]
    for row in rows:
        lines.append(format_row(row))
    return "\n".join(lines)


def _format_json(recommendations: list, plan) -> str:
    """Format recommendations as JSON."""
    output = plan.to_dict()
    return json.dumps(output, indent=2)


def cmd_planning(args: argparse.Namespace) -> int:
    """Execute the planning command."""
    # Load data
    products = _load_products(args.products)
    suppliers = _load_suppliers(args.suppliers)

    # Load settings
    settings = Settings(config_path=args.config)

    # Create planner
    margin_calc = MarginCalculator(
        platform_fee_pct=settings.default_margin.get("platform_fee_pct", 0.15),
        payment_processing_fee_pct=settings.default_margin.get("payment_processing_fee_pct", 0.029),
        fixed_payment_fee=settings.default_margin.get("fixed_payment_fee", 0.30),
        currency=settings.default_margin.get("currency", "USD"),
    )

    planner = PlannerEngine(
        margin_calculator=margin_calc,
        min_net_margin_pct=settings.planner.get("min_net_margin_pct", 5.0),
        max_recommendations=settings.planner.get("max_recommendations", 50),
    )

    # Generate plan
    plan = planner.generate_plan(products, suppliers)

    # Filter if requested
    if args.min_margin:
        plan = planner.filter_by_margin(plan, args.min_margin)

    if args.supplier_ids:
        plan = planner.filter_by_supplier(plan, args.supplier_ids)

    # Output
    fmt = args.format or settings.output.get("format", "table")
    if fmt == "json":
        print(_format_json(plan.recommendations, plan))
    else:
        print(f"\n=== Sourcing Plan ===\n")
        print(plan.summary)
        print(f"\nTop {min(len(plan.recommendations), 10)} Recommendations:\n")
        print(_format_table(plan.recommendations[:10]))
        if len(plan.recommendations) > 10:
            print(f"\n... and {len(plan.recommendations) - 10} more recommendations")

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Execute the config command."""
    settings = Settings(config_path=args.config)

    if args.action == "show":
        print(json.dumps(settings.as_dict, indent=2))
    elif args.action == "set":
        if not args.key or not args.value:
            print("Error: --key and --value required", file=sys.stderr)
            return 1
        settings.set(args.key, args.value)
        print(f"Set {args.key} = {args.value}")
    elif args.action == "get":
        if not args.key:
            print("Error: --key required", file=sys.stderr)
            return 1
        value = settings.get(args.key)
        print(value if value is not None else "Not found")
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        return 1

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute the validate command."""
    errors = []
    warnings = []

    # Validate products
    if args.products:
        try:
            products = _load_products(args.products)
            for i, p in enumerate(products):
                if p.gross_margin <= 0:
                    errors.append(f"Product {i+1} ({p.title}): No gross margin")
                if p.weight_kg <= 0:
                    warnings.append(f"Product {i+1} ({p.title}): Weight <= 0")
        except Exception as e:
            errors.append(f"Products file error: {e}")

    # Validate suppliers
    if args.suppliers:
        try:
            suppliers = _load_suppliers(args.suppliers)
            for i, s in enumerate(suppliers):
                if s.rating < 3.0:
                    warnings.append(f"Supplier {i+1} ({s.name}): Low rating ({s.rating})")
                if s.lead_time_days > 30:
                    warnings.append(f"Supplier {i+1} ({s.name}): Long lead time ({s.lead_time_days} days)")
        except Exception as e:
            errors.append(f"Suppliers file error: {e}")

    if errors:
        print("Errors:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        return 1
    return 0


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="dropgentic",
        description="Dropshipping and agentic commerce planner",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Planning command
    plan_parser = subparsers.add_parser("plan", help="Generate sourcing plan")
    plan_parser.add_argument("--products", required=True, help="Path to products JSON file")
    plan_parser.add_argument("--suppliers", required=True, help="Path to suppliers JSON file")
    plan_parser.add_argument("--config", help="Path to config file")
    plan_parser.add_argument("--format", choices=["table", "json"], help="Output format")
    plan_parser.add_argument("--min-margin", type=float, help="Minimum net margin percentage")
    plan_parser.add_argument("--supplier-ids", nargs="+", help="Filter by supplier IDs")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("--config", help="Path to config file")
    config_parser.add_argument("action", choices=["show", "set", "get"], help="Config action")
    config_parser.add_argument("--key", help="Configuration key")
    config_parser.add_argument("--value", help="Configuration value")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate data files")
    validate_parser.add_argument("--products", help="Path to products JSON file")
    validate_parser.add_argument("--suppliers", help="Path to suppliers JSON file")

    args = parser.parse_args(argv)

    if args.command == "plan":
        return cmd_planning(args)
    elif args.command == "config":
        return cmd_config(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
