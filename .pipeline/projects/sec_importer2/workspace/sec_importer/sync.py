"""Delta-sync orchestrator for SEC Importer 2."""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from .fetcher import SECFetcher, TICKER_TO_CIK_URL
from .parser import parse_filings
from .storage import (
    init_db,
    get_session,
    upsert_company,
    get_last_sync_date,
    get_existing_accession_numbers,
    insert_filings,
    count_filings,
)
from .models import Filing

logger = logging.getLogger(__name__)

DEFAULT_TICKERS_FILE = os.path.join(os.path.dirname(__file__), "tickers.csv")


def run_sync(
    tickers_file: Optional[str] = None,
    limit_per_ticker: int = 100,
    db_path: Optional[str] = None,
) -> dict:
    """Run a delta-sync: fetch new filings for all tickers and store them.

    Args:
        tickers_file: Path to CSV file with ticker symbols (one per line).
        limit_per_ticker: Maximum number of filings to fetch per ticker.
        db_path: Path to the SQLite database.

    Returns:
        Summary dict with counts of new and skipped filings per ticker.
    """
    if tickers_file is None:
        tickers_file = DEFAULT_TICKERS_FILE

    # Initialize database
    session_factory = init_db(db_path)
    session = session_factory()

    # Load tickers
    tickers = _load_tickers(tickers_file)
    if not tickers:
        logger.error(f"No tickers found in {tickers_file}")
        return {"error": "No tickers found"}

    logger.info(f"Starting delta-sync for {len(tickers)} tickers")

    summary = {
        "tickers": [],
        "total_new": 0,
        "total_skipped": 0,
        "start_time": datetime.now(timezone.utc).isoformat(),
    }

    with SECFetcher() as fetcher:
        for ticker in tickers:
            ticker_summary = _sync_ticker(
                session=session,
                fetcher=fetcher,
                ticker=ticker,
                limit=limit_per_ticker,
            )
            summary["tickers"].append(ticker_summary)
            summary["total_new"] += ticker_summary.get("new", 0)
            summary["total_skipped"] += ticker_summary.get("skipped", 0)

    summary["end_time"] = datetime.now(timezone.utc).isoformat()
    summary["total_filings"] = count_filings(session)
    session.close()

    logger.info(
        f"Delta-sync complete: {summary['total_new']} new, "
        f"{summary['total_skipped']} skipped, "
        f"{summary['total_filings']} total filings"
    )
    return summary


def _sync_ticker(
    session,
    fetcher: SECFetcher,
    ticker: str,
    limit: int = 100,
) -> dict:
    """Sync filings for a single ticker.

    Returns:
        Summary dict with new and skipped counts.
    """
    result = {"ticker": ticker, "new": 0, "skipped": 0}

    # Get last sync date for this ticker
    last_sync = get_last_sync_date(session, ticker)
    logger.info(f"Ticker {ticker}: last synced = {last_sync}")

    # Fetch filings
    try:
        raw_filings = fetcher.fetch_filings(ticker=ticker)
    except Exception as e:
        logger.error(f"Failed to fetch filings for {ticker}: {e}")
        result["error"] = str(e)
        return result

    if not raw_filings:
        logger.info(f"No filings returned for {ticker}")
        return result

    # Get CIK and company name from the ticker lookup (available in fetcher)
    cik = fetcher.get_cik_from_ticker(ticker)
    company_name = None
    if cik:
        # Fetch the ticker lookup to get company name
        ticker_url = TICKER_TO_CIK_URL.format(ticker=ticker.upper())
        try:
            resp = fetcher._session.get(ticker_url)
            if resp.status_code == 200:
                ticker_data = resp.json()
                company_name = ticker_data.get("companyName")
        except Exception:
            pass

    # Parse filings
    parsed = parse_filings(raw_filings)
    if not parsed:
        logger.warning(f"No valid filings parsed for {ticker}")
        return result

    # Limit filings
    parsed = parsed[:limit]

    # Get existing accession numbers to avoid duplicates
    existing = get_existing_accession_numbers(session, ticker)

    # Filter out duplicates
    new_filings = []
    skipped = 0
    for record in parsed:
        accession = record.get("accession_number", "")
        if accession in existing:
            skipped += 1
            continue
        new_filings.append(record)

    # Insert new filings
    if new_filings:
        filing_objects = []
        for record in new_filings:
            filing = Filing(
                ticker=record.get("ticker", ticker),
                filing_type=record.get("filing_type", ""),
                filing_date=record.get("filing_date", ""),
                accession_number=record.get("accession_number", ""),
                document_url=record.get("document_url", ""),
                form_description=record.get("form_description", ""),
                accepted_date=record.get("accepted_date", ""),
                fill_url=record.get("fill_url", ""),
                raw_json=_serialize_raw(record.get("raw_json")),
            )
            filing_objects.append(filing)

        count = insert_filings(session, filing_objects)
        result["new"] = count

        # Upsert company with CIK and name from ticker lookup
        upsert_company(session, ticker, name=company_name, cik=cik)

    result["skipped"] = skipped
    result["fetched"] = len(parsed)
    logger.info(
        f"Ticker {ticker}: {result['new']} new, {result['skipped']} skipped "
        f"of {result['fetched']} fetched"
    )
    return result


def _load_tickers(tickers_file: str) -> list[str]:
    """Load tickers from a CSV file (one per line, first column)."""
    tickers = []
    try:
        with open(tickers_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    ticker = row[0].strip().upper()
                    if ticker and not ticker.startswith("#"):
                        tickers.append(ticker)
    except FileNotFoundError:
        logger.error(f"Tickers file not found: {tickers_file}")
    return tickers


def _serialize_raw(raw: Optional[dict]) -> Optional[str]:
    """Serialize raw data to JSON string for storage."""
    if raw is None:
        return None
    try:
        import json
        return json.dumps(raw)
    except Exception:
        return str(raw)
