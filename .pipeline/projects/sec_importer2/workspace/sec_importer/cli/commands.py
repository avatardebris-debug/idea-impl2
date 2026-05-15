"""CLI commands for SEC Importer 2 — scheduling, importing, and management."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta

from ..config import get_config
from ..storage import init_db
from ..fetcher import SECFetcher
from ..parser import XBRLParser, HTMLParser
from ..storage import get_session
from ..models import Filing, FilingContent, Company

logger = logging.getLogger(__name__)


def cmd_schedule(args: argparse.Namespace) -> None:
    """Schedule a recurring import job."""
    settings = get_config()
    logger.info("Scheduling import job")
    logger.info(f"  Ticker: {args.ticker}")
    logger.info(f"  Filing type: {args.filing_type}")
    logger.info(f"  Interval: {args.interval}")
    logger.info(f"  Start date: {args.start_date}")

    # In a production system, this would register with a scheduler (e.g., APScheduler, Celery)
    # For now, we just log the configuration
    print(f"Job scheduled: {args.ticker} {args.filing_type} every {args.interval}")
    print(f"Start date: {args.start_date}")
    print("Note: This is a demo. In production, use a task queue like Celery or APScheduler.")


def cmd_import(args: argparse.Namespace) -> None:
    """Import filings for a given ticker and filing type."""
    settings = get_config()
    init_db(settings["db_path"])

    fetcher = SECFetcher()
    parser = XBRLParser()
    html_parser = HTMLParser()

    ticker = args.ticker.upper()
    filing_type = args.filing_type.upper() if args.filing_type else None
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else None
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None

    logger.info(f"Importing {filing_type or 'all'} filings for {ticker}")
    logger.info(f"  Date range: {start_date or 'earliest'} to {end_date or 'latest'}")

    # Fetch filings
    filings = fetcher.get_filings(
        ticker=ticker,
        filing_type=filing_type,
        start_date=start_date,
        end_date=end_date,
    )

    if not filings:
        logger.info(f"No filings found for {ticker}")
        return

    logger.info(f"Found {len(filings)} filings")

    # Store filings
    session = get_session()
    try:
        for filing in filings:
            # Check if already exists
            existing = session.query(Filing).filter_by(
                accession_number=filing.accession_number
            ).first()
            if existing:
                logger.debug(f"Skipping existing filing: {filing.accession_number}")
                continue

            # Store filing record
            db_filing = Filing(
                ticker=filing.ticker,
                filing_type=filing.filing_type,
                filing_date=filing.filing_date,
                accession_number=filing.accession_number,
                form_description=filing.form_description,
                document_url=filing.document_url,
                accepted_date=filing.accepted_date,
                fill_url=filing.fill_url,
            )
            session.add(db_filing)
            session.flush()

            # Parse and store content
            if filing.html_content:
                html_sections = html_parser.parse(filing.html_content)
                if html_sections:
                    content = FilingContent(
                        filing_id=db_filing.id,
                        accession_number=filing.accession_number,
                        content_type="html",
                        content_data=str(html_sections),
                    )
                    session.add(content)

            if filing.xbrl_content:
                xbrl_data = parser.parse(filing.xbrl_content)
                if xbrl_data:
                    content = FilingContent(
                        filing_id=db_filing.id,
                        accession_number=filing.accession_number,
                        content_type="xbrl",
                        content_data=str(xbrl_data),
                    )
                    session.add(content)

        session.commit()
        logger.info(f"Imported {len(filings)} filings successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Import failed: {e}")
        raise
    finally:
        session.close()


def cmd_list(args: argparse.Namespace) -> None:
    """List stored filings."""
    settings = get_config()
    init_db(settings["db_path"])

    session = get_session()
    try:
        filings = session.query(Filing).order_by(Filing.filing_date.desc()).all()
        if not filings:
            print("No filings found.")
            return

        print(f"{'Ticker':<10} {'Type':<10} {'Date':<12} {'Accession':<25} {'Description'}")
        print("-" * 80)
        for f in filings[:args.limit]:
            print(f"{f.ticker:<10} {f.filing_type:<10} {f.filing_date or 'N/A':<12} {f.accession_number:<25} {f.form_description or ''}")
    finally:
        session.close()


def cmd_status(args: argparse.Namespace) -> None:
    """Show import status and statistics."""
    settings = get_config()
    init_db(settings["db_path"])

    session = get_session()
    try:
        total_filings = session.query(Filing).count()
        total_companies = session.query(Company).count()
        total_xbrl = session.query(FilingContent).filter_by(content_type="xbrl").count()
        total_html = session.query(FilingContent).filter_by(content_type="html").count()

        print("=== SEC Importer 2 Status ===")
        print(f"Total filings: {total_filings}")
        print(f"Total companies: {total_companies}")
        print(f"XBRL content: {total_xbrl}")
        print(f"HTML content: {total_html}")
    finally:
        session.close()


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sec-importer",
        description="SEC Importer 2 — CLI for managing SEC filing imports",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Schedule a recurring import")
    schedule_parser.add_argument("--ticker", required=True, help="Company ticker")
    schedule_parser.add_argument("--filing-type", default="10-K", help="Filing type (default: 10-K)")
    schedule_parser.add_argument("--interval", default="daily", help="Import interval (daily, weekly, monthly)")
    schedule_parser.add_argument("--start-date", default=datetime.now().strftime("%Y-%m-%d"), help="Start date")
    schedule_parser.set_defaults(func=cmd_schedule)

    # Import command
    import_parser = subparsers.add_parser("import", help="Import filings")
    import_parser.add_argument("--ticker", required=True, help="Company ticker")
    import_parser.add_argument("--filing-type", default=None, help="Filing type (e.g. 10-K, 10-Q)")
    import_parser.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD)")
    import_parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD)")
    import_parser.set_defaults(func=cmd_import)

    # List command
    list_parser = subparsers.add_parser("list", help="List stored filings")
    list_parser.add_argument("--limit", default=50, type=int, help="Max results")
    list_parser.set_defaults(func=cmd_list)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show import status")
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
