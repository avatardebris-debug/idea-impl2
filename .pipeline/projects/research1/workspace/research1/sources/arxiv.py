"""
sources/arxiv.py — arXiv search via the public Atom feed API (no key required).

Returns up to `max_results` Result dicts per query.
API docs: https://arxiv.org/help/api/user-manual
"""
from __future__ import annotations
import re
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from typing import TypedDict


class Result(TypedDict):
    source: str
    title: str
    authors: list[str]
    abstract: str
    url: str
    published: str
    relevance_score: float


_BASE = "https://export.arxiv.org/api/query"
_NS = {"atom": "http://www.w3.org/2005/Atom",
       "arxiv": "http://arxiv.org/schemas/atom"}


def search(query: str, max_results: int = 5, timeout: int = 15) -> list[Result]:
    """Search arXiv and return up to max_results paper summaries.

    Args:
        query:       Natural language or boolean query string.
        max_results: Maximum number of results to return.
        timeout:     HTTP timeout in seconds.

    Returns:
        List of Result dicts.
    """
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{_BASE}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "research1/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_text = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        return []  # offline or rate-limited

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    results: list[Result] = []
    for entry in root.findall("atom:entry", _NS):
        title_el   = entry.find("atom:title", _NS)
        summary_el = entry.find("atom:summary", _NS)
        id_el      = entry.find("atom:id", _NS)
        pub_el     = entry.find("atom:published", _NS)
        authors    = [
            a.find("atom:name", _NS).text or ""
            for a in entry.findall("atom:author", _NS)
            if a.find("atom:name", _NS) is not None
        ]

        title    = _clean(title_el.text if title_el is not None else "")
        abstract = _clean(summary_el.text if summary_el is not None else "")
        url      = (id_el.text or "").strip()
        published = (pub_el.text or "")[:10]

        results.append(Result(
            source="arxiv",
            title=title,
            authors=authors[:5],
            abstract=abstract[:1500],
            url=url,
            published=published,
            relevance_score=1.0,  # API returns by relevance already
        ))

    return results


def _clean(text: str) -> str:
    """Normalise whitespace and remove XML artifacts."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())
