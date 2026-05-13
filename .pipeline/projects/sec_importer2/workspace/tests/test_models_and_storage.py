"""Tests for SEC Importer 2 models and storage modules."""

from __future__ import annotations

import datetime as dt
import os
import tempfile

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session, sessionmaker

from sec_importer.models import Base, Company, Filing
from sec_importer.storage import (
    init_db,
    get_session,
    upsert_company,
    get_last_sync_date,
    get_existing_accession_numbers,
    insert_filings,
    query_filings,
    count_filings,
)


@pytest.fixture()
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sm = sessionmaker(bind=engine)
    session = sm()
    yield session
    session.close()


@pytest.fixture()
def temp_db_path():
    """Create a temporary SQLite database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


# ---- Company tests ----


class TestUpsertCompany:
    """Tests for upsert_company."""

    def test_insert_new_company(self, db_session: Session):
        company = upsert_company(db_session, ticker="AAPL", name="Apple Inc.", cik="0000320193")
        assert company.ticker == "AAPL"
        assert company.name == "Apple Inc."
        assert company.cik == "0000320193"

    def test_update_existing_company(self, db_session: Session):
        upsert_company(db_session, ticker="AAPL", name="Apple Inc.", cik="0000320193")
        company = upsert_company(db_session, ticker="AAPL", name="Apple Corp.", cik="0000320193")
        assert company.name == "Apple Corp."
        assert company.cik == "0000320193"

    def test_partial_update(self, db_session: Session):
        upsert_company(db_session, ticker="AAPL", name="Apple Inc.", cik="0000320193")
        company = upsert_company(db_session, ticker="AAPL", name=None, cik="0000320194")
        assert company.name == "Apple Inc."
        assert company.cik == "0000320194"

    def test_company_unique_ticker(self, db_session: Session):
        upsert_company(db_session, ticker="AAPL", name="Apple Inc.")
        with pytest.raises(Exception):
            upsert_company(db_session, ticker="AAPL", name="Apple 2 Inc.")


class TestCompanyModel:
    """Tests for the Company ORM model."""

    def test_company_creation(self):
        company = Company(ticker="AAPL", name="Apple Inc.", cik="0000320193")
        assert company.ticker == "AAPL"
        assert company.name == "Apple Inc."
        assert company.cik == "0000320193"
        assert company.created_at is not None

    def test_company_default_created_at(self):
        company = Company(ticker="MSFT")
        assert company.created_at is not None
        assert isinstance(company.created_at, dt.datetime)


# ---- Filing tests ----


class TestFilingModel:
    """Tests for the Filing ORM model."""

    def test_filing_creation(self):
        filing = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
            document_url="https://example.com/filing.html",
        )
        assert filing.ticker == "AAPL"
        assert filing.filing_type == "10-K"
        assert filing.filing_date == "2024-01-01"
        assert filing.accession_number == "000123456724000001"
        assert filing.synced_at is not None

    def test_filing_nullable_fields(self):
        filing = Filing(ticker="AAPL", filing_type="10-K", filing_date="2024-01-01")
        assert filing.document_url is None
        assert filing.form_description is None
        assert filing.accepted_date is None
        assert filing.fill_url is None
        assert filing.raw_json is None


# ---- Storage tests ----


class TestGetSession:
    """Tests for get_session."""

    def test_get_session_returns_session(self, temp_db_path: str):
        session = get_session(temp_db_path)
        assert isinstance(session, Session)
        session.close()

    def test_get_session_creates_tables(self, temp_db_path: str):
        get_session(temp_db_path)
        # Verify tables exist by querying
        engine = create_engine(f"sqlite:///{temp_db_path}")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        assert "companies" in inspector.get_table_names()
        assert "filings" in inspector.get_table_names()


class TestGetLastSyncDate:
    """Tests for get_last_sync_date."""

    def test_no_filings_returns_none(self, db_session: Session):
        assert get_last_sync_date(db_session, "AAPL") is None

    def test_returns_latest_sync_date(self, db_session: Session):
        filing1 = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
            synced_at=dt.datetime(2024, 1, 1, 10, 0, 0),
        )
        filing2 = Filing(
            ticker="AAPL",
            filing_type="10-Q",
            filing_date="2024-04-01",
            accession_number="000123456724000002",
            synced_at=dt.datetime(2024, 4, 1, 10, 0, 0),
        )
        db_session.add_all([filing1, filing2])
        db_session.commit()

        result = get_last_sync_date(db_session, "AAPL")
        assert result == dt.datetime(2024, 4, 1, 10, 0, 0)

    def test_different_tickers(self, db_session: Session):
        filing1 = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
            synced_at=dt.datetime(2024, 1, 1, 10, 0, 0),
        )
        filing2 = Filing(
            ticker="MSFT",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000002",
            synced_at=dt.datetime(2024, 6, 1, 10, 0, 0),
        )
        db_session.add_all([filing1, filing2])
        db_session.commit()

        assert get_last_sync_date(db_session, "AAPL") == dt.datetime(2024, 1, 1, 10, 0, 0)
        assert get_last_sync_date(db_session, "MSFT") == dt.datetime(2024, 6, 1, 10, 0, 0)


class TestGetExistingAccessionNumbers:
    """Tests for get_existing_accession_numbers."""

    def test_no_filings_returns_empty(self, db_session: Session):
        result = get_existing_accession_numbers(db_session, "AAPL")
        assert result == set()

    def test_returns_existing_accessions(self, db_session: Session):
        filing1 = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
        )
        filing2 = Filing(
            ticker="AAPL",
            filing_type="10-Q",
            filing_date="2024-04-01",
            accession_number="000123456724000002",
        )
        db_session.add_all([filing1, filing2])
        db_session.commit()

        result = get_existing_accession_numbers(db_session, "AAPL")
        assert result == {"000123456724000001", "000123456724000002"}

    def test_different_tickers(self, db_session: Session):
        filing1 = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
        )
        filing2 = Filing(
            ticker="MSFT",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000002",
        )
        db_session.add_all([filing1, filing2])
        db_session.commit()

        assert get_existing_accession_numbers(db_session, "AAPL") == {"000123456724000001"}
        assert get_existing_accession_numbers(db_session, "MSFT") == {"000123456724000002"}


class TestInsertFilings:
    """Tests for insert_filings."""

    def test_insert_single_filing(self, db_session: Session):
        filing = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
        )
        count = insert_filings(db_session, [filing])
        assert count == 1
        assert count_filings(db_session) == 1

    def test_insert_multiple_filings(self, db_session: Session):
        filings = [
            Filing(
                ticker="AAPL",
                filing_type="10-K",
                filing_date="2024-01-01",
                accession_number=f"00012345672400000{i}",
            )
            for i in range(1, 6)
        ]
        count = insert_filings(db_session, filings)
        assert count == 5

    def test_insert_returns_count(self, db_session: Session):
        filing = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
        )
        count = insert_filings(db_session, [filing])
        assert count == 1

    def test_insert_empty_list(self, db_session: Session):
        count = insert_filings(db_session, [])
        assert count == 0


class TestQueryFilings:
    """Tests for query_filings."""

    def test_query_all_filings(self, db_session: Session):
        for i in range(3):
            db_session.add(Filing(
                ticker="AAPL",
                filing_type="10-K",
                filing_date="2024-01-01",
                accession_number=f"00012345672400000{i}",
            ))
        db_session.commit()

        filings = query_filings(db_session, limit=10)
        assert len(filings) == 3

    def test_query_with_ticker_filter(self, db_session: Session):
        db_session.add(Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
        ))
        db_session.add(Filing(
            ticker="MSFT",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000002",
        ))
        db_session.commit()

        filings = query_filings(db_session, ticker="AAPL", limit=10)
        assert len(filings) == 1
        assert filings[0].ticker == "AAPL"

    def test_query_with_limit(self, db_session: Session):
        for i in range(5):
            db_session.add(Filing(
                ticker="AAPL",
                filing_type="10-K",
                filing_date="2024-01-01",
                accession_number=f"00012345672400000{i}",
            ))
        db_session.commit()

        filings = query_filings(db_session, limit=3)
        assert len(filings) == 3

    def test_query_no_results(self, db_session: Session):
        filings = query_filings(db_session, ticker="NONEXISTENT", limit=10)
        assert filings == []


class TestCountFilings:
    """Tests for count_filings."""

    def test_count_all(self, db_session: Session):
        for i in range(5):
            db_session.add(Filing(
                ticker="AAPL",
                filing_type="10-K",
                filing_date="2024-01-01",
                accession_number=f"00012345672400000{i}",
            ))
        db_session.commit()

        assert count_filings(db_session) == 5

    def test_count_with_ticker_filter(self, db_session: Session):
        db_session.add(Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000001",
        ))
        db_session.add(Filing(
            ticker="MSFT",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="000123456724000002",
        ))
        db_session.commit()

        assert count_filings(db_session, ticker="AAPL") == 1
        assert count_filings(db_session, ticker="MSFT") == 1
        assert count_filings(db_session, ticker="NONEXISTENT") == 0

    def test_count_empty_db(self, db_session: Session):
        assert count_filings(db_session) == 0


class TestInitDb:
    """Tests for init_db."""

    def test_init_db_creates_tables(self, temp_db_path: str):
        session_factory = init_db(temp_db_path)
        session = session_factory()
        from sqlalchemy import inspect
        inspector = inspect(session.get_bind())
        assert "companies" in inspector.get_table_names()
        assert "filings" in inspector.get_table_names()
        session.close()

    def test_init_db_returns_session_factory(self, temp_db_path: str):
        session_factory = init_db(temp_db_path)
        session = session_factory()
        assert isinstance(session, Session)
        session.close()

    def test_init_db_with_none_path(self):
        session_factory = init_db(None)
        session = session_factory()
        assert isinstance(session, Session)
        session.close()
