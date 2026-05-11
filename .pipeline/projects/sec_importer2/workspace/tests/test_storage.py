"""Tests for SEC Importer 2 storage module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sec_importer.storage import (
    init_db,
    get_session,
    upsert_company,
    get_last_sync_date,
    get_existing_accession_numbers,
    insert_filings,
    count_filings,
    upsert_filing_content,
    get_filing_content,
    get_filing_content_data,
    get_all_filing_contents,
)
from sec_importer.models import Filing, Company, FilingContent


class TestInitDb:
    """Tests for init_db function."""

    def test_init_db_creates_tables(self, tmp_path):
        """Test that init_db creates tables."""
        db_path = str(tmp_path / "test.db")
        session_factory = init_db(db_path)
        assert session_factory is not None

    def test_init_db_default_path(self):
        """Test init_db with default path."""
        session_factory = init_db()
        assert session_factory is not None


class TestUpsertCompany:
    """Tests for upsert_company function."""

    def test_upsert_company_new(self):
        """Test inserting a new company."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = None

        company = upsert_company(session, ticker="AAPL", name="Apple Inc.", cik="12345")
        assert company.ticker == "AAPL"
        assert company.name == "Apple Inc."
        assert company.cik == "12345"

    def test_upsert_company_existing(self):
        """Test updating an existing company."""
        session = MagicMock()
        existing_company = Company(ticker="AAPL", name="Old Name", cik="11111")
        session.execute.return_value.scalar_one_or_none.return_value = existing_company

        company = upsert_company(session, ticker="AAPL", name="New Name", cik="22222")
        assert company.ticker == "AAPL"
        assert company.name == "New Name"
        assert company.cik == "22222"


class TestGetLastSyncDate:
    """Tests for get_last_sync_date function."""

    def test_get_last_sync_date_with_data(self):
        """Test getting last sync date with data."""
        session = MagicMock()
        mock_date = MagicMock()
        mock_date.strftime.return_value = "2024-01-01"
        session.execute.return_value.scalar_one_or_none.return_value = mock_date

        result = get_last_sync_date(session, "AAPL")
        assert result == "2024-01-01"

    def test_get_last_sync_date_no_data(self):
        """Test getting last sync date with no data."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = None

        result = get_last_sync_date(session, "AAPL")
        assert result is None


class TestGetExistingAccessionNumbers:
    """Tests for get_existing_accession_numbers function."""

    def test_get_existing_accession_numbers(self):
        """Test getting existing accession numbers."""
        session = MagicMock()
        session.execute.return_value.scalars.return_value.all.return_value = [
            "0001234567-24-000001",
            "0001234567-24-000002",
        ]

        result = get_existing_accession_numbers(session, "AAPL")
        assert result == {"0001234567-24-000001", "0001234567-24-000002"}


class TestInsertFilings:
    """Tests for insert_filings function."""

    def test_insert_filings(self):
        """Test inserting filings."""
        session = MagicMock()
        filings = [
            Filing(ticker="AAPL", filing_type="10-K", filing_date="2024-01-01", accession_number="0001234567-24-000001"),
            Filing(ticker="AAPL", filing_type="10-Q", filing_date="2024-04-01", accession_number="0001234567-24-000002"),
        ]

        result = insert_filings(session, filings)
        assert result == 2

    def test_insert_filings_deduplication(self):
        """Test that insert_filings deduplicates by accession_number."""
        session = MagicMock()
        filings = [
            Filing(ticker="AAPL", filing_type="10-K", filing_date="2024-01-01", accession_number="0001234567-24-000001"),
            Filing(ticker="AAPL", filing_type="10-Q", filing_date="2024-04-01", accession_number="0001234567-24-000001"),  # Duplicate
        ]

        result = insert_filings(session, filings)
        assert result == 1


class TestCountFilings:
    """Tests for count_filings function."""

    def test_count_filings_with_data(self):
        """Test counting filings with data."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = 10

        result = count_filings(session, "AAPL")
        assert result == 10

    def test_count_filings_no_data(self):
        """Test counting filings with no data."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = None

        result = count_filings(session, "AAPL")
        assert result == 0


class TestUpsertFilingContent:
    """Tests for upsert_filing_content function."""

    def test_upsert_filing_content_new(self):
        """Test inserting new filing content."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = None

        content = upsert_filing_content(session, 1, "xbrl", {"fact1": "value1"})
        assert content.content_type == "xbrl"
        assert content.content_data == {"fact1": "value1"}

    def test_upsert_filing_content_existing(self):
        """Test updating existing filing content."""
        session = MagicMock()
        existing_content = FilingContent(filing_id=1, content_type="xbrl", content_data={"old": "data"})
        session.execute.return_value.scalar_one_or_none.return_value = existing_content

        content = upsert_filing_content(session, 1, "xbrl", {"new": "data"})
        assert content.content_type == "xbrl"
        assert content.content_data == {"new": "data"}


class TestGetFilingContent:
    """Tests for get_filing_content function."""

    def test_get_filing_content_with_data(self):
        """Test getting filing content with data."""
        session = MagicMock()
        mock_content = FilingContent(filing_id=1, content_type="xbrl", content_data={"fact1": "value1"})
        session.execute.return_value.scalar_one_or_none.return_value = mock_content

        result = get_filing_content(session, 1)
        assert result is not None
        assert result.content_type == "xbrl"

    def test_get_filing_content_no_data(self):
        """Test getting filing content with no data."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = None

        result = get_filing_content(session, 1)
        assert result is None


class TestGetFilingContentData:
    """Tests for get_filing_content_data function."""

    def test_get_filing_content_data_with_data(self):
        """Test getting filing content data with data."""
        session = MagicMock()
        mock_content = FilingContent(filing_id=1, content_type="xbrl", content_data={"fact1": "value1"})
        session.execute.return_value.scalar_one_or_none.return_value = mock_content

        result = get_filing_content_data(session, 1)
        assert result == {"fact1": "value1"}

    def test_get_filing_content_data_no_data(self):
        """Test getting filing content data with no data."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = None

        result = get_filing_content_data(session, 1)
        assert result == {}


class TestGetAllFilingContents:
    """Tests for get_all_filing_contents function."""

    def test_get_all_filing_contents(self):
        """Test getting all filing contents."""
        session = MagicMock()
        mock_contents = [
            FilingContent(filing_id=1, content_type="xbrl", content_data={"fact1": "value1"}),
            FilingContent(filing_id=2, content_type="html", content_data={"html": "data"}),
        ]
        session.execute.return_value.scalars.return_value.all.return_value = mock_contents

        result = get_all_filing_contents(session)
        assert len(result) == 2
