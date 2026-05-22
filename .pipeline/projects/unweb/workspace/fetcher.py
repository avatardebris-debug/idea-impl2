"""
fetcher.py — Fetch article text from a URL or accept raw text.

Strips HTML, extracts the article body (main/article tags first,
then largest text block as fallback), and returns clean plain text.
"""
from __future__ import annotations
import html
import re
import urllib.request
import urllib.error
import urllib.parse

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; unweb/0.1; +https://github.com/unweb)"
    ),
    "Accept": "text/html,application/xhtml+xml",
}
_MAX_BYTES = 200_000


def fetch_url(url: str, timeout: int = 15) -> str:
    """Download a URL and return the extracted plain text body."""
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(_MAX_BYTES).decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not fetch {url}: {e}") from e

    return _extract_text(raw)


def _extract_text(html_src: str) -> str:
    """Extract article body text from raw HTML."""
    # Remove scripts, styles, nav, header, footer
    for tag in ["script", "style", "nav", "header", "footer", "aside", "form"]:
        html_src = re.sub(
            rf"<{tag}[^>]*>.*?</{tag}>", " ", html_src,
            flags=re.DOTALL | re.IGNORECASE,
        )

    # Try to extract <article> or <main> content first
    for block_tag in ["article", "main"]:
        m = re.search(
            rf"<{block_tag}[^>]*>(.*?)</{block_tag}>",
            html_src, re.DOTALL | re.IGNORECASE,
        )
        if m:
            html_src = m.group(1)
            break

    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", html_src)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:15000]  # cap for LLM context
