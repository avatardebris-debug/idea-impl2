"""Financial line-item normalization module."""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# Standard line items
STANDARD_LINE_ITEMS = [
    "revenue",
    "cogs",
    "gross_profit",
    "operating_income",
    "net_income",
    "total_assets",
    "total_liabilities",
    "total_equity",
    "cash_and_equivalents",
    "cash_flow_ops",
    "capex",
    "free_cash_flow",
]

# Alias map: various names -> standard name
ALIAS_MAP = {
    "revenue": "revenue",
    "total revenue": "revenue",
    "sales": "revenue",
    "net revenue": "revenue",
    "gross sales": "revenue",
    "cost of goods sold": "cogs",
    "cost of sales": "cogs",
    "cost of revenue": "cogs",
    "cogs": "cogs",
    "gross profit": "gross_profit",
    "operating income": "operating_income",
    "operating profit": "operating_income",
    "income from operations": "operating_income",
    "net income": "net_income",
    "net income (loss)": "net_income",
    "net earnings": "net_income",
    "total assets": "total_assets",
    "assets": "total_assets",
    "total liabilities": "total_liabilities",
    "liabilities": "total_liabilities",
    "total equity": "total_equity",
    "shareholders equity": "total_equity",
    "stockholders equity": "total_equity",
    "cash and cash equivalents": "cash_and_equivalents",
    "cash": "cash_and_equivalents",
    "operating cash flow": "cash_flow_ops",
    "cash flow from operations": "cash_flow_ops",
    "capital expenditures": "capex",
    "capex": "capex",
    "purchase of property and equipment": "capex",
    "free cash flow": "free_cash_flow",
}


def get_standard_line_items() -> List[str]:
    """Return the list of standard line items."""
    return list(STANDARD_LINE_ITEMS)


def _parse_number(text: str) -> Optional[float]:
    """Extract a number from text, handling commas, B/M/K suffixes."""
    # Look for dollar amounts
    match = re.search(r'\$[\s,]*([\d,]+(?:\.\d+)?)\s*([BbMmKk]?)', text)
    if match:
        num_str = match.group(1).replace(',', '')
        value = float(num_str)
        suffix = match.group(2).upper()
        if suffix == 'B':
            value *= 1_000_000_000
        elif suffix == 'M':
            value *= 1_000_000
        elif suffix == 'K':
            value *= 1_000
        return value
    return None


@dataclass
class NormalizedCompany:
    """Normalized financial data for a company."""
    ticker: str
    cik: str
    accession_no: str
    filing_date: str
    items: Dict[str, float] = field(default_factory=dict)
    normalized: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "accession_no": self.accession_no,
            "filing_date": self.filing_date,
            "items": self.items,
            "normalized": self.normalized,
        }


def normalize_items(
    ticker: str,
    cik: str,
    accession_no: str,
    filing_date: str,
    text_parts: List[str],
) -> NormalizedCompany:
    """Normalize text parts into standard line items."""
    result = NormalizedCompany(
        ticker=ticker,
        cik=cik,
        accession_no=accession_no,
        filing_date=filing_date,
    )

    if not text_parts:
        return result

    # Combine all text
    full_text = "\n".join(text_parts)

    # Extract line items
    for line in full_text.split("\n"):
        line_lower = line.lower().strip()
        for alias, standard in ALIAS_MAP.items():
            if alias in line_lower:
                value = _parse_number(line)
                if value is not None:
                    result.items[standard] = value
                break

    # Normalize values (divide by revenue if available)
    if result.items.get("revenue", 0) > 0:
        for key, value in result.items.items():
            result.normalized[key] = value / result.items["revenue"]
    else:
        # Use total_assets as fallback normalizer
        if result.items.get("total_assets", 0) > 0:
            for key, value in result.items.items():
                result.normalized[key] = value / result.items["total_assets"]
        else:
            result.normalized = dict(result.items)

    return result


def normalize_multiple(
    companies: List[NormalizedCompany],
) -> List[NormalizedCompany]:
    """Normalize multiple companies using a global normalizer."""
    if not companies:
        return []

    # Find the global normalizer (use total_assets if available, else revenue)
    global_normalizer = None
    for comp in companies:
        if comp.items.get("total_assets", 0) > 0:
            global_normalizer = "total_assets"
            break
        elif comp.items.get("revenue", 0) > 0:
            global_normalizer = "revenue"
            break

    if global_normalizer is None:
        # No normalizer available, just return as-is
        return companies

    # Apply global normalization
    for comp in companies:
        norm_value = comp.items.get(global_normalizer, 0)
        if norm_value > 0:
            comp.normalized = {
                key: value / norm_value
                for key, value in comp.items.items()
            }
        else:
            comp.normalized = dict(comp.items)

    return companies
