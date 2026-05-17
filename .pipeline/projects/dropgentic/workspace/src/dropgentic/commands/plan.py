"""Plan command implementation."""

from __future__ import annotations

import argparse
import json
import sys

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


def run_plan(args: argparse.Namespace) -> int:
    """Run the plan command."""
    products = _load_products(args.products)
    suppliers = _load_suppliers(args.suppliers)

    settings = Settings(config_path=args.config)

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

    plan = planner.generate_plan(products, suppliers)

    if args.min_margin:
        plan = planner.filter_by_margin(plan, args.min_margin)

    if args.supplier_ids:
        plan = planner.filter_by_supplier(plan, args.supplier_ids)

    fmt = args.format or settings.output.get("format", "table")
    if fmt == "json":
        print(json.dumps(plan.to_dict(), indent=2))
    else:
        print(f"\n=== Sourcing Plan ===\n")
        print(plan.summary)
        print(f"\nTop {min(len(plan.recommendations), 10)} Recommendations:\n")
        for i, r in enumerate(plan.recommendations[:10]):
            print(f"{i+1}. {r.product_title} via {r.supplier_name}")
            print(f"   Net Margin: {r.margin_result.net_margin_pct:.1f}% | "
                  f"Gross Margin: {r.margin_result.gross_margin_pct:.1f}%")
            print(f"   Action: {r.margin_result.recommended_action}")
            print()
        if len(plan.recommendations) > 10:
            print(f"... and {len(plan.recommendations) - 10} more recommendations")

    return 0
