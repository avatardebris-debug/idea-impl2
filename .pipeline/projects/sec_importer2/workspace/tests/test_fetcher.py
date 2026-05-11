"""Tests for SEC Importer 2 fetcher module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import httpx

from sec_importer.fetcher import SECFetcher


class TestSECFetcher:
    """Tests for SECFetcher class."""

    def test_fetch_filings_success(self):
        """Test fetching filings successfully."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "filings": {
                "recent": [
                    {
                        "type": "10-K",
                        "filingDate": "2024-01-01",
                        "accessionNumber": "0001234567-24-000001",
                    }
                ]
            }
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            fetcher = SECFetcher()
            result = fetcher.fetch_filings("AAPL", limit=10)

            assert len(result) == 1
            assert result[0]["type"] == "10-K"
            assert result[0]["filingDate"] == "2024-01-01"

    def test_fetch_filings_http_error(self):
        """Test fetching filings with HTTP error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.side_effect = httpx.HTTPError("HTTP error")

            fetcher = SECFetcher()
            result = fetcher.fetch_filings("AAPL", limit=10)

            assert result == []

    def test_get_cik_from_ticker_success(self):
        """Test getting CIK from ticker successfully."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<cik>0001234567</cik>'

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            fetcher = SECFetcher()
            cik = fetcher.get_cik_from_ticker("AAPL")

            assert cik == "0001234567"

    def test_get_cik_from_ticker_http_error(self):
        """Test getting CIK from ticker with HTTP error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.side_effect = httpx.HTTPError("HTTP error")

            fetcher = SECFetcher()
            cik = fetcher.get_cik_from_ticker("AAPL")

            assert cik is None

    def test_get_company_name_success(self):
        """Test getting company name successfully."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '<name>Test Company Inc.</name>'

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            fetcher = SECFetcher()
            name = fetcher.get_company_name("AAPL")

            assert name == "Test Company Inc."

    def test_get_company_name_http_error(self):
        """Test getting company name with HTTP error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.side_effect = httpx.HTTPError("HTTP error")

            fetcher = SECFetcher()
            name = fetcher.get_company_name("AAPL")

            assert name is None

    def test_rate_limit(self):
        """Test rate limiting."""
        fetcher = SECFetcher(rate_limit_delay=0)
        # Should not raise any exceptions
        fetcher._rate_limit()
