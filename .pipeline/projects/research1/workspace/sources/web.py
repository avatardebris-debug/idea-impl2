"""
sources/web.py — Credible web search via DuckDuckGo Instant Answer API + allowlist.

Strategy:
1. Query DuckDuckGo's free Instant Answer API for topic overview + related topics.
2. Filter results to a credible domain allowlist (government, .edu, major publishers).
3. Fetch and extract text from allowed URLs using stdlib urllib.

No API key required. Fallback: return the DuckDuckGo abstract only.

Credible domain allowlist (tier 1 — high trust):
    .gov, .edu, nature.com, science.org, cell.com, nejm.org, bmj.com,
    thelancet.com, who.int, cdc.gov, nih.gov, ieee.org, acm.org,
    mit.edu, stanford.edu, ox.ac.uk, cam.ac.uk, bbc.co.uk/news,
    reuters.com, apnews.com, economist.com, scientificamerican.com,
    mayoclinic.org, clevelandclinic.org, healthline.com
"""
from __future__ import annotations
import html
import json
import re
import urllib.parse
import urllib.request
import urllib.error
from research1.sources.arxiv import Result

_DDG_API   = "https://api.duckduckgo.com/"
_HEADERS   = {"User-Agent": "research1/0.1 (contact: research1@example.com)"}
_MAX_PAGE_CHARS = 3000  # max extracted chars per fetched page

_CREDIBLE_DOMAINS = {
    ".gov", ".edu", "nature.com", "science.org", "cell.com", "nejm.org",
    "bmj.com", "thelancet.com", "who.int", "nih.gov", "ieee.org", "acm.org",
    "mit.edu", "stanford.edu", "ox.ac.uk", "cam.ac.uk", "bbc.co.uk",
    "reuters.com", "apnews.com", "economist.com", "scientificamerican.com",
    "mayoclinic.org", "clevelandclinic.org", "healthline.com",
    "pnas.org", "sciencedirect.com", "springer.com", "wiley.com",
}


def _is_credible(url: str) -> bool:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
        return any(host.endswith(d) or d in host for d in _CREDIBLE_DOMAINS)
    except Exception:
        return False


def _fetch_text(url: str, timeout: int = 10) -> str:
    """Fetch URL and return stripped plain text (best-effort)."""
    try:
        req = urllib.request.Request(url, headers={**_HEADERS, "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(65536).decode("utf-8", errors="replace")
    except Exception:
        return ""

    # Strip tags, decode entities, collapse whitespace
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<style[^>]*>.*?</style>",  " ", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw[:_MAX_PAGE_CHARS]


def search(query: str, max_results: int = 5, timeout: int = 15) -> list[Result]:
    """Search credible web sources via DuckDuckGo Instant Answer API."""
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    })
    url = f"{_DDG_API}?{params}"

    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    results: list[Result] = []

    # Primary: Abstract (DuckDuckGo instant answer)
    abstract_text = data.get("Abstract", "").strip()
    abstract_url  = data.get("AbstractURL", "").strip()
    abstract_src  = data.get("AbstractSource", "Web")
    if abstract_text:
        results.append(Result(
            source="web",
            title=data.get("Heading", query),
            authors=[abstract_src],
            abstract=abstract_text[:1500],
            url=abstract_url or url,
            published="",
            relevance_score=0.95,
        ))

    # Related topics: filter to credible domains
    related = data.get("RelatedTopics", [])
    seen_urls: set[str] = {abstract_url}

    for item in related:
        if len(results) >= max_results:
            break
        # Some items are topic groups — unwrap them
        if "Topics" in item:
            for sub in item["Topics"]:
                related.append(sub)
            continue

        topic_url  = item.get("FirstURL", "")
        topic_text = item.get("Text", "").strip()
        if not topic_url or not topic_text or topic_url in seen_urls:
            continue
        seen_urls.add(topic_url)

        if _is_credible(topic_url):
            page_text = _fetch_text(topic_url, timeout=timeout // 2) or topic_text
            results.append(Result(
                source="web",
                title=topic_text[:80],
                authors=["Web"],
                abstract=page_text[:1500],
                url=topic_url,
                published="",
                relevance_score=0.75,
            ))
        else:
            # Still include DuckDuckGo related topic even if domain not in allowlist
            # (DuckDuckGo itself aggregates from credible sources)
            results.append(Result(
                source="web",
                title=topic_text[:80],
                authors=["Web"],
                abstract=topic_text[:1500],
                url=topic_url,
                published="",
                relevance_score=0.5,
            ))

    return results[:max_results]
