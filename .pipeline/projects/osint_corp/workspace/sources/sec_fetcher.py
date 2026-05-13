"""SEC EDGAR API client."""

from __future__ import annotations

import time
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Optional


class SECFetcher:
    """HTTP client for the SEC EDGAR Full-Text Search API."""

    BASE_URL = "https://efts.sec.gov/LATEST/search-index"

    def __init__(self, user_agent: str = "osint-corp/0.1.0"):
        self.user_agent = user_agent

    def _build_url(self, params: dict[str, str]) -> str:
        query = urllib.parse.urlencode(params)
        return f"{self.BASE_URL}?{query}"

    def _request(self, params: dict[str, str]) -> dict:
        url = self._build_url(params)
        req = urllib.request.Request(url)
        req.add_header("User-Agent", self.user_agent)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"SEC API HTTP error {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"SEC API network error: {e.reason}") from e

    def search_filings(
        self,
        ticker: Optional[str] = None,
        company_name: Optional[str] = None,
        filing_types: Optional[list[str]] = None,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Search SEC filings via the EDGAR Full-Text Search API.

        Returns the raw JSON response from the SEC API.
        """
        params: dict[str, str] = {
            "format": "json",
            "limit": str(limit),
        }
        if ticker:
            params["ticker"] = ticker
        if company_name:
            params["companyName"] = company_name
        if filing_types:
            params["filingTypes"] = ",".join(filing_types)
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        # EDGAR rate limit: 10 requests/second
        time.sleep(0.11)
        return self._request(params)

    def latest_filings(
        self,
        ticker: Optional[str] = None,
        company_name: Optional[str] = None,
        filing_type: str = "10-K",
        limit: int = 10,
    ) -> dict:
        """Fetch the latest filings for a ticker or company name."""
        return self.search_filings(
            ticker=ticker,
            company_name=company_name,
            filing_types=[filing_type],
            limit=limit,
        )
