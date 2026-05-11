"""Tests for SEC Importer 2 parser module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from sec_importer.parser import parse_filings, _parse_single_filing, parse_and_store
from sec_importer.models import Filing


class TestParseFilings:
    """Tests for parse_filings function."""

    def test_parse_filings_empty(self):
        """Test parsing empty filings list."""
        result = parse_filings([])
        assert result == []

    def test_parse_filings_single(self):
        """Test parsing a single filing."""
        raw_filings = [
            {
                "type": "10-K",
                "filingDate": "2024-01-01",
                "accessionNumber": "0001234567-24-000001",
                "ticker": "AAPL",
                "documentUrl": "https://example.com/filing.html",
                "formDescription": "Annual report",
                "acceptedDate": "2024-01-01T12:00:00",
                "fillUrl": "https://example.com/fill",
            }
        ]
        result = parse_filings(raw_filings)
        assert len(result) == 1
        assert isinstance(result[0], Filing)
        assert result[0].ticker == "AAPL"
        assert result[0].filing_type == "10-K"
        assert result[0].filing_date == "2024-01-01"
        assert result[0].accession_number == "0001234567-24-000001"

    def test_parse_filings_multiple(self):
        """Test parsing multiple filings."""
        raw_filings = [
            {
                "type": "10-K",
                "filingDate": "2024-01-01",
                "accessionNumber": "0001234567-24-000001",
            },
            {
                "type": "10-Q",
                "filingDate": "2024-04-01",
                "accessionNumber": "0001234567-24-000002",
            },
        ]
        result = parse_filings(raw_filings)
        assert len(result) == 2

    def test_parse_filings_invalid(self):
        """Test parsing invalid filing data."""
        raw_filings = [
            {
                "type": None,
                "filingDate": None,
                "accessionNumber": None,
            }
        ]
        result = parse_filings(raw_filings)
        assert len(result) == 1
        assert result[0].filing_type is None
        assert result[0].filing_date is None
        assert result[0].accession_number is None


class TestParseSingleFiling:
    """Tests for _parse_single_filing function."""

    def test_parse_single_filing_valid(self):
        """Test parsing a single valid filing."""
        raw = {
            "type": "10-K",
            "filingDate": "2024-01-01",
            "accessionNumber": "0001234567-24-000001",
            "ticker": "AAPL",
            "documentUrl": "https://example.com/filing.html",
            "formDescription": "Annual report",
            "acceptedDate": "2024-01-01T12:00:00",
            "fillUrl": "https://example.com/fill",
        }
        result = _parse_single_filing(raw)
        assert result is not None
        assert isinstance(result, Filing)
        assert result.ticker == "AAPL"
        assert result.filing_type == "10-K"
        assert result.filing_date == "2024-01-01"
        assert result.accession_number == "0001234567-24-000001"

    def test_parse_single_filing_missing_fields(self):
        """Test parsing a filing with missing fields."""
        raw = {
            "type": "10-K",
            "filingDate": "2024-01-01",
            "accessionNumber": "0001234567-24-000001",
        }
        result = _parse_single_filing(raw)
        assert result is not None
        assert result.ticker == ""
        assert result.document_url == ""
        assert result.form_description == ""
        assert result.accepted_date == ""
        assert result.fill_url == ""

    def test_parse_single_filing_invalid(self):
        """Test parsing an invalid filing."""
        raw = None
        result = _parse_single_filing(raw)
        assert result is None


class TestParseAndStore:
    """Tests for parse_and_store function."""

    def test_parse_and_store_xbrl(self):
        """Test parsing and storing XBRL content."""
        session = MagicMock()
        filing = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="0001234567-24-000001",
        )

        result = parse_and_store(session, filing, content_type="xbrl")
        assert result["status"] == "success"
        assert "sections" in result

    def test_parse_and_store_html(self):
        """Test parsing and storing HTML content."""
        session = MagicMock()
        filing = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="0001234567-24-000001",
        )

        result = parse_and_store(session, filing, content_type="html")
        assert result["status"] == "success"
        assert "sections" in result

    def test_parse_and_store_invalid_content_type(self):
        """Test parsing with invalid content type."""
        session = MagicMock()
        filing = Filing(
            ticker="AAPL",
            filing_type="10-K",
            filing_date="2024-01-01",
            accession_number="0001234567-24-000001",
        )

        result = parse_and_store(session, filing, content_type="invalid")
        assert result["status"] == "failed"
        assert "error" in result
