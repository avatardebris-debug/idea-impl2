"""Financial line-item normalization for forensic analysis.

Normalizes financial data across companies so that line items are
comparable on a common scale (e.g., as a fraction of revenue or
total assets).

Standard line items supported (8+):
    revenue, cogs, operating_income, gross_profit, net_income,
    total_assets, total_liabilities, cash_flow_ops, capex,
    working_capital, ebitda, depreciation_amortization
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NormalizedItem:
    """A single financial line item after normalization."""
    ticker: str
    accession_no: str
    filing_date: str
    line_item: str          # canonical name, e.g. "revenue"
    raw_value: float
    normalized_value: float
    normalizer: str         # e.g. "revenue", "total_assets", "none"


@dataclass
class NormalizedCompany:
    """All normalized line items for one company."""
    ticker: str
    cik: str
    accession_no: str
    filing_date: str
    items: Dict[str, float] = field(default_factory=dict)  # line_item -> raw_value
    normalized: Dict[str, float] = field(default_factory=dict)  # line_item -> norm_value

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "accession_no": self.accession_no,
            "filing_date": self.filing_date,
            "items": self.items,
            "normalized": self.normalized,
        }


# ---------------------------------------------------------------------------
# Canonical line-item names
# ---------------------------------------------------------------------------

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
    "free_cash_flow",
    "capex",
    "working_capital",
    "ebitda",
    "depreciation_amortization",
]

# Mapping from common filing-text aliases to canonical names
ALIAS_MAP: Dict[str, str] = {
    # revenue
    "revenue": "revenue",
    "total_revenue": "revenue",
    "net_revenue": "revenue",
    "sales": "revenue",
    "total_sales": "revenue",
    "gross_sales": "revenue",
    # cogs
    "cogs": "cogs",
    "cost_of_goods_sold": "cogs",
    "cost_of_revenue": "cogs",
    "cost_of_sales": "cogs",
    # gross_profit
    "gross_profit": "gross_profit",
    "gross_margin": "gross_profit",
    # operating_income
    "operating_income": "operating_income",
    "operating_profit": "operating_income",
    "ebit": "operating_income",
    "income_from_operations": "operating_income",
    # net_income
    "net_income": "net_income",
    "net_profit": "net_income",
    "net_earnings": "net_income",
    "income_after_tax": "net_income",
    "profit_loss": "net_income",
    # total_assets
    "total_assets": "total_assets",
    "assets": "total_assets",
    # total_liabilities
    "total_liabilities": "total_liabilities",
    "liabilities": "total_liabilities",
    "total_debt": "total_liabilities",
    # total_equity
    "total_equity": "total_equity",
    "equity": "total_equity",
    "shareholders_equity": "total_equity",
    "stockholders_equity": "total_equity",
    # cash_and_equivalents
    "cash_and_equivalents": "cash_and_equivalents",
    "cash": "cash_and_equivalents",
    "cash_and_cash_equivalents": "cash_and_equivalents",
    # free_cash_flow
    "free_cash_flow": "free_cash_flow",
    "free_cash_flow_from_operations": "free_cash_flow",
    # cash_flow_ops
    "cash_flow_ops": "cash_flow_ops",
    "cash_flow_from_operations": "cash_flow_ops",
    "operating_cash_flow": "cash_flow_ops",
    "cash_from_operating_activities": "cash_flow_ops",
    # capex
    "capex": "capex",
    "capital_expenditures": "capex",
    "capital_expenditure": "capex",
    "ppe": "capex",
    # working_capital
    "working_capital": "working_capital",
    "net_working_capital": "working_capital",
    # ebitda
    "ebitda": "ebitda",
    "ebitda_adjusted": "ebitda",
    # depreciation_amortization
    "depreciation_amortization": "depreciation_amortization",
    "depreciation": "depreciation_amortization",
    "amortization": "depreciation_amortization",
    "depreciation_and_amortization": "depreciation_amortization",
}


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_value(text: str, key: str) -> Optional[float]:
    """Try to extract a dollar value for *key* from *text*.

    Looks for patterns like:
        "Revenue  $1,234,567"
        "Revenue of $1.23B"
        "Revenue: $1.23M"

    Underscores in the key are treated as matching either underscores or
    whitespace in the text, so that aliases like ``cost_of_goods_sold``
    match ``Cost of goods sold`` in filing text.
    """
    if not text:
        return None

    # Replace underscores with a pattern that matches underscore or whitespace
    # so that "cost_of_goods_sold" matches "Cost of goods sold"
    # We replace underscores BEFORE escaping to handle them specially
    # First, split on underscores and rejoin with the space-matching pattern
    parts = key.split("_")
    escaped_parts = [re.escape(part) for part in parts]
    escaped_key = r"[\s_]+".join(escaped_parts)
    patterns = [
        # "key  $1,234,567"
        rf"{escaped_key}\s+\$?([\d,]+(?:\.\d+)?)",
        # "key of $1.23B / $1.23M / $1.23K"
        rf"{escaped_key}\s+of\s+\$?([\d,]+(?:\.\d+)?)\s*(B|M|K|b|m|k)?",
        # "key: $1,234,567"
        rf"{escaped_key}\s*:\s*\$?([\d,]+(?:\.\d+)?)",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(",", "")
            multiplier = 1.0
            suffix = m.group(2) if m.lastindex and m.lastindex >= 2 else None
            if suffix:
                suffix = suffix.lower()
                if suffix in ("b", "bb"):
                    multiplier = 1e9
                elif suffix in ("m", "mm"):
                    multiplier = 1e6
                elif suffix in ("k", "kk"):
                    multiplier = 1e3
            return float(raw) * multiplier

    return None


# ---------------------------------------------------------------------------
# Core normalization logic
# ---------------------------------------------------------------------------

def normalize_items(
    ticker: str,
    cik: str,
    accession_no: str,
    filing_date: str,
    text_parts: List[str],
) -> NormalizedCompany:
    """Normalize financial line items from filing text.

    Parameters
    ----------
    ticker : str
        Company ticker symbol.
    cik : str
        CIK identifier.
    accession_no : str
        SEC accession number.
    filing_date : str
        Filing date string.
    text_parts : list[str]
        Concatenated text from filing items (e.g. item_content fields).

    Returns
    -------
    NormalizedCompany
        Contains both raw and normalized values for each standard line item.
    """
    combined = "\n".join(text_parts)
    combined_lower = combined.lower()

    raw: Dict[str, float] = {}

    for canonical in STANDARD_LINE_ITEMS:
        # Find all aliases for this canonical name
        aliases = [k for k, v in ALIAS_MAP.items() if v == canonical]
        value = None
        for alias in aliases:
            value = _extract_value(combined, alias)
            if value is not None:
                break
        if value is not None:
            raw[canonical] = value

    # Determine normalizer: prefer "revenue" if available, else "total_assets"
    normalizer_name: Optional[str] = None
    if "revenue" in raw and raw["revenue"] != 0:
        normalizer_name = "revenue"
    elif "total_assets" in raw and raw["total_assets"] != 0:
        normalizer_name = "total_assets"

    normalized: Dict[str, float] = {}
    for line_item, val in raw.items():
        if normalizer_name and normalizer_name in raw and raw[normalizer_name] != 0:
            normalized[line_item] = val / raw[normalizer_name]
        else:
            normalized[line_item] = val  # no normalization possible

    return NormalizedCompany(
        ticker=ticker,
        cik=cik,
        accession_no=accession_no,
        filing_date=filing_date,
        items=raw,
        normalized=normalized,
    )


def normalize_multiple(
    companies: List[NormalizedCompany],
) -> List[NormalizedCompany]:
    """Ensure all companies share the same normalizer (revenue if available).

    Re-normalizes every company using the same base (revenue > total_assets).
    """
    # Pick a global normalizer: revenue if any company has it
    global_normalizer: Optional[str] = None
    for comp in companies:
        if "revenue" in comp.items and comp.items["revenue"] != 0:
            global_normalizer = "revenue"
            break
    if global_normalizer is None:
        for comp in companies:
            if "total_assets" in comp.items and comp.items["total_assets"] != 0:
                global_normalizer = "total_assets"
                break

    if global_normalizer is None:
        return companies  # nothing to normalize

    for comp in companies:
        base = comp.items.get(global_normalizer, 0)
        if base == 0:
            continue
        for key in comp.items:
            comp.normalized[key] = comp.items[key] / base

    return companies


# ---------------------------------------------------------------------------
# Convenience / export
# ---------------------------------------------------------------------------

def get_standard_line_items() -> List[str]:
    """Return the list of supported standard line-item names."""
    return list(STANDARD_LINE_ITEMS)
