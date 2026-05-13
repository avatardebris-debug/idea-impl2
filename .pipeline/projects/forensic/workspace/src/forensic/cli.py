"""Forensic CLI - Command line interface for forensic analysis."""

import argparse
import json
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

    # capital command
    capital_parser = subparsers.add_parser("capital", help="Analyze capital flows and advanced fraud flags")
    capital_parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    capital_parser.add_argument("--db-path", type=str, default="forensic.db", help="Database path")
    capital_parser.add_argument("--output", type=str, default=None, help="Output file path (JSON)")

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
    elif parsed_args.command == "capital":
        return cmd_capital(parsed_args)
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


def cmd_capital(args: argparse.Namespace) -> int:
    """Run the capital analysis command."""
    pipeline = ForensicPipeline(db_path=args.db_path)
    result = pipeline.analyze_filing(args.ticker)

    # Print capital flows summary
    if result.capital_flows:
        print(f"Capital Flows Analysis for {args.ticker}:")
        cf = result.capital_flows
        print(f"  Summary: {cf.get('summary', 'N/A')}")
        print(f"  Cash Flow Quality: {cf.get('cash_flow_quality', 'N/A')}")
        print(f"  Debt Trend: {cf.get('debt_trend', 'N/A')}")
        print(f"  Dividend Trend: {cf.get('dividend_trend', 'N/A')}")
        print(f"  Repurchase Trend: {cf.get('repurchase_trend', 'N/A')}")
        if cf.get('capex_to_revenue_ratios'):
            print(f"  CapEx to Revenue Ratios:")
            for r in cf['capex_to_revenue_ratios']:
                print(f"    - {r.get('period_label', 'N/A')}: {r.get('ratio', 'N/A')}")
        if cf.get('periods'):
            print(f"  Periods:")
            for p in cf['periods']:
                print(f"    - {p.get('period_label', 'N/A')}:")
                print(f"      Operating CF: {p.get('operating_cash_flow', 'N/A')}")
                print(f"      CapEx: {p.get('capital_expenditures', 'N/A')}")
                print(f"      Debt Issuance: {p.get('debt_issuance', 'N/A')}")
                print(f"      Debt Repayment: {p.get('debt_repayment', 'N/A')}")
                print(f"      Dividends Paid: {p.get('dividends_paid', 'N/A')}")
                print(f"      Share Repurchases: {p.get('share_repurchases', 'N/A')}")

    # Print advanced flags summary
    if result.advanced_flags:
        print(f"\nAdvanced Fraud Flags for {args.ticker}:")
        af = result.advanced_flags
        if af.get('benford'):
            bf = af['benford']
            print(f"  Benford's Law:")
            print(f"    - First Digit Chi-Square: {bf.get('chi_square', 'N/A')}")
            print(f"    - P-value: {bf.get('p_value', 'N/A')}")
            print(f"    - Violation: {bf.get('violation', 'N/A')}")
        if af.get('beneish'):
            b = af['beneish']
            print(f"  Beneish M-Score:")
            print(f"    - M-Score: {b.get('m_score', 'N/A')}")
            print(f"    - Manipulation Risk: {b.get('manipulation_risk', 'N/A')}")
        if af.get('altman_z'):
            az = af['altman_z']
            print(f"  Altman Z-Score:")
            print(f"    - Z-Score: {az.get('z_score', 'N/A')}")
            print(f"    - Risk Level: {az.get('risk_level', 'N/A')}")
        if af.get('red_flags'):
            print(f"  Red Flags:")
            for flag in af['red_flags']:
                print(f"    - [{flag.get('category', 'N/A')}] {flag.get('description', 'N/A')} (Severity: {flag.get('severity', 'N/A')})")

    if args.output:
        output_data = {
            "ticker": args.ticker,
            "capital_flows": result.capital_flows,
            "advanced_flags": result.advanced_flags,
        }
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nOutput written to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
