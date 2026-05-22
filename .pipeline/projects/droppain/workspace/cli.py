"""CLI entry point for droppain.

Provides command-line interface for campaign management.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Optional

from droppain.config import Config, get_config
from droppain.executor import CampaignExecutor
from droppain.health_check import run_health_check
from droppain.models import Product, Variant
from droppain.planner import CampaignPlanner

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def cmd_health_check(args: argparse.Namespace) -> int:
    """Run health check command."""
    fix = getattr(args, "fix", False)
    json_output = getattr(args, "json", False)

    findings = run_health_check(fix=fix)

    if json_output:
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            severity = finding.severity.upper()
            print(f"[{severity}] {finding.check}: {finding.message}")
            if finding.fixed:
                print(f"  -> Fixed")

    # Return non-zero if there are errors or critical issues
    has_errors = any(f.severity in ("error", "critical") for f in findings)
    return 1 if has_errors else 0


def cmd_create_plan(args: argparse.Namespace) -> int:
    """Create a campaign plan command."""
    config = get_config()
    planner = CampaignPlanner(config=config)

    # Parse products from JSON file
    products = []
    if args.products:
        with open(args.products) as f:
            data = json.load(f)
            for p in data:
                variants = [Variant(**v) for v in p.get("variants", [])]
                product = Product(
                    id=p["id"],
                    title=p["title"],
                    description=p.get("description", ""),
                    price=p["price"],
                    variants=variants,
                    tags=p.get("tags", []),
                )
                products.append(product)

    if not products:
        print("No products provided. Use --products with a JSON file.")
        return 1

    campaign_name = getattr(args, "name", None)
    total_budget = getattr(args, "budget", None)

    plan = planner.create_plan(
        products=products,
        campaign_name=campaign_name,
        total_budget=total_budget,
    )

    if getattr(args, "json", False):
        plan_dict = {
            "campaign_name": plan.campaign_name,
            "total_budget": plan.total_budget,
            "channels": [
                {
                    "platform": ch.platform,
                    "frequency": ch.frequency,
                    "budget": ch.budget,
                    "target_audience": ch.target_audience,
                }
                for ch in plan.channels
            ],
            "content_briefs": [
                {
                    "title": b.title,
                    "copy": b.copy,
                    "platform": b.platform,
                    "target_audience": b.target_audience,
                }
                for b in plan.content_briefs
            ],
        }
        print(json.dumps(plan_dict, indent=2))
    else:
        print(f"Campaign: {plan.campaign_name}")
        print(f"Budget: ${plan.total_budget:.2f}")
        print(f"Channels: {len(plan.channels)}")
        print(f"Content Briefs: {len(plan.content_briefs)}")

    return 0


def cmd_execute(args: argparse.Namespace) -> int:
    """Execute a campaign command."""
    executor = CampaignExecutor()

    # Load plan from JSON file
    with open(args.plan) as f:
        plan_data = json.load(f)

    # Reconstruct plan (simplified)
    from droppain.planner import CampaignPlan, ChannelConfig, ContentBrief

    channels = [
        ChannelConfig(**ch) for ch in plan_data.get("channels", [])
    ]
    briefs = [
        ContentBrief(**b) for b in plan_data.get("content_briefs", [])
    ]

    plan = CampaignPlan(
        campaign_name=plan_data["campaign_name"],
        channels=channels,
        content_briefs=briefs,
        schedule=[],
        total_budget=plan_data["total_budget"],
    )

    result = executor.execute(plan)

    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
    else:
        print(f"Status: {result['status']}")
        print(f"Results: {len(result.get('results', []))} channels")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="droppain",
        description="Droppain - Automated Dropshipping Campaign Manager",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Health check command
    health_parser = subparsers.add_parser("health", help="Run health checks")
    health_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    health_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Create plan command
    plan_parser = subparsers.add_parser("plan", help="Create a campaign plan")
    plan_parser.add_argument("--products", required=True, help="Path to products JSON file")
    plan_parser.add_argument("--name", help="Campaign name")
    plan_parser.add_argument("--budget", type=float, help="Total budget")
    plan_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Execute command
    exec_parser = subparsers.add_parser("execute", help="Execute a campaign")
    exec_parser.add_argument("--plan", required=True, help="Path to plan JSON file")
    exec_parser.add_argument("--json", action="store_true", help="Output as JSON")

    return parser


def main(argv: Optional[list] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    setup_logging(args.log_level)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "health":
        return cmd_health_check(args)
    elif args.command == "plan":
        return cmd_create_plan(args)
    elif args.command == "execute":
        return cmd_execute(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
