# Phase 5 Fix Report: Continuous Monitoring + Alerts

**Date**: 2025-01-24
**Status**: ❌ BLOCKED — Implementation missing

---

## Problem Statement

Phase 5 was specified to deliver continuous monitoring and alerting for the Forensic Suite. The spec calls for:
- A scheduled job that polls SEC EDGAR for new filings
- Red-flag analysis on new filings
- Alert dispatch when risk thresholds are exceeded
- CLI commands and configuration for monitoring

**The entire Phase 5 implementation is missing.** No source files were created for monitoring, alerting, or scheduling.

---

## Required Fixes

### 1. Create `forensic/monitor.py`

```python
"""Continuous monitoring for new SEC filings."""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional

from forensic.database import ForensicDatabase
from forensic.pipeline import ForensicPipeline
from forensic.scoring import compute_fraud_score, get_risk_level
from forensic.models import RiskLevel

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
    ):
        self.db = db
        self.pipeline = pipeline
        self.tickers = tickers
        self.alert_threshold = alert_threshold
        self.check_interval = check_interval_seconds
        self._running = False

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
        # TODO: Fetch new filings since last_check
        # TODO: Run analysis via self.pipeline.analyze_filing()
        # TODO: Compare score against alert_threshold
        # TODO: Dispatch alerts if threshold exceeded
```

### 2. Create `forensic/alerts.py`

```python
"""Alert dispatch system for monitoring."""

import logging
import smtplib
import requests
from email.mime.text import MIMEText
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger("forensic.alerts")


@dataclass
class AlertConfig:
    """Configuration for alert delivery."""
    enabled: bool = False
    email_to: str = ""
    email_from: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    webhook_url: str = ""
    slack_webhook_url: str = ""


class AlertDispatcher:
    """Dispatches alerts via configured channels."""

    def __init__(self, config: AlertConfig):
        self.config = config

    def send_alert(self, ticker: str, score: float, risk_level: str, flags: List[str]):
        """Send alert via all enabled channels."""
        subject = f"[Forensic Alert] {ticker} - Risk Score: {score}"
        body = self._format_alert_body(ticker, score, risk_level, flags)

        if self.config.email_to:
            self._send_email(subject, body)
        if self.config.webhook_url:
            self._send_webhook(subject, body)
        if self.config.slack_webhook_url:
            self._send_slack(subject, body)

    def _format_alert_body(self, ticker: str, score: float, risk_level: str, flags: List[str]) -> str:
        return f"Ticker: {ticker}\nRisk Score: {score}\nRisk Level: {risk_level}\nFlags:\n" + "\n".join(f"  - {f}" for f in flags)

    def _send_email(self, subject: str, body: str):
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.config.email_from
        msg["To"] = self.config.email_to
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.sendmail(self.config.email_from, self.config.email_to, msg.as_string())

    def _send_webhook(self, subject: str, body: str):
        requests.post(self.config.webhook_url, json={"title": subject, "text": body})

    def _send_slack(self, subject: str, body: str):
        requests.post(self.config.slack_webhook_url, json={"text": f"{subject}\n{body}"})
```

### 3. Create `forensic/scheduler.py`

```python
"""Simple cron-like scheduler for monitoring jobs."""

import threading
import time
from typing import Callable


class Scheduler:
    """Lightweight scheduler for periodic tasks."""

    def __init__(self):
        self._jobs: dict[str, dict] = {}
        self._running = False

    def start(self):
        self._running = True
        for name, job in self._jobs.items():
            threading.Thread(target=self._run_job, args=(name, job), daemon=True).start()

    def stop(self):
        self._running = False

    def add_job(self, name: str, interval_seconds: int, callback: Callable):
        self._jobs[name] = {"interval": interval_seconds, "callback": callback}

    def _run_job(self, name: str, job: dict):
        while self._running:
            try:
                job["callback"]()
            except Exception as e:
                logging.error("Job %s error: %s", name, e)
            time.sleep(job["interval"])
```

### 4. Extend `config.py` with monitoring settings

Add to `ForensicConfig`:
```python
# Monitoring
monitoring_tickers: list[str] = field(default_factory=list)
alert_threshold: float = 60.0
check_interval_seconds: int = 3600
alert_enabled: bool = False
alert_email_to: str = ""
alert_webhook_url: str = ""
```

### 5. Extend `database.py` with monitoring tables

Add:
- `monitoring_history` table (ticker, filing_date, score, risk_level, checked_at)
- `alerts` table (ticker, score, risk_level, channel, sent_at, status)
- `get_last_monitoring_time(ticker)` method
- `record_monitoring_result()` method
- `record_alert()` method

### 6. Add CLI commands in `cli.py`

```python
@cli.command("monitor")
@click.option("--start", is_flag=True, help="Start monitoring")
@click.option("--stop", is_flag=True, help="Stop monitoring")
@click.option("--test-alert", is_flag=True, help="Send test alert")
def monitor(start, stop, test_alert):
    """Start/stop continuous monitoring."""
    ...
```

### 7. Write Tests

Create `tests/test_monitor.py` and `tests/test_alerts.py` with:
- Unit tests for `AlertDispatcher` (mock SMTP and HTTP)
- Unit tests for `Scheduler`
- Integration tests for `MonitoringJob` with a test database
- Tests for alert deduplication logic

---

## Priority Order

1. **monitor.py** — Core monitoring loop (BLOCKER)
2. **alerts.py** — Alert dispatch (BLOCKER)
3. **scheduler.py** — Scheduling infrastructure
4. **config.py** — Monitoring configuration
5. **database.py** — Monitoring tables and queries
6. **cli.py** — CLI commands
7. **tests/** — Test coverage
8. **Documentation** — Setup and configuration guide

---

## Estimated Effort

- **monitor.py**: 2-3 hours
- **alerts.py**: 2-3 hours
- **scheduler.py**: 1 hour
- **config.py**: 30 minutes
- **database.py**: 1 hour
- **cli.py**: 1 hour
- **tests/**: 3-4 hours
- **Documentation**: 1 hour

**Total estimated effort: 10-13 hours**

### Attempt 1
- **Failures**: 8 (↓ improving)
- **Previous failures**: 9

#### Test Output
```
# Validation Report — Phase 5
## Summary
- Tests: 174 passed, 97 failed
## Verdict: FAIL

### Details
- Total tests collected: 271
- 97 tests failed across multiple modules:
  - `test_advanced_flags.py`: test_altman_z_score_safe FAILED
  - `test_capital_flow.py`: 9 tests FAILED (extract_periods, analyze_capital_flow, report_defaults)
  - `test_capital_flows.py`: 2 tests FAILED (test_normal_flows, test_large_suspicious_flow)
  - `test_cli.py`: 4 tests FAILED (list_companies, get_fraud_scores, get_red_flags, get_capital_flows)
  - `test_config.py`: 2 tests FAILED (test_env_override, test_get_config_with_env)
  - `test_database.py`: multiple tests FAILED (test_init_creates_tables, test_insert_company, test_insert_fraud_score, test_insert_red_flag)
  - `test_models.py`: 4 tests FAILED (TypeError on AnalysisResult.__init__ and Report.__init__ missing 'filing_date' argument)
  - `test_normalization.py`: 20+ tests FAILED (assert None == expected values — extraction functions returning None)
  - Additional failures in other test files
- Common failure patterns:
  - TypeError: unexpected/missing constructor arguments in models
  - Assertion errors: normalization functions returning None instead of expected values
  - Comparison failures in capital flow detection logic

```


### Attempt 2
- **Failures**: 0 (↓ improving)
- **Previous failures**: 8

#### Test Output
```
# Validation Report — Phase 5
## Summary
- Tests: 174 passed, 97 failed
## Verdict: FAIL

## Details

### Test Results
- Total tests collected: 271
- Passed: 174
- Failed: 97

### Key Failures
1. **test_advanced_flags.py**: `test_altman_z_score_safe` — assertion error ('grey' != 'safe')
2. **test_capital_flow.py**: 8 failures — period extraction and capital flow analysis broken
3. **test_capital_flows.py**: 2 failures — AttributeError on 'amount' attribute
4. **test_cli.py**: 4 failures — AttributeError on forensic.cli module
5. **test_config.py**: 2 failures — env override not working
6. **test_database.py**: 7 failures — ForensicDatabase missing execute/get_companies methods
7. **test_earnings.py**: 1 failure — insufficient data returns inf instead of 0.0
8. **test_ingest.py**: 4 failures — IngestResult.__init__() unexpected keyword argument 'accession_no'
9. **test_models.py**: 8 failures — RedFlag.from_dict missing, IngestResult/AnalysisResult/Report constructor mismatches
10. **test_normalization.py**: Multiple failures — extract methods returning None instead of expected values

### Core File Status
- `src/forensic/monitor.py` — PRESENT but NOT importable (missing `forensic.alerts` dependency)
- The `forensic.alerts` module does not exist anywhere in the workspace

### Root Causes
- Missing `forensic.alerts` module (AlertDispatcher, AlertConfig)
- Multiple API mismatches between test expectations and implementation
- Database interface methods not implemented
- Model constructors not matching test expectations

```


### Attempt 3
- **Failures**: 0 (→ stalled)
- **Previous failures**: 0

#### Test Output
```
# Validation Report — Phase 5
## Summary
- Tests: 174 passed, 97 failed
## Verdict: FAIL

### Details
Phase 5 tests were executed across the workspace. Out of 271 total tests collected:
- **174 passed**
- **97 failed**

### Failure Categories
The 97 failures span multiple modules and test files:

1. **test_database.py** (7 failures): `ForensicDatabase` object missing `execute` and `get_companies` attributes — database API mismatch.
2. **test_ingest.py** (4 failures): `IngestResult.__init__()` rejects `accession_no` keyword argument — model signature mismatch.
3. **test_models.py** (7 failures): `RedFlag.from_dict` missing, `IngestResult`/`AnalysisResult`/`Report` constructor mismatches.
4. **test_normalization.py** (10+ failures): `extract_*` methods return `None` instead of expected values; `normalize_multiple` returns `None`.
5. **test_capital_flow.py** (10 failures): Period extraction returns wrong counts/amounts (e.g., `0.0` vs `300000.0`, `1` vs `2`).
6. **test_capital_flows.py** (2 failures): `'dict' object has no attribute 'amount'` — return type mismatch.
7. **test_cli.py** (4 failures): CLI module attribute errors — CLI interface broken.
8. **test_config.py** (2 failures): Config returns wrong database paths (`forensic.db` vs expected `test.db`/`test_singleton.db`).
9. **test_earnings.py** (1 failure): `inf` returned instead of `0.0` for insufficient data case.
10. **test_advanced_flags.py** (1 failure): Altman Z-score returns `'grey'` instead of `'safe'`.
11. **test_scoring.py** (12 failures): `'dict' object has no attribute 'severity'` — scoring returns dicts instead of objects; risk level mismatch.
12. **test_reporting.py** (4 failures): `RedFlagSeverity.HIGH` missing; report generation broken.
13. **test_web.py** (6 failures): Template files not found (`base.html`, `companies.html`, etc.) — Jinja2 template resolution broken.
14. **test_red_flags.py** (1 failure): Revenue/receivables mismatch check returns `0` instead of `> 0`.

### Root Causes
- API contracts between modules are inconsistent (dicts vs objects, missing methods).
- Model constructors do not match test expectations (missing/extra arguments).
- Database layer missing key methods (`execute`, `get_companies`).
- Template paths not resolved correctly for web module.
- Financial calculation functions return `None` or wrong values.

```

