"""
sources/wikipedia.py — Wikipedia summary search via the public REST API.

Uses the Wikipedia search API to find relevant articles, then fetches
the extract (intro section) for each. No API key required.

API docs: https://www.mediawiki.org/wiki/API:Search
"""
from __future__ import annotations
import json
import re
import urllib.parse
import urllib.request
import urllib.error
from research1.sources.arxiv import Result

_SEARCH_URL  = "https://en.wikipedia.org/w/api.php"
_EXTRACT_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_HEADERS     = {"User-Agent": "research1/0.1 (contact: research1@example.com)"}


def search(query: str, max_results: int = 3, timeout: int = 15) -> list[Result]:
    """Search Wikipedia and return article extracts."""
    # Step 1: find candidate titles
    params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": max_results,
        "format": "json",
        "utf8": 1,
    })
    search_url = f"{_SEARCH_URL}?{params}"
    try:
        req = urllib.request.Request(search_url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        hits = data.get("query", {}).get("search", [])
    except Exception:
        return []

    results: list[Result] = []
    for hit in hits[:max_results]:
        title = hit.get("title", "")
        snippet = re.sub(r"<[^>]+>", "", hit.get("snippet", ""))  # strip HTML tags

        # Step 2: fetch full extract via REST summary endpoint
        abstract = snippet
        url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        try:
            encoded_title = urllib.parse.quote(title.replace(" ", "_"))
            ext_url = _EXTRACT_URL.format(title=encoded_title)
            req2 = urllib.request.Request(ext_url, headers=_HEADERS)
            with urllib.request.urlopen(req2, timeout=timeout) as resp2:
                ext_data = json.loads(resp2.read().decode("utf-8"))
            abstract = ext_data.get("extract", snippet)[:1500]
            url = ext_data.get("content_urls", {}).get("desktop", {}).get("page", url)
        except Exception:
            pass  # fallback to snippet

        results.append(Result(
            source="wikipedia",
            title=title,
            authors=["Wikipedia contributors"],
            abstract=_clean(abstract),
            url=url,
            published="",
            relevance_score=0.9,  # Wikipedia is useful but not peer-reviewed
        ))
    return results


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text.strip())
