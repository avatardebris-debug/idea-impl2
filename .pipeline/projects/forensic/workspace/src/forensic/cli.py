"""Forensic CLI - Command line interface for forensic analysis."""

import argparse
import sys
import logging
from typing import Optional

from forensic.pipeline import ForensicPipeline
from forensic.models import IngestResult, AnalysisResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("forensic.cli")


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="forensic",
        description="Forensic Suite - Fraud detection analysis for SEC EDGAR filings",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest SEC filings")
    ingest_parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    ingest_parser.add_argument("--filing-type", type=str, default="10-K", help="Filing type (default: 10-K)")
    ingest_parser.add_argument("--db-path", type=str, default="forensic.db", help="Database path")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze filings for fraud indicators")
    analyze_parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    analyze_parser.add_argument("--db-path", type=str, default="forensic.db", help="Database path")
    analyze_parser.add_argument("--output", type=str, default=None, help="Output file path (JSON)")

    # report command
    report_parser = subparsers.add_parser("report", help="Generate fraud risk report")
    report_parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    report_parser.add_argument("--db-path", type=str, default="forensic.db", help="Database path")
    report_parser.add_argument("--output", type=str, default=None, help="Output file path (JSON)")

    return parser


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = _build_parser()
    return parser.parse_args(args)


def main(args: Optional[list] = None) -> int:
    """Main entry point for the forensic CLI."""
    parser = _build_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.command == "ingest":
        return cmd_ingest(parsed_args)
    elif parsed_args.command == "analyze":
        return cmd_analyze(parsed_args)
    elif parsed_args.command == "report":
        return cmd_report(parsed_args)
    else:
        parser.print_help()
        return 1


def cmd_ingest(args: argparse.Namespace) -> int:
    """Run the ingest command."""
    pipeline = ForensicPipeline(db_path=args.db_path)
    result: IngestResult = pipeline.ingest_filing(args.ticker, args.filing_type)
    print(f"Ingested {result.item_count} items for {result.ticker} (CIK={result.cik}, {result.filing_type}, {result.filing_date})")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run the analyze command."""
    pipeline = ForensicPipeline(db_path=args.db_path)
    result: AnalysisResult = pipeline.analyze_filing(args.ticker)
    print(f"Analysis complete for {args.ticker}:")
    print(f"  Fraud Risk Score: {result.fraud_risk_score:.2f}/100")
    print(f"  Red Flags: {len(result.red_flags)}")
    for flag in result.red_flags:
        print(f"    - [{flag.severity}] {flag.description}")
    if args.output:
        result.to_json(args.output)
        print(f"Results written to {args.output}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Run the report command."""
    pipeline = ForensicPipeline(db_path=args.db_path)
    report = pipeline.generate_report(args.ticker)
    print(f"Fraud Risk Report for {args.ticker}:")
    print(f"  Overall Risk: {report.overall_risk}")
    print(f"  Risk Score: {report.risk_score:.2f}/100")
    print(f"  Recommendations:")
    for rec in report.recommendations:
        print(f"    - {rec}")
    if args.output:
        report.to_json(args.output)
        print(f"Report written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
