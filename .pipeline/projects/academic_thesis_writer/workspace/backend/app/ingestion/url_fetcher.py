"""URL-based source metadata extraction."""

from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ..models import Source


class URLFetcher:
    """Fetch metadata from a URL (arXiv, general web pages)."""

    @staticmethod
    def fetch(url: str) -> Source:
        """Extract source metadata from a URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (AcademicThesisWriter/1.0)"
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Try arXiv first
        if "arxiv.org" in url or "arxiv" in url.lower():
            return URLFetcher._extract_arxiv(soup, url)

        # Try general HTML metadata
        title = URLFetcher._extract_title(soup)
        authors = URLFetcher._extract_authors(soup)
        year = URLFetcher._extract_year(soup)
        abstract = URLFetcher._extract_abstract(soup)

        return Source(
            title=title or "Unknown Title",
            authors=authors,
            year=year,
            abstract=abstract,
            url=url,
            source_type="url",
        )

    @staticmethod
    def _extract_arxiv(soup: BeautifulSoup, url: str) -> Source:
        """Extract metadata from an arXiv page."""
        title_el = soup.find("title")
        title = title_el.get_text(strip=True) if title_el else "Unknown Title"
        # Clean arXiv title (remove arXiv:xxxx.xxxxx)
        title = re.sub(r"^arXiv:\s*\d{4}\.\d{4,5}\s*-\s*", "", title)

        # Authors
        author_els = soup.find_all("meta", attrs={"name": "dc.creator"})
        authors = [a.get("content", "").strip() for a in author_els if a.get("content")]

        # Year
        year_el = soup.find("meta", attrs={"name": "dc.date"})
        year = None
        if year_el and year_el.get("content"):
            try:
                year = int(year_el["content"][:4])
            except (ValueError, IndexError):
                pass

        # Abstract
        abs_el = soup.find("blockquote", class_="abstract")
        abstract = abs_el.get_text(strip=True) if abs_el else ""

        # arXiv ID
        arxiv_id = url.split("/")[-1]
        if not arxiv_id.endswith(".pdf"):
            arxiv_id = arxiv_id.split("v")[0]

        return Source(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            url=url,
            source_type="url",
        )

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> Optional[str]:
        for el in [
            soup.find("meta", attrs={"name": "dc.title"}),
            soup.find("meta", attrs={"property": "og:title"}),
            soup.find("meta", attrs={"name": "citation_title"}),
            soup.find("h1"),
        ]:
            if el and el.get("content"):
                return el["content"].strip()
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return None

    @staticmethod
    def _extract_authors(soup: BeautifulSoup) -> List[str]:
        authors = []
        for el in [
            soup.find("meta", attrs={"name": "dc.creator"}),
            soup.find("meta", attrs={"property": "og:author"}),
            soup.find("meta", attrs={"name": "citation_author"}),
        ]:
            if el and el.get("content"):
                authors.extend([a.strip() for a in el["content"].split(";") if a.strip()])
        return authors

    @staticmethod
    def _extract_year(soup: BeautifulSoup) -> Optional[int]:
        for el in [
            soup.find("meta", attrs={"name": "dc.date"}),
            soup.find("meta", attrs={"name": "citation_publication_date"}),
            soup.find("meta", attrs={"property": "article:published_time"}),
        ]:
            if el and el.get("content"):
                try:
                    return int(el["content"][:4])
                except (ValueError, IndexError):
                    pass
        return None

    @staticmethod
    def _extract_abstract(soup: BeautifulSoup) -> str:
        for el in [
            soup.find("meta", attrs={"name": "dc.description"}),
            soup.find("meta", attrs={"property": "og:description"}),
            soup.find("meta", attrs={"name": "citation_abstract"}),
            soup.find("div", class_="abstract"),
            soup.find("blockquote", class_="abstract"),
        ]:
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""
