"""Scheduler configuration for SEC Importer 2."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""

    mode: str = "apscheduler"  # 'apscheduler' or 'cron'
    sync_hour: int = 2
    sync_minute: int = 0
    timezone: str = "UTC"
    cron_expression: str = "0 2 * * *"
    run_once: bool = False
    tickers_file: str = "sec_importer/tickers.csv"
    limit_per_ticker: int = 100
    db_path: str = "sec_importer.db"

    @classmethod
    def from_env(cls) -> SchedulerConfig:
        """Load configuration from environment variables."""
        return cls(
            mode=os.getenv("SCHEDULER_MODE", "apscheduler"),
            sync_hour=int(os.getenv("SCHEDULER_SYNC_HOUR", "2")),
            sync_minute=int(os.getenv("SCHEDULER_SYNC_MINUTE", "0")),
            timezone=os.getenv("SCHEDULER_TIMEZONE", "UTC"),
            cron_expression=os.getenv("SCHEDULER_CRON_EXPRESSION", "0 2 * * *"),
            run_once=os.getenv("SCHEDULER_RUN_ONCE", "false").lower() == "true",
            tickers_file=os.getenv("SCHEDULER_TICKERS_FILE", "sec_importer/tickers.csv"),
            limit_per_ticker=int(os.getenv("SCHEDULER_LIMIT_PER_TICKER", "100")),
            db_path=os.getenv("SCHEDULER_DB_PATH", "sec_importer.db"),
        )

    def to_dict(self) -> dict:
        """Convert configuration to a dictionary."""
        return {
            "mode": self.mode,
            "sync_hour": self.sync_hour,
            "sync_minute": self.sync_minute,
            "timezone": self.timezone,
            "cron_expression": self.cron_expression,
            "run_once": self.run_once,
            "tickers_file": self.tickers_file,
            "limit_per_ticker": self.limit_per_ticker,
            "db_path": self.db_path,
        }

    def __str__(self) -> str:
        """String representation of the configuration."""
        return (
            f"SchedulerConfig(\n"
            f"  mode={self.mode!r},\n"
            f"  sync_hour={self.sync_hour},\n"
            f"  sync_minute={self.sync_minute},\n"
            f"  timezone={self.timezone!r},\n"
            f"  cron_expression={self.cron_expression!r},\n"
            f"  run_once={self.run_once},\n"
            f"  tickers_file={self.tickers_file!r},\n"
            f"  limit_per_ticker={self.limit_per_ticker},\n"
            f"  db_path={self.db_path!r}\n"
            f")"
        )
