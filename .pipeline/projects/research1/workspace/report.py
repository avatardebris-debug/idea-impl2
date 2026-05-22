"""
report.py — Assembles the final structured markdown research report.

Combines ranked results + per-source summaries + LLM synthesis into
a single, citation-complete markdown document ready for saving or printing.
"""
from __future__ import annotations
from datetime import datetime, timezone
from research1.sources.arxiv import Result


_EMOJI = {
    "arxiv":     "📄",
    "pubmed":    "🧬",
    "wikipedia": "📖",
    "web":       "🌐",
}


def build_report(
    query: str,
    results: list[Result],
    summaries: list[str],
    synthesis: str,
    sources_used: list[str],
    model: str = "qwen3:6b",
) -> str:
    """Build the full markdown report string.

    Args:
        query:       Original research topic.
        results:     Ranked Result list.
        summaries:   Per-source summary strings (parallel to results).
        synthesis:   LLM-generated synthesis section.
        sources_used: Names of sources queried.
        model:       LLM model used (for metadata).

    Returns:
        Complete markdown document as a string.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    # Header
    lines += [
        f"# Research Report: {query}",
        "",
        f"> **Generated:** {now}  ",
        f"> **Sources queried:** {', '.join(sources_used)}  ",
        f"> **Results found:** {len(results)}  ",
        f"> **Model:** {model}  ",
        "",
        "---",
        "",
    ]

    # Synthesis
    lines += [
        "## Synthesis",
        "",
        synthesis,
        "",
        "---",
        "",
    ]

    # Source Digest
    lines += ["## Source Digest", ""]
    for i, (result, summary) in enumerate(zip(results, summaries), 1):
        source  = result.get("source", "web")
        emoji   = _EMOJI.get(source, "🔗")
        title   = result.get("title", "(no title)")
        url     = result.get("url", "")
        authors = result.get("authors", [])
        pub     = result.get("published", "")
        score   = result.get("relevance_score", 0.0)

        author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
        meta_parts = [f"{emoji} **{source.upper()}**"]
        if author_str:
            meta_parts.append(author_str)
        if pub:
            meta_parts.append(pub)

        lines += [
            f"### [{i}] {title}",
            "",
            "  ".join(meta_parts),
            "",
            summary,
            "",
            f"🔗 [{url}]({url})" if url else "",
            "",
        ]

    # Full Abstracts (collapsible reference section)
    lines += [
        "---",
        "",
        "## Full Abstracts",
        "",
        "<details>",
        "<summary>Click to expand raw abstracts</summary>",
        "",
    ]
    for i, result in enumerate(results, 1):
        title    = result.get("title", "")
        abstract = result.get("abstract", "(none)")
        lines += [f"**[{i}] {title}**", "", abstract, ""]
    lines += ["</details>", ""]

    return "\n".join(lines)


def save_report(report: str, path: str) -> None:
    """Write report to disk."""
    import pathlib
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(report, encoding="utf-8")
    print(f"  Report saved to {p}")
