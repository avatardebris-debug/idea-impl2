"""CLI interface for Dropsearch."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from src.scraper.multi_analyzer import MultiStoreAnalyzer
from src.reporter.formatter import ReportFormatter
from src.reporter.comparative_formatter import ComparativeReportFormatter

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def cmd_scan(args):
    """Handle the 'scan' subcommand."""
    setup_logging(args.verbose)

    # Determine input source
    urls: List[str] = []

    if args.url:
        urls.append(args.url)
    elif args.file:
        input_path = Path(args.file)
        if input_path.suffix == ".json":
            with open(input_path) as f:
                data = json.load(f)
                urls = data.get("urls", [])
        elif input_path.suffix == ".txt":
            with open(input_path) as f:
                urls = [line.strip() for line in f if line.strip()]
        else:
            # Assume HTML file
            with open(input_path) as f:
                html = f.read()
            # For single HTML file, use a placeholder URL
            urls = ["file://" + str(input_path.resolve())]
    else:
        print("Error: Please provide --url or --file argument.")
        sys.exit(1)

    if not urls:
        print("Error: No URLs provided.")
        sys.exit(1)

    print(f"Analyzing {len(urls)} store(s)...")

    # Analyze stores
    analyzer = MultiStoreAnalyzer()
    comparison = analyzer.compare(urls)

    # Format report
    formatter = ComparativeReportFormatter()
    report = formatter.format_comparison(
        stores=comparison.stores,
        overlaps=comparison.product_overlaps,
        margins=comparison.margins,
        price_gaps=comparison.price_gaps,
        insights=comparison.insights,
    )

    # Output report
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            f.write(report)
        print(f"Report saved to {output_path}")
    else:
        print(report)

    # Output JSON if requested
    if args.json:
        json_output = {
            "stores": [
                {
                    "url": s.stores_url,
                    "platform": s.platform,
                    "product_count": len(s.products),
                    "supplier_count": len(s.supplier_info),
                }
                for s in comparison.stores
            ],
            "product_overlaps": comparison.product_overlaps,
            "price_gaps": comparison.price_gaps,
            "margins": comparison.margins,
            "insights": comparison.insights,
        }
        if args.json:
            json_path = Path(args.json)
            with open(json_path, "w") as f:
                json.dump(json_output, f, indent=2)
            print(f"JSON output saved to {json_path}")


def cmd_compare(args):
    """Handle the 'compare' subcommand (alias for scan)."""
    cmd_scan(args)


def cmd_inspect(args):
    """Handle the 'inspect' subcommand for detailed product inspection."""
    setup_logging(args.verbose)

    if not args.url:
        print("Error: Please provide --url argument.")
        sys.exit(1)

    print(f"Inspecting {args.url}...")

    # Fetch and analyze
    analyzer = MultiStoreAnalyzer()
    analysis = analyzer._analyze_single(args.url)

    # Format detailed report
    formatter = ComparativeReportFormatter()
    report = formatter.format_store_detail(analysis)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)


def cmd_export(args):
    """Handle the 'export' subcommand for exporting data."""
    setup_logging(args.verbose)

    if not args.file:
        print("Error: Please provide --file argument.")
        sys.exit(1)

    # Load existing data or create new
    output_path = Path(args.file)
    if output_path.exists():
        with open(output_path) as f:
            data = json.load(f)
    else:
        data = {"stores": [], "products": [], "insights": []}

    # Add new data (placeholder - in real implementation, this would merge results)
    print(f"Exporting data to {output_path}")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Data exported to {output_path}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="dropsearch",
        description="Dropsearch - Competitor analysis for e-commerce",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Analyze competitor stores")
    scan_parser.add_argument("--url", type=str, help="Store URL to analyze")
    scan_parser.add_argument("--file", type=str, help="Input file (JSON, TXT, or HTML)")
    scan_parser.add_argument("--output", type=str, help="Output report file")
    scan_parser.add_argument("--json", type=str, help="Output JSON file")
    scan_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    scan_parser.set_defaults(func=cmd_scan)

    # Compare command (alias)
    compare_parser = subparsers.add_parser("compare", help="Compare competitor stores")
    compare_parser.add_argument("--url", type=str, help="Store URL to analyze")
    compare_parser.add_argument("--file", type=str, help="Input file (JSON, TXT, or HTML)")
    compare_parser.add_argument("--output", type=str, help="Output report file")
    compare_parser.add_argument("--json", type=str, help="Output JSON file")
    compare_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    compare_parser.set_defaults(func=cmd_compare)

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a single store in detail")
    inspect_parser.add_argument("--url", type=str, required=True, help="Store URL to inspect")
    inspect_parser.add_argument("--output", type=str, help="Output report file")
    inspect_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    inspect_parser.set_defaults(func=cmd_inspect)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export analysis data")
    export_parser.add_argument("--file", type=str, required=True, help="Output JSON file")
    export_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    export_parser.set_defaults(func=cmd_export)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
