"""Tests for SEC Importer 2 scheduler module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sec_importer.scheduler import (
    SchedulerConfig,
    Scheduler,
    start_scheduler,
    run_now,
    show_config,
)


class TestSchedulerConfig:
    """Tests for SchedulerConfig dataclass."""

    def test_scheduler_config_default_values(self):
        """Test SchedulerConfig with default values."""
        config = SchedulerConfig()
        assert config.mode == "apscheduler"
        assert config.sync_hour == 2
        assert config.sync_minute == 0
        assert config.timezone == "UTC"
        assert config.cron_expression == "0 2 * * *"
        assert config.run_once is False
        assert config.tickers_file == "sec_importer/tickers.csv"
        assert config.limit_per_ticker == 100
        assert config.db_path == "sec_importer.db"

    def test_scheduler_config_custom_values(self):
        """Test SchedulerConfig with custom values."""
        config = SchedulerConfig(
            mode="cron",
            sync_hour=3,
            sync_minute=30,
            timezone="America/New_York",
            cron_expression="0 3 * * *",
            run_once=True,
            tickers_file="/path/to/tickers.csv",
            limit_per_ticker=50,
            db_path="/path/to/db.sqlite",
        )
        assert config.mode == "cron"
        assert config.sync_hour == 3
        assert config.sync_minute == 30
        assert config.timezone == "America/New_York"
        assert config.cron_expression == "0 3 * * *"
        assert config.run_once is True
        assert config.tickers_file == "/path/to/tickers.csv"
        assert config.limit_per_ticker == 50
        assert config.db_path == "/path/to/db.sqlite"

    def test_scheduler_config_from_env(self, monkeypatch):
        """Test SchedulerConfig.from_env with environment variables."""
        monkeypatch.setenv("SCHEDULER_MODE", "cron")
        monkeypatch.setenv("SCHEDULER_SYNC_HOUR", "3")
        monkeypatch.setenv("SCHEDULER_SYNC_MINUTE", "30")
        monkeypatch.setenv("SCHEDULER_TIMEZONE", "America/New_York")
        monkeypatch.setenv("SCHEDULER_CRON_EXPRESSION", "0 3 * * *")
        monkeypatch.setenv("SCHEDULER_RUN_ONCE", "true")
        monkeypatch.setenv("SCHEDULER_TICKERS_FILE", "/path/to/tickers.csv")
        monkeypatch.setenv("SCHEDULER_LIMIT_PER_TICKER", "50")
        monkeypatch.setenv("SCHEDULER_DB_PATH", "/path/to/db.sqlite")

        config = SchedulerConfig.from_env()
        assert config.mode == "cron"
        assert config.sync_hour == 3
        assert config.sync_minute == 30
        assert config.timezone == "America/New_York"
        assert config.cron_expression == "0 3 * * *"
        assert config.run_once is True
        assert config.tickers_file == "/path/to/tickers.csv"
        assert config.limit_per_ticker == 50
        assert config.db_path == "/path/to/db.sqlite"

    def test_scheduler_config_from_env_missing(self, monkeypatch):
        """Test SchedulerConfig.from_env with missing environment variables."""
        # Clear all scheduler-related env vars
        for key in list(monkeypatch._dict.keys()):
            if key.startswith("SCHEDULER_"):
                monkeypatch.delenv(key)

        config = SchedulerConfig.from_env()
        assert config.mode == "apscheduler"
        assert config.sync_hour == 2
        assert config.sync_minute == 0
        assert config.timezone == "UTC"
        assert config.cron_expression == "0 2 * * *"
        assert config.run_once is False
        assert config.tickers_file == "sec_importer/tickers.csv"
        assert config.limit_per_ticker == 100
        assert config.db_path == "sec_importer.db"

    def test_scheduler_config_str(self):
        """Test SchedulerConfig.__str__ method."""
        config = SchedulerConfig(mode="cron", sync_hour=3, sync_minute=30)
        result = str(config)
        assert "SchedulerConfig" in result
        assert "mode='cron'" in result
        assert "sync_hour=3" in result
        assert "sync_minute=30" in result

    def test_scheduler_config_str_default(self):
        """Test SchedulerConfig.__str__ with default values."""
        config = SchedulerConfig()
        result = str(config)
        assert "mode='apscheduler'" in result
        assert "sync_hour=2" in result
        assert "sync_minute=0" in result
        assert "timezone='UTC'" in result
        assert "cron_expression='0 2 * * *'" in result
        assert "run_once=False" in result
        assert "tickers_file='sec_importer/tickers.csv'" in result
        assert "limit_per_ticker=100" in result
        assert "db_path='sec_importer.db'" in result


class TestScheduler:
    """Tests for Scheduler class."""

    def test_scheduler_init_default_config(self):
        """Test Scheduler initialization with default config."""
        scheduler = Scheduler()
        assert scheduler.config.mode == "apscheduler"
        assert scheduler.config.sync_hour == 2
        assert scheduler.config.sync_minute == 0
        assert scheduler.config.timezone == "UTC"
        assert scheduler.config.cron_expression == "0 2 * * *"
        assert scheduler.config.run_once is False
        assert scheduler.config.tickers_file == "sec_importer/tickers.csv"
        assert scheduler.config.limit_per_ticker == 100
        assert scheduler.config.db_path == "sec_importer.db"
        assert scheduler.is_running is False

    def test_scheduler_init_custom_config(self):
        """Test Scheduler initialization with custom config."""
        config = SchedulerConfig(
            mode="cron",
            sync_hour=3,
            sync_minute=30,
            timezone="America/New_York",
            cron_expression="0 3 * * *",
            run_once=True,
            tickers_file="/path/to/tickers.csv",
            limit_per_ticker=50,
            db_path="/path/to/db.sqlite",
        )
        scheduler = Scheduler(config)
        assert scheduler.config == config
        assert scheduler.is_running is False

    def test_scheduler_is_running_property(self):
        """Test Scheduler.is_running property."""
        scheduler = Scheduler()
        assert scheduler.is_running is False

    def test_scheduler_start(self):
        """Test starting scheduler."""
        scheduler = Scheduler()
        scheduler.start()
        assert scheduler.is_running is True

    def test_scheduler_start_already_running(self):
        """Test starting scheduler when already running."""
        scheduler = Scheduler()
        scheduler.start()
        # Should not raise an error, just log a warning
        scheduler.start()
        assert scheduler.is_running is True

    def test_scheduler_stop(self):
        """Test stopping scheduler."""
        scheduler = Scheduler()
        scheduler.start()
        scheduler.stop()
        assert scheduler.is_running is False

    def test_scheduler_stop_without_start(self):
        """Test stopping scheduler without starting it."""
        scheduler = Scheduler()
        # Should not raise an error
        scheduler.stop()
        assert scheduler.is_running is False


class TestStartScheduler:
    """Tests for start_scheduler function."""

    def test_start_scheduler(self):
        """Test start_scheduler function."""
        config = SchedulerConfig()

        with patch("sec_importer.scheduler.run.Scheduler") as mock_scheduler_class:
            mock_scheduler_instance = MagicMock()
            mock_scheduler_class.return_value = mock_scheduler_instance

            result = start_scheduler(config)

            mock_scheduler_class.assert_called_once_with(config)
            mock_scheduler_instance.start.assert_called_once()
            assert result == mock_scheduler_instance

    def test_start_scheduler_default_config(self):
        """Test start_scheduler with default config (from env)."""
        with patch("sec_importer.scheduler.run.SchedulerConfig.from_env") as mock_from_env:
            mock_config = SchedulerConfig()
            mock_from_env.return_value = mock_config

            with patch("sec_importer.scheduler.run.Scheduler") as mock_scheduler_class:
                mock_scheduler_instance = MagicMock()
                mock_scheduler_class.return_value = mock_scheduler_instance

                result = start_scheduler()

                mock_from_env.assert_called_once()
                mock_scheduler_class.assert_called_once_with(mock_config)
                mock_scheduler_instance.start.assert_called_once()
                assert result == mock_scheduler_instance


class TestRunNow:
    """Tests for run_now function."""

    def test_run_now(self):
        """Test run_now function."""
        config = SchedulerConfig()

        with patch("sec_importer.scheduler.run.run_sync") as mock_run_sync:
            mock_run_sync.return_value = {"total_new": 10, "total_skipped": 5}

            result = run_now(config)

            mock_run_sync.assert_called_once_with(
                tickers_file=config.tickers_file,
                limit_per_ticker=config.limit_per_ticker,
                db_path=config.db_path,
            )
            assert result == {"total_new": 10, "total_skipped": 5}

    def test_run_now_default_config(self):
        """Test run_now with default config (from env)."""
        with patch("sec_importer.scheduler.run.SchedulerConfig.from_env") as mock_from_env:
            mock_config = SchedulerConfig()
            mock_from_env.return_value = mock_config

            with patch("sec_importer.scheduler.run.run_sync") as mock_run_sync:
                mock_run_sync.return_value = {"total_new": 10, "total_skipped": 5}

                result = run_now()

                mock_from_env.assert_called_once()
                mock_run_sync.assert_called_once_with(
                    tickers_file=mock_config.tickers_file,
                    limit_per_ticker=mock_config.limit_per_ticker,
                    db_path=mock_config.db_path,
                )
                assert result == {"total_new": 10, "total_skipped": 5}


class TestShowConfig:
    """Tests for show_config function."""

    def test_show_config(self):
        """Test show_config function."""
        config = SchedulerConfig(mode="cron", sync_hour=3, sync_minute=30)

        result = show_config(config)

        assert "SchedulerConfig" in result
        assert "mode='cron'" in result
        assert "sync_hour=3" in result
        assert "sync_minute=30" in result

    def test_show_config_default(self):
        """Test show_config with default config."""
        result = show_config()

        assert "SchedulerConfig" in result
        assert "mode='apscheduler'" in result
        assert "sync_hour=2" in result
        assert "sync_minute=0" in result

    def test_show_config_default_from_env(self):
        """Test show_config with default config from env."""
        with patch("sec_importer.scheduler.run.SchedulerConfig.from_env") as mock_from_env:
            mock_config = SchedulerConfig()
            mock_from_env.return_value = mock_config

            result = show_config()

            mock_from_env.assert_called_once()
            assert "SchedulerConfig" in result
