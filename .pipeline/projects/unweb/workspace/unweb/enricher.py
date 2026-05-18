"""
enricher.py — Enrich extracted entities with Wikipedia background data.

For each person and org found, queries Wikipedia to add:
  - Brief biography / org description
  - Known affiliations and funding (from Wikipedia text)
  - Any notable controversies mentioned

Results are merged back into the connection graph dict.
"""
from __future__ import annotations
import json
import re
import urllib.parse
import urllib.request
import urllib.error

_WIKI_API   = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
_HEADERS    = {"User-Agent": "unweb/0.1 (contact: unweb@example.com)"}
_MAX_EXTRACT = 800


def _wiki_summary(name: str, timeout: int = 8) -> str:
    """Fetch Wikipedia summary for a name. Returns empty string on failure."""
    encoded = urllib.parse.quote(name.replace(" ", "_"))
    url = _WIKI_API.format(encoded)
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("extract", "")[:_MAX_EXTRACT]
    except Exception:
        return ""


def enrich(graph: dict, max_entities: int = 10, timeout: int = 8) -> dict:
    """Add Wikipedia background to the top entities in the graph.

    Modifies graph in-place, adding a 'wiki_summary' key to each person/org.

    Args:
        graph:         Connection graph from extractor.extract_connections()
        max_entities:  Maximum number of entities to look up (rate limit guard)
        timeout:       Per-request timeout in seconds

    Returns:
        Same graph dict with wiki_summary fields populated.
    """
    entities_done = 0

    for person in graph.get("people", []):
        if entities_done >= max_entities:
            break
        if not person.get("wiki_summary"):
            summary = _wiki_summary(person["name"], timeout=timeout)
            person["wiki_summary"] = summary
            if summary:
                entities_done += 1

    for org in graph.get("orgs", []):
        if entities_done >= max_entities:
            break
        if not org.get("wiki_summary"):
            summary = _wiki_summary(org["name"], timeout=timeout)
            org["wiki_summary"] = summary
            if summary:
                entities_done += 1

    return graph
