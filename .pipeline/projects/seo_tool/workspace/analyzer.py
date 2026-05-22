"""HTML analyzer — fetches a URL and extracts SEO-relevant metadata."""

from __future__ import annotations

import re
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag

from seo_tool.models import (
    SEOReport,
    ImageInfo,
    LinkInfo,
    MetaTag,
    OpenGraphTag,
)


class AnalyzerError(Exception):
    """Raised when the analyzer encounters a problem."""


class Analyzer:
    """Fetches HTML from a URL and extracts SEO metadata."""

    DEFAULT_TIMEOUT = 15  # seconds

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_and_parse(self, url: str) -> SEOReport:
        """Fetch *url*, parse its HTML, and return an SEOReport.

        Raises:
            AnalyzerError: On HTTP errors or network failures.
        """
        report = SEOReport(url=url)

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": "SEO-Tool/0.1"},
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            report.fetch_error = str(exc)
            report.http_status = getattr(exc.response, "status_code", None) if hasattr(exc, "response") and exc.response else None
            raise AnalyzerError(f"Failed to fetch {url}: {exc}") from exc

        report.http_status = response.status_code
        self._parse_html(response.text, report)
        return report

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_html(self, html: str, report: SEOReport) -> None:
        """Populate *report* from *html* string."""
        soup = BeautifulSoup(html, "lxml")

        self._extract_title(soup, report)
        self._extract_meta_tags(soup, report)
        self._extract_headings(soup, report)
        self._extract_images(soup, report)
        self._extract_canonical(soup, report)
        self._extract_og_tags(soup, report)
        self._extract_links(soup, report)
        self._extract_word_count(soup, report)

    # -- Title --------------------------------------------------------

    def _extract_title(self, soup: BeautifulSoup, report: SEOReport) -> None:
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            report.title = title_tag.string.strip()

    # -- Meta tags ----------------------------------------------------

    def _extract_meta_tags(self, soup: BeautifulSoup, report: SEOReport) -> None:
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property") or ""
            content = meta.get("content")
            if name:
                report.meta_tags.append(MetaTag(name=name, content=content))
                # Convenience shortcuts
                if name == "description":
                    report.meta_description = content
                elif name == "keywords":
                    report.meta_keywords = content

    # -- Headings -----------------------------------------------------

    def _extract_headings(self, soup: BeautifulSoup, report: SEOReport) -> None:
        for level in range(1, 7):
            tag_name = f"h{level}"
            for heading in soup.find_all(tag_name):
                text = heading.get_text(strip=True)
                if text:
                    report.headings.append((level, text))

    # -- Images -------------------------------------------------------

    def _extract_images(self, soup: BeautifulSoup, report: SEOReport) -> None:
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            alt = img.get("alt")
            report.images.append(ImageInfo(src=src, alt=alt))

    # -- Canonical link -----------------------------------------------

    def _extract_canonical(self, soup: BeautifulSoup, report: SEOReport) -> None:
        canonical = soup.find("link", rel="canonical")
        if canonical:
            report.canonical_link = canonical.get("href")

    # -- Open Graph tags ----------------------------------------------

    def _extract_og_tags(self, soup: BeautifulSoup, report: SEOReport) -> None:
        for meta in soup.find_all("meta", property=re.compile(r"^og:")):
            prop = meta.get("property", "")
            content = meta.get("content")
            report.og_tags.append(OpenGraphTag(property=prop, content=content))

    # -- Links --------------------------------------------------------

    def _extract_links(self, soup: BeautifulSoup, report: SEOReport) -> None:
        base_url = self._extract_base_domain(report.url)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            is_internal = self._is_internal_link(href, base_url)
            info = LinkInfo(href=href, text=text, is_internal=is_internal)
            if is_internal:
                report.internal_links.append(info)
            else:
                report.external_links.append(info)
        report.link_count = len(report.internal_links) + len(report.external_links)

    # -- Word count ---------------------------------------------------

    def _extract_word_count(self, soup: BeautifulSoup, report: SEOReport) -> None:
        text = soup.get_text(separator=" ", strip=True)
        words = [w for w in text.split() if w]
        report.word_count = len(words)

    # -- Helpers ------------------------------------------------------

    @staticmethod
    def _extract_base_domain(url: str) -> str:
        """Return the scheme + domain from *url* (e.g. 'https://example.com')."""
        match = re.match(r"(https?://[^/]+)", url)
        return match.group(1) if match else ""

    @staticmethod
    def _is_internal_link(href: str, base_domain: str) -> bool:
        """Heuristic: is *href* likely internal?"""
        if href.startswith(("/", "javascript:", "mailto:", "tel:")):
            return True
        match = re.match(r"(https?://[^/]+)", href)
        if match:
            return match.group(1) == base_domain
        return False
