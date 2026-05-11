"""Tests for Forensic Suite CLI module."""

import sys
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from forensic.cli import main


class TestCLI:
    @patch("forensic.cli.ForensicDatabase")
    def test_list_companies(self, mock_db):
        """Test the list_companies command."""
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_companies.return_value = [
            {"ticker": "AAPL", "name": "Apple Inc.", "cik": "0000320193", "sic": "3571", "industry": "Computer Manufacturing", "state": "CA"}
        ]

        with patch("sys.argv", ["forensic", "list-companies"]):
            main()

        mock_db_instance.get_companies.assert_called_once()
        mock_db_instance.close.assert_called_once()

    @patch("forensic.cli.Database")
    def test_get_fraud_scores(self, mock_db):
        """Test the get-fraud-scores command."""
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_fraud_scores.return_value = [
            {"ticker": "AAPL", "fraud_score": 75.5, "risk_level": "high", "filing_date": "2023-01-01", "accession_no": "0000320193-23-000001"}
        ]

        with patch("sys.argv", ["forensic", "get-fraud-scores", "--ticker", "AAPL"]):
            main()

        mock_db_instance.get_fraud_scores.assert_called_once()
        mock_db_instance.close.assert_called_once()

    @patch("forensic.cli.Database")
    def test_get_red_flags(self, mock_db):
        """Test the get-red-flags command."""
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_red_flags.return_value = [
            {"ticker": "AAPL", "category": "accounting", "severity": "high", "description": "Revenue recognition issues", "filing_date": "2023-01-01", "accession_no": "0000320193-23-000001"}
        ]

        with patch("sys.argv", ["forensic", "get-red-flags", "--ticker", "AAPL"]):
            main()

        mock_db_instance.get_red_flags.assert_called_once()
        mock_db_instance.close.assert_called_once()

    @patch("forensic.cli.Database")
    def test_get_capital_flows(self, mock_db):
        """Test the get-capital-flows command."""
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.get_capital_flows.return_value = [
            {"ticker": "AAPL", "period_label": "2023-Q1", "operating_cash_flow": 100.0, "investing_cash_flow": -50.0, "financing_cash_flow": -30.0, "net_change_in_cash": 20.0, "capital_expenditures": 40.0, "free_cash_flow": 60.0, "filing_date": "2023-01-01", "accession_no": "0000320193-23-000001"}
        ]

        with patch("sys.argv", ["forensic", "get-capital-flows", "--ticker", "AAPL"]):
            main()

        mock_db_instance.get_capital_flows.assert_called_once()
        mock_db_instance.close.assert_called_once()
