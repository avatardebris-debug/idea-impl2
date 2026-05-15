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
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "filings": {
                "recent": {
                    "accessionNumber": ["0001234567-24-000001"],
                    "filingDate": ["2024-01-01"],
                    "form": ["10-K"],
                }
            }
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = mock_response

            fetcher = SECFetcher(base_delay=0.001)
            result = fetcher.fetch_filings(cik="12345", limit=10)

            assert len(result) == 1
            assert result[0]["form"] == "10-K"
            assert result[0]["filingDate"] == "2024-01-01"

    def test_fetch_filings_http_error(self):
        """Test fetching filings with HTTP error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.side_effect = httpx.HTTPError("HTTP error")

            fetcher = SECFetcher(base_delay=0.001)
            result = fetcher.fetch_filings("AAPL", limit=10)

            assert result == []

    def test_get_cik_from_ticker_success(self):
        """Test getting CIK from ticker successfully."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.json.return_value = {"cik": 1234567}

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = mock_response

            fetcher = SECFetcher(base_delay=0.001)
            cik = fetcher.get_cik_from_ticker("AAPL")

            assert cik == "0001234567"

    def test_get_cik_from_ticker_http_error(self):
        """Test getting CIK from ticker with HTTP error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.side_effect = httpx.HTTPError("HTTP error")

            fetcher = SECFetcher(base_delay=0.001)
            cik = fetcher.get_cik_from_ticker("AAPL")

            assert cik is None

    def test_fetch_filings_no_cik_found(self):
        """Test fetching filings when CIK lookup fails."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.side_effect = httpx.HTTPError("HTTP error")

            fetcher = SECFetcher(base_delay=0.001)
            result = fetcher.fetch_filings("INVALID")

            assert result == []

    def test_fetch_filings_empty_response(self):
        """Test fetching filings when SEC returns no filings."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.json.return_value = {"filings": {"recent": {}}}

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = mock_response

            fetcher = SECFetcher(base_delay=0.001)
            result = fetcher.fetch_filings(cik="12345", limit=10)

            assert result == []
