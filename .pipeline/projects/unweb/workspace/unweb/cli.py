"""
cli.py — unweb command-line interface.

Usage:
    python -m unweb "https://reuters.com/some-article"
    python -m unweb "https://..." --no-enrich --output report.md
    python -m unweb --text-input "EPA official joins ExxonMobil board..."
    python -m unweb "https://..." --format json
"""
from __future__ import annotations
import argparse
import json
import sys
import textwrap
import time


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="unweb",
        description="Unmask the connections behind any news story",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python -m unweb "https://reuters.com/article"
              python -m unweb "https://..." --output report.md
              python -m unweb --text-input "story text here..."
              python -m unweb "https://..." --no-enrich --no-llm
        """),
    )
    parser.add_argument("source", help="URL or story text (use --text-input for raw text)")
    parser.add_argument("--text-input", action="store_true",
                        help="Treat source as raw text, not a URL")
    parser.add_argument("--output",     default=None,
                        help="Save report to this file (.md or .json)")
    parser.add_argument("--format",     choices=["markdown","json"], default="markdown")
    parser.add_argument("--model",      default="qwen3:6b")
    parser.add_argument("--no-enrich",  action="store_true",
                        help="Skip Wikipedia entity enrichment")
    parser.add_argument("--no-llm",     action="store_true",
                        help="Use rule-based extraction only (no Ollama needed)")

    args = parser.parse_args()

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  unweb — Connection Mapper", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    # Step 1: Get text
    if args.text_input:
        text       = args.source
        source_url = ""
        print(f"  [1/3] Using provided text ({len(text)} chars)...", file=sys.stderr)
    else:
        print(f"  [1/3] Fetching {args.source[:60]}...", file=sys.stderr, flush=True)
        t0 = time.time()
        from unweb.fetcher import fetch_url
        try:
            text = fetch_url(args.source)
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        source_url = args.source
        print(f"         {len(text)} chars in {time.time()-t0:.1f}s", file=sys.stderr)

    # Step 2: Extract connections
    print("  [2/3] Extracting entities and connections...", file=sys.stderr, flush=True)
    t0 = time.time()
    from unweb.extractor import extract_connections, _fallback_extract
    if args.no_llm:
        graph = _fallback_extract(text)
        graph["metadata"] = {
            "model": "fallback", "source_url": source_url,
            "text_length": len(text),
            "extracted_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc).isoformat(),
            "n_people": len(graph.get("people",[])),
            "n_orgs": len(graph.get("orgs",[])),
            "n_connections": len(graph.get("connections",[])),
        }
    else:
        graph = extract_connections(text, model=args.model, source_url=source_url)
    print(f"         {graph['metadata']['n_people']} people · "
          f"{graph['metadata']['n_orgs']} orgs · "
          f"{graph['metadata']['n_connections']} connections "
          f"in {time.time()-t0:.1f}s", file=sys.stderr)

    # Step 3: Enrich with Wikipedia
    if not args.no_enrich:
        print("  [3/3] Enriching with Wikipedia...", file=sys.stderr, flush=True)
        t0 = time.time()
        from unweb.enricher import enrich
        graph = enrich(graph)
        print(f"         Done in {time.time()-t0:.1f}s", file=sys.stderr)
    else:
        print("  [3/3] Skipping enrichment (--no-enrich)", file=sys.stderr)

    # Output
    if args.format == "json":
        output_str = json.dumps(graph, indent=2, ensure_ascii=False)
    else:
        from unweb.reporter import build_report
        output_str = build_report(graph, source=args.source if not args.text_input else "")

    if args.output:
        from unweb.reporter import save_report
        save_report(output_str, args.output)
    else:
        print(output_str)

    print(f"\n  Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
