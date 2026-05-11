"""HTML parser for SEC EDGAR filings.

Downloads and parses HTML filing documents from SEC EDGAR to extract
structured text sections (MD&A, Risk Factors, Business, Financial Statements, etc.).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTMLParser:
    """Parse HTML filing documents from SEC filings.

    Downloads HTML filings from SEC EDGAR and extracts key sections
    like MD&A, Risk Factors, Business Overview, Financial Statements, etc.
    """

    # Section detection patterns (case-insensitive)
    SECTION_PATTERNS = {
        "mda": [
            "management\'s discussion and analysis",
            "management discussion and analysis",
            "md&a",
            "md&a.",
            "management's discussion",
        ],
        "risk_factors": [
            "risk factors",
            "risk factor",
            "risks",
        ],
        "business": [
            "business overview",
            "overview of our business",
            "our business",
            "general business",
            "business.",
        ],
        "financial_statements": [
            "financial statements",
            "consolidated financial statements",
            "financial statement",
            "consolidated statements",
            "standalone financial statements",
        ],
        "body": [
            "item 1a",
            "item 1",
            "item 7",
            "item 7a",
            "item 8",
            "item 9",
            "item 10",
            "item 11",
            "item 12",
            "forward-looking statements",
            "safe harbor",
        ],
    }

    def __init__(self, timeout: int = 60):
        """Initialize the HTML parser.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self._session = httpx.Client(
            headers={
                "User-Agent": "SECImporter/0.1.0 (contact: sec-importer@example.com)",
                "Accept": "text/html, application/xhtml+xml, */*",
            },
            timeout=self.timeout,
        )

    def parse_from_url(self, url: str) -> dict[str, Any]:
        """Download and parse HTML filing from a URL.

        Args:
            url: URL to the HTML filing document.

        Returns:
            Dict with extracted sections and parse status.
        """
        try:
            response = self._session.get(url)
            response.raise_for_status()
            return self.parse_html(response.text)
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch HTML from {url}: {e}")
            return {"sections": {}, "parse_status": "failed", "parse_error": str(e)}

    def parse_html(self, html_content: str) -> dict[str, Any]:
        """Parse HTML content and extract key sections.

        Args:
            html_content: Raw HTML string.

        Returns:
            Dict with section keys and extracted text content.
        """
        if not html_content or not html_content.strip():
            return {
                "sections": {},
                "parse_status": "failed",
                "parse_error": "Empty HTML content",
            }

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            sections = self._extract_sections(soup)
            return {
                "sections": sections,
                "parse_status": "success",
                "parse_error": None,
            }
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            return {
                "sections": {},
                "parse_status": "failed",
                "parse_error": str(e),
            }

    def _extract_sections(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract key sections from the parsed HTML.

        Args:
            soup: Parsed BeautifulSoup object.

        Returns:
            Dict mapping section names to their text content.
        """
        sections = {}

        for section_name, patterns in self.SECTION_PATTERNS.items():
            content = self._find_section_content(soup, patterns)
            if content:
                sections[section_name] = content

        return sections

    def _find_section_content(self, soup: BeautifulSoup, patterns: list[str]) -> Optional[str]:
        """Find content matching any of the given patterns.

        Args:
            soup: Parsed BeautifulSoup object.
            patterns: List of text patterns to search for.

        Returns:
            Text content of the first matching section, or None.
        """
        for pattern in patterns:
            # Search in headings
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                if pattern.lower() in tag.get_text(strip=True).lower():
                    # Get content after this heading
                    content = self._get_section_after_heading(tag)
                    if content:
                        return content

            # Search in paragraphs
            for tag in soup.find_all("p"):
                if pattern.lower() in tag.get_text(strip=True).lower():
                    content = self._get_section_after_heading(tag)
                    if content:
                        return content

        return None

    def _get_section_after_heading(self, tag) -> Optional[str]:
        """Get text content after a heading until the next heading or end.

        Args:
            tag: The heading element.

        Returns:
            Concatenated text content, or None.
        """
        texts = []
        current = tag.find_next_sibling()
        while current:
            # Stop at the next heading of the same or higher level
            if current.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                break
            if current.name == "p":
                text = current.get_text(strip=True)
                if text:
                    texts.append(text)
            current = current.find_next_sibling()

        return "\n\n".join(texts) if texts else None

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
