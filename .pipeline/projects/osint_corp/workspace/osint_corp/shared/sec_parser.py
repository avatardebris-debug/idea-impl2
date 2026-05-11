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
    "N-CSR": "Certified shareholder report",
    "N-Q": "Quarterly portfolio report",
    "1-A": "Regulation A offering statement",
    "1-U": "Regulation A offering statement (pre-effective)",
    "1-E": "Regulation A reporting",
    "D": "Notice of exempt offering",
    "F-1": "Registration statement for foreign private issuers",
    "F-3": "Registration statement for foreign private issuers",
    "F-4": "Registration statement for business combinations",
    "F-8": "Registration statement for employee stock purchase plan",
    "F-9": "Registration statement for American depositary shares",
    "S-3": "Registration statement for well-known seasoned issuers",
    "S-4": "Registration statement for business combinations",
    "S-8": "Registration statement for employee benefit plans",
    "PRE 14A": "Preliminary proxy statement",
    "DEFA14A": "Additional proxy materials",
    "DEFC14A": "Definitive proxy statement (additional)",
    "DEFM14A": "Definitive proxy statement (merger)",
    "DEFR14A": "Definitive proxy statement (revision)",
    "8-A12B": "Registration of securities (section 12(b))",
    "8-A12G": "Registration of securities (section 12(g))",
    "15-12B": "Suspension of reporting obligation (section 12(b))",
    "15-12G": "Suspension of reporting obligation (section 12(g))",
    "15F-12B": "Suspension of reporting obligation (section 12(b)) - foreign",
    "15F-12G": "Suspension of reporting obligation (section 12(g)) - foreign",
    "AW": "Withdrawal of registration statement",
    "CORR": "Correspondence",
    "FWP": "Free writing prospectus",
    "G-405": "Government securities filing",
    "N-14": "Registration statement for business combination",
    "N-23C": "Closed-end management company filing",
    "N-30B-2": "Periodic report for registered management investment companies",
    "N-30D": "Statement of additional information",
    "N-CEN": "Annual report for registered management investment companies",
    "N-PX": "Annual report of proxy voting record",
    "N-RFP": "Request for proposals",
    "N-RS": "Annual report for registered management investment companies",
    "N-CSR": "Certified shareholder report",
    "N-Q": "Quarterly portfolio report",
    "POS AM": "Post-effective amendment",
    "POS EX": "Pricing supplement",
    "POS I": "Post-effective amendment (initial)",
    "PRE 14C": "Preliminary information statement",
    "DEFA14C": "Additional information statement materials",
    "DEF 14C": "Definitive information statement",
    "SC 13E1": "Issuer tender offer filing",
    "SC 13E3": "Issuer statement regarding purchase of securities",
    "SC 14D1": "Tender offer statement",
    "SC 14F1": "Issuer statement regarding disposal of business",
    "SC 14N": "Tender offer statement",
    "SC TO-C": "Tender offer statement (common stock)",
    "SC XR": "Withdrawal of filing",
    "S-3ASR": "Automatic shelf registration statement",
    "S-8ASR": "Automatic shelf registration for employee plans",
    "SB-2": "Registration statement for small business issuers",
    "UPLOAD": "Upload document",
    "X-17A-5": "Annual report for brokers/dealers",
}


def _get_filing_description(filing_type: str) -> str:
    """Get a human-readable description for a filing type."""
    return FILING_TYPES.get(filing_type, f"Unknown filing type: {filing_type}")


def parse_filings(raw_filings: list[dict[str, Any]]) -> list:
    """Parse raw EDGAR filing data into Filing model instances.

    Args:
        raw_filings: List of raw filing dicts from SECFetcher.

    Returns:
        List of Filing model instances.
    """
    from osint_corp.models.entities import Filing

    filings = []
    for raw in raw_filings:
        filing_type = raw.get("filing_type", "Unknown")
        description = _get_filing_description(filing_type)

        filing = Filing(
            accession_number=raw.get("accession_number", ""),
            filing_type=filing_type,
            filing_date=raw.get("filing_date", ""),
            company_name=raw.get("company_name", "Unknown"),
            ticker=raw.get("ticker"),
            cik=raw.get("cik"),
            document_url=raw.get("document_url"),
            accepted_date=raw.get("accepted_date"),
            form_description=description,
            financials={},
            material_events=[],
            primary_document=None,
            source="sec_edgar",
            metadata={
                "raw_filing": raw,
                "description": description,
            },
        )
        filings.append(filing)

    return filings


def parse_filing_json(json_str: str) -> list:
    """Parse a JSON string containing EDGAR filing data.

    Args:
        json_str: JSON string from EDGAR API.

    Returns:
        List of Filing model instances.
    """
    data = json.loads(json_str)
    filings_data = data.get("filings", {}).get("recent", {})
    if not filings_data:
        return []

    # Build raw filings list
    raw_filings = []
    accession_numbers = filings_data.get("accessionNumber", [])
    for acc_num in accession_numbers:
        clean_acc = acc_num.replace("-", "")
        raw_filings.append({
            "accession_number": clean_acc,
            "filing_type": filings_data.get("primaryDocDescription", {}).get(clean_acc, ""),
            "filing_date": filings_data.get("filingDate", {}).get(clean_acc, ""),
            "company_name": data.get("companyName", "Unknown"),
            "cik": data.get("cik"),
            "document_url": f"https://www.sec.gov/Archives/edgar/data/{data.get('cik', '').zfill(10)}/{clean_acc}/{clean_acc}.htm",
            "accepted_date": filings_data.get("acceptanceDateTime", {}).get(clean_acc, ""),
        })

    return parse_filings(raw_filings)
