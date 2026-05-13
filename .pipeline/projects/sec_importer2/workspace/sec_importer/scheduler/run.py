"""Scheduler entry point — runs SEC Importer sync on a schedule.

Supports two modes:
  - 'apscheduler': In-process scheduling via APScheduler (default).
  - 'cron': Delegates to system cron (user must set up crontab manually).

Usage:
    sec-importer scheduler start          # Start the scheduler
    sec-importer scheduler run-now        # Run sync immediately (one-shot)
    sec-importer scheduler show-config    # Show current configuration
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
import traceback
from datetime import datetime, timezone
from typing import Optional

from sec_importer.scheduler.config import SchedulerConfig

logger = logging.getLogger("sec_importer.scheduler")


class Scheduler:
    """Manages periodic execution of SEC Importer sync jobs."""

    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig.from_env()
        self._stop_event = False

    # -------------- Public API --------------

    def start(self) -> None:
        """Start the scheduler in the configured mode."""
        logger.info("Starting SEC Importer scheduler (mode=%s)", self.config.mode)
        logger.info("Config: %s", json.dumps(self.config.to_dict(), indent=2))

        if self.config.mode == "cron":
            self._start_cron_mode()
        elif self.config.mode == "apscheduler":
            self._start_apscheduler_mode()
        else:
            raise ValueError(f"Unknown scheduler mode: {self.config.mode}")

    def run_now(self) -> dict:
        """Run a sync job immediately (one-shot).

        Returns:
            Summary dict from run_sync.
        """
        logger.info("Running immediate sync job...")
        from sec_importer.sync import run_sync

        summary = run_sync(
            tickers_file=self.config.tickers_file or None,
            limit_per_ticker=self.config.limit_per_ticker,
            db_path=self.config.db_path or None,
        )
        logger.info("Immediate sync complete. Summary: %s", summary)
        return summary

    def stop(self) -> None:
        """Signal the scheduler to stop."""
        self._stop_event = True
        logger.info("Scheduler stop signal sent.")

    # -------------- Internal --------------

    def _start_apscheduler_mode(self) -> None:
        """Start the scheduler using APScheduler."""
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.error(
                "APScheduler is not installed. Install it with: pip install apscheduler"
            )
            sys.exit(1)

        # Import run_sync here to avoid circular imports
        from sec_importer.sync import run_sync

        def _sync_job():
            """Execute the sync job."""
            logger.info("Running scheduled sync job...")
            try:
                summary = run_sync(
                    tickers_file=self.config.tickers_file or None,
                    limit_per_ticker=self.config.limit_per_ticker,
                    db_path=self.config.db_path or None,
                )
                logger.info("Scheduled sync complete. Summary: %s", summary)
            except Exception:
                logger.exception("Scheduled sync job failed.")

        # Create scheduler
        tz = self.config.timezone or "UTC"
        scheduler = BlockingScheduler(timezone=tz)

        # Add the sync job
        scheduler.add_job(
            _sync_job,
            trigger=CronTrigger(
                hour=self.config.sync_hour,
                minute=self.config.sync_minute,
            ),
            id="sec_importer_sync",
            name="SEC Importer Sync",
            replace_existing=True,
        )

        logger.info(
            "Scheduler started. Next run at %s (timezone=%s)",
            scheduler.get_job("sec_importer_sync").next_run_time,
            tz,
        )

        # Handle graceful shutdown
        def _signal_handler(signum, frame):
            logger.info("Received signal %d. Shutting down scheduler...", signum)
            scheduler.shutdown(wait=True)
            sys.exit(0)

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        # Start the scheduler (blocks until shutdown)
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")

    def _start_cron_mode(self) -> None:
        """Start the scheduler in cron mode.

        In cron mode, the scheduler runs once and exits.
        The user is responsible for setting up system cron to run periodically.
        """
        if self.config.run_once:
            logger.info("Cron mode: running once and exiting.")
            from sec_importer.sync import run_sync

            summary = run_sync(
                tickers_file=self.config.tickers_file or None,
                limit_per_ticker=self.config.limit_per_ticker,
                db_path=self.config.db_path or None,
            )
            logger.info("Cron mode sync complete. Summary: %s", summary)
            return

        # If not run_once, we still run once but log instructions
        logger.info(
            "Cron mode: Please set up system cron to run:\n"
            "  %s\n"
            "Then run 'sec-importer scheduler run-now' to execute immediately.",
            f"sec-importer scheduler run-now",
        )
        logger.info("For now, running once...")
        from sec_importer.sync import run_sync

        summary = run_sync(
            tickers_file=self.config.tickers_file or None,
            limit_per_ticker=self.config.limit_per_ticker,
            db_path=self.config.db_path or None,
        )
        logger.info("Cron mode sync complete. Summary: %s", summary)


# -------------- Module-level convenience functions --------------

def start_scheduler() -> None:
    """Start the scheduler (entry point for CLI)."""
    config = SchedulerConfig.from_env()
    scheduler = Scheduler(config)
    scheduler.start()


def run_now() -> dict:
    """Run a sync job immediately (entry point for CLI)."""
    config = SchedulerConfig.from_env()
    scheduler = Scheduler(config)
    return scheduler.run_now()


def show_config() -> None:
    """Show current scheduler configuration."""
    config = SchedulerConfig.from_env()
    try:
        import click
        click.echo(click.style("Scheduler Configuration", fg="cyan"))
        click.echo()
        for key, value in config.to_dict().items():
            click.echo(f"  {key:20s}: {value}")
    except ImportError:
        print("Scheduler Configuration")
        print()
        for key, value in config.to_dict().items():
            print(f"  {key:20s}: {value}")
