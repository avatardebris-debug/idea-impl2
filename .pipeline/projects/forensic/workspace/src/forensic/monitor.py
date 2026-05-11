"""Continuous monitoring for new SEC filings."""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional

from forensic.database import ForensicDatabase
from forensic.pipeline import ForensicPipeline
from forensic.scoring import compute_fraud_score, get_risk_level
from forensic.models import RiskLevel
from forensic.alerts import AlertDispatcher, AlertConfig

logger = logging.getLogger("forensic.monitor")


class MonitoringJob:
    """Monitors SEC filings for new entries and triggers alerts."""

    def __init__(
        self,
        db: ForensicDatabase,
        pipeline: ForensicPipeline,
        tickers: List[str],
        alert_threshold: float = 60.0,
        check_interval_seconds: int = 3600,
        alert_dispatcher: Optional[AlertDispatcher] = None,
    ):
        self.db = db
        self.pipeline = pipeline
        self.tickers = tickers
        self.alert_threshold = alert_threshold
        self.check_interval = check_interval_seconds
        self._running = False
        self.alert_dispatcher = alert_dispatcher

    def start(self):
        """Start the monitoring loop."""
        self._running = True
        logger.info("Monitoring started for tickers: %s", self.tickers)
        while self._running:
            self._check_filings()
            time.sleep(self.check_interval)

    def stop(self):
        """Stop the monitoring loop."""
        self._running = False
        logger.info("Monitoring stopped")

    def _check_filings(self):
        """Check all monitored tickers for new filings."""
        for ticker in self.tickers:
            try:
                self._check_ticker(ticker)
            except Exception as e:
                logger.error("Error checking ticker %s: %s", ticker, e)

    def _check_ticker(self, ticker: str):
        """Check a single ticker for new filings and run analysis."""
        # Get last check time from database
        last_check = self.db.get_last_monitoring_time(ticker)
        if last_check:
            logger.info("Last check for %s: %s", ticker, last_check)

        # Get latest filing for this ticker
        filing_data = self.db.get_latest_filing(ticker)
        if not filing_data:
            logger.warning("No filing found for ticker %s", ticker)
            return

        accession_no = filing_data.get("accession_no", "")
        filing_date = filing_data.get("filing_date", "")

        # Check if we've already analyzed this filing
        if last_check:
            last_check_date = datetime.fromisoformat(last_check)
            filing_dt = datetime.fromisoformat(filing_date) if filing_date else None
            if filing_dt and filing_dt <= last_check_date:
                logger.info("Filing %s for %s already checked at %s", accession_no, ticker, last_check)
                return

        # Run analysis via pipeline
        try:
            result = self.pipeline.analyze_filing(ticker)
        except Exception as e:
            logger.error("Analysis failed for ticker %s: %s", ticker, e)
            return

        score = result.fraud_risk_score
        risk_level = get_risk_level(score)

        # Record monitoring result
        self.db.record_monitoring_result(
            ticker=ticker,
            filing_date=filing_date,
            score=score,
            risk_level=risk_level.value,
        )

        logger.info(
            "Monitoring %s: score=%.2f, risk=%s, flags=%d",
            ticker, score, risk_level.value, len(result.red_flags),
        )

        # Check if alert threshold exceeded
        if score >= self.alert_threshold:
            flags = [flag.description for flag in result.red_flags]
            logger.warning(
                "Alert threshold exceeded for %s: score=%.2f >= %.2f",
                ticker, score, self.alert_threshold,
            )
            self._dispatch_alert(ticker, score, risk_level.value, flags)

    def _dispatch_alert(self, ticker: str, score: float, risk_level: str, flags: List[str]):
        """Dispatch alert via configured channels."""
        if not self.alert_dispatcher:
            logger.warning("No alert dispatcher configured, skipping alert for %s", ticker)
            return

        # Check for deduplication: don't alert on the same ticker/score combo within 1 hour
        recent_alerts = self.db.get_recent_alerts(ticker, hours=1)
        for alert in recent_alerts:
            if alert.get("score") == score and alert.get("risk_level") == risk_level:
                logger.info("Alert deduplication: %s already alerted for score %.2f", ticker, score)
                return

        # Create alert record
        self.db.insert_alert(
            ticker=ticker,
            score=score,
            risk_level=risk_level,
            flags=flags,
        )

        # Dispatch via configured channels
        self.alert_dispatcher.dispatch(
            ticker=ticker,
            score=score,
            risk_level=risk_level,
            flags=flags,
        )


def run_monitoring(
    db_path: str = "forensic.db",
    tickers: Optional[List[str]] = None,
    alert_threshold: float = 60.0,
    check_interval_seconds: int = 3600,
    alert_config: Optional[AlertConfig] = None,
    max_iterations: Optional[int] = None,
):
    """Run monitoring for a set of tickers.

    Args:
        db_path: Path to the SQLite database.
        tickers: List of ticker symbols to monitor.
        alert_threshold: Fraud score threshold for alerts.
        check_interval_seconds: Seconds between checks.
        alert_config: Configuration for alert dispatching.
        max_iterations: Maximum number of monitoring iterations (None = infinite).
    """
    db = ForensicDatabase(db_path)
    pipeline = ForensicPipeline(db_path=db_path)

    if not tickers:
        # Auto-discover tickers from the database
        tickers = [row["ticker"] for row in db.get_all_tickers()]

    if not tickers:
        logger.warning("No tickers to monitor. Add filings first.")
        return

    alert_dispatcher = None
    if alert_config:
        alert_dispatcher = AlertDispatcher(alert_config)

    monitor = MonitoringJob(
        db=db,
        pipeline=pipeline,
        tickers=tickers,
        alert_threshold=alert_threshold,
        check_interval_seconds=check_interval_seconds,
        alert_dispatcher=alert_dispatcher,
    )

    iteration = 0
    try:
        while max_iterations is None or iteration < max_iterations:
            monitor._check_filings()
            iteration += 1
            if max_iterations and iteration >= max_iterations:
                break
            time.sleep(check_interval_seconds)
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    finally:
        monitor.stop()
