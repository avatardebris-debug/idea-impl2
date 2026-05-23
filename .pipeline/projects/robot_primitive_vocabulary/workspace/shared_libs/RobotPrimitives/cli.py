"""CLI interface for RobotPrimitives library.

Provides a command-line tool to list, describe, and instantiate
canonical robot action primitives.

Usage:
    python -m shared_libs.RobotPrimitives.cli list
    python -m shared_libs.RobotPrimitives.cli describe <primitive_name>
    python -m shared_libs.RobotPrimitives.cli instantiate <primitive_name> [args...]
"""

import argparse
import json
import sys
from typing import Dict, List, Type

from shared_libs.RobotPrimitives import (
    VALID_CATEGORIES,
    load_all_primitives,
    category_map,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="robot-primitives",
        description="Canonical atomic robot action primitives CLI",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # list command
    list_parser = sub.add_parser("list", help="List all available primitives")
    list_parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter by category (locomotion, manipulation, observation, force, control_flow)",
    )
    list_parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    # describe command
    desc_parser = sub.add_parser("describe", help="Describe a primitive in detail")
    desc_parser.add_argument("name", type=str, help="Primitive name (e.g., move_to)")

    # instantiate command
    inst_parser = sub.add_parser("instantiate", help="Instantiate a primitive and print its config")
    inst_parser.add_argument("name", type=str, help="Primitive name")
    inst_parser.add_argument(
        "--args",
        type=str,
        nargs="*",
        default=[],
        help="Keyword arguments as key=value pairs",
    )
    inst_parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    return parser


def _cmd_list(args: argparse.Namespace) -> int:
    """List all primitives, optionally filtered by category."""
    primitives = load_all_primitives()
    cat_map = category_map()

    if args.category:
        cat = args.category.lower()
        if cat not in VALID_CATEGORIES:
            print(f"Error: Unknown category '{args.category}'. Valid: {sorted(VALID_CATEGORIES)}", file=sys.stderr)
            return 1
        primitives = [p for p in primitives if p["category"] == cat]

    if not primitives:
        print("No primitives found.")
        return 0

    if args.format == "json":
        print(json.dumps(primitives, indent=2))
    else:
        # Group by category for display
        by_cat: Dict[str, List[Dict]] = {}
        for p in primitives:
            by_cat.setdefault(p["category"], []).append(p)
        for cat in sorted(by_cat.keys()):
            print(f"\n[{cat.upper()}]")
            for p in by_cat[cat]:
                print(f"  {p['name']:20s}  {p['description'][:50]}")
    return 0


def _cmd_describe(args: argparse.Namespace) -> int:
    """Describe a single primitive in detail."""
    primitives = load_all_primitives()
    for p in primitives:
        if p["name"] == args.name:
            if args.format == "json":
                print(json.dumps(p, indent=2))
            else:
                print(f"Name:        {p['name']}")
                print(f"Category:    {p['category']}")
                print(f"Description: {p['description']}")
                print(f"Parameters:")
                for param in p.get("parameters", []):
                    print(f"  - {param['name']} ({param['type']}): {param['description']}")
                print(f"Returns:     {p.get('returns', 'None')}")
            return 0
    print(f"Error: Unknown primitive '{args.name}'", file=sys.stderr)
    return 1


def _cmd_instantiate(args: argparse.Namespace) -> int:
    """Instantiate a primitive and print its configuration."""
    primitives = _load_all_primitives()
    for p in primitives:
        if p["name"] == args.name:
            # Parse keyword arguments
            kwargs = {}
            for kv in args.args:
                if "=" not in kv:
                    print(f"Error: Argument '{kv}' is not a key=value pair", file=sys.stderr)
                    return 1
                k, v = kv.split("=", 1)
                # Try to convert value types
                try:
                    v = int(v)
                except ValueError:
                    try:
                        v = float(v)
                    except ValueError:
                        if v.lower() in ("true", "false"):
                            v = v.lower() == "true"
                        # else keep as string
                kwargs[k] = v

            # Import and instantiate
            cat = p["category"]
            class_name = p["name"].replace("_", "_")
            module = f"shared_libs.RobotPrimitives.{cat}"
            mod = __import__(module, fromlist=[class_name])
            cls = getattr(mod, class_name)
            instance = cls(**kwargs)

            if args.format == "json":
                print(json.dumps({
                    "name": instance.name,
                    "category": instance.category,
                    "parameters": instance.parameters,
                    "status": instance.status,
                }, indent=2))
            else:
                print(f"Primitive:   {instance.name}")
                print(f"Category:    {instance.category}")
                print(f"Parameters:  {instance.parameters}")
                print(f"Status:      {instance.status}")
            return 0
    print(f"Error: Unknown primitive '{args.name}'", file=sys.stderr)
    return 1


def main(argv=None) -> int:
    """Main entry point for the CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "list":
        return _cmd_list(args)
    elif args.command == "describe":
        return _cmd_describe(args)
    elif args.command == "instantiate":
        return _cmd_instantiate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
