"""CLI interface for SEC Importer 2."""

from __future__ import annotations

import csv
import logging
import os
import sys
from datetime import datetime

import click
from sqlalchemy import func, select

from .config import DEFAULT_DB_PATH, DEFAULT_TICKERS_FILE, get_config
from .sync import run_sync
from .storage import init_db, get_session, query_filings, count_filings
from .models import Filing

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sec-importer")


@click.group()
@click.option("--db-path", default=None, help="Path to SQLite database file.")
@click.option("--log-level", default=None, help="Logging level (DEBUG, INFO, WARNING, ERROR).")
@click.pass_context
def cli(ctx, db_path, log_level):
    """SEC Importer 2 — Fetch, parse, and store SEC filing data.

    Examples:

    \b
    # Run delta-sync for all tickers
    sec-importer sync

    \b
    # List stored filings
    sec-importer list

    \b
    # Add a ticker to the ticker list
    sec-importer add-ticker AAPL
    """
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db_path or DEFAULT_DB_PATH

    if log_level:
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(numeric_level)


@cli.command()
@click.option("--tickers-file", default=None, help="Path to CSV file with tickers.")
@click.option("--limit", default=100, help="Maximum filings to fetch per ticker.")
@click.option("--db-path", default=None, help="Path to SQLite database file.")
@click.pass_context
def sync(ctx, tickers_file, limit, db_path):
    """Run delta-sync: fetch new filings for all configured tickers."""
    db_path = db_path or ctx.obj.get("db_path") or DEFAULT_DB_PATH
    tickers_file = tickers_file or DEFAULT_TICKERS_FILE

    click.echo(f"Starting delta-sync...")
    click.echo(f"  Tickers file: {tickers_file}")
    click.echo(f"  Limit per ticker: {limit}")
    click.echo(f"  Database: {db_path}")
    click.echo()

    try:
        summary = run_sync(tickers_file=tickers_file, limit_per_ticker=limit, db_path=db_path)

        if "error" in summary:
            click.echo(click.style(f"Error: {summary['error']}", fg="red"))
            sys.exit(1)

        click.echo(click.style("Delta-sync complete!", fg="green"))
        click.echo()
        click.echo(f"  Total new filings: {summary.get('total_new', 0)}")
        click.echo(f"  Total skipped (duplicates): {summary.get('total_skipped', 0)}")
        click.echo(f"  Total filings in DB: {summary.get('total_filings', 0)}")
        click.echo()

        # Print per-ticker summary
        if summary.get("tickers"):
            click.echo(click.style("Per-ticker summary:", fg="cyan"))
            for t in summary["tickers"]:
                status = click.style("OK", fg="green")
                if "error" in t:
                    status = click.style(f"ERR: {t['error']}", fg="red")
                click.echo(
                    f"  {t['ticker']:10s}  "
                    f"new={t.get('new', 0):4d}  "
                    f"skipped={t.get('skipped', 0):4d}  "
                    f"{status}"
                )

    except Exception as e:
        click.echo(click.style(f"Sync failed: {e}", fg="red"))
        logger.exception("Sync error")
        sys.exit(1)


@cli.command("list")
@click.option("--ticker", default=None, help="Filter by ticker symbol.")
@click.option("--limit", default=50, help="Maximum number of filings to display.")
@click.option("--db-path", default=None, help="Path to SQLite database file.")
@click.pass_context
def list_filings(ctx, ticker, limit, db_path):
    """Query and display stored filings."""
    db_path = db_path or ctx.obj.get("db_path") or DEFAULT_DB_PATH

    session_factory = init_db(db_path)
    session = session_factory()

    try:
        filings = query_filings(session, ticker=ticker, limit=limit)

        if not filings:
            click.echo("No filings found.")
            return

        click.echo(click.style(f"Stored Filings ({len(filings)} records)", fg="cyan"))
        click.echo()

        # Table header
        header = f"{'Ticker':<10} {'Type':<10} {'Date':<12} {'Accession':<30} {'Description':<30}"
        click.echo(click.style(header, fg="yellow"))
        click.echo("-" * len(header))

        for f in filings:
            accession = (f.accession_number or "")[:28]
            desc = (f.form_description or "")[:28]
            row = (
                f"{f.ticker:<10} "
                f"{f.filing_type:<10} "
                f"{f.filing_date or 'N/A':<12} "
                f"{accession:<30} "
                f"{desc:<30}"
            )
            click.echo(row)

        click.echo()
        click.echo(f"Total filings in DB: {count_filings(session, ticker=ticker)}")

    finally:
        session.close()


@cli.command("add-ticker")
@click.argument("ticker", type=str)
@click.option("--tickers-file", default=None, help="Path to tickers CSV file.")
@click.pass_context
def add_ticker(ctx, ticker, tickers_file):
    """Add a ticker to the ticker list CSV file."""
    tickers_file = tickers_file or DEFAULT_TICKERS_FILE

    ticker = ticker.strip().upper()
    if not ticker:
        click.echo(click.style("Error: Ticker cannot be empty.", fg="red"))
        sys.exit(1)

    # Check if ticker already exists
    tickers = []
    if os.path.exists(tickers_file):
        with open(tickers_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    t = row[0].strip().upper()
                    if t and not t.startswith("#"):
                        tickers.append(t)

    if ticker in tickers:
        click.echo(click.style(f"Ticker {ticker} already exists in {tickers_file}", fg="yellow"))
        return

    # Add ticker
    tickers.append(ticker)
    with open(tickers_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for t in tickers:
            writer.writerow([t])

    click.echo(click.style(f"Added {ticker} to {tickers_file}", fg="green"))


@cli.command("stats")
@click.option("--ticker", default=None, help="Filter by ticker symbol.")
@click.option("--db-path", default=None, help="Path to SQLite database file.")
@click.pass_context
def stats(ctx, ticker, db_path):
    """Display database statistics."""
    db_path = db_path or ctx.obj.get("db_path") or DEFAULT_DB_PATH

    session_factory = init_db(db_path)
    session = session_factory()

    try:
        total = count_filings(session, ticker=ticker)
        click.echo(click.style("Database Statistics", fg="cyan"))
        click.echo()
        click.echo(f"  Total filings: {total}")
        if ticker:
            click.echo(f"  Filtered by ticker: {ticker}")

        # Get date range
        if total > 0:
            min_date = session.execute(
                select(func.min(Filing.filing_date))
            ).scalar_one_or_none()
            max_date = session.execute(
                select(func.max(Filing.filing_date))
            ).scalar_one_or_none()
            click.echo(f"  Date range: {min_date} to {max_date}")

    finally:
        session.close()


if __name__ == "__main__":
    cli()
