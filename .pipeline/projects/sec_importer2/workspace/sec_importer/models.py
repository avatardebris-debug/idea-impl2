"""SQLAlchemy ORM models for SEC Importer 2."""

from __future__ import annotations

import datetime as dt
from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Company(Base):
    """Represents a US publicly traded company."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    cik = Column(String(10), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))


class Filing(Base):
    """Represents a single SEC filing."""

    __tablename__ = "filings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    filing_type = Column(String(20), nullable=False)
    filing_date = Column(String(10), nullable=True)
    accession_number = Column(String(50), nullable=True, index=True)
    document_url = Column(Text, nullable=True)
    form_description = Column(Text, nullable=True)
    accepted_date = Column(String(25), nullable=True)
    fill_url = Column(Text, nullable=True)
    raw_json = Column(Text, nullable=True)
    synced_at = Column(DateTime, default=lambda: dt.datetime.now(dt.timezone.utc))

    __table_args__ = (
        # Unique constraint on accession_number to prevent duplicates.
        # SQLite does not enforce unique on nullable columns, so we also
        # deduplicate at the application layer in storage.py.
        UniqueConstraint("accession_number", name="uq_accession_number"),
    )
