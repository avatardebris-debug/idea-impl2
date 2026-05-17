"""
summarizer.py — LLM-powered synthesis of research results.

Given a ranked list of Result dicts from researcher.py, uses an LLM to:
1. Extract key findings from each source (per-source digest)
2. Synthesise all digests into a coherent research summary with citations

Falls back gracefully to extractive summarisation if no LLM is available.
"""
from __future__ import annotations
import json
import textwrap
import urllib.request
import urllib.error
from research1.sources.arxiv import Result

_OLLAMA_HOST = "http://localhost:11434"


def _call_ollama(prompt: str, model: str = "qwen3:6b", timeout: int = 120) -> str:
    """Call Ollama /api/generate and return the response string."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{_OLLAMA_HOST}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        return raw.get("response", "").strip()
    except Exception:
        return ""


def _extractive_summary(result: Result) -> str:
    """No-LLM fallback: return first 3 sentences of abstract."""
    abstract = result.get("abstract", "")
    sentences = [s.strip() for s in abstract.split(".") if len(s.strip()) > 20]
    return ". ".join(sentences[:3]) + ("." if sentences else "")


def summarize_source(result: Result, model: str = "qwen3:6b") -> str:
    """Summarise a single source result into 2-3 key sentences."""
    abstract = result.get("abstract", "")
    if not abstract:
        return "(no abstract available)"

    prompt = textwrap.dedent(f"""
        Summarise the following research content in 2-3 concise sentences.
        Focus on: what was studied/found, key methods or data, and significance.
        Do not add information not present in the text.

        SOURCE: {result.get("source", "").upper()} — {result.get("title", "")}
        TEXT: {abstract[:2000]}

        SUMMARY:
    """).strip()

    summary = _call_ollama(prompt, model=model)
    if not summary:
        summary = _extractive_summary(result)
    return summary


def synthesize(
    query: str,
    results: list[Result],
    model: str = "qwen3:6b",
    per_source_summaries: list[str] | None = None,
) -> str:
    """Synthesise all source summaries into a coherent research narrative.

    Args:
        query:                The original research question.
        results:              Ranked Result list from researcher.research().
        model:                Ollama model for synthesis.
        per_source_summaries: Pre-computed per-source summaries (optional).

    Returns:
        A markdown-formatted synthesis string.
    """
    if not results:
        return "_No sources found for this query._"

    if per_source_summaries is None:
        per_source_summaries = [_extractive_summary(r) for r in results]

    # Build context block
    context_parts = []
    for i, (r, summary) in enumerate(zip(results, per_source_summaries), 1):
        source_line = f"[{i}] {r.get('source','').upper()}: {r.get('title','')}"
        context_parts.append(f"{source_line}\n{summary}")

    context = "\n\n".join(context_parts)

    prompt = textwrap.dedent(f"""
        You are a research analyst. Based on the following source summaries,
        write a clear, structured research overview answering the topic below.

        Use markdown with these sections:
        ## Overview
        (2-3 paragraph synthesis of key themes and findings)

        ## Key Findings
        (bullet list of the most important findings across all sources)

        ## Gaps & Open Questions
        (1-2 sentences on what is not yet resolved or studied)

        Be factual. Cite sources as [1], [2], etc. matching the numbered list below.
        Do not add information not present in the sources.

        TOPIC: {query}

        SOURCES:
        {context}

        SYNTHESIS:
    """).strip()

    synthesis = _call_ollama(prompt, model=model, timeout=180)
    if not synthesis:
        # Fallback: join summaries
        lines = [f"**{r.get('title','')}** ({r.get('source','').upper()})  \n{s}"
                 for r, s in zip(results, per_source_summaries)]
        synthesis = "\n\n".join(lines)
    return synthesis
