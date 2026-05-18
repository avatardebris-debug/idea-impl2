"""
cli.py — pdf_schema command-line interface.
"""
from __future__ import annotations
import argparse, json, pathlib, sys, textwrap


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdf_schema",
        description="Extract and validate structured data from PDF documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python -m pdf_schema invoice.pdf --schema invoice --output data.json
              python -m pdf_schema contract.pdf --discover
              python -m pdf_schema document.pdf --text-only
              python -m pdf_schema --list-schemas
        """),
    )
    parser.add_argument("pdf", nargs="?", help="PDF file to analyse")
    parser.add_argument("--schema",   default=None,
                        help="Schema to extract (invoice, contract, resume, medical, report)")
    parser.add_argument("--discover", action="store_true",
                        help="Auto-discover document type and fields")
    parser.add_argument("--text-only",action="store_true",
                        help="Only extract raw text, no schema analysis")
    parser.add_argument("--output",   default=None, help="Save output to this file")
    parser.add_argument("--model",    default="qwen3:6b")
    parser.add_argument("--no-llm",   action="store_true",
                        help="Rule-based only, no LLM")
    parser.add_argument("--list-schemas", action="store_true",
                        help="Print available schema names and exit")
    parser.add_argument("--pretty",   action="store_true")

    args = parser.parse_args()

    if args.list_schemas:
        from pdf_schema.analyzer import list_schemas
        print("Available schemas: " + ", ".join(list_schemas()))
        return

    if not args.pdf:
        parser.print_help()
        sys.exit(1)

    p = pathlib.Path(args.pdf)
    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        sys.exit(1)

    # Step 1: Extract text
    print(f"  [1] Extracting text from {p.name}...", file=sys.stderr, flush=True)
    from pdf_schema.extractor import extract_text
    try:
        result = extract_text(str(p))
        print(f"      {result.pages} pages · {len(result.text)} chars · backend={result.backend}",
              file=sys.stderr)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.text_only:
        print(result.text)
        return

    # Step 2: Analyse
    from pdf_schema.analyzer import discover_schema, extract_schema
    if args.no_llm:
        output = {"text_preview": result.text[:1000], "backend": result.backend, "pages": result.pages}
    elif args.discover or not args.schema:
        print(f"  [2] Discovering schema...", file=sys.stderr, flush=True)
        output = discover_schema(result.text, model=args.model)
    else:
        print(f"  [2] Extracting {args.schema} schema...", file=sys.stderr, flush=True)
        try:
            output = extract_schema(result.text, args.schema, model=args.model)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    indent = 2 if args.pretty else None
    out_str = json.dumps(output, indent=indent, ensure_ascii=False)

    if args.output:
        out = pathlib.Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(out_str, encoding="utf-8")
        print(f"  Saved to {out}", file=sys.stderr)
    else:
        print(out_str)


if __name__ == "__main__":
    main()
