"""
api.py — Programmatic API for unweb.

This module provides the high-level `run()` function that ties together
fetching, extraction, enrichment, and reporting into a single call.

Usage:
    from unweb.api import run
    result = run("https://example.com/article")
    print(result.report)

    result = run("raw article text", source_type="text")
    print(result.graph)
"""
from __future__ import annotations
import json
import pathlib
from dataclasses import dataclass, field
from typing import Optional

from unweb.fetcher import fetch_url
from unweb.extractor import extract_connections
from unweb.enricher import enrich
from unweb.reporter import build_report, save_report


@dataclass
class UnwebResult:
    """Result of running unweb on a story."""
    graph: dict = field(default_factory=dict)
    report: str = ""
    source: str = ""
    enriched: bool = False
    errors: list[str] = field(default_factory=list)


def run(
    source: str,
    *,
    source_type: str = "url",
    enrich_entities: bool = True,
    max_entities: int = 10,
    output_path: Optional[str] = None,
    format: str = "markdown",
) -> UnwebResult:
    """Run the full unweb pipeline on a news story.

    Args:
        source: URL of the article, or raw article text (if source_type="text").
        source_type: "url" or "text".
        enrich_entities: Whether to enrich entities with Wikipedia data.
        max_entities: Maximum number of entities to enrich.
        output_path: Optional file path to save the report.
        format: Output format — "markdown" or "json".

    Returns:
        UnwebResult with graph, report, source, enriched flag, and any errors.
    """
    result = UnwebResult(source=source)

    # Step 1: Fetch the article text
    try:
        if source_type == "url":
            text = fetch_url(source)
        else:
            text = source
        if not text or len(text.strip()) < 50:
            result.errors.append("Article text too short or empty after fetching.")
            return result
    except Exception as exc:
        result.errors.append(f"Fetch error: {exc}")
        return result

    # Step 2: Extract entities and connections
    try:
        graph = extract_connections(text)
        if not graph:
            result.errors.append("Extractor returned empty graph.")
            return result
        result.graph = graph
    except Exception as exc:
        result.errors.append(f"Extraction error: {exc}")
        return result

    # Step 3: Enrich entities (optional)
    if enrich_entities:
        try:
            graph = enrich(graph, max_entities=max_entities)
            result.graph = graph
            result.enriched = True
        except Exception as exc:
            result.errors.append(f"Enrichment error: {exc}")
            # Continue without enrichment

    # Step 4: Build the report
    try:
        if format == "json":
            result.report = json.dumps(result.graph, indent=2, ensure_ascii=False)
        else:
            result.report = build_report(result.graph, source=result.source)
    except Exception as exc:
        result.errors.append(f"Report generation error: {exc}")
        return result

    # Step 5: Save report to file if requested
    if output_path:
        try:
            save_report(result.report, output_path)
        except Exception as exc:
            result.errors.append(f"Save error: {exc}")

    return result
