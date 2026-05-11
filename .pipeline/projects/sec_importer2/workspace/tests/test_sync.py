"""Tests for SEC Importer 2 sync module."""

from __future__ import annotations

import csv
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from sec_importer.sync import run_sync, _load_tickers, _sync_ticker
from sec_importer.storage import init_db
from sec_importer.fetcher import SECFetcher
from sec_importer.models import Filing


class TestLoadTickers:
    """Tests for _load_tickers function."""

    def test_load_tickers_from_csv(self, tmp_path):
        """Test loading tickers from a CSV file."""
        tickers_file = tmp_path / "tickers.csv"
        with open(tickers_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["AAPL"])
            writer.writerow(["MSFT"])
            writer.writerow(["GOOGL"])

        tickers = _load_tickers(str(tickers_file))
        assert tickers == ["AAPL", "MSFT", "GOOGL"]

    def test_load_tickers_empty_file(self, tmp_path):
        """Test loading tickers from an empty CSV file."""
        tickers_file = tmp_path / "empty.csv"
        tickers_file.write_text("")

        tickers = _load_tickers(str(tickers_file))
        assert tickers == []

    def test_load_tickers_nonexistent_file(self):
        """Test loading tickers from a nonexistent file."""
        tickers = _load_tickers("/nonexistent/path/tickers.csv")
        assert tickers == []

    def test_load_tickers_with_whitespace(self, tmp_path):
        """Test loading tickers with whitespace."""
        tickers_file = tmp_path / "whitespace.csv"
        with open(tickers_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["  AAPL  "])
            writer.writerow([""])
            writer.writerow(["  MSFT  "])

        tickers = _load_tickers(str(tickers_file))
        assert tickers == ["AAPL", "MSFT"]


class TestSyncTicker:
    """Tests for _sync_ticker function."""

    def test_sync_ticker_no_filings(self):
        """Test syncing a ticker with no filings."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = None
        session.execute.return_value.scalars.return_value.all.return_value = []

        fetcher = MagicMock(spec=SECFetcher)
        fetcher.fetch_filings.return_value = []
        fetcher.get_cik_from_ticker.return_value = "12345"
        fetcher.get_company_name.return_value = "Test Company"

        result = _sync_ticker(session, fetcher, "AAPL", limit=100)
        assert result["ticker"] == "AAPL"
        assert result["new"] == 0
        assert result["skipped"] == 0

    def test_sync_ticker_with_filings(self):
        """Test syncing a ticker with new filings."""
        session = MagicMock()
        session.execute.return_value.scalar_one_or_none.return_value = None
        session.execute.return_value.scalars.return_value.all.return_value = []
        session.execute.return_value.scalar_one_or_none.return_value = None

        fetcher = MagicMock(spec=SECFetcher)
        fetcher.fetch_filings.return_value = [
            {
                "type": "10-K",
                "filingDate": "2024-01-01",
                "accessionNumber": "0001234567-24-000001",
            }
        ]
        fetcher.get_cik_from_ticker.return_value = "12345"
        fetcher.get_company_name.return_value = "Test Company"

        result = _sync_ticker(session, fetcher, "AAPL", limit=100)
        assert result["ticker"] == "AAPL"
        assert result["new"] > 0


class TestRunSync:
    """Tests for run_sync function."""

    def test_run_sync_no_tickers(self, tmp_path):
        """Test running sync with no tickers."""
        tickers_file = tmp_path / "empty.csv"
        tickers_file.write_text("")

        summary = run_sync(tickers_file=str(tickers_file))
        assert "error" in summary

    def test_run_sync_with_tickers(self, tmp_path):
        """Test running sync with tickers."""
        tickers_file = tmp_path / "tickers.csv"
        with open(tickers_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["AAPL"])

        with patch("sec_importer.sync.init_db") as mock_init_db, \
             patch("sec_importer.sync.SECFetcher") as mock_fetcher_class, \
             patch("sec_importer.sync.parse_filings") as mock_parse, \
             patch("sec_importer.sync.parse_and_store") as mock_parse_store, \
             patch("sec_importer.sync.count_filings") as mock_count:

            # Setup mocks
            mock_session = MagicMock()
            mock_init_db.return_value.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            mock_session.execute.return_value.scalars.return_value.all.return_value = []

            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value.__enter__.return_value = mock_fetcher
            mock_fetcher.fetch_filings.return_value = [
                {
                    "type": "10-K",
                    "filingDate": "2024-01-01",
                    "accessionNumber": "0001234567-24-000001",
                }
            ]
            mock_fetcher.get_cik_from_ticker.return_value = "12345"
            mock_fetcher.get_company_name.return_value = "Test Company"

            mock_parse.return_value = [
                Filing(
                    ticker="AAPL",
                    filing_type="10-K",
                    filing_date="2024-01-01",
                    accession_number="0001234567-24-000001",
                )
            ]
            mock_count.return_value = 1

            summary = run_sync(tickers_file=str(tickers_file))
            assert "tickers" in summary
            assert "total_new" in summary
            assert "total_skipped" in summary
