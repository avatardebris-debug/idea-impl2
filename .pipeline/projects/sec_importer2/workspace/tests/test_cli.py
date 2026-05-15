"""Tests for SEC Importer 2 CLI module."""

from __future__ import annotations

import argparse
from unittest.mock import patch

from sec_importer.cli.commands import (
    cmd_schedule,
    cmd_import,
    cmd_list,
    cmd_status,
    main,
)


class TestCli:
    """Tests for CLI entry point."""

    @patch("sec_importer.cli.commands.logger")
    def test_cmd_schedule(self, mock_logger):
        """Test cmd_schedule."""
        args = argparse.Namespace(ticker="AAPL", filing_type="10-K", interval="daily", start_date="2023-01-01")
        cmd_schedule(args)
        mock_logger.info.assert_called()

    @patch("sec_importer.cli.commands.get_session")
    @patch("sec_importer.cli.commands.init_db")
    @patch("sec_importer.cli.commands.SECFetcher")
    def test_cmd_import(self, mock_fetcher_cls, mock_init_db, mock_get_session):
        """Test cmd_import."""
        mock_fetcher = mock_fetcher_cls.return_value
        mock_fetcher.get_filings.return_value = []
        args = argparse.Namespace(ticker="AAPL", filing_type="10-K", start_date="2023-01-01", end_date="2023-12-31")
        cmd_import(args)
        mock_fetcher.get_filings.assert_called_once()

    @patch("sec_importer.cli.commands.get_session")
    @patch("sec_importer.cli.commands.init_db")
    def test_cmd_list(self, mock_init_db, mock_get_session):
        """Test cmd_list."""
        mock_session = mock_get_session.return_value
        mock_session.query.return_value.order_by.return_value.all.return_value = []
        args = argparse.Namespace(limit=10)
        cmd_list(args)
        mock_session.query.assert_called()

    @patch("sec_importer.cli.commands.get_session")
    @patch("sec_importer.cli.commands.init_db")
    def test_cmd_status(self, mock_init_db, mock_get_session):
        """Test cmd_status."""
        mock_session = mock_get_session.return_value
        mock_session.query.return_value.count.return_value = 0
        args = argparse.Namespace()
        cmd_status(args)
        mock_session.query.assert_called()
