"""
researcher.py — Orchestrates all sources, deduplicates, and ranks results.

Runs all enabled sources concurrently using ThreadPoolExecutor, then:
1. Deduplicates by URL and title similarity
2. Scores results by source credibility × relevance_score
3. Returns the top-N results sorted by final score
"""
from __future__ import annotations
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from research1.sources.arxiv import Result


# Credibility multipliers per source
_SOURCE_CREDIBILITY = {
    "arxiv":     1.0,   # peer-reviewed preprints
    "pubmed":    1.05,  # published peer-reviewed
    "wikipedia": 0.80,  # encyclopedic, useful but not primary
    "web":       0.70,  # variable; filtered to credible domains
}


def _title_fingerprint(title: str) -> str:
    """Normalised title for deduplication."""
    t = re.sub(r"[^a-z0-9 ]", "", title.lower())
    t = re.sub(r"\s+", " ", t).strip()
    return hashlib.md5(t.encode()).hexdigest()


def _deduplicate(results: list[Result]) -> list[Result]:
    """Remove duplicate entries by URL and title fingerprint."""
    seen_urls: set[str] = set()
    seen_fp: set[str]   = set()
    unique: list[Result] = []
    for r in results:
        url = r.get("url", "").strip()
        fp  = _title_fingerprint(r.get("title", ""))
        if url in seen_urls or fp in seen_fp:
            continue
        if url:
            seen_urls.add(url)
        seen_fp.add(fp)
        unique.append(r)
    return unique


def _score(result: Result) -> float:
    cred = _SOURCE_CREDIBILITY.get(result.get("source", "web"), 0.7)
    rel  = result.get("relevance_score", 1.0)
    # Boost results with non-empty abstracts
    has_abstract = 1.1 if len(result.get("abstract", "")) > 100 else 0.9
    return cred * rel * has_abstract


def research(
    query: str,
    sources: list[str] | None = None,
    results_per_source: int = 5,
    timeout: int = 20,
) -> list[Result]:
    """Run all enabled sources concurrently and return ranked, deduplicated results.

    Args:
        query:              Research topic / search query.
        sources:            List of source names to use. None = all sources.
        results_per_source: Max results to request from each source.
        timeout:            Per-source timeout in seconds.

    Returns:
        Ranked list of Result dicts (highest quality first).
    """
    from research1.sources import SOURCES

    enabled = {k: v for k, v in SOURCES.items()
               if sources is None or k in sources}

    all_results: list[Result] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=len(enabled)) as pool:
        futures = {
            pool.submit(fn, query, results_per_source, timeout): name
            for name, fn in enabled.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
                print(f"  [{name:10s}] {len(results)} result(s)")
            except Exception as e:
                errors.append(f"{name}: {e}")
                print(f"  [{name:10s}] ERROR: {e}")

    if errors:
        print(f"  Warning: {len(errors)} source(s) failed: {', '.join(errors)}")

    deduped  = _deduplicate(all_results)
    ranked   = sorted(deduped, key=_score, reverse=True)
    return ranked
