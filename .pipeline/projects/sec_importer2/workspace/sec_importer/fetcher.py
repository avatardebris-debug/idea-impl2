"""SEC EDGAR JSON API fetcher with rate limiting and retry logic."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# SEC EDGAR endpoints
COMPANY_FILINGS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
TICKER_TO_CIK_URL = "https://data.sec.gov/submissions/CIK{ticker}.json"

# Default SEC User-Agent per EDGAR requirements
DEFAULT_USER_AGENT = "SECImporter/0.1.0 (contact: sec-importer@example.com)"


class SECFetcher:
    """HTTP client for querying SEC EDGAR APIs with rate limiting and retry."""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        base_delay: float = 1.0,
        max_retries: int = 5,
        request_delay: float = 0.1,
        timeout: int = 60,
    ):
        """Initialize the SEC fetcher.

        Args:
            user_agent: User-Agent header for SEC EDGAR compliance.
            base_delay: Base delay in seconds for exponential backoff.
            max_retries: Maximum number of retry attempts.
            request_delay: Fixed delay between requests (seconds).
            timeout: Request timeout in seconds.
        """
        self.user_agent = user_agent
        self.base_delay = base_delay
        self.max_retries = max_retries
        self.request_delay = request_delay
        self.timeout = timeout
        self._session = httpx.Client(
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
            timeout=self.timeout,
        )
        # Cache for the last company name lookup
        self._last_company_name: Optional[str] = None

    def fetch_filings(self, ticker: Optional[str] = None,
                      cik: Optional[str] = None,
                      limit: int = 100) -> list[dict[str, Any]]:
        """Fetch latest filings for a company.

        Uses the company filings endpoint (CIK-based) as the primary source.

        Args:
            ticker: Company ticker symbol (e.g., 'AAPL'). Will be used to
                    look up the CIK first.
            cik: SEC Central Index Key (CIK). If provided, uses the company
                 filings endpoint directly.
            limit: Maximum number of filings to return.

        Returns:
            List of raw filing dicts from the SEC API.
        """
        # If we have a ticker but no CIK, look up the CIK first
        if ticker and not cik:
            cik = self.get_cik_from_ticker(ticker)
            if not cik:
                logger.warning(f"Could not find CIK for ticker {ticker}")
                return []

        if cik:
            return self._fetch_by_cik(cik, limit)

        raise ValueError("Either ticker or cik must be provided")

    def _fetch_by_cik(self, cik: str, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch filings using the CIK-based company filings endpoint.

        The SEC API returns 'recent' as a dict with parallel arrays:
        {
            "accessionNumber": ["...", "..."],
            "filingDate": ["2026-05-06", "2026-05-05"],
            "form": ["10-K", "10-Q"],
            ...
        }

        We convert this to a list of dicts for easier consumption.
        """
        # Normalize CIK to 10-digit string
        cik_str = str(cik).zfill(10)
        url = COMPANY_FILINGS_URL.format(cik=cik_str)
        logger.info(f"Fetching filings for CIK {cik_str} from {url}")

        response = self._request_with_retry("GET", url)
        data = response.json()

        # SEC company filings endpoint returns:
        # { "filings": { "recent": { "accessionNumber": [...], "filingDate": [...], ... } }, "ticker": "...", ... }
        recent = data.get("filings", {}).get("recent", {})

        if not recent:
            logger.info(f"No filings returned for CIK {cik_str}")
            return []

        # Convert parallel arrays to list of dicts
        filings = self._parallel_arrays_to_dicts(recent, limit)
        logger.info(f"Retrieved {len(filings)} filings for CIK {cik_str}")
        return filings

    def _parallel_arrays_to_dicts(self, recent: dict, limit: int) -> list[dict[str, Any]]:
        """Convert parallel arrays to list of dicts.

        Args:
            recent: Dict with parallel arrays from SEC API.
            limit: Maximum number of filings to return.

        Returns:
            List of dicts, one per filing.
        """
        if not recent:
            return []

        # Get the keys (field names) and the first array to determine length
        keys = list(recent.keys())
        if not keys:
            return []

        # Get the length from the first array
        first_array = recent[keys[0]]
        if not isinstance(first_array, (list, tuple)):
            return []

        n = min(len(first_array), limit)
        if n == 0:
            return []

        result = []
        for i in range(n):
            filing = {}
            for key in keys:
                val = recent[key]
                if isinstance(val, (list, tuple)) and i < len(val):
                    filing[key] = val[i]
                else:
                    filing[key] = val
            result.append(filing)

        return result

    def _request_with_retry(self, method: str, url: str) -> httpx.Response:
        """Make an HTTP request with exponential backoff retry logic.

        Args:
            method: HTTP method.
            url: Request URL.

        Returns:
            httpx.Response on success.

        Raises:
            httpx.HTTPError: If all retries are exhausted.
        """
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._session.request(method, url)

                # Handle 429 Too Many Requests with exponential backoff
                if response.status_code == 429:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"Rate limited (429) on attempt {attempt + 1}/{self.max_retries + 1}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    continue

                # Handle other HTTP errors
                if response.status_code >= 400:
                    logger.error(
                        f"HTTP {response.status_code} for {url}: {response.text[:200]}"
                    )
                    response.raise_for_status()

                return response

            except httpx.HTTPError as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"HTTP error on attempt {attempt + 1}/{self.max_retries + 1}: {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} retries exhausted for {url}")

        raise last_exception  # type: ignore[misc]

    def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Look up the CIK for a given ticker using the SEC submissions endpoint.

        The SEC provides a direct mapping: https://data.sec.gov/submissions/CIK{TICKER}.json
        This returns a JSON with the CIK and company name.

        Args:
            ticker: Company ticker symbol.

        Returns:
            CIK string (zero-padded) or None if not found.
        """
        ticker_upper = str(ticker).upper()
        url = TICKER_TO_CIK_URL.format(ticker=ticker_upper)
        logger.info(f"Looking up CIK for ticker {ticker_upper} from {url}")

        try:
            response = self._request_with_retry("GET", url)
            data = response.json()
            cik = data.get("cik")
            # Also cache the company name for use by sync.py
            self._last_company_name = data.get("companyName")
            if cik:
                # CIK might be returned as int or string
                cik_str = str(cik).zfill(10)
                logger.info(f"Found CIK {cik_str} for ticker {ticker_upper}")
                return cik_str
            else:
                logger.warning(f"No CIK found for ticker {ticker_upper}")
                return None
        except Exception as e:
            logger.warning(f"Could not look up CIK for {ticker_upper}: {e}")
            return None

    def close(self):
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
