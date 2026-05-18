"""
cli.py — finance_tracker command-line interface.
"""
from __future__ import annotations
import argparse, pathlib, sys, textwrap


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="finance_tracker",
        description="Personal finance tracker: CSV import → categorize → monthly report → anomaly alerts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python -m finance_tracker report transactions.csv
              python -m finance_tracker report transactions.csv --month 2024-01
              python -m finance_tracker report transactions.csv --output report.md
              python -m finance_tracker alerts transactions.csv
              python -m finance_tracker categorize transactions.csv --output categorized.csv
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # report
    p_rep = sub.add_parser("report", help="Generate monthly budget report")
    p_rep.add_argument("csv",    help="Bank CSV file")
    p_rep.add_argument("--month", default=None, help="Filter to YYYY-MM (default: all months)")
    p_rep.add_argument("--output", default=None, help="Save report to file")
    p_rep.add_argument("--anomalies", action="store_true", help="Include anomaly section")

    # alerts
    p_alerts = sub.add_parser("alerts", help="Show spending anomalies")
    p_alerts.add_argument("csv")
    p_alerts.add_argument("--threshold", type=float, default=2.5,
                          help="Z-score threshold (default: 2.5)")

    # categorize
    p_cat = sub.add_parser("categorize", help="Add category column to CSV")
    p_cat.add_argument("csv")
    p_cat.add_argument("--output", default=None, help="Output CSV path")

    args = parser.parse_args()
    p = pathlib.Path(args.csv)
    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        sys.exit(1)

    csv_text = p.read_text(encoding="utf-8", errors="replace")
    from finance_tracker.categorizer import parse_csv
    transactions = parse_csv(csv_text)
    print(f"  Loaded {len(transactions)} transactions from {p.name}", file=sys.stderr)

    if args.command == "report":
        from finance_tracker.reporter import summarize_by_month, detect_anomalies, format_report
        summaries  = summarize_by_month(transactions, month=args.month)
        anomalies  = detect_anomalies(transactions) if args.anomalies else None
        report     = format_report(summaries, anomalies)
        if args.output:
            out = pathlib.Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(report, encoding="utf-8")
            print(f"  Report saved to {out}", file=sys.stderr)
        else:
            print(report)

    elif args.command == "alerts":
        from finance_tracker.reporter import detect_anomalies
        anomalies = detect_anomalies(transactions, z_threshold=args.threshold)
        if not anomalies:
            print("  No anomalies detected.")
        for a in anomalies[:20]:
            print(f"  ⚠️  {a['date']}  {a['description'][:40]:40s}  "
                  f"${a['amount']:>10,.2f}  z={a['z_score']}  ({a['category']})")

    elif args.command == "categorize":
        import csv, io
        reader = csv.DictReader(io.StringIO(csv_text))
        fieldnames = (reader.fieldnames or []) + ["category"]
        out_rows = []
        for row, t in zip(reader, transactions):
            row["category"] = t.category
            out_rows.append(row)
        import io as _io
        buf = _io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
        out_csv = buf.getvalue()
        if args.output:
            out = pathlib.Path(args.output)
            out.write_text(out_csv, encoding="utf-8")
            print(f"  Saved to {out}", file=sys.stderr)
        else:
            print(out_csv)


if __name__ == "__main__":
    main()
