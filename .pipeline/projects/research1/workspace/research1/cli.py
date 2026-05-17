"""
cli.py — research1 command-line interface.

Usage:
    python -m research1 "quantum error correction" --depth 5 --output report.md
    python -m research1 "CRISPR applications" --sources arxiv pubmed --no-llm
    python -m research1 "climate change tipping points" --model qwen3:14b --depth 8
"""
from __future__ import annotations
import argparse
import sys
import textwrap
import time


ALL_SOURCES = ["arxiv", "pubmed", "wikipedia", "web"]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="research1",
        description="Multi-source research assistant: arXiv + PubMed + Wikipedia + credible web → report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python -m research1 "quantum error correction" --depth 5
              python -m research1 "CRISPR gene editing" --sources arxiv pubmed --output report.md
              python -m research1 "climate tipping points" --no-llm --depth 3
              python -m research1 "depression treatment" --model qwen3:14b --depth 8
        """),
    )
    parser.add_argument("topic", help="Research topic or question")
    parser.add_argument(
        "--sources", nargs="+", choices=ALL_SOURCES, default=ALL_SOURCES,
        metavar="SOURCE",
        help=f"Sources to query (default: all). Choices: {', '.join(ALL_SOURCES)}",
    )
    parser.add_argument(
        "--depth", type=int, default=5,
        help="Results per source (default: 5)",
    )
    parser.add_argument(
        "--output", default=None,
        help="Save report to this file (default: print to stdout)",
    )
    parser.add_argument(
        "--model", default="qwen3:6b",
        help="Ollama model for summarisation (default: qwen3:6b)",
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="Skip LLM summarisation (extractive only, no Ollama needed)",
    )
    parser.add_argument(
        "--timeout", type=int, default=20,
        help="Per-source fetch timeout in seconds (default: 20)",
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  research1 — {args.topic}")
    print(f"{'='*60}")
    print(f"  Sources: {', '.join(args.sources)}")
    print(f"  Depth:   {args.depth} results/source")
    print(f"  LLM:     {'disabled' if args.no_llm else args.model}\n")

    # Step 1: Gather
    print("  [1/3] Gathering sources...")
    t0 = time.time()
    from research1.researcher import research
    results = research(
        query=args.topic,
        sources=args.sources,
        results_per_source=args.depth,
        timeout=args.timeout,
    )
    print(f"        {len(results)} unique results in {time.time()-t0:.1f}s\n")

    if not results:
        print("  No results found. Check your network connection or try different sources.")
        sys.exit(1)

    # Step 2: Summarise
    print("  [2/3] Summarising sources...")
    t0 = time.time()
    from research1.summarizer import summarize_source, synthesize, _extractive_summary

    per_source_summaries: list[str] = []
    for i, result in enumerate(results, 1):
        if args.no_llm:
            summary = _extractive_summary(result)
        else:
            print(f"        [{i:2d}/{len(results)}] {result.get('source','')} — {result.get('title','')[:50]}")
            summary = summarize_source(result, model=args.model)
        per_source_summaries.append(summary)

    synthesis = "(LLM disabled — see source digests below.)"
    if not args.no_llm:
        print("        Synthesising...", flush=True)
        synthesis = synthesize(
            query=args.topic,
            results=results,
            model=args.model,
            per_source_summaries=per_source_summaries,
        )
    print(f"        Done in {time.time()-t0:.1f}s\n")

    # Step 3: Assemble report
    print("  [3/3] Building report...")
    from research1.report import build_report, save_report
    report = build_report(
        query=args.topic,
        results=results,
        summaries=per_source_summaries,
        synthesis=synthesis,
        sources_used=args.sources,
        model=args.model,
    )

    if args.output:
        save_report(report, args.output)
    else:
        print(f"\n{'='*60}\n")
        print(report)

    print(f"  Done. {len(results)} sources summarised.")


if __name__ == "__main__":
    main()
