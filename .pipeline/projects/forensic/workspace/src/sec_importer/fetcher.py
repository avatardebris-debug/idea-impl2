"""sec_importer fetcher stub for the forensic suite."""

from __future__ import annotations

from typing import Optional, Dict, Any


def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """Resolve a stock ticker to a CIK number.
    
    Stub — returns None. Real implementation lives in sec_importer.
    """
    return None


def get_latest_filing(cik: str, filing_type: str = "10-K") -> Optional[Dict[str, Any]]:
    """Get the latest filing metadata for a CIK.
    
    Stub — returns None. Real implementation lives in sec_importer.
    """
    return None


def download_filing_text(accession_no: str, cik: str) -> Optional[str]:
    """Download the full text of a filing.
    
    Stub — returns None. Real implementation lives in sec_importer.
    """
    return None


def get_company_info(cik: str) -> Optional[Dict[str, str]]:
    """Get company information for a CIK.
    
    Stub — returns None. Real implementation lives in sec_importer.
    """
    return None
