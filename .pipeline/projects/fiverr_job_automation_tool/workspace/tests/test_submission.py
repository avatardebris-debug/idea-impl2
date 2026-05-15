"""Tests for the BidSubmissionEngine."""

import csv
import os
import pytest
from src.submission import BidSubmissionEngine
from src.models import JobOpportunity
from tests.fixtures.mock_jobs import create_mock_job


class TestBidSubmissionEngineInitialization:
    """Tests for BidSubmissionEngine initialization."""

    def test_default_initialization(self, tmp_path):
        """Test default engine initialization."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        assert engine.log_file == log_file
        assert engine.rate_limit_delay == 30.0
        assert os.path.exists(log_file)

    def test_custom_initialization(self, tmp_path):
        """Test engine with custom parameters."""
        log_file = str(tmp_path / "custom_log.csv")
        engine = BidSubmissionEngine(log_file=log_file, rate_limit_delay=60.0)
        assert engine.rate_limit_delay == 60.0


class TestLogSubmission:
    """Tests for the log_submission method."""

    def test_log_creates_csv(self, tmp_path):
        """Test that log_submission creates CSV file."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        job = create_mock_job()
        engine.log_submission(job, "Test proposal")
        assert os.path.exists(log_file)

    def test_log_writes_entry(self, tmp_path):
        """Test that log_submission writes an entry."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        job = create_mock_job(id="123", title="Test Job")
        engine.log_submission(job, "Test proposal")

        with open(log_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["job_id"] == "123"
        assert rows[0]["job_title"] == "Test Job"

    def test_log_multiple_entries(self, tmp_path):
        """Test that multiple submissions are logged."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        for i in range(3):
            job = create_mock_job(id=str(i), title=f"Job {i}")
            engine.log_submission(job, f"Proposal {i}")

        with open(log_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3

    def test_log_dry_run_status(self, tmp_path):
        """Test that dry run submissions are logged correctly."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        job = create_mock_job()
        engine.log_submission(job, "Test proposal", status="DRY_RUN")

        with open(log_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]["status"] == "DRY_RUN"


class TestSubmitDryRun:
    """Tests for the submit_dry_run method."""

    def test_dry_run_returns_log_entry(self, tmp_path):
        """Test that submit_dry_run returns a log entry."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        job = create_mock_job()
        log_entry = engine.submit_dry_run(job, "Test proposal")
        assert "status" in log_entry
        assert log_entry["status"] == "DRY_RUN"

    def test_dry_run_logs_entry(self, tmp_path):
        """Test that submit_dry_run logs the entry."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        job = create_mock_job(id="123")
        engine.submit_dry_run(job, "Test proposal")

        with open(log_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1


class TestSubmitLive:
    """Tests for the submit_live method."""

    def test_submit_live_raises_not_implemented(self, tmp_path):
        """Test that submit_live raises NotImplementedError."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        job = create_mock_job()
        with pytest.raises(NotImplementedError, match="Not implemented"):
            engine.submit_live(job, "Test proposal")


class TestSubmit:
    """Tests for the main submit method."""

    def test_submit_calls_dry_run_when_dry_run_flag(self, tmp_path):
        """Test that submit calls submit_dry_run when dry_run flag is set."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file, dry_run=True)
        job = create_mock_job()
        log_entry = engine.submit(job, "Test proposal")
        assert log_entry["status"] == "DRY_RUN"

    def test_submit_calls_live_when_not_dry_run(self, tmp_path):
        """Test that submit calls submit_live when dry_run flag is not set."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file, dry_run=False)
        job = create_mock_job()
        with pytest.raises(NotImplementedError, match="Not implemented"):
            engine.submit(job, "Test proposal")


class TestRateLimit:
    """Tests for rate limiting."""

    def test_rate_limit_applied(self, tmp_path):
        """Test that rate limit is applied between submissions."""
        import time
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file, rate_limit_delay=0.1)
        job = create_mock_job()

        # Use submit_dry_run twice; second call goes through _enforce_rate_limit
        # because we manually set _last_submission_time before the second call
        engine.submit_dry_run(job, "Proposal 1")
        engine._last_submission_time = time.time() - 0.0  # simulate just submitted

        start = time.time()
        engine._enforce_rate_limit()  # should sleep ~0.1s
        elapsed = time.time() - start

        assert elapsed >= 0.05  # allow some slack for CI


class TestSubmissionEdgeCases:
    """Tests for edge cases in submission."""

    def test_log_with_none_job(self, tmp_path):
        """Test logging with None job."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        engine.log_submission(None, "Test proposal")

        with open(log_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1

    def test_log_with_empty_proposal(self, tmp_path):
        """Test logging with empty proposal."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        job = create_mock_job()
        engine.log_submission(job, "")

        with open(log_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1

    def test_log_with_unicode_content(self, tmp_path):
        """Test logging with unicode content."""
        log_file = str(tmp_path / "test_log.csv")
        engine = BidSubmissionEngine(log_file=log_file)
        job = create_mock_job(title="日本語 Job", buyer_name="田中太郎")
        engine.log_submission(job, "Proposal 日本語")

        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert "日本語" in rows[0]["job_title"]
