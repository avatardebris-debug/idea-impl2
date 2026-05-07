"""CLI entry point for URL Health Checker."""

import argparse
import sys
from typing import List, Optional

from .checker import URLChecker
from .concurrent import check_urls_concurrent
from .logging_config import setup_logging, log_check_result
from .output import format_results, format_table


def _read_urls(path: str) -> List[str]:
    """Read URLs from a text file, one per line, stripping blanks."""
    with open(path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Check the health of URLs via HEAD requests."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to a text file with one URL per line.",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=10,
        help="Request timeout in seconds (default 10).",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=5,
        help="Max concurrent workers (default 5).",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Path to write structured JSON logs. Default: stdout.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default INFO).",
    )
    parser.add_argument(
        "--format",
        default="table",
        choices=["table", "json", "csv", "html"],
        help="Output format (default: table).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Max retry attempts per URL (default 1 = no retry).",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="Seconds between retry attempts (default 1.0).",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=None,
        help="Max requests per second (default: unlimited).",
    )

    args = parser.parse_args(argv)

    # Set up logging
    logger = setup_logging(log_file=args.log_file, log_level=args.log_level)

    # Log startup
    if logger:
        logger.info("URL Health Checker starting", extra={
            "url": None,
            "status_code": None,
            "response_time_ms": None,
            "is_up": None,
        })

    # Read URLs
    urls = _read_urls(args.input)
    if not urls:
        print("Error: No URLs found in input file.", file=sys.stderr)
        sys.exit(1)

    if logger:
        logger.info(f"Checking {len(urls)} URLs", extra={
            "url": None,
            "status_code": None,
            "response_time_ms": None,
            "is_up": None,
        })

    # Run checks
    results = check_urls_concurrent(
        urls=urls,
        max_workers=args.workers,
        timeout=args.timeout,
        max_attempts=args.retries,
        retry_delay=args.retry_delay,
        rate_limit=args.rate_limit,
        logger=logger,
    )

    # Format and print output
    output = format_results(results, fmt=args.format)
    print(output)

    # Log shutdown
    if logger:
        logger.info("URL Health Checker finished", extra={
            "url": None,
            "status_code": None,
            "response_time_ms": None,
            "is_up": None,
        })

    # Exit with code 1 if any URL is down
    if any(not r["is_up"] for r in results):
        sys.exit(1)


# Keep _format_table for backward compatibility with existing tests
_format_table = format_table


if __name__ == "__main__":
    main()
