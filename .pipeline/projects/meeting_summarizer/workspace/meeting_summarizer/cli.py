"""
cli.py — meeting_summarizer CLI.
"""
import argparse, json, pathlib, sys
from meeting_summarizer.summarizer import analyze_transcript, format_markdown

def main():
    parser = argparse.ArgumentParser(prog="meeting_summarizer")
    parser.add_argument("command", choices=["summarize"])
    parser.add_argument("transcript", help="Path to meeting transcript text file")
    parser.add_argument("--output", default=None, help="Output file path (.md or .json)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--model", default="qwen3:6b")

    args = parser.parse_args()

    p = pathlib.Path(args.transcript)
    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        sys.exit(1)

    text = p.read_text(encoding="utf-8", errors="replace")
    print(f"Summarizing meeting ({len(text)} chars)...", file=sys.stderr)
    data = analyze_transcript(text, model=args.model)

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
