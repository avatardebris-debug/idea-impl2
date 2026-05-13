"""Correlation engine for linking companies and filings."""

from __future__ import annotations

import re
from typing import Any, Optional

from osint_corp.models.entities import Company, Filing


def _normalize(text: str) -> str:
    """Normalize a string for comparison."""
    return re.sub(r"[^a-z0-9]", "", text.lower().strip())


def _fuzzy_match(a: str, b: str, threshold: float = 0.8) -> bool:
    """Simple fuzzy match: check if one string contains the other or they share significant overlap."""
    a_norm = _normalize(a)
    b_norm = _normalize(b)
    if not a_norm or not b_norm:
        return False
    if a_norm == b_norm:
        return True
    # Check containment
    if a_norm in b_norm or b_norm in a_norm:
        return True
    # Check shared characters ratio
    if len(a_norm) == 0 or len(b_norm) == 0:
        return False
    shared = len(set(a_norm) & set(b_norm))
    union = len(set(a_norm) | set(b_norm))
    ratio = shared / union if union > 0 else 0
    return ratio >= threshold


def correlate(
    companies: list[Company],
    filings: list[Filing],
    threshold: float = 0.8,
) -> list[dict[str, Any]]:
    """Correlate companies with filings based on ticker, CIK, and name matching.

    Returns a list of relationship dicts with keys:
      - company_name
      - filing_accession
      - match_type (ticker | cik | name)
      - confidence (float)
    """
    relationships: list[dict[str, Any]] = []

    for company in companies:
        for filing in filings:
            confidence = 0.0
            match_type = ""

            # CIK match (highest confidence)
            if company.cik and filing.cik and company.cik == filing.cik:
                confidence = 1.0
                match_type = "cik"

            # Ticker match
            elif company.ticker and filing.ticker and company.ticker.upper() == filing.ticker.upper():
                confidence = 0.95
                match_type = "ticker"

            # Name fuzzy match
            elif company.name and filing.company_name:
                if _fuzzy_match(company.name, filing.company_name, threshold):
                    confidence = 0.85
                    match_type = "name"

            if confidence >= threshold:
                relationships.append({
                    "company_name": company.name,
                    "filing_accession": filing.accession_number,
                    "match_type": match_type,
                    "confidence": confidence,
                })

    return relationships


def deduplicate_companies(companies: list[Company]) -> list[Company]:
    """Remove duplicate companies based on ticker and CIK."""
    seen_tickers: set[str] = set()
    seen_ciks: set[str] = set()
    unique: list[Company] = []

    for company in companies:
        ticker_key = company.ticker.upper() if company.ticker else None
        cik_key = company.cik if company.cik else None

        if ticker_key and ticker_key in seen_tickers:
            continue
        if cik_key and cik_key in seen_ciks:
            continue

        if ticker_key:
            seen_tickers.add(ticker_key)
        if cik_key:
            seen_ciks.add(cik_key)

        unique.append(company)

    return unique


def find_companies_by_name(companies: list[Company], query: str) -> list[Company]:
    """Find companies whose name contains the query (case-insensitive)."""
    query_lower = query.lower()
    return [c for c in companies if query_lower in c.name.lower()]
