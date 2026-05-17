"""Dropsearch CLI — extract product catalogs from e-commerce stores."""

import argparse
import sys
import logging

from src.scraper.extractor import ProductExtractor
from src.reporter.formatter import ReportFormatter
from src.scraper.multi_analyzer import MultiStoreAnalyzer
from src.reporter.comparative_formatter import ComparativeReportFormatter


def cmd_scan(args):
    """Handle the 'scan' subcommand — single store analysis."""
    extractor = ProductExtractor()
    reporter = ReportFormatter()

    if args.url.startswith("file://"):
        with open(args.url[7:], "r") as f:
            html = f.read()
    else:
        print("ERROR: URL fetching not yet implemented. Use 'file://' prefix to read from a local HTML file.", file=sys.stderr)
        sys.exit(1)

    products = extractor.extract(html, args.url)
    report = reporter.format(products, args.url, fmt=args.format)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


def cmd_analyze(args):
    """Handle the 'analyze' subcommand — multi-store competitor analysis."""
    urls = args.urls
    if not urls:
        print("ERROR: At least one URL is required for analyze.", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    analyzer = MultiStoreAnalyzer()
    comparative_formatter = ComparativeReportFormatter()

    # Run analysis
    comparison = analyzer.compare(urls)

    # Generate report
    report = comparative_formatter.format_comparison(
        stores=comparison.stores,
        overlaps=comparison.product_overlaps,
        margins=comparison.margins,
        price_gaps=comparison.price_gaps,
        insights=comparison.insights,
    )

    # Filter overlaps by min-overlap if specified
    if args.min_overlap:
        filtered_overlaps = [
            o for o in comparison.product_overlaps
            if len(o.get("stores", [])) >= args.min_overlap
        ]
        if filtered_overlaps:
            report = comparative_formatter.format_comparison(
                stores=comparison.stores,
                overlaps=filtered_overlaps,
                margins=comparison.margins,
                price_gaps=comparison.price_gaps,
                insights=comparison.insights,
            )

    # Add insights flag output
    if args.insights:
        report += "\n\n## Additional Insights\n\n"
        for i, insight in enumerate(comparison.insights, 1):
            report += f"{i}. {insight}\n"

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


def main():
    parser = argparse.ArgumentParser(description="Dropsearch — extract product catalogs from e-commerce stores.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Scan a single store for products")
    scan_parser.add_argument("url", help="URL of the store or product page to scan.")
    scan_parser.add_argument("-f", "--format", choices=["markdown", "text", "comparative"], default="markdown", help="Output format (default: markdown).")
    scan_parser.add_argument("-o", "--output", help="Output file path (default: stdout).")
    scan_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")

    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Compare multiple competitor stores")
    analyze_parser.add_argument("urls", nargs="+", help="URLs of the stores to compare.")
    analyze_parser.add_argument("-f", "--format", choices=["markdown", "text", "comparative"], default="comparative", help="Output format (default: comparative).")
    analyze_parser.add_argument("-o", "--output", help="Output file path (default: stdout).")
    analyze_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    analyze_parser.add_argument("--insights", action="store_true", help="Include actionable insights in output.")
    analyze_parser.add_argument("--min-overlap", type=int, default=1, help="Minimum number of stores a product must appear in to be included (default: 1).")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
