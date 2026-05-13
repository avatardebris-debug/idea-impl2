"""Data correlation engine — links entities across data sources."""

from __future__ import annotations

import logging
from difflib import SequenceMatcher
from typing import Any, Optional

from osint_corp.models.entities import Company, Filing, Manifest, Relationship

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """Normalize a company name for comparison."""
    if not name:
        return ""
    # Lowercase, strip common suffixes, remove punctuation
    name = name.lower().strip()
    for suffix in (" inc", " incorporated", " llc", " ltd", " corp", " company", " co", " llp", " lp", " plc", " gmbh", " ag", " sa", " s.a.", " b.v.", " n.v."):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    name = name.replace("-", " ").replace("_", " ")
    # Remove extra whitespace
    return " ".join(name.split())


def _name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two company names (0.0 to 1.0)."""
    n1 = _normalize_name(name1)
    n2 = _normalize_name(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return SequenceMatcher(None, n1, n2).ratio()


def correlate(
    companies: list[Company],
    filings: list[Filing],
    threshold: float = 0.7,
    relationships: Optional[list[Relationship]] = None,
) -> list[Relationship]:
    """Correlate companies and filings across data sources.

    Args:
        companies: List of Company entities from various sources.
        filings: List of Filing entities from SEC and other sources.
        threshold: Minimum similarity score for name matching (0.0 to 1.0).
        relationships: Optional pre-existing relationships.

    Returns:
        Manifest with correlated entities and inferred relationships.
    """
    if relationships is None:
        relationships = []

    # Build lookup maps
    company_by_ticker: dict[str, Company] = {}
    company_by_cik: dict[str, Company] = {}
    company_by_name: dict[str, Company] = {}

    for company in companies:
        if company.ticker:
            company_by_ticker[company.ticker.upper()] = company
        if company.cik:
            company_by_cik[company.cik] = company
        if company.name:
            company_by_name[_normalize_name(company.name)] = company

    # Correlate filings to companies
    correlated_filings: list[dict[str, Any]] = []
    for filing in filings:
        matched_company: Optional[Company] = None
        best_score = 0.0

        # Try exact ticker match
        if filing.ticker and filing.ticker.upper() in company_by_ticker:
            matched_company = company_by_ticker[filing.ticker.upper()]
            best_score = 1.0

        # Try exact CIK match
        elif filing.cik and filing.cik in company_by_cik:
            matched_company = company_by_cik[filing.cik]
            best_score = 1.0

        # Try name similarity
        elif filing.company_name:
            best_match_name: Optional[Company] = None
            best_score_name = 0.0
            for norm_name, company in company_by_name.items():
                score = _name_similarity(filing.company_name, company.name or "")
                if score > best_score_name and score > threshold:
                    best_score_name = score
                    best_match_name = company

            if best_match_name:
                matched_company = best_match_name
                best_score = best_score_name

        correlated_filings.append({
            "filing": filing,
            "matched_company": matched_company,
            "confidence": best_score if (matched_company and best_score > threshold) else 0.0,
        })

        # If we found a match, add a relationship
        if matched_company and filing.ticker:
            rel = Relationship(
                source_type="Filing",
                source_id=filing.accession_number,
                target_type="Company",
                target_id=matched_company.ticker or matched_company.name or "",
                relationship_type="filed_by",
                confidence=best_score if best_score > threshold else 0.5,
                evidence=[f"Name similarity: {_name_similarity(filing.company_name or '', matched_company.name or ''):.2f}"],
                metadata={"filing_type": filing.filing_type, "filing_date": filing.filing_date},
            )
            relationships.append(rel)

    # Infer relationships between companies based on shared filings
    inferred_relationships: list[Relationship] = []
    company_filings: dict[str, list[Filing]] = {}

    for cf in correlated_filings:
        if cf["matched_company"] and cf["matched_company"].ticker:
            ticker = cf["matched_company"].ticker
            if ticker not in company_filings:
                company_filings[ticker] = []
            company_filings[ticker].append(cf["filing"])

    # Companies that filed in the same period may be related
    ticker_list = list(company_filings.keys())
    for i in range(len(ticker_list)):
        for j in range(i + 1, len(ticker_list)):
            t1, t2 = ticker_list[i], ticker_list[j]
            # Check for overlapping filing dates
            dates1 = {f.filing_date for f in company_filings[t1] if f.filing_date}
            dates2 = {f.filing_date for f in company_filings[t2] if f.filing_date}
            overlap = dates1 & dates2

            if overlap:
                rel = Relationship(
                    source_type="Company",
                    source_id=t1,
                    target_type="Company",
                    target_id=t2,
                    relationship_type="co_filer",
                    confidence=0.3,
                    evidence=[f"Both filed on: {', '.join(list(overlap)[:3])}"],
                    metadata={"shared_filing_dates": list(overlap)[:5]},
                )
                inferred_relationships.append(rel)

    all_relationships = relationships + inferred_relationships

    logger.info(f"Correlation complete: {len(companies)} companies, {len(filings)} filings, {len(all_relationships)} relationships")
    return all_relationships


def find_companies_by_name(
    companies: list[Company],
    name: str,
    threshold: float = 0.5,
) -> list[Company]:
    """Find companies matching a name with similarity score.

    Args:
        companies: List of companies to search.
        name: Name to search for.
        threshold: Minimum similarity score (0.0 to 1.0).

    Returns:
        List of Company objects sorted by score descending.
    """
    results = []
    norm_target = _normalize_name(name)

    for company in companies:
        score = _name_similarity(name, company.name or "")
        if score >= threshold:
            results.append(company)

    results.sort(key=lambda c: _name_similarity(name, c.name or ""), reverse=True)
    return results


def deduplicate_companies(companies: list[Company]) -> list[Company]:
    """Deduplicate a list of companies by name/ticker/cik.

    Args:
        companies: List of Company entities.

    Returns:
        Deduplicated list of Company entities.
    """
    seen_tickers: set[str] = set()
    seen_ciks: set[str] = set()
    seen_names: set[str] = set()
    unique: list[Company] = []

    for company in companies:
        # Skip if we've seen this ticker
        if company.ticker and company.ticker.upper() in seen_tickers:
            continue
        # Skip if we've seen this CIK
        if company.cik and company.cik in seen_ciks:
            continue
        # Skip if we've seen this name
        norm_name = _normalize_name(company.name or "")
        if norm_name and norm_name in seen_names:
            continue

        seen_tickers.add(company.ticker.upper()) if company.ticker else None
        seen_ciks.add(company.cik) if company.cik else None
        seen_names.add(norm_name) if norm_name else None

        unique.append(company)

    logger.info(f"Deduplicated {len(companies)} companies to {len(unique)}")
    return unique
