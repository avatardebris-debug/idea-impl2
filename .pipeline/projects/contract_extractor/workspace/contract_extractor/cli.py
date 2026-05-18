"""
cli.py — contract_extractor CLI.
"""
import argparse, json, pathlib, sys
from contract_extractor.extractor import extract_clauses, format_markdown

def main():
    parser = argparse.ArgumentParser(prog="contract_extractor")
    parser.add_argument("command", choices=["extract"])
    parser.add_argument("file", help="Path to contract text file")
    parser.add_argument("--output", default=None, help="Output file path (.md or .json)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--model", default="qwen3:6b")

    args = parser.parse_args()

    p = pathlib.Path(args.file)
    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        sys.exit(1)

    text = p.read_text(encoding="utf-8", errors="replace")
    print(f"Analyzing contract ({len(text)} chars)...", file=sys.stderr)
    data = extract_clauses(text, model=args.model)

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
