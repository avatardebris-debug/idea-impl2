"""Tests for SEC Importer repository layer.

Tests the CompanyRepository, FilingRepository, and FilingItemRepository
with proper SQLite connection handling.
"""

import os
import pytest
import sqlite3
from sec_importer.repository import (
    CompanyRepository,
    FilingRepository,
    FilingItemRepository,
    SECDatabase,
)
from sec_importer.models import CompanyModel, FilingModel, FilingItemModel
from sec_importer.schema import init_db


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary SQLite database."""
    db_file = tmp_path / "test_sec_importer.db"
    return str(db_file)


@pytest.fixture
def conn(db_path):
    """Create a database connection."""
    return init_db(db_path)


@pytest.fixture
def repositories(conn):
    """Create all repositories with the same connection."""
    return {
        "company": CompanyRepository(conn),
        "filing": FilingRepository(conn),
        "item": FilingItemRepository(conn),
    }


@pytest.fixture
def mock_company():
    """Create a mock company model."""
    return CompanyModel(
        cik="0000320193",
        name="Apple Inc.",
        ticker="AAPL",
        sic="3600",
        industry="Consumer Electronics",
        state="CA",
    )


@pytest.fixture
def mock_filing():
    """Create a mock filing model."""
    return FilingModel(
        accession_no="000032019321000099",
        cik="0000320193",
        filing_type="10-K",
        filing_date="2021-01-29",
        accepted_date="2021-01-29T16:30:00",
        file_url="https://www.sec.gov/Archives/edgar/full-text/000032019321000099.txt",
        is_xbrl=False,
    )


@pytest.fixture
def mock_filing_text():
    """Create mock 10-K filing text."""
    return """
<HTML>
<HEAD><TITLE>Apple Inc. 10-K Filing</TITLE></HEAD>
<BODY>
<H1>UNITED STATES SECURITIES AND EXCHANGE COMMISSION</H1>
<H2>Washington, D.C. 20549</H2>
<H3>FORM 10-K</H3>

<BR><BR><B>Item 1. Business</B><BR><BR>
Apple Inc. designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories, and sells a variety of related services.

<BR><BR><B>Item 1A. Risk Factors</B><BR><BR>
Our business, operating results and financial condition depend on global economic conditions.

<BR><BR><B>Item 7. Management's Discussion and Analysis</B><BR><BR>
Fiscal 2020 was a record year for Apple with revenue of $274.5 billion.

<BR><BR><B>Item 8. Financial Statements</B><BR><BR>
See consolidated financial statements on page F-1.

</BODY>
</HTML>
"""


class TestCompanyRepository:
    """Tests for CompanyRepository."""

    def test_upsert_company(self, repositories, mock_company):
        """Test inserting a new company."""
        company_id = repositories["company"].upsert(mock_company)
        assert company_id > 0

        # Verify it was inserted
        stored = repositories["company"].get_by_cik("0000320193")
        assert stored is not None
        assert stored["name"] == "Apple Inc."
        assert stored["ticker"] == "AAPL"

    def test_upsert_updates_existing(self, repositories, mock_company):
        """Test that upsert updates an existing company."""
        # Insert initial company
        repositories["company"].upsert(mock_company)

        # Update with new data
        updated_company = CompanyModel(
            cik="0000320193",
            name="Apple Inc. (Updated)",
            ticker="AAPL",
            sic="3600",
            industry="Consumer Electronics",
            state="CA",
        )
        repositories["company"].upsert(updated_company)

        # Verify update
        stored = repositories["company"].get_by_cik("0000320193")
        assert stored["name"] == "Apple Inc. (Updated)"

    def test_exists_by_cik(self, repositories, mock_company):
        """Test exists_by_cik method."""
        # Should not exist initially
        assert not repositories["company"].exists_by_cik("0000320193")

        # Insert and verify exists
        repositories["company"].upsert(mock_company)
        assert repositories["company"].exists_by_cik("0000320193")

    def test_get_nonexistent_company(self, repositories):
        """Test getting a company that doesn't exist."""
        result = repositories["company"].get_by_cik("0000000000")
        assert result is None


class TestFilingRepository:
    """Tests for FilingRepository."""

    def test_upsert_filing(self, repositories, mock_filing):
        """Test inserting a new filing."""
        filing_id = repositories["filing"].upsert(mock_filing)
        assert filing_id > 0

        # Verify it was inserted
        stored = repositories["filing"].get_by_accession_no("000032019321000099")
        assert stored is not None
        assert stored["filing_type"] == "10-K"
        assert stored["cik"] == "0000320193"

    def test_upsert_updates_existing(self, repositories, mock_filing):
        """Test that upsert updates an existing filing."""
        # Insert initial filing
        repositories["filing"].upsert(mock_filing)

        # Update with new data
        updated_filing = FilingModel(
            accession_no="000032019321000099",
            cik="0000320193",
            filing_type="10-K (Updated)",
            filing_date="2021-01-29",
            accepted_date="2021-01-29T16:30:00",
            file_url="https://updated.url",
            is_xbrl=True,
        )
        repositories["filing"].upsert(updated_filing)

        # Verify update
        stored = repositories["filing"].get_by_accession_no("000032019321000099")
        assert stored["filing_type"] == "10-K (Updated)"
        assert stored["is_xbrl"] == 1  # SQLite stores booleans as integers

    def test_normalize_accession(self, repositories):
        """Test that accession numbers are normalized (dashes removed)."""
        filing_with_dashes = FilingModel(
            accession_no="0000320193-21-000099",  # With dashes
            cik="0000320193",
            filing_type="10-K",
            filing_date="2021-01-29",
        )
        repositories["filing"].upsert(filing_with_dashes)

        # Should be retrievable with or without dashes
        stored = repositories["filing"].get_by_accession_no("000032019321000099")
        assert stored is not None

    def test_exists_by_accession_no(self, repositories, mock_filing):
        """Test exists_by_accession_no method."""
        # Should not exist initially
        assert not repositories["filing"].exists_by_accession_no("000032019321000099")

        # Insert and verify exists
        repositories["filing"].upsert(mock_filing)
        assert repositories["filing"].exists_by_accession_no("000032019321000099")

    def test_get_nonexistent_filing(self, repositories):
        """Test getting a filing that doesn't exist."""
        result = repositories["filing"].get_by_accession_no("000000000000000000")
        assert result is None


class TestFilingItemRepository:
    """Tests for FilingItemRepository."""

    def test_upsert_item(self, repositories, mock_filing):
        """Test inserting a new filing item."""
        filing_id = repositories["filing"].upsert(mock_filing)

        item = FilingItemModel(
            filing_id=filing_id,
            accession_no="000032019321000099",
            item_label="Item 1. Business",
            item_content="Apple Inc. designs, manufactures...",
            item_type="text",
        )
        item_id = repositories["item"].upsert(item)
        assert item_id > 0

        # Verify it was inserted
        stored_items = repositories["item"].get_by_filing_id(filing_id)
        assert len(stored_items) == 1
        assert stored_items[0]["item_label"] == "Item 1. Business"

    def test_get_by_accession_no(self, repositories, mock_filing):
        """Test getting items by accession number."""
        filing_id = repositories["filing"].upsert(mock_filing)

        item = FilingItemModel(
            filing_id=filing_id,
            accession_no="000032019321000099",
            item_label="Item 1. Business",
            item_content="Test content",
            item_type="text",
        )
        repositories["item"].upsert(item)

        # Should be retrievable by accession number
        stored_items = repositories["item"].get_by_accession_no("000032019321000099")
        assert len(stored_items) == 1

    def test_bulk_insert(self, repositories, mock_filing):
        """Test bulk insert of filing items."""
        filing_id = repositories["filing"].upsert(mock_filing)

        items = [
            FilingItemModel(
                filing_id=filing_id,
                accession_no="000032019321000099",
                item_label=f"Item {i}. Test",
                item_content=f"Content {i}",
                item_type="text",
            )
            for i in range(1, 6)
        ]

        count = repositories["item"].bulk_insert(items)
        assert count == 5

        # Verify all were inserted
        stored_items = repositories["item"].get_by_filing_id(filing_id)
        assert len(stored_items) == 5

    def test_bulk_insert_empty(self, repositories):
        """Test bulk insert with empty list."""
        count = repositories["item"].bulk_insert([])
        assert count == 0


class TestSECDatabase:
    """Tests for SECDatabase integration."""

    def test_init_creates_tables(self, db_path):
        """Test that SECDatabase initializes the database correctly."""
        db = SECDatabase(db_path)
        try:
            # Check that tables exist
            cursor = db.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            assert "companies" in tables
            assert "filings" in tables
            assert "filing_items" in tables
        finally:
            db.close()

    def test_context_manager(self, db_path):
        """Test SECDatabase context manager."""
        with SECDatabase(db_path) as db:
            assert db.conn is not None
            assert db.companies is not None
            assert db.filings is not None
            assert db.items is not None

    def test_close(self, db_path):
        """Test closing the database."""
        db = SECDatabase(db_path)
        db.close()
        # Connection should be closed
        assert db.conn is None


class TestDeduplicationManager:
    """Tests for DeduplicationManager."""

    def test_mark_and_check_accession(self, conn):
        """Test marking and checking accession numbers."""
        from sec_importer.repository import DeduplicationManager
        dedup = DeduplicationManager(conn)

        accession = "000032019321000099"
        assert not dedup.is_accession_seen(accession)

        dedup.mark_seen_accession(accession)
        assert dedup.is_accession_seen(accession)

    def test_mark_and_check_cik(self, conn):
        """Test marking and checking CIKs."""
        from sec_importer.repository import DeduplicationManager
        dedup = DeduplicationManager(conn)

        cik = "0000320193"
        assert not dedup.is_cik_seen(cik)

        dedup.mark_seen_cik(cik)
        assert dedup.is_cik_seen(cik)

    def test_is_accession_in_db(self, conn, mock_filing):
        """Test checking if accession exists in database."""
        from sec_importer.repository import DeduplicationManager
        dedup = DeduplicationManager(conn)

        # Should not exist initially
        assert not dedup.is_accession_in_db("000032019321000099")

        # Insert and verify exists
        filing_repo = FilingRepository(conn)
        filing_repo.upsert(mock_filing)
        assert dedup.is_accession_in_db("000032019321000099")
