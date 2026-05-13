"""Tests for SEC Importer 2 CLI module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from sec_importer.cli import cli


class TestMain:
    """Tests for main CLI function."""

    def test_main_help(self):
        """Test that main shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SEC Importer 2" in result.output

    def test_main_sync_help(self):
        """Test that main sync subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["sync", "--help"])
        assert result.exit_code == 0
        assert "tickers-file" in result.output

    def test_main_list_help(self):
        """Test that main list subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--help"])
        assert result.exit_code == 0
        assert "ticker" in result.output.lower()

    def test_main_add_ticker_help(self):
        """Test that main add-ticker subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add-ticker", "--help"])
        assert result.exit_code == 0

    def test_main_stats_help(self):
        """Test that main stats subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0

    def test_main_show_help(self):
        """Test that main show subcommand shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "--help"])
        assert result.exit_code == 0


class TestSyncCommand:
    """Tests for sync_command CLI function."""

    def test_sync_command_default(self):
        """Test sync_command with defaults."""
        with patch("sec_importer.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = {
                "total_new": 5,
                "total_skipped": 2,
                "total_filings": 100,
                "tickers": [{"ticker": "AAPL", "new": 5, "skipped": 2}],
            }
            runner = CliRunner()
            result = runner.invoke(cli, ["sync"])
            assert result.exit_code == 0
            assert "Delta-sync complete!" in result.output

    def test_sync_command_with_tickers_file(self, tmp_path):
        """Test sync_command with tickers file."""
        tickers_file = tmp_path / "tickers.csv"
        tickers_file.write_text("ticker\nAAPL\nGOOGL")

        with patch("sec_importer.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = {
                "total_new": 5,
                "total_skipped": 0,
                "total_filings": 50,
                "tickers": [{"ticker": "AAPL", "new": 3, "skipped": 0}, {"ticker": "GOOGL", "new": 2, "skipped": 0}],
            }
            runner = CliRunner()
            result = runner.invoke(cli, ["sync", "--tickers-file", str(tickers_file)])
            assert result.exit_code == 0

    def test_sync_command_with_limit(self):
        """Test sync_command with limit."""
        with patch("sec_importer.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = {
                "total_new": 10,
                "total_skipped": 0,
                "total_filings": 100,
                "tickers": [{"ticker": "AAPL", "new": 10, "skipped": 0}],
            }
            runner = CliRunner()
            result = runner.invoke(cli, ["sync", "--limit", "50"])
            assert result.exit_code == 0

    def test_sync_command_error(self):
        """Test sync_command with error."""
        with patch("sec_importer.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = {"error": "API error"}
            runner = CliRunner()
            result = runner.invoke(cli, ["sync"])
            assert result.exit_code == 1
            assert "Error:" in result.output

    def test_sync_command_exception(self):
        """Test sync_command with exception."""
        with patch("sec_importer.cli.run_sync") as mock_run_sync:
            mock_run_sync.side_effect = Exception("Test error")
            runner = CliRunner()
            result = runner.invoke(cli, ["sync"])
            assert result.exit_code == 1
            assert "Sync failed:" in result.output


class TestListFilingsCommand:
    """Tests for list_filings_command CLI function."""

    def test_list_filings_command(self):
        """Test list_filings_command with data."""
        mock_filing = MagicMock()
        mock_filing.ticker = "AAPL"
        mock_filing.filing_type = "10-K"
        mock_filing.filing_date = "2024-01-01"
        mock_filing.accession_number = "0001234567-24-000001"
        mock_filing.form_description = "Annual report"
        mock_filing.document_url = "https://example.com"

        with patch("sec_importer.cli.init_db") as mock_init_db, \
             patch("sec_importer.cli.query_filings") as mock_query_filings, \
             patch("sec_importer.cli.count_filings") as mock_count_filings:
            mock_session = MagicMock()
            mock_init_db.return_value.return_value = mock_session
            mock_query_filings.return_value = [mock_filing]
            mock_count_filings.return_value = 1

            runner = CliRunner()
            result = runner.invoke(cli, ["list"])
            assert result.exit_code == 0
            assert "AAPL" in result.output
            assert "10-K" in result.output

    def test_list_filings_command_no_filings(self):
        """Test list_filings_command with no filings."""
        with patch("sec_importer.cli.init_db") as mock_init_db, \
             patch("sec_importer.cli.query_filings") as mock_query_filings:
            mock_session = MagicMock()
            mock_init_db.return_value.return_value = mock_session
            mock_query_filings.return_value = []

            runner = CliRunner()
            result = runner.invoke(cli, ["list"])
            assert result.exit_code == 0
            assert "No filings found." in result.output

    def test_list_filings_command_with_ticker(self):
        """Test list_filings_command with ticker filter."""
        mock_filing = MagicMock()
        mock_filing.ticker = "AAPL"
        mock_filing.filing_type = "10-K"
        mock_filing.filing_date = "2024-01-01"
        mock_filing.accession_number = "0001234567-24-000001"
        mock_filing.form_description = "Annual report"
        mock_filing.document_url = "https://example.com"

        with patch("sec_importer.cli.init_db") as mock_init_db, \
             patch("sec_importer.cli.query_filings") as mock_query_filings, \
             patch("sec_importer.cli.count_filings") as mock_count_filings:
            mock_session = MagicMock()
            mock_init_db.return_value.return_value = mock_session
            mock_query_filings.return_value = [mock_filing]
            mock_count_filings.return_value = 1

            runner = CliRunner()
            result = runner.invoke(cli, ["list", "--ticker", "AAPL"])
            assert result.exit_code == 0
            assert "AAPL" in result.output


class TestAddTickerCommand:
    """Tests for add_ticker_command CLI function."""

    def test_add_ticker_command(self, tmp_path):
        """Test add_ticker_command."""
        tickers_file = tmp_path / "tickers.csv"
        tickers_file.write_text("ticker\nGOOGL")

        runner = CliRunner()
        result = runner.invoke(cli, ["add-ticker", "AAPL", "--tickers-file", str(tickers_file)])
        assert result.exit_code == 0
        assert "Added AAPL" in result.output

        # Verify the file was updated
        content = tickers_file.read_text()
        assert "AAPL" in content
        assert "GOOGL" in content

    def test_add_ticker_command_duplicate(self, tmp_path):
        """Test add_ticker_command with duplicate ticker."""
        tickers_file = tmp_path / "tickers.csv"
        tickers_file.write_text("ticker\nAAPL")

        runner = CliRunner()
        result = runner.invoke(cli, ["add-ticker", "AAPL", "--tickers-file", str(tickers_file)])
        assert result.exit_code == 0
        assert "already exists" in result.output

    def test_add_ticker_command_empty(self):
        """Test add_ticker_command with empty ticker."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add-ticker", ""])
        assert result.exit_code == 1
        assert "Error: Ticker cannot be empty." in result.output

    def test_add_ticker_command_uppercase(self, tmp_path):
        """Test add_ticker_command converts to uppercase."""
        tickers_file = tmp_path / "tickers.csv"
        tickers_file.write_text("ticker\n")

        runner = CliRunner()
        result = runner.invoke(cli, ["add-ticker", "aapl", "--tickers-file", str(tickers_file)])
        assert result.exit_code == 0
        content = tickers_file.read_text()
        assert "AAPL" in content


class TestStatsCommand:
    """Tests for stats_command CLI function."""

    def test_stats_command(self):
        """Test stats_command with data."""
        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = 100

        with patch("sec_importer.cli.init_db") as mock_init_db, \
             patch("sec_importer.cli.count_filings") as mock_count_filings:
            mock_init_db.return_value.return_value = mock_session
            mock_count_filings.return_value = 100

            runner = CliRunner()
            result = runner.invoke(cli, ["stats"])
            assert result.exit_code == 0
            assert "Total filings: 100" in result.output

    def test_stats_command_with_ticker(self):
        """Test stats_command with ticker filter."""
        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = 50

        with patch("sec_importer.cli.init_db") as mock_init_db, \
             patch("sec_importer.cli.count_filings") as mock_count_filings:
            mock_init_db.return_value.return_value = mock_session
            mock_count_filings.return_value = 50

            runner = CliRunner()
            result = runner.invoke(cli, ["stats", "--ticker", "AAPL"])
            assert result.exit_code == 0
            assert "Filtered by ticker: AAPL" in result.output

    def test_stats_command_no_filings(self):
        """Test stats_command with no filings."""
        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = 0

        with patch("sec_importer.cli.init_db") as mock_init_db, \
             patch("sec_importer.cli.count_filings") as mock_count_filings:
            mock_init_db.return_value.return_value = mock_session
            mock_count_filings.return_value = 0

            runner = CliRunner()
            result = runner.invoke(cli, ["stats"])
            assert result.exit_code == 0
            assert "Total filings: 0" in result.output


class TestShowFilingCommand:
    """Tests for show_filing_command CLI function."""

    def test_show_filing_command(self):
        """Test show_filing_command with data."""
        mock_filing = MagicMock()
        mock_filing.id = 1
        mock_filing.ticker = "AAPL"
        mock_filing.filing_type = "10-K"
        mock_filing.filing_date = "2024-01-01"
        mock_filing.accession_number = "0001234567-24-000001"
        mock_filing.form_description = "Annual report"
        mock_filing.document_url = "https://example.com"

        mock_content = MagicMock()
        mock_content.content_type = "xbrl"
        mock_content.parse_status = "success"
        mock_content.content_data = '{"key_metrics": {"revenue": {"value": "100"}}}'

        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_filing

        with patch("sec_importer.cli.init_db") as mock_init_db, \
             patch("sec_importer.cli.FilingContent") as mock_filing_content_class:
            mock_init_db.return_value.return_value = mock_session
            mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_content]

            runner = CliRunner()
            result = runner.invoke(cli, ["show", "1"])
            assert result.exit_code == 0
            assert "AAPL" in result.output
            assert "10-K" in result.output

    def test_show_filing_command_not_found(self):
        """Test show_filing_command with non-existent filing."""
        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        with patch("sec_importer.cli.init_db") as mock_init_db:
            mock_init_db.return_value.return_value = mock_session

            runner = CliRunner()
            result = runner.invoke(cli, ["show", "999"])
            assert result.exit_code == 0
            assert "not found" in result.output

    def test_show_filing_command_no_content(self):
        """Test show_filing_command with no content."""
        mock_filing = MagicMock()
        mock_filing.id = 1
        mock_filing.ticker = "AAPL"
        mock_filing.filing_type = "10-K"
        mock_filing.filing_date = "2024-01-01"
        mock_filing.accession_number = "0001234567-24-000001"
        mock_filing.form_description = "Annual report"
        mock_filing.document_url = "https://example.com"

        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_filing

        with patch("sec_importer.cli.init_db") as mock_init_db:
            mock_init_db.return_value.return_value = mock_session
            mock_session.execute.return_value.scalars.return_value.all.return_value = []

            runner = CliRunner()
            result = runner.invoke(cli, ["show", "1"])
            assert result.exit_code == 0
            assert "No parsed content available" in result.output


class TestCliIntegration:
    """Integration tests for CLI."""

    def test_cli_help(self):
        """Test CLI help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SEC Importer 2" in result.output

    def test_cli_sync_help(self):
        """Test CLI sync help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["sync", "--help"])
        assert result.exit_code == 0

    def test_cli_list_help(self):
        """Test CLI list help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--help"])
        assert result.exit_code == 0

    def test_cli_add_ticker_help(self):
        """Test CLI add-ticker help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add-ticker", "--help"])
        assert result.exit_code == 0

    def test_cli_stats_help(self):
        """Test CLI stats help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0

    def test_cli_show_help(self):
        """Test CLI show help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "--help"])
        assert result.exit_code == 0
