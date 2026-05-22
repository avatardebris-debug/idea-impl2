"""CLI entry point for the financial document analyzer."""

import argparse
import sys
import os

from financial_document_analyzer.parsers import parse_csv, parse_pdf
from financial_document_analyzer.reporters import generate_report


def main():
    parser = argparse.ArgumentParser(
        description="Financial Document Analyzer — extract metrics from PDFs and CSVs"
    )
    parser.add_argument(
        "--file", "-f",
        required=True,
        help="Path to the financial document (CSV or PDF)",
    )
    parser.add_argument(
        "--previous", "-p",
        default=None,
        help="Path to a previous period file for trend comparison",
    )
    args = parser.parse_args()

    file_path = args.file

    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Determine file type and parse
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".csv":
            metrics = parse_csv(file_path)
        elif ext in (".pdf",):
            metrics = parse_pdf(file_path)
        else:
            print(f"Error: Unsupported file type '{ext}'. Supported: .csv, .pdf", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse previous file if provided
    previous_metrics = None
    if args.previous:
        if not os.path.isfile(args.previous):
            print(f"Error: Previous file not found: {args.previous}", file=sys.stderr)
            sys.exit(1)
        prev_ext = os.path.splitext(args.previous)[1].lower()
        try:
            if prev_ext == ".csv":
                previous_metrics = parse_csv(args.previous)
            elif prev_ext in (".pdf",):
                previous_metrics = parse_pdf(args.previous)
        except Exception as e:
            print(f"Warning: Could not parse previous file for trend comparison: {e}", file=sys.stderr)
            previous_metrics = None

    # Generate and print report
    report = generate_report(metrics, previous_metrics)
    print(report)
    sys.exit(0)


if __name__ == "__main__":
    main()
