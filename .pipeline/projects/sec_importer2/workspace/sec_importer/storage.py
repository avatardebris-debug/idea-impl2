"""Storage layer for SEC Importer 2 — SQLite with SQLAlchemy ORM."""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Company, Filing

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sec_importer.db")


def init_db(db_path: Optional[str] = None) -> sessionmaker:
    """Initialize the SQLite database and return a session factory.

    Creates tables if they don't exist.

    Args:
        db_path: Path to the SQLite database file. Defaults to sec_importer.db
                 in the package directory.

    Returns:
        A SQLAlchemy sessionmaker bound to the engine.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    # Ensure the directory exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def get_session(db_path: Optional[str] = None) -> Session:
    """Get a new database session."""
    sm = init_db(db_path)
    return sm()


def upsert_company(session: Session, ticker: str, name: Optional[str] = None,
                   cik: Optional[str] = None) -> Company:
    """Insert or update a company record. Returns the company."""
    company = session.execute(select(Company).where(Company.ticker == ticker)).scalar_one_or_none()
    if company:
        company.ticker = ticker
        company.name = name or company.name
        company.cik = cik or company.cik
    else:
        company = Company(ticker=ticker, name=name, cik=cik)
        session.add(company)
    session.commit()
    return company


def get_last_sync_date(session: Session, ticker: str) -> Optional[str]:
    """Get the most recent synced_at date for a ticker.

    Returns the date string in YYYY-MM-DD format, or None if no filings exist.
    """
    result = session.execute(
        select(func.max(Filing.synced_at)).where(Filing.ticker == ticker)
    ).scalar_one_or_none()
    if result is None:
        return None
    return result.strftime("%Y-%m-%d") if hasattr(result, "strftime") else str(result)


def get_existing_accession_numbers(session: Session, ticker: str) -> set:
    """Get set of existing accession_numbers for a ticker."""
    result = session.execute(
        select(Filing.accession_number).where(Filing.ticker == ticker)
    ).scalars().all()
    return set(result)


def insert_filings(session: Session, filings: list[Filing]) -> int:
    """Insert a list of Filing objects. Returns count of inserted records.

    Deduplicates by accession_number before inserting to prevent duplicates
    even if the caller bypasses the sync layer's deduplication.
    """
    # Deduplicate by accession_number (first occurrence wins)
    seen = set()
    unique_filings = []
    for f in filings:
        if f.accession_number and f.accession_number not in seen:
            seen.add(f.accession_number)
            unique_filings.append(f)
    session.add_all(unique_filings)
    session.commit()
    return len(unique_filings)


def query_filings(session: Session, ticker: Optional[str] = None,
                  limit: Optional[int] = None) -> list[Filing]:
    """Query stored filings with optional ticker filter and limit."""
    stmt = select(Filing)
    if ticker:
        stmt = stmt.where(Filing.ticker == ticker)
    stmt = stmt.order_by(Filing.filing_date.desc())
    if limit:
        stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


def count_filings(session: Session, ticker: Optional[str] = None) -> int:
    """Count stored filings, optionally filtered by ticker."""
    stmt = select(func.count(Filing.id))
    if ticker:
        stmt = stmt.where(Filing.ticker == ticker)
    return session.execute(stmt).scalar_one()
