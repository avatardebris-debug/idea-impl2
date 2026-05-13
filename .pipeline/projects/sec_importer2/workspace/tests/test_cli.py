"""Tests for SEC Importer 2 CLI module."""

from __future__ import annotations

import csv
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from sec_importer.cli import (
    cli,
    sync_cmd,
    scheduler_start,
    scheduler_run_now,
    scheduler_show_config,
)


class TestSyncCmd:
    """Tests for sync_cmd function."""

    def test_sync_cmd_no_tickers_file(self):
        """Test sync_cmd with no tickers file."""
        with patch("sec_importer.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = {"error": "No tickers file found"}
            result = sync_cmd(tickers_file=None, limit=10)
            assert result == {"error": "No tickers file found"}

    def test_sync_cmd_with_tickers_file(self, tmp_path):
        """Test sync_cmd with tickers file."""
        tickers_file = tmp_path / "tickers.csv"
        with open(tickers_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["AAPL"])

        with patch("sec_importer.cli.run_sync") as mock_run_sync:
            mock_run_sync.return_value = {"tickers": 1, "total_new": 5}
            result = sync_cmd(tickers_file=str(tickers_file), limit=10)
            assert result == {"tickers": 1, "total_new": 5}


class TestSchedulerStart:
    """Tests for scheduler_start function."""

    def test_scheduler_start(self):
        """Test scheduler_start function."""
        with patch("sec_importer.cli.Scheduler") as mock_scheduler:
            mock_instance = MagicMock()
            mock_scheduler.return_value = mock_instance
            result = scheduler_start()
            mock_instance.start.assert_called_once()
            assert result is None


class TestSchedulerRunNow:
    """Tests for scheduler_run_now function."""

    def test_scheduler_run_now(self):
        """Test scheduler_run_now function."""
        with patch("sec_importer.cli.Scheduler") as mock_scheduler:
            mock_instance = MagicMock()
            mock_instance.run_now.return_value = {"total_new": 5}
            mock_scheduler.return_value = mock_instance
            result = scheduler_run_now()
            assert result == {"total_new": 5}


class TestSchedulerShowConfig:
    """Tests for scheduler_show_config function."""

    def test_scheduler_show_config(self):
        """Test scheduler_show_config function."""
        with patch("sec_importer.cli.SchedulerConfig") as mock_config:
            mock_config_instance = MagicMock()
            mock_config_instance.to_dict.return_value = {
                "tickers_file": "tickers.csv",
                "limit_per_ticker": 10,
            }
            mock_config.from_env.return_value = mock_config_instance
            result = scheduler_show_config()
            assert result is None


class TestCli:
    """Tests for CLI entry point."""

    def test_cli_sync(self):
        """Test CLI sync command."""
        with patch("sec_importer.cli.sync_cmd") as mock_sync:
            mock_sync.return_value = {"total_new": 5}
            with patch("sys.argv", ["sec-importer", "sync"]):
                result = cli()
                mock_sync.assert_called_once()
                assert result == {"total_new": 5}

    def test_cli_scheduler_start(self):
        """Test CLI scheduler start command."""
        with patch("sec_importer.cli.scheduler_start") as mock_start:
            mock_start.return_value = None
            with patch("sys.argv", ["sec-importer", "scheduler", "start"]):
                result = cli()
                mock_start.assert_called_once()
                assert result is None

    def test_cli_scheduler_run_now(self):
        """Test CLI scheduler run-now command."""
        with patch("sec_importer.cli.scheduler_run_now") as mock_run_now:
            mock_run_now.return_value = {"total_new": 5}
            with patch("sys.argv", ["sec-importer", "scheduler", "run-now"]):
                result = cli()
                mock_run_now.assert_called_once()
                assert result == {"total_new": 5}

    def test_cli_scheduler_show_config(self):
        """Test CLI scheduler show-config command."""
        with patch("sec_importer.cli.scheduler_show_config") as mock_show_config:
            mock_show_config.return_value = None
            with patch("sys.argv", ["sec-importer", "scheduler", "show-config"]):
                result = cli()
                mock_show_config.assert_called_once()
                assert result is None
