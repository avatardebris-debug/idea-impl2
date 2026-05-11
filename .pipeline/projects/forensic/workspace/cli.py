"""Forensic CLI module."""

import argparse
import sys


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Forensic SEC filing analyzer")
    subparsers = parser.add_subparsers(dest="command")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest SEC filings")
    ingest_parser.add_argument("--ticker", required=True, help="Stock ticker")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze filings for fraud risk")
    analyze_parser.add_argument("--ticker", required=True, help="Stock ticker")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate comparative report")
    report_parser.add_argument("--ticker", required=True, help="Stock ticker")

    parsed = parser.parse_args(args)
    return parsed


def main(args=None):
    """Main entry point."""
    if args is None:
        args = sys.argv[1:]

    parsed = parse_args(args)

    if parsed is None or parsed.command is None:
        return 1

    if parsed.command == "ingest":
        print(f"Ingesting ticker: {parsed.ticker}")
    elif parsed.command == "analyze":
        print(f"Analyzing ticker: {parsed.ticker}")
    elif parsed.command == "report":
        print(f"Generating report for ticker: {parsed.ticker}")

    return 0
