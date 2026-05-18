"""
cli.py — dropsearch CLI.
"""
import argparse, json, pathlib, sys
from dropsearch.researcher import analyze_niche, format_markdown

def main():
    parser = argparse.ArgumentParser(prog="dropsearch")
    parser.add_argument("command", choices=["analyze"])
    parser.add_argument("niche", help="The niche or product to research")
    parser.add_argument("--output", default=None, help="Output file path (.md or .json)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--model", default="qwen3:6b")

    args = parser.parse_args()

    print(f"Spying on competitors in niche: '{args.niche}'...", file=sys.stderr)
    data = analyze_niche(args.niche, model=args.model)

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
