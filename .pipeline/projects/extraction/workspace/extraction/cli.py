"""
cli.py — extraction command-line interface.

Usage:
    python -m extraction article.txt --topic "how to make sourdough" --format recipe
    python -m extraction article.txt --format steps --output steps.json
    python -m extraction article.txt --no-llm   # rule-based only, no Ollama
    cat article.txt | python -m extraction -
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
import textwrap


def _validate_args(args: argparse.Namespace) -> None:
    """Validate parsed arguments and exit with error messages if invalid."""
    # Validate format
    valid_formats = ("recipe", "steps", "sop")
    if args.format not in valid_formats:
        print(
            f"ERROR: invalid format '{args.format}'. Choose from: {', '.join(valid_formats)}",
            file=sys.stderr,
        )
        sys.exit(2)

    # Validate input source
    if args.input == "-":
        # stdin will be read later; just ensure it's available
        pass
    else:
        p = pathlib.Path(args.input)
        if not p.exists():
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            sys.exit(2)
        if not p.is_file():
            print(f"ERROR: not a regular file: {p}", file=sys.stderr)
            sys.exit(2)

    # Validate output path if given
    if args.output:
        out = pathlib.Path(args.output)
        if out.exists() and not out.parent.exists():
            print(f"ERROR: output directory does not exist: {out.parent}", file=sys.stderr)
            sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="extraction",
        description="Turn source material into a structured step-by-step extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python -m extraction article.txt --topic "sourdough bread" --format recipe
              python -m extraction lecture.txt --format steps --output steps.json
              cat transcript.txt | python -m extraction - --format sop
        """),
    )
    parser.add_argument("input", help="Input file path or '-' for stdin")
    parser.add_argument("--topic",   default="", help="Topic description (helps LLM understand context)")
    parser.add_argument("--format",  choices=["recipe", "steps", "sop"], default="steps",
                        help="Output format (default: steps)")
    parser.add_argument("--model",   default="qwen3:6b", help="Ollama model (default: qwen3:6b)")
    parser.add_argument("--output",  default=None, help="Write JSON output to this file")
    parser.add_argument("--no-llm",  action="store_true", help="Use rule-based extraction (no Ollama)")
    parser.add_argument("--pretty",  action="store_true", help="Pretty-print JSON output")

    args = parser.parse_args()

    # Validate arguments
    _validate_args(args)

    # Read input
    if args.input == "-":
        text = sys.stdin.read()
    else:
        p = pathlib.Path(args.input)
        text = p.read_text(encoding="utf-8")

    # Validate non-empty text
    if not text.strip():
        print("ERROR: empty input — provide text via file or stdin", file=sys.stderr)
        sys.exit(1)

    from extraction.extractor import extract, _fallback_extract

    if args.no_llm:
        result = _fallback_extract(text, args.topic, args.format)
    else:
        print(f"  Extracting ({args.format}) via {args.model}...", file=sys.stderr, flush=True)
        result = extract(text, topic=args.topic, fmt=args.format, model=args.model)

    indent = 2 if args.pretty else None
    output_str = json.dumps(result, indent=indent, ensure_ascii=False)

    if args.output:
        out = pathlib.Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output_str, encoding="utf-8")
        print(f"  Written to {out} ({len(result.get('steps',[]))} steps)", file=sys.stderr)
    else:
        print(output_str)


if __name__ == "__main__":
    main()
