"""CLI entry point for url_health_checker."""

import argparse
import sys

from url_health_checker.checker import check_urls
from url_health_checker.formatter import format_results


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 = all up, 1 = some down, 2 = error).
    """
    parser = argparse.ArgumentParser(
        description="Check the health of one or more URLs."
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="URLs to check (e.g. http://example.com http://google.com)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for each request (default: 5.0)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Max concurrent workers (default: 10)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args(argv)

    try:
        results = check_urls(
            args.urls, timeout=args.timeout, max_workers=args.workers
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(format_results(results, fmt=args.format))

    # Exit code: 0 if all up, 1 if any down
    if any(not r["up"] for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
