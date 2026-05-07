"""CLI interface for SEC Importer."""

import argparse
import sys


def main():
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="sec_importer",
        description="Fetch, parse, and display SEC EDGAR filing data.",
    )
    parser.add_argument("ticker", help="Company ticker symbol (e.g. AAPL)")
    parser.add_argument(
        "--type",
        dest="filing_type",
        default="10-K",
        help="Filing type to fetch (default: 10-K)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: print to stdout)",
    )
    args = parser.parse_args()

    print(f"Fetching latest {args.filing_type} for {args.ticker}...")
    print("Done.")


if __name__ == "__main__":
    main()
