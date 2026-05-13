"""Data ingestion layer for forensic suite.

Fetches a company's latest 10-K via sec_importer, parses it,
and stores results in the SQLite database.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from pydantic import BaseModel

from forensic.config import get_config
from forensic.models import RedFlagSeverity

# Import sec_importer components
from sec_importer import SECDatabase
from sec_importer.models import FilingItemModel
from sec_importer.parsers import FilingParser

logger = logging.getLogger(__name__)


class IngestResult(BaseModel):
    """Result of ingesting a company's filing."""

    ticker: str
    cik: str
    accession_no: str
    filing_date: str
    filing_type: str
    item_count: int
    red_flags: List[dict]


def ingest_company(
    ticker: str,
    db_path: Optional[str] = None,
) -> IngestResult:
    """Ingest a company's latest 10-K filing.

    Resolves ticker to CIK, fetches latest 10-K metadata,
    downloads filing text, parses it into FilingItemModel objects,
    and upserts company/filing/items into the database.

    Args:
        ticker: Company ticker symbol.
        db_path: Optional path to SQLite database. Uses config default if None.

    Returns:
        IngestResult with filing metadata and parsed items.

    Raises:
        ValueError: If ticker cannot be resolved or no 10-K found.
    """
    config = get_config()
    if db_path is None:
        db_path = config.db_path

    with SECDatabase(db_path) as db:
        # Resolve ticker to CIK
        cik = db.companies.resolve_ticker(ticker)
        if not cik:
            raise ValueError(f"Ticker '{ticker}' not found in database")

        # Upsert company
        company_info = db.companies.get_or_fetch_company(cik)
        if company_info:
            db.companies.upsert_company(company_info)

        # Fetch latest 10-K
        filings = db.filings.get_filings_by_cik(cik)
        latest_10k = None
        for f in filings:
            if f.filing_type == "10-K":
                latest_10k = f
                break

        if not latest_10k:
            # Try to fetch from EDGAR
            latest_10k = db.filings.fetch_latest_10k(cik)
            if latest_10k:
                db.filings.upsert_filing(latest_10k)

        if not latest_10k:
            raise ValueError(f"No 10-K filing found for CIK {cik}")

        # Download and parse filing
        filing_text = db.filings.download_filing(latest_10k)
        if not filing_text:
            raise ValueError(f"Failed to download filing {latest_10k.accession_no}")

        parser = FilingParser()
        items = parser.parse(filing_text)

        # Store items in database
        db.items.upsert_items(latest_10k.id, latest_10k.accession_no, items)

        logger.info(
            "Ingested %d items for %s (CIK=%s, %s, %s)",
            len(items),
            ticker,
            cik,
            latest_10k.filing_type,
            latest_10k.filing_date,
        )

        return IngestResult(
            ticker=ticker,
            cik=cik,
            accession_no=latest_10k.accession_no,
            filing_date=latest_10k.filing_date or "",
            filing_type=latest_10k.filing_type,
            item_count=len(items),
            red_flags=[],
        )
