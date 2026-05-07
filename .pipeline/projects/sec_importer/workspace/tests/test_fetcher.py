"""Tests for the SEC fetcher module."""

import json
import pytest
from unittest.mock import patch, MagicMock
from sec_importer.fetcher import (
    resolve_ticker_to_cik,
    get_cik_submissions,
    get_latest_filing,
    download_filing_text,
)


# --- resolve_ticker_to_cik ---

class TestResolveTickerToCik:
    @patch("sec_importer.fetcher.requests.get")
    def test_resolve_valid_ticker(self, mock_get):
        """Test resolving a valid ticker to CIK."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = """
        <html>
        <table>
          <tr><td><a href="/cgi-bin/browse-edgar?CIK=0000320193&amp;owner=include&amp;count=40">0000320193</a></td></tr>
        </table>
        </html>
        """
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        cik = resolve_ticker_to_cik("AAPL")
        assert cik == "0000320193"

    @patch("sec_importer.fetcher.requests.get")
    def test_resolve_ticker_not_found(self, mock_get):
        """Test ticker not found raises ValueError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><table></table></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ValueError, match="not found"):
            resolve_ticker_to_cik("ZZZZZ")

    @patch("sec_importer.fetcher.requests.get")
    def test_resolve_ticker_http_error(self, mock_get):
        """Test HTTP error raises exception."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_resp

        with pytest.raises(Exception):
            resolve_ticker_to_cik("AAPL")


# --- get_cik_submissions ---

class TestGetCikSubmissions:
    @patch("sec_importer.fetcher.requests.get")
    def test_get_submissions(self, mock_get):
        """Test fetching CIK submissions."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "cik": "0000320193",
            "filings": {
                "recent": {
                    "accessionNo": ["0000320193-21-000099"],
                    "form": ["10-K"],
                    "filingDate": ["2021-01-29"],
                    "acceptanceDateTime": ["20210129162513"],
                    "primaryDoc": ["aapl-20201231.htm"],
                    "primaryDocument": ["aapl-20201231.htm"],
                }
            },
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        data = get_cik_submissions("0000320193")
        assert data["cik"] == "0000320193"
        assert data["filings"]["recent"]["form"] == ["10-K"]


# --- get_latest_filing ---

class TestGetLatestFiling:
    @patch("sec_importer.fetcher.get_cik_submissions")
    def test_get_latest_10k(self, mock_submissions):
        """Test getting latest 10-K filing."""
        mock_submissions.return_value = {
            "cik": "0000320193",
            "filings": {
                "recent": {
                    "accessionNo": ["0000320193-21-000099", "0000320193-21-000030"],
                    "form": ["10-K", "10-Q"],
                    "filingDate": ["2021-01-29", "2021-04-28"],
                    "acceptanceDateTime": ["20210129162513", "20210428161500"],
                    "primaryDoc": ["aapl-20201231.htm", "aapl-20210327.htm"],
                    "primaryDocument": ["aapl-20201231.htm", "aapl-20210327.htm"],
                }
            },
        }

        filing = get_latest_filing("0000320193", "10-K")
        assert filing["accession_no"] == "000032019321000099"
        assert filing["filing_type"] == "10-K"
        assert filing["filing_date"] == "2021-01-29"

    @patch("sec_importer.fetcher.get_cik_submissions")
    def test_get_latest_filing_not_found(self, mock_submissions):
        """Test no filing of given type raises ValueError."""
        mock_submissions.return_value = {
            "cik": "0000320193",
            "filings": {
                "recent": {
                    "accessionNo": ["0000320193-21-000030"],
                    "form": ["10-Q"],
                    "filingDate": ["2021-04-28"],
                    "acceptanceDateTime": ["20210428161500"],
                    "primaryDoc": ["aapl-20210327.htm"],
                    "primaryDocument": ["aapl-20210327.htm"],
                }
            },
        }

        with pytest.raises(ValueError, match="No 8-K filing found"):
            get_latest_filing("0000320193", "8-K")


# --- download_filing_text ---

class TestDownloadFilingText:
    @patch("sec_importer.fetcher.requests.get")
    def test_download_filing_text(self, mock_get):
        """Test downloading filing text."""
        mock_resp = MagicMock()
        mock_resp.text = "Item 1. Business\nApple Inc. is a technology company..."
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        text = download_filing_text("000032019321000099")
        assert "Item 1. Business" in text

    @patch("sec_importer.fetcher.requests.get")
    def test_download_filing_text_http_error(self, mock_get):
        """Test HTTP error raises exception."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_resp

        with pytest.raises(Exception):
            download_filing_text("000032019321000099")
