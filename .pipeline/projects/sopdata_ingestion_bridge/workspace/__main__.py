"""CLI entry point for SOPData Ingestion Bridge.

Usage:
    python -m sopdata_ingestion_bridge --csv sample_data.csv
    python -m sopdata_ingestion_bridge --csv data.csv --format table
    python -m sopdata_ingestion_bridge --csv data.csv --mapping custom.json
"""

import argparse
import json
import sys
from typing import Dict, List, Optional

from sopdata_ingestion_bridge.bridge import SOPBridge
from sopdata_ingestion_bridge.models import SOPInputRow


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="sopdata-ingestion-bridge",
        description="Ingest CSV files and convert them into structured SOP input data.",
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--mapping",
        default=None,
        help="Path to a JSON file containing a custom column mapping.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Output format: 'json' (default) or 'table'.",
    )
    return parser


def _load_mapping(mapping_path: str) -> Dict[str, str]:
    """Load a custom mapping from a JSON file."""
    with open(mapping_path, "r", encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def _format_as_json(rows: List[SOPInputRow]) -> str:
    """Format SOP rows as a JSON string."""
    return json.dumps([row.to_dict() for row in rows], indent=2, ensure_ascii=False)


def _format_as_table(rows: List[SOPInputRow]) -> str:
    """Format SOP rows as a human-readable table."""
    if not rows:
        return "(no data)"

    headers = ["task_name", "description", "steps", "assignee", "deadline", "priority"]
    # Calculate column widths
    widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            val = getattr(row, h, "")
            widths[h] = max(widths[h], len(val))

    # Build separator
    sep = "+" + "+".join("-" * (widths[h] + 2) for h in headers) + "+"

    # Build header row
    header_line = "|" + "|".join(
        f" {h:<{widths[h]}} " for h in headers
    ) + "|"

    lines = [sep, header_line, sep]
    for row in rows:
        line = "|" + "|".join(
            f" {getattr(row, h, ''):<{widths[h]}} " for h in headers
        ) + "|"
        lines.append(line)
    lines.append(sep)
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> None:
    """Main CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Load custom mapping if provided
    mapping = None
    if args.mapping:
        mapping = _load_mapping(args.mapping)

    # Ingest
    bridge = SOPBridge()
    rows = bridge.ingest(args.csv, mapping=mapping)

    # Format and print
    if args.format == "json":
        print(_format_as_json(rows))
    else:
        print(_format_as_table(rows))


if __name__ == "__main__":
    main()
