"""CLI entry point for DropGentic."""

import argparse
import sys
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point for dropgentic."""
    parser = argparse.ArgumentParser(
        prog="dropgentic",
        description="Dropshipping and agentic commerce planner",
    )
    subparsers = parser.add_subparsers(dest="command")

    # plan subcommand
    plan_parser = subparsers.add_parser("plan", help="Generate a sourcing plan")
    plan_parser.add_argument(
        "--products", "-p",
        required=True,
        help="Path to products JSON file",
    )
    plan_parser.add_argument(
        "--suppliers", "-s",
        required=True,
        help="Path to suppliers JSON file",
    )
    plan_parser.add_argument(
        "--config", "-c",
        default=None,
        help="Path to config file (YAML or JSON)",
    )
    plan_parser.add_argument(
        "--min-margin",
        type=float,
        default=None,
        help="Minimum net margin percentage",
    )
    plan_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default=None,
        help="Output format",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "plan":
        from dropgentic.commands import run_plan
        run_plan(args)


if __name__ == "__main__":
    main()
