"""
cli.py — code_reviewer CLI.
"""
import argparse, json, pathlib, sys
from code_reviewer.reviewer import analyze_diff, format_markdown

def main():
    parser = argparse.ArgumentParser(prog="code_reviewer")
    parser.add_argument("command", choices=["analyze"])
    parser.add_argument("diff_file", nargs="?", help="Path to diff file (optional, can pipe from stdin)")
    parser.add_argument("--output", default=None, help="Output file path (.md or .json)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--model", default="qwen3:6b")

    args = parser.parse_args()

    diff_text = ""
    if args.diff_file:
        p = pathlib.Path(args.diff_file)
        if not p.exists():
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            sys.exit(1)
        diff_text = p.read_text(encoding="utf-8", errors="replace")
    elif not sys.stdin.isatty():
        diff_text = sys.stdin.read()
    else:
        print("ERROR: Provide a diff file or pipe diff content via stdin.", file=sys.stderr)
        sys.exit(1)

    if not diff_text.strip():
        print("ERROR: Diff content is empty.", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing diff ({len(diff_text)} chars)...", file=sys.stderr)
    data = analyze_diff(diff_text, model=args.model)

    out_str = json.dumps(data, indent=2) if args.format == "json" else format_markdown(data)

    if args.output:
        out = pathlib.Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(out_str, encoding="utf-8")
        print(f"Saved to {out}", file=sys.stderr)
    else:
        print(out_str)

if __name__ == "__main__":
    main()
