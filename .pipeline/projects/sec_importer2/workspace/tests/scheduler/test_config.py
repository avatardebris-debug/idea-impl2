"""Tests for SEC Importer 2 scheduler config module."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from sec_importer.scheduler.config import SchedulerConfig


class TestSchedulerConfigDefaults:
    """Test default values for SchedulerConfig."""

    def test_default_mode(self):
        config = SchedulerConfig()
        assert config.mode == "apscheduler"

    def test_default_sync_hour(self):
        config = SchedulerConfig()
        assert config.sync_hour == 2

    def test_default_sync_minute(self):
        config = SchedulerConfig()
        assert config.sync_minute == 0

    def test_default_timezone(self):
        config = SchedulerConfig()
        assert config.timezone == "America/New_York"

    def test_default_cron_expression(self):
        config = SchedulerConfig()
        assert config.cron_expression == "0 2 * * *"

    def test_default_run_once(self):
        config = SchedulerConfig()
        assert config.run_once is False

    def test_default_tickers_file(self):
        config = SchedulerConfig()
        assert config.tickers_file == "/workspace/tickers.csv"

    def test_default_limit_per_ticker(self):
        config = SchedulerConfig()
        assert config.limit_per_ticker == 100

    def test_default_db_path(self):
        config = SchedulerConfig()
        assert config.db_path == "/workspace/data/sec_filings.db"


class TestSchedulerConfigFromEnv:
    """Test SchedulerConfig.from_env() with environment variables."""

    @patch.dict(os.environ, {
        "SCHEDULER_MODE": "cron",
        "SYNC_HOUR": "3",
        "SYNC_MINUTE": "30",
        "TIMEZONE": "UTC",
        "CRON_EXPRESSION": "0 3 * * *",
        "RUN_ONCE": "true",
        "TICKERS_FILE": "/custom/tickers.csv",
        "LIMIT_PER_TICKER": "50",
        "DB_PATH": "/custom/data.db",
    }, clear=False)
    def test_from_env_all_values(self):
        config = SchedulerConfig.from_env()
        assert config.mode == "cron"
        assert config.sync_hour == 3
        assert config.sync_minute == 30
        assert config.timezone == "UTC"
        assert config.cron_expression == "0 3 * * *"
        assert config.run_once is True
        assert config.tickers_file == "/custom/tickers.csv"
        assert config.limit_per_ticker == 50
        assert config.db_path == "/custom/data.db"

    @patch.dict(os.environ, {}, clear=False)
    def test_from_env_defaults(self):
        config = SchedulerConfig.from_env()
        assert config.mode == "apscheduler"
        assert config.sync_hour == 2
        assert config.sync_minute == 0
        assert config.timezone == "America/New_York"
        assert config.cron_expression == "0 2 * * *"
        assert config.run_once is False
        assert config.tickers_file == "/workspace/tickers.csv"
        assert config.limit_per_ticker == 100
        assert config.db_path == "/workspace/data/sec_filings.db"

    @patch.dict(os.environ, {"RUN_ONCE": "false"}, clear=False)
    def test_from_env_run_once_false_string(self):
        config = SchedulerConfig.from_env()
        assert config.run_once is False

    @patch.dict(os.environ, {"RUN_ONCE": "TRUE"}, clear=False)
    def test_from_env_run_once_uppercase(self):
        config = SchedulerConfig.from_env()
        assert config.run_once is True

    @patch.dict(os.environ, {"RUN_ONCE": "True"}, clear=False)
    def test_from_env_run_once_mixed_case(self):
        config = SchedulerConfig.from_env()
        assert config.run_once is True

    @patch.dict(os.environ, {"RUN_ONCE": "1"}, clear=False)
    def test_from_env_run_once_one(self):
        config = SchedulerConfig.from_env()
        assert config.run_once is False

    @patch.dict(os.environ, {"SYNC_HOUR": "23"}, clear=False)
    def test_from_env_sync_hour_max(self):
        config = SchedulerConfig.from_env()
        assert config.sync_hour == 23

    @patch.dict(os.environ, {"SYNC_MINUTE": "59"}, clear=False)
    def test_from_env_sync_minute_max(self):
        config = SchedulerConfig.from_env()
        assert config.sync_minute == 59

    @patch.dict(os.environ, {"LIMIT_PER_TICKER": "1000"}, clear=False)
    def test_from_env_limit_per_ticker(self):
        config = SchedulerConfig.from_env()
        assert config.limit_per_ticker == 1000


class TestSchedulerConfigToDict:
    """Test SchedulerConfig.to_dict() method."""

    def test_to_dict_returns_all_keys(self):
        config = SchedulerConfig(
            mode="cron",
            sync_hour=3,
            sync_minute=30,
            timezone="UTC",
            cron_expression="0 3 * * *",
            run_once=True,
            tickers_file="/custom/tickers.csv",
            limit_per_ticker=50,
            db_path="/custom/data.db",
        )
        d = config.to_dict()
        assert set(d.keys()) == {
            "mode", "sync_hour", "sync_minute", "timezone",
            "cron_expression", "run_once", "tickers_file",
            "limit_per_ticker", "db_path",
        }

    def test_to_dict_values_match(self):
        config = SchedulerConfig(
            mode="cron",
            sync_hour=3,
            sync_minute=30,
            timezone="UTC",
            cron_expression="0 3 * * *",
            run_once=True,
            tickers_file="/custom/tickers.csv",
            limit_per_ticker=50,
            db_path="/custom/data.db",
        )
        d = config.to_dict()
        assert d["mode"] == "cron"
        assert d["sync_hour"] == 3
        assert d["sync_minute"] == 30
        assert d["timezone"] == "UTC"
        assert d["cron_expression"] == "0 3 * * *"
        assert d["run_once"] is True
        assert d["tickers_file"] == "/custom/tickers.csv"
        assert d["limit_per_ticker"] == 50
        assert d["db_path"] == "/custom/data.db"

    def test_to_dict_is_copy(self):
        config = SchedulerConfig()
        d1 = config.to_dict()
        d2 = config.to_dict()
        assert d1 is not d2
        d1["mode"] = "modified"
        assert config.to_dict()["mode"] == "apscheduler"


class TestSchedulerConfigStr:
    """Test SchedulerConfig.__str__() method."""

    def test_str_contains_mode(self):
        config = SchedulerConfig(mode="cron")
        s = str(config)
        assert "cron" in s

    def test_str_contains_sync_hour(self):
        config = SchedulerConfig(sync_hour=3)
        s = str(config)
        assert "3" in s

    def test_str_contains_db_path(self):
        config = SchedulerConfig(db_path="/custom/data.db")
        s = str(config)
        assert "/custom/data.db" in s

    def test_str_is_multiline(self):
        config = SchedulerConfig()
        s = str(config)
        assert "\n" in s


class TestSchedulerConfigEquality:
    """Test SchedulerConfig equality."""

    def test_equal_configs(self):
        c1 = SchedulerConfig(mode="cron", sync_hour=3)
        c2 = SchedulerConfig(mode="cron", sync_hour=3)
        assert c1 == c2

    def test_unequal_configs(self):
        c1 = SchedulerConfig(mode="cron")
        c2 = SchedulerConfig(mode="apscheduler")
        assert c1 != c2

    def test_equal_to_self(self):
        config = SchedulerConfig()
        assert config == config

    def test_not_equal_to_non_config(self):
        config = SchedulerConfig()
        assert config != "not a config"


class TestSchedulerConfigValidation:
    """Test SchedulerConfig validation."""

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="mode"):
            SchedulerConfig(mode="invalid_mode")

    def test_sync_hour_range(self):
        # Valid range
        SchedulerConfig(sync_hour=0)
        SchedulerConfig(sync_hour=23)

    def test_sync_minute_range(self):
        # Valid range
        SchedulerConfig(sync_minute=0)
        SchedulerConfig(sync_minute=59)

    def test_limit_per_ticker_positive(self):
        SchedulerConfig(limit_per_ticker=1)
        with pytest.raises(ValueError, match="limit_per_ticker"):
            SchedulerConfig(limit_per_ticker=0)
        with pytest.raises(ValueError, match="limit_per_ticker"):
            SchedulerConfig(limit_per_ticker=-1)

    def test_invalid_timezone_raises(self):
        with pytest.raises(ValueError, match="timezone"):
            SchedulerConfig(timezone="Invalid/Timezone")
