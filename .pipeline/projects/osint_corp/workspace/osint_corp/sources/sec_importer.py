"""SEC filing importer — fetches and parses EDGAR filings."""

from __future__ import annotations

import logging
from typing import Any, Optional

from osint_corp.models.entities import Filing
from osint_corp.shared.sec_fetcher import SECFetcher
from osint_corp.shared.sec_parser import parse_filings as _parse_filings

logger = logging.getLogger(__name__)


class SECImporter:
    """Fetches and parses SEC EDGAR filings for a given company."""

    def __init__(self, user_agent: str = "osint-corp/0.1.0"):
        self._fetcher = SECFetcher(user_agent=user_agent)

    def fetch_filings(
        self,
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        filing_types: Optional[list[str]] = None,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> list[Filing]:
        """Fetch filings for a company by ticker or CIK.

        Args:
            ticker: Company ticker symbol (e.g., 'AAPL').
            cik: SEC Central Index Key (e.g., '0000320193').
            filing_types: List of filing types to fetch (e.g., ['10-K', '10-Q', '8-K']).
            limit: Maximum number of filings to return.
            start_date: Start date filter (ISO format).
            end_date: End date filter (ISO format).
            output_dir: Directory to save raw filing data.

        Returns:
            List of Filing model instances.
        """
        if not ticker and not cik:
            raise ValueError("Either ticker or cik must be provided.")

        # Fetch raw filing data
        raw_filings = self._fetcher.get_filings(
            ticker=ticker,
            cik=cik,
            filing_types=filing_types or ["10-K", "10-Q", "8-K"],
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )

        # Parse into Filing models
        filings = _parse_filings(raw_filings)

        # Save to output_dir if specified
        if output_dir:
            import os
            os.makedirs(output_dir, exist_ok=True)
            for filing in filings:
                if filing.primary_document:
                    filepath = os.path.join(output_dir, filing.primary_document)
                    with open(filepath, "w") as f:
                        f.write(filing.primary_document)

        logger.info(f"Fetched {len(filings)} filings for {ticker or cik}")
        return filings

    def fetch_latest_10k(self, ticker: str) -> Optional[Filing]:
        """Fetch the most recent 10-K filing for a company."""
        filings = self.fetch_filings(ticker=ticker, filing_types=["10-K"], limit=1)
        return filings[0] if filings else None

    def fetch_latest_10q(self, ticker: str) -> Optional[Filing]:
        """Fetch the most recent 10-Q filing for a company."""
        filings = self.fetch_filings(ticker=ticker, filing_types=["10-Q"], limit=1)
        return filings[0] if filings else None

    def fetch_latest_8k(self, ticker: str) -> Optional[Filing]:
        """Fetch the most recent 8-K filing for a company."""
        filings = self.fetch_filings(ticker=ticker, filing_types=["8-K"], limit=1)
        return filings[0] if filings else None

    def latest(self, ticker: str, filing_type: str = "10-K", limit: int = 1) -> Optional[Filing]:
        """Fetch the most recent filing of a given type for a company.

        Args:
            ticker: Company ticker symbol.
            filing_type: Filing type (default '10-K').
            limit: Maximum number of filings to fetch (default 1).

        Returns:
            The most recent Filing, or None.
        """
        filings = self.fetch_filings(ticker=ticker, filing_types=[filing_type], limit=limit)
        return filings[0] if filings else None

    def close(self):
        """Close the HTTP client."""
        if hasattr(self._fetcher, 'close'):
            self._fetcher.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
