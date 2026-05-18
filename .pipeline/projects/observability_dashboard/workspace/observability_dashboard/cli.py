"""
cli.py — observability_dashboard CLI.
"""
import argparse, pathlib, sys
from observability_dashboard.dashboard import parse_logs, format_dashboard

def main():
    parser = argparse.ArgumentParser(prog="observability_dashboard")
    parser.add_argument("command", choices=["report"])
    parser.add_argument("log_file", help="Path to agent JSONL log file")

    args = parser.parse_args()

    p = pathlib.Path(args.log_file)
    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        sys.exit(1)

    log_text = p.read_text(encoding="utf-8", errors="replace")
    lines = log_text.splitlines()
    
    print(f"Parsing {len(lines)} log lines...", file=sys.stderr)
    stats = parse_logs(lines)

    print(format_dashboard(stats))

if __name__ == "__main__":
    main()
