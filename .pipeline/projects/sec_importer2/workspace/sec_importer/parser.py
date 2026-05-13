"""Metadata parser for SEC filing JSON responses."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Known filing type codes
FILING_TYPES = {
    "10-K": "Annual report",
    "10-Q": "Quarterly report",
    "8-K": "Current report",
    "S-1": "Registration statement (IPO)",
    "DEF 14A": "Definitive proxy statement",
    "SC 13G": "Schedule 13G (beneficial ownership)",
    "SC 13D": "Schedule 13D (beneficial ownership)",
    "4": "Statement of changes in beneficial ownership",
    "5": "Annual statement of beneficial ownership",
    "20-F": "Annual report for foreign private issuers",
    "40-F": "Registration statement for foreign private issuers",
    "N-1A": "Investment company registration statement",
    "N-CSR": "Certified annual/semi-annual shareholder report",
    "11-K": "Annual/quarterly report of employee stock purchase plan",
    "PRD": "Periodic report",
    "NT 10-K": "Notice of late 10-K filing",
    "NT 10-Q": "Notice of late 10-Q filing",
    "SC TO-I": "Tender offer investment statement",
    "SC 13E3": "Going private transaction",
}


def parse_filings(raw_json_list: list[dict[str, Any]], ticker: Optional[str] = None) -> list[dict[str, Any]]:
    """Parse raw SEC JSON responses into structured metadata dicts.

    Each item in raw_json_list should be a dict with keys like:
    accessionNumber, form, filingDate, primaryDocument, etc.

    Args:
        raw_json_list: List of raw JSON dicts from the SEC API.
        ticker: Fallback ticker symbol to use when the raw data
                doesn't include a ticker (SEC company filings endpoint
                returns parallel arrays, not per-record tickers).

    Returns:
        List of parsed metadata dicts with keys:
        ticker, filing_type, filing_date, accession_number, document_url,
        form_description, accepted_date, fill_url, raw_json.
    """
    parsed = []
    for i, raw in enumerate(raw_json_list):
        try:
            record = _parse_single_filing(raw, ticker=ticker)
            if record and _is_valid_record(record):
                record["raw_json"] = raw  # Include raw JSON for storage
                parsed.append(record)
            else:
                logger.warning(f"Skipping invalid filing record at index {i}")
        except Exception as e:
            logger.warning(f"Error parsing filing record at index {i}: {e}")
    return parsed


def _parse_single_filing(raw: dict[str, Any], ticker: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Parse a single filing record from raw JSON.

    Handles the company filings endpoint format where each item in recent
    is a dict with keys like: accessionNumber, form, filingDate, etc.

    Args:
        raw: Raw filing dict from the SEC API.
        ticker: Fallback ticker symbol if not present in raw data.
    """
    # Extract accession number (normalize to remove dashes)
    accession = raw.get("accessionNumber") or raw.get("accession_number") or ""
    accession = str(accession).replace("-", "")

    # Extract filing type
    filing_type = raw.get("form") or raw.get("type") or ""
    filing_type = str(filing_type).strip()

    # Extract filing date
    filing_date = raw.get("filingDate") or raw.get("filedAsOfDate") or ""
    filing_date = str(filing_date).strip()

    # Extract accepted date
    accepted_date = raw.get("acceptanceDateTime") or raw.get("acceptedDate") or ""
    accepted_date = str(accepted_date).strip()

    # Extract document URL
    document_url = raw.get("primaryDocument") or raw.get("primary_doc") or ""
    if document_url and not document_url.startswith("http"):
        # Build URL from accession number and document name
        accession_with_dashes = _format_accession(accession)
        document_url = f"https://www.sec.gov/Archives/edgar/data/" \
                       f"{_get_edgar_path(accession)}/{document_url}"

    # Extract form description
    form_description = raw.get("primaryDocDescription") or raw.get("documentDescription") or raw.get("formDescription") or ""
    form_description = str(form_description).strip()

    # Get ticker: prefer raw data, fall back to passed ticker parameter
    raw_ticker = raw.get("ticker") or raw.get("companyName") or ""
    resolved_ticker = raw_ticker or ticker or ""

    # Extract fill_url (full submission URL) if available
    fill_url = raw.get("fullSubmission") or raw.get("fullSubmissionUrl") or None

    return {
        "ticker": resolved_ticker,
        "filing_type": filing_type,
        "filing_date": filing_date,
        "accession_number": accession,
        "document_url": document_url,
        "form_description": form_description,
        "accepted_date": accepted_date,
        "fill_url": fill_url,
    }


def _format_accession(accession: str) -> str:
    """Format accession number with dashes for SEC URLs.

    Format: XX XXXXXX-XX-XXXXXX -> XX XXXXXX-XX-XXXXXX
    """
    if len(accession) < 18:
        return accession
    return f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"


def _get_edgar_path(accession: str) -> str:
    """Get the EDGAR data path from an accession number.

    The path is derived from the CIK (first 10 digits of accession).
    """
    if len(accession) < 10:
        return "0000000000"
    cik = accession[:10]
    # EDGAR paths use the CIK zero-padded to 10 digits
    return str(int(cik)).zfill(10)


def _is_valid_record(record: dict[str, Any]) -> bool:
    """Check if a parsed record has the minimum required fields."""
    return bool(record.get("filing_type")) and bool(record.get("filing_date"))


def get_filing_type_label(filing_type: str) -> str:
    """Get a human-readable label for a filing type code.

    Args:
        filing_type: SEC filing type code (e.g., '10-K', '8-K').

    Returns:
        Human-readable description.
    """
    return FILING_TYPES.get(filing_type, filing_type)


def parse_raw_json(raw_json: Optional[str]) -> Optional[dict]:
    """Parse a raw JSON string into a dict, handling errors gracefully."""
    if not raw_json:
        return None
    try:
        return json.loads(raw_json)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse raw JSON: {e}")
        return None
