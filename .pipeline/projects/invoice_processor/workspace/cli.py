"""CLI entry point for the invoice processor."""

import argparse
import os
import sys
from datetime import date

from invoice_processor.models import InvoiceLedger
from invoice_processor.parsers import get_parser
from invoice_processor.ledger import LedgerExporter


def process_directory(input_dir: str, output_csv: str) -> int:
    """Process all supported invoice files in a directory and export to CSV.

    Returns 0 on success, 1 on error.
    """
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.", file=sys.stderr)
        return 1

    supported_extensions = {'.pdf', '.csv'}
    ledger = InvoiceLedger()
    processed = 0
    skipped = 0
    errors = 0

    for filename in sorted(os.listdir(input_dir)):
        file_path = os.path.join(input_dir, filename)
        if not os.path.isfile(file_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in supported_extensions:
            skipped += 1
            print(f"  Skipped (unsupported): {filename}")
            continue

        try:
            parser = get_parser(file_path)
            result = parser.parse(file_path)
            if result:
                # parse() may return Invoice or List[Invoice]
                if isinstance(result, list):
                    for inv in result:
                        if inv:
                            ledger.add_invoice(inv)
                            processed += 1
                            print(f"  Processed: {filename} (vendor: {inv.vendor}, total: {inv.total} {inv.currency})")
                else:
                    ledger.add_invoice(result)
                    processed += 1
                    print(f"  Processed: {filename} (vendor: {result.vendor}, total: {result.total} {result.currency})")
            else:
                skipped += 1
                print(f"  Skipped (no parseable data): {filename}")
        except Exception as e:
            errors += 1
            print(f"  Error processing {filename}: {e}", file=sys.stderr)

    # Export ledger to CSV
    try:
        exporter = LedgerExporter()
        exporter.export_to_csv(ledger, output_csv)
        print(f"\nLedger exported to: {output_csv}")
    except Exception as e:
        print(f"Error exporting ledger: {e}", file=sys.stderr)
        return 1

    print(f"\nSummary: {processed} processed, {skipped} skipped, {errors} errors")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Process invoice files and export a CSV ledger.'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input directory containing invoice files (PDF/CSV)'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output CSV file path for the ledger'
    )

    args = parser.parse_args()
    sys.exit(process_directory(args.input, args.output))


if __name__ == '__main__':
    main()
