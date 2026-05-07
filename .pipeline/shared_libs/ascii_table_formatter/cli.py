"""CLI entry point for URL Health Checker."""

import argparse
import sys
from typing import List, Optional

from .checker import URLChecker
from .concurrent import check_urls_concurrent


def _read_urls(path: str) -> List[str]:
    """Read URLs from a text file, one per line, stripping blanks."""
    with open(path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def _format_table(results: list) -> str:
    """Format results as an aligned text table."""
    if not results:
        return "(no results)"
    # Column widths
    url_w = max(len(r["url"]) for r in results)
    url_w = max(url_w, len("URL"))
    status_w = max(len(str(r["status_code"] or "N/A")) for r in results)
    status_w = max(status_w, len("Status"))
    time_w = max(len(f'{r["response_time_ms"] or "N/A"}') for r in results)
    time_w = max(time_w, len("Time (ms)"))
    health_w = max(len("UP" if r["is_up"] else "DOWN") for r in results)
    health_w = max(health_w, len("Status"))

    sep = "+" + "-" * (url_w + 2) + "+" + "-" * (status_w + 2) + "+" + "-" * (time_w + 2) + "+" + "-" * (health_w + 2) + "+"

    def _row(url: str, status: str, time: str, health: str) -> str:
        return (
            f"| {url:<{url_w}} | {status:>{status_w}} | {time:>{time_w}} | {health:^{health_w}} |"
        )

    lines = [
        sep,
        _row("URL", "Status", "Time (ms)", "Status"),
        sep,
    ]
    for r in results:
        sc = str(r["status_code"]) if r["status_code"] is not None else "N/A"
        rt = f'{r["response_time_ms"]}' if r["response_time_ms"] is not None else "N/A"
        health = "UP" if r["is_up"] else "DOWN"
        lines.append(_row(r["url"], sc, rt, health))
    lines.append(sep)
    return "\n".join(lines)


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
    args = parser.parse_args(argv)

    urls = _read_urls(args.input)
    if not urls:
        print("No URLs found in input file.", file=sys.stderr)
        sys.exit(1)

    results = check_urls_concurrent(urls, max_workers=args.workers, timeout=args.timeout)
    print(_format_table(results))


if __name__ == "__main__":
    main()
