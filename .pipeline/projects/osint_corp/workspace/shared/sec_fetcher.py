"""SEC EDGAR API client — fetches filing data from EDGAR's public API."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

EDGAR_FILING_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_INDEX_URL = "https://www.sec.gov/Archives/edgar/full-index/{ticker}/master.idx"


class SECFetcher:
    """Fetches filing data from SEC EDGAR's public API."""

    def __init__(self, user_agent: str = "osint-corp/0.1.0"):
        self.user_agent = user_agent
        self._client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=30.0,
        )

    def _get(self, url: str) -> dict[str, Any]:
        """Make a GET request and return JSON response."""
        try:
            response = self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise SECFetchError(f"Failed to fetch {url}: {e}") from e
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise SECFetchError(f"Unexpected error fetching {url}: {e}") from e

    def get_cik_by_ticker(self, ticker: str) -> Optional[str]:
        """Look up a CIK number by ticker symbol using SEC's CIK lookup API."""
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=include&count=1&search_text=&action=company"
        try:
            response = self._client.get(
                "https://efts.sec.gov/LATEST/search-index",
                params={"tickers": ticker},
                timeout=15.0,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("tickers") and len(data["tickers"]) > 0:
                    return data["tickers"][0].get("cik")
        except Exception as e:
            logger.warning(f"CIK lookup by ticker failed: {e}")
        return None

    def get_filings(
        self,
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        filing_types: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch filing data from EDGAR.

        Args:
            ticker: Company ticker symbol.
            cik: SEC Central Index Key.
            filing_types: List of filing types to filter (e.g., ['10-K', '10-Q']).
            limit: Maximum number of filings to return.

        Returns:
            List of raw filing dicts from EDGAR API.
        """
        if not ticker and not cik:
            raise ValueError("Either ticker or cik must be provided.")

        # Resolve CIK if only ticker provided
        target_cik = cik
        if ticker and not cik:
            target_cik = self.get_cik_by_ticker(ticker)
            if not target_cik:
                logger.warning(f"Could not resolve CIK for ticker {ticker}")
                return []

        # Pad CIK to 10 digits
        padded_cik = target_cik.zfill(10)
        url = EDGAR_FILING_URL.format(cik=padded_cik)

        data = self._get(url)

        filings = data.get("filings", {}).get("recent", [])
        if not filings:
            logger.warning(f"No filings found for CIK {padded_cik}")
            return []

        # Parse and filter filings
        result = []
        for acc_num in filings.get("accessionNumber", []):
            # Clean accession number (remove dashes)
            clean_acc = acc_num.replace("-", "")
            filing_info = {
                "accession_number": clean_acc,
                "filing_type": filings.get("primaryDocDescription", {}).get(clean_acc, ""),
                "filing_date": filings.get("filingDate", {}).get(clean_acc, ""),
                "company_name": data.get("companyName", "Unknown"),
                "cik": target_cik,
                "ticker": ticker,
                "document_url": f"https://www.sec.gov/Archives/edgar/data/{padded_cik}/{clean_acc}/{clean_acc}.htm",
                "accepted_date": filings.get("acceptanceDateTime", {}).get(clean_acc, ""),
            }

            # Filter by filing type if specified
            if filing_types:
                primary_type = filing_info["filing_type"]
                if primary_type not in filing_types:
                    continue

            result.append(filing_info)

            if len(result) >= limit:
                break

        return result

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class SECFetchError(Exception):
    """Exception raised when SEC API fetch fails."""
    pass
