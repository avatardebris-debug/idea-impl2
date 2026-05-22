"""Command-line interface for the JSON diff tool."""

import argparse
import sys
from .loader import load_json
from .diff import compare_json
from .formatter import format_diff


def create_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="json_diff_tool",
        description="Compare two JSON files and display the differences."
    )
    parser.add_argument(
        "file1",
        help="Path to the first JSON file"
    )
    parser.add_argument(
        "file2",
        help="Path to the second JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Load JSON files
        obj1 = load_json(args.file1)
        obj2 = load_json(args.file2)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        return 1

    # Compute diff
    diff_entries = compare_json(obj1, obj2)

    # Format and display output
    if args.output == "json":
        import json
        print(json.dumps(diff_entries, indent=2))
    else:
        print(format_diff(diff_entries))

    return 0


if __name__ == "__main__":
    sys.exit(main())
