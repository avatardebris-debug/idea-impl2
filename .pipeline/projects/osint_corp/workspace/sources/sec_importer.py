"""SEC filing importer — fetches and parses SEC filings."""

from __future__ import annotations

import os
import pathlib
from typing import Optional

from osint_corp.models.entities import Filing
from osint_corp.sources.sec_fetcher import SECFetcher
from osint_corp.sources.sec_parser import SECParser


class SECImporter:
    """Fetch SEC filings from the EDGAR API and parse them."""

    def __init__(self, user_agent: str = "osint-corp/0.1.0"):
        self.fetcher = SECFetcher(user_agent=user_agent)
        self.parser = SECParser()

    def fetch_filings(
        self,
        ticker: str,
        filing_types: list[str] | None = None,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> list[Filing]:
        """Fetch filings for a given ticker, optionally saving to output_dir."""
        raw = self.fetcher.search_filings(
            ticker=ticker,
            filing_types=filing_types,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )
        filings = self.parser.parse_response(raw)

        if output_dir:
            pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
            cache_file = pathlib.Path(output_dir) / f"filings_{ticker}.json"
            with open(cache_file, "w") as f:
                import json
                json.dump([filing.to_dict() for filing in filings], f, indent=2, default=str)

        return filings

    def latest(
        self,
        ticker: str,
        filing_type: str = "10-K",
        limit: int = 10,
    ) -> list[Filing]:
        """Fetch the latest filings for a ticker."""
        raw = self.fetcher.latest_filings(ticker=ticker, filing_type=filing_type, limit=limit)
        return self.parser.parse_latest(raw)
