"""Filing parser for SEC EDGAR filings.

Parses raw filing text into structured filing items (sections like Item 1,
Item 7, Financial Statements, etc.).

Supports both 10-K (annual) and 10-Q (quarterly) filing formats.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from sec_importer.models import FilingItemModel

logger = logging.getLogger(__name__)

# Regex patterns for section headers in 10-K filings
# Matches patterns like "Item 1. Business", "Item 7. Management's Discussion", etc.
ITEM_PATTERN = re.compile(
    r"^(Item\s+\d+[A-Z]?\s*\.?\s*.+?)(?=\n|$)",
    re.MULTILINE | re.IGNORECASE,
)

# More specific patterns for common 10-K sections
SECTION_PATTERNS = [
    # Item headers (must come first to capture "Item N" patterns including Item 2.01)
    (re.compile(r"^(Item\s+\d+[A-Z]?\s*\.?\s*.+?)$", re.MULTILINE | re.IGNORECASE), "item"),
    # Financial statement headers
    (re.compile(r"^Consolidated\s+Statements?\s+of\s+", re.MULTILINE | re.IGNORECASE), "financial_statement"),
    (re.compile(r"^Balance\s+Sheet", re.MULTILINE | re.IGNORECASE), "financial_statement"),
    (re.compile(r"^Statements?\s+of\s+Stockholders?['\s]?\s*Equity", re.MULTILINE | re.IGNORECASE), "financial_statement"),
    (re.compile(r"^Statements?\s+of\s+Cash\s+Flows", re.MULTILINE | re.IGNORECASE), "financial_statement"),
    (re.compile(r"^Notes?\s+to\s+Consolidated\s+Financial\s+Statements?", re.MULTILINE | re.IGNORECASE), "financial_statement"),
    # MD&A sections
    (re.compile(r"^Management['\s]?\s*Discussion\s+and\s+Analysis", re.MULTILINE | re.IGNORECASE), "mda"),
    # Risk factors
    (re.compile(r"^Risk\s+Factors", re.MULTILINE | re.IGNORECASE), "risk_factors"),
    # Legal proceedings
    (re.compile(r"^Legal\s+Proceedings", re.MULTILINE | re.IGNORECASE), "legal"),
    # Market for securities
    (re.compile(r"^Market\s+for\s+Registrant['\s]?\s*Common\s+Equity", re.MULTILINE | re.IGNORECASE), "market"),
    # Properties
    (re.compile(r"^Properties", re.MULTILINE | re.IGNORECASE), "properties"),
    # Management
    (re.compile(r"^Management\s+of\s+Companies", re.MULTILINE | re.IGNORECASE), "management"),
    # Executive compensation
    (re.compile(r"^Executive\s+Compensation", re.MULTILINE | re.IGNORECASE), "compensation"),
    # Directors
    (re.compile(r"^Directors", re.MULTILINE | re.IGNORECASE), "directors"),
    # Audit
    (re.compile(r"^Audit\s+Reports?", re.MULTILINE | re.IGNORECASE), "audit"),
    # Quantitative/Qualitative disclosures
    (re.compile(r"^Quantitative\s+and\s+Qualitative\s+Disclosures", re.MULTILINE | re.IGNORECASE), "disclosure"),
]

# XBRL-specific patterns
XBRL_ITEM_PATTERN = re.compile(
    r"<[^>]*>([A-Z][A-Z0-9._-]*)</[^>]*>",
    re.IGNORECASE,
)

# Pattern to detect if content is XBRL-formatted
XBRL_MARKER = re.compile(r"<[^>]*>")


class FilingParser:
    """Parses raw SEC filing text into structured sections."""

    def __init__(self):
        """Initialize the filing parser."""
        self._sections: List[Dict[str, Optional[str]]] = []
        self._raw_text: str = ""
        self._filing_type: str = ""

    def parse(self, raw_text: str, filing_type: str = "10-K") -> List[FilingItemModel]:
        """Parse raw filing text into structured filing items.

        Args:
            raw_text: Raw text content of the filing.
            filing_type: Type of filing (e.g. '10-K', '10-Q', '8-K').

        Returns:
            List of FilingItemModel objects representing parsed sections.
        """
        self._raw_text = raw_text
        self._filing_type = filing_type
        self._sections = []

        if self._is_xbrl(raw_text):
            self.items = self._parse_xbrl(raw_text)
        else:
            self.items = self._parse_text(raw_text)
        return self.items

    def _is_xbrl(self, text: str) -> bool:
        """Detect if the filing text is in XBRL format.

        XBRL filings contain XML tags and structured data elements.

        Args:
            text: Raw filing text.

        Returns:
            True if the filing appears to be XBRL-formatted.
        """
        # Check for XML/XBRL markers
        xml_count = len(re.findall(r"<[^>]+>", text[:10000]))
        return xml_count > 5

    def _parse_text(self, text: str) -> List[FilingItemModel]:
        """Parse text-based filing (traditional HTML/text format).

        Args:
            text: Raw filing text.

        Returns:
            List of FilingItemModel objects.
        """
        lines = text.split("\n")
        items: List[FilingItemModel] = []
        current_section: Optional[str] = None
        current_content: List[str] = []

        for line in lines:
            section_match = self._match_section_header(line)
            if section_match:
                # Save previous section
                if current_section and current_content:
                    items.append(FilingItemModel(
                        filing_id=None,  # Placeholder; set by repository before persistence
                        accession_no="0",  # Placeholder; set by repository before persistence
                        item_label=current_section,
                        item_content="\n".join(current_content).strip(),
                        item_type=self._classify_section(current_section),
                    ))
                # Extract section label from the match
                # SECTION_PATTERNS have no capture groups (group(0) only)
                # The Item regex has groups 1 and 2
                # Use try/except to safely extract the label
                try:
                    current_section = section_match.group(2) or section_match.group(1) or section_match.group(0)
                except IndexError:
                    current_section = section_match.group(0)
                current_content = []
            elif current_section is not None:
                current_content.append(line)
            else:
                # Content before any section header (e.g., cover page)
                if line.strip():
                    current_content.append(line)

        # Save last section
        if current_section and current_content:
            items.append(FilingItemModel(
                filing_id=None,
                accession_no="0",
                item_label=current_section,
                item_content="\n".join(current_content).strip(),
                item_type=self._classify_section(current_section),
            ))

        # If no sections were found, treat entire content as one item
        if not items:
            items.append(FilingItemModel(
                filing_id=None,
                accession_no="0",
                item_label="Full Filing",
                item_content=text.strip() if text.strip() else "",
                item_type="full_text",
            ))

        return items

    def _parse_xbrl(self, text: str) -> List[FilingItemModel]:
        """Parse XBRL-formatted filing.

        XBRL filings have structured XML elements. We extract the
        element names and their text content.

        Args:
            text: Raw XBRL filing text.

        Returns:
            List of FilingItemModel objects.
        """
        items: List[FilingItemModel] = []

        # Extract XBRL elements with their content
        # Pattern matches <element>content</element>, handling namespace prefixes like us-gaap:
        element_pattern = re.compile(
            r"<([a-zA-Z][a-zA-Z0-9._-]*:[a-zA-Z][a-zA-Z0-9._-]*)>([^<]*(?:<[^/][^>]*>[^<]*)*)</\1>",
            re.DOTALL,
        )

        for match in element_pattern.finditer(text):
            element_name = match.group(1)
            content = match.group(2).strip()

            if content and len(content) > 10:  # Skip very short elements
                items.append(FilingItemModel(
                    filing_id=None,
                    accession_no="0",
                    item_label=element_name,
                    item_content=content,
                    item_type="xbrl_element",
                ))

        # If no structured elements found, treat as full text
        if not items:
            items.append(FilingItemModel(
                filing_id=None,
                accession_no="0",
                item_label="XBRL Content",
                item_content=text.strip(),
                item_type="xbrl_full",
            ))

        return items

    def _match_section_header(self, line: str) -> Optional[re.Match]:
        """Match a section header in the filing text.

        Args:
            line: A single line from the filing.

        Returns:
            Regex match object if a section header is found, None otherwise.
        """
        stripped = line.strip()

        # Try each pattern
        for pattern, section_type in SECTION_PATTERNS:
            match = pattern.match(stripped)
            if match:
                return match

        # Try generic Item header (with optional label)
        item_match = re.match(r"^Item\s+(\d+[A-Z]?)\s*\.?\s*(.+?)$", stripped, re.IGNORECASE)
        if item_match:
            return item_match

        return None

    def _classify_section(self, label: str) -> str:
        """Classify a section label into a type category.

        Args:
            label: Section label text.

        Returns:
            Section type category string.
        """
        label_lower = label.lower()

        if "item" in label_lower:
            return "item"
        elif any(kw in label_lower for kw in ["financial", "balance", "statement", "equity", "cash flow", "note"]):
            return "financial_statement"
        elif "management" in label_lower or "discussion" in label_lower or "analysis" in label_lower:
            return "mda"
        elif "risk" in label_lower:
            return "risk_factors"
        elif "legal" in label_lower:
            return "legal"
        elif "market" in label_lower:
            return "market"
        elif "property" in label_lower:
            return "properties"
        elif "compensation" in label_lower:
            return "compensation"
        elif "director" in label_lower:
            return "directors"
        elif "audit" in label_lower:
            return "audit"
        elif "disclosure" in label_lower:
            return "disclosure"
        else:
            return "other"

    def get_sections(self) -> List[Dict[str, Optional[str]]]:
        """Get the parsed sections.

        Returns:
            List of dictionaries with section information.
        """
        return [{"label": item.item_label, "content": item.item_content, "type": item.item_type} for item in getattr(self, "items", [])]

    def get_summary(self) -> Dict[str, int]:
        """Get a summary of parsed sections by type.

        Returns:
            Dictionary mapping section types to counts.
        """
        summary: Dict[str, int] = {}
        for item in getattr(self, "items", []):
            section_type = item.item_type or "unknown"
            summary[section_type] = summary.get(section_type, 0) + 1
        return summary


def parse_filing(raw_text: str, filing_type: str = "10-K") -> List[FilingItemModel]:
    """Convenience function to parse a filing.

    Args:
        raw_text: Raw filing text.
        filing_type: Type of filing.

    Returns:
        List of FilingItemModel objects.
    """
    parser = FilingParser()
    return parser.parse(raw_text, filing_type)
