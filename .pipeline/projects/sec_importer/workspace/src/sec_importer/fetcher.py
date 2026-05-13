"""Fetcher module for SEC EDGAR data.

Provides functions to:
- Resolve a ticker symbol to a CIK number
- Retrieve the filing index for a CIK
- Download the latest filing of a given type
- Download the full-text content of a filing
"""

import time
import logging
import requests
from typing import Optional

from sec_importer.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# SEC EDGAR API endpoints
CIK_LOOKUP_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=include&count=1&search_text=&action=submit"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
FULL_TEXT_URL = "https://www.sec.gov/Archives/edgar/full-text/{accession_no}.txt"
FULL_TEXT_URL_NO_DASHES = "https://www.sec.gov/Archives/edgar/full-text/{accession_no}.txt"

# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def _get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(requests_per_second=10, delay=0.1)
    return _rate_limiter


def _throttle():
    """Respect SEC EDGAR rate limits using the RateLimiter."""
    rl = _get_rate_limiter()
    rl.wait()


def _fetch_json(url: str) -> dict:
    """Fetch JSON from a URL with basic error handling."""
    _throttle()
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _fetch_text(url: str) -> str:
    """Fetch text from a URL with basic error handling."""
    _throttle()
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def resolve_ticker_to_cik(ticker: str) -> str:
    """Resolve a ticker symbol to a CIK number.

    Uses SEC's EDGAR company lookup page to find the CIK.

    Args:
        ticker: Company ticker symbol (e.g. 'AAPL').

    Returns:
        CIK string (e.g. '0000320193').

    Raises:
        ValueError: If the ticker is not found.
    """
    ticker = ticker.strip().upper()
    url = CIK_LOOKUP_URL.format(ticker=ticker)
    _throttle()
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    # Parse the HTML to find the CIK link
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")

    # The CIK is in the table results, look for the accession number link
    # which contains the CIK in the URL
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href", "")
        if "CIK=" in href:
            cik = href.split("CIK=")[1].split("&")[0]
            # SEC CIKs are zero-padded to 10 digits
            cik = cik.zfill(10)
            return cik

    raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR database")


def get_cik_submissions(cik: str) -> dict:
    """Get the filing index for a CIK from SEC's submissions JSON.

    Args:
        cik: CIK string (with or without leading zeros).

    Returns:
        Dictionary with 'filings' key containing 'recent' list of filings.
    """
    cik_str = cik.strip().lstrip("0") or "0"
    url = SUBMISSIONS_URL.format(cik=cik_str)
    return _fetch_json(url)


def get_latest_filing(cik: str, filing_type: str = "10-K") -> dict:
    """Get the latest filing of a given type for a CIK.

    Args:
        cik: CIK string.
        filing_type: Filing type (e.g. '10-K', '10-Q', '8-K').

    Returns:
        Dictionary with keys: accession_no, filing_type, filing_date, accepted_date,
        primary_document, document_url.

    Raises:
        ValueError: If no filing of the given type is found.
    """
    cik_str = cik.strip().lstrip("0") or "0"
    data = get_cik_submissions(cik)

    filings = data.get("filings", {}).get("recent", [])
    accession_numbers = filings.get("accessionNo", [])
    filing_types = filings.get("form", [])
    filing_dates = filings.get("filingDate", [])
    accepted_dates = filings.get("acceptanceDateTime", [])
    primary_docs = filings.get("primaryDoc", [])
    primary_urls = filings.get("primaryDocument", [])

    for i in range(len(accession_numbers)):
        if filing_types[i].upper() == filing_type.upper():
            accession_no = accession_numbers[i].replace("-", "")
            return {
                "accession_no": accession_no,
                "filing_type": filing_types[i],
                "filing_date": filing_dates[i],
                "accepted_date": accepted_dates[i] if accepted_dates else None,
                "primary_document": primary_docs[i] if primary_docs else None,
                "document_url": primary_urls[i] if primary_urls else None,
            }

    raise ValueError(
        f"No {filing_type} filing found for CIK {cik}"
    )


def download_filing_text(accession_no: str) -> str:
    """Download the full-text filing from SEC EDGAR.

    Args:
        accession_no: Accession number without dashes (e.g. '000032019321000099').

    Returns:
        Raw text content of the filing.
    """
    # SEC full-text URL format
    url = FULL_TEXT_URL.format(accession_no=accession_no)
    return _fetch_text(url)
