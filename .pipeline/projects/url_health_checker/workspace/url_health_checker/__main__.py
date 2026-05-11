"""CLI entry point for URL Health Checker."""

import argparse
import sys

from url_health_checker.loader import load_urls
from url_health_checker.checker import check_urls
from url_health_checker.formatter import format_results


def main():
    parser = argparse.ArgumentParser(
        prog="url_health_checker",
        description="Check the health of URLs via HEAD requests.",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to a text file containing URLs (one per line).",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=5.0,
        help="Timeout in seconds for each URL check (default: 5.0).",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=10,
        help="Maximum number of concurrent workers (default: 10).",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format: text (default) or json.",
    )
    args = parser.parse_args()

    # Load URLs
    urls = load_urls(args.input)

    # Check URLs
    results = check_urls(urls, timeout=args.timeout, max_workers=args.workers)

    # Format and print report
    output = format_results(results, fmt=args.format)
    print(output)


if __name__ == "__main__":
    main()
