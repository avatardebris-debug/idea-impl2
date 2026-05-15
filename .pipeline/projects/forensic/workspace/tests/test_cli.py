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
    @patch("forensic.cli.ForensicPipeline")
    def test_ingest(self, mock_pipeline_cls):
        """Test the ingest command."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_result = MagicMock()
        mock_result.item_count = 10
        mock_result.ticker = "AAPL"
        mock_result.cik = "320193"
        mock_result.filing_type = "10-K"
        mock_result.filing_date = "2023-01-01"
        mock_pipeline.ingest_filing.return_value = mock_result

        with patch("sys.argv", ["forensic", "ingest", "--ticker", "AAPL"]):
            main()

        mock_pipeline.ingest_filing.assert_called_once_with("AAPL", "10-K")

    @patch("forensic.cli.ForensicPipeline")
    def test_analyze(self, mock_pipeline_cls):
        """Test the analyze command."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_result = MagicMock()
        mock_result.fraud_risk_score = 50.0
        mock_result.red_flags = []
        mock_pipeline.analyze_filing.return_value = mock_result

        with patch("sys.argv", ["forensic", "analyze", "--ticker", "AAPL"]):
            main()

        mock_pipeline.analyze_filing.assert_called_once_with("AAPL")

    @patch("forensic.cli.ForensicPipeline")
    def test_report(self, mock_pipeline_cls):
        """Test the report command."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_report = MagicMock()
        mock_report.overall_risk = "medium"
        mock_report.risk_score = 50.0
        mock_report.recommendations = []
        mock_pipeline.generate_report.return_value = mock_report

        with patch("sys.argv", ["forensic", "report", "--ticker", "AAPL"]):
            main()

        mock_pipeline.generate_report.assert_called_once_with("AAPL")

    @patch("forensic.cli.ForensicPipeline")
    def test_capital(self, mock_pipeline_cls):
        """Test the capital command."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline
        mock_result = MagicMock()
        mock_result.capital_flows = {"summary": "test"}
        mock_result.advanced_flags = {}
        mock_pipeline.analyze_filing.return_value = mock_result

        with patch("sys.argv", ["forensic", "capital", "--ticker", "AAPL"]):
            main()

        mock_pipeline.analyze_filing.assert_called_once_with("AAPL")
