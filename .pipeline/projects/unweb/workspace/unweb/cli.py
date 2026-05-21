"""
cli.py — unweb command-line interface.

Usage:
    python -m unweb "https://reuters.com/some-article"
    python -m unweb "https://..." --no-enrich --output report.md
    python -m unweb --text-input "EPA official joins ExxonMobil board..."
    python -m unweb "https://..." --format json
"""
from __future__ import annotations
import argparse
import json
import sys
import textwrap
import time


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="unweb",
        description=textwrap.dedent("""\
            unweb — Unmask the connections behind any news story.

            Given a news story URL or raw text, maps people, organizations,
            funding sources, and cross-connections into a structured report.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="URL of the article, or raw text (with --text-input).",
    )
    parser.add_argument(
        "--text-input",
        action="store_true",
        help="Treat source as raw article text instead of a URL.",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip Wikipedia enrichment step.",
    )
    parser.add_argument(
        "--max-entities",
        type=int,
        default=10,
        help="Maximum number of entities to enrich (default: 10).",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Write report to this file path.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="HTTP timeout in seconds (default: 15).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="unweb 0.1.0",
    )

    args = parser.parse_args()

    if not args.source:
        parser.print_help()
        sys.exit(1)

    # Import here to avoid circular imports
    from unweb.api import run

    result = run(
        args.source,
        source_type="text" if args.text_input else "url",
        enrich_entities=not args.no_enrich,
        max_entities=args.max_entities,
        output_path=args.output,
        format=args.format,
    )

    # Print report to stdout
    print(result.report)

    # Print summary to stderr
    errors = result.errors
    enriched = "enriched" if result.enriched else "not enriched"
    print(
        f"\n[unweb] Source: {result.source}\n"
        f"[unweb] Entities: {enriched}\n"
        f"[unweb] Errors: {len(errors)}",
        file=sys.stderr,
    )
    if errors:
        for err in errors:
            print(f"  [unweb]   - {err}", file=sys.stderr)

    if args.output:
        print(f"[unweb] Report saved to: {args.output}", file=sys.stderr)

    # Exit code: 0 if no errors, 1 if there were errors
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
