"""Bid submission engine for the Fiverr Job Automation Tool."""

import csv
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

from .models import JobOpportunity


class BidSubmissionEngine:
    """Handles bid submission with dry-run mode support and CSV logging.

    Attributes:
        log_file: Path to the CSV submission log file.
        rate_limit_delay: Seconds to wait between submissions.
    """

    CSV_COLUMNS = [
        "timestamp",
        "job_id",
        "job_title",
        "budget",
        "score",
        "proposal_preview",
        "status",
        "mode",
    ]

    def __init__(
        self,
        log_file: str = "submission_log.csv",
        rate_limit_delay: float = 30.0,
        dry_run: bool = False,
    ):
        """Initialize the submission engine.

        Args:
            log_file: Path to the CSV log file.
            rate_limit_delay: Delay in seconds between submissions.
            dry_run: If True, only log without submitting.
        """
        self.log_file = log_file
        self.rate_limit_delay = rate_limit_delay
        self.dry_run = dry_run
        self._last_submission_time: Optional[float] = None
        self._submission_log: List[Dict[str, str]] = []

        # Ensure CSV file exists with headers
        self._ensure_csv_exists()

    def _ensure_csv_exists(self) -> None:
        """Create the CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_COLUMNS)
                writer.writeheader()

    def log_submission(
        self,
        job: JobOpportunity,
        proposal: str,
        status: str = "SUCCESS",
        mode: str = "LIVE",
    ) -> Dict[str, str]:
        """Log a submission to the CSV file and internal log.

        Args:
            job: The JobOpportunity that was submitted.
            proposal: The proposal text that was submitted.
            status: Status of the submission (e.g., SUCCESS, FAILED, DRY_RUN).
            mode: Mode of submission (LIVE or DRY_RUN).

        Returns:
            The log entry as a dictionary.
        """
        budget_str = ""
        if job and job.budget_max is not None and job.budget_min is not None:
            budget_str = f"${job.budget_min}-{job.budget_max}"
        elif job and job.budget_min is not None:
            budget_str = f"${job.budget_min}"
        elif job and job.budget_max is not None:
            budget_str = f"Up to ${job.budget_max}"

        # Truncate proposal preview to 200 chars
        proposal_preview = proposal[:200].replace("\n", " ").replace(",", ";")

        entry = {
            "timestamp": datetime.now().isoformat(),
            "job_id": job.id if job else None,
            "job_title": job.title if job else "",
            "budget": budget_str,
            "score": str(job.score) if job and job.score is not None else "",
            "proposal_preview": proposal_preview,
            "status": status,
            "mode": mode,
        }

        # Write to CSV file
        file_exists = os.path.exists(self.log_file) and os.path.getsize(self.log_file) > 0
        with open(self.log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(entry)

        # Keep in memory
        self._submission_log.append(entry)
        return entry

    def get_submission_log(self) -> List[Dict[str, str]]:
        """Return the in-memory submission log.

        Returns:
            List of log entry dictionaries.
        """
        return list(self._submission_log)

    def _enforce_rate_limit(self) -> None:
        """Enforce the rate limit delay between submissions."""
        if self._last_submission_time is not None:
            elapsed = time.time() - self._last_submission_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self._last_submission_time = time.time()

    def submit_dry_run(self, job: JobOpportunity, proposal: str) -> Dict[str, str]:
        """Submit a bid in dry-run mode (no actual submission).

        Logs the submission to CSV with status="DRY_RUN" without making
        any browser or API calls.

        Args:
            job: The JobOpportunity to submit for.
            proposal: The proposal text.

        Returns:
            The log entry dictionary.
        """
        entry = self.log_submission(job, proposal, status="DRY_RUN", mode="DRY_RUN")
        return entry

    def submit_live(self, job: JobOpportunity, proposal: str) -> Dict[str, str]:
        """Submit a bid live (not implemented in base class).

        Subclasses should override this to implement actual submission
        via Playwright or API.

        Args:
            job: The JobOpportunity to submit for.
            proposal: The proposal text.

        Raises:
            NotImplementedError: Always raised in the base class.
        """
        raise NotImplementedError("Not implemented: use submit_dry_run or subclass")

    def submit(self, job: JobOpportunity, proposal: str) -> Dict[str, str]:
        """Submit a bid for a job.

        Routes to submit_dry_run or submit_live based on the dry_run flag.

        Args:
            job: The JobOpportunity to submit for.
            proposal: The proposal text.

        Returns:
            The log entry dictionary.
        """
        if self.dry_run:
            return self.submit_dry_run(job, proposal)
        self._enforce_rate_limit()
        return self.submit_live(job, proposal)
