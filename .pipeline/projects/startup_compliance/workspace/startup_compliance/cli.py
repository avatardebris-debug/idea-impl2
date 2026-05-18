"""
cli.py — startup_compliance CLI.
"""
import argparse, json, pathlib, sys
from startup_compliance.scanner import generate_checklist, format_markdown

def main():
    parser = argparse.ArgumentParser(prog="startup_compliance")
    parser.add_argument("command", choices=["generate"])
    parser.add_argument("--name", required=True, help="Company name")
    parser.add_argument("--desc", required=True, help="Brief description of tech stack & business model")
    parser.add_argument("--output", default=None, help="Output file path (.md or .json)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--model", default="qwen3:6b")

    args = parser.parse_args()

    print(f"Generating checklist for {args.name}...", file=sys.stderr)
    data = generate_checklist(args.name, args.desc, model=args.model)

    out_str = json.dumps(data, indent=2) if args.format == "json" else format_markdown(data)

    if args.output:
        p = pathlib.Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out_str, encoding="utf-8")
        print(f"Saved to {p}", file=sys.stderr)
    else:
        print(out_str)

if __name__ == "__main__":
    main()
