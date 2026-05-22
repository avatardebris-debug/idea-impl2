"""Retry Policy — configurable retry logic for bulk SOP execution.

Supports FIXED, EXPONENTIAL, and LINEAR backoff strategies.

Usage:
    from drop_servicing_tool.retry_policy import RetryPolicy, BackoffStrategy

    policy = RetryPolicy(max_retries=3, backoff_strategy=BackoffStrategy.EXPONENTIAL, base_delay=1.0)
    delay = policy.get_delay(0)   # 1.0
    delay = policy.get_delay(1)   # 2.0
    should = policy.should_retry("task_1", current_retry_count=2)  # True
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# BackoffStrategy enum
# ---------------------------------------------------------------------------

class BackoffStrategy(str, Enum):
    """How to compute delay between retry attempts."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


# ---------------------------------------------------------------------------
# RetryRecord dataclass
# ---------------------------------------------------------------------------

@dataclass
class RetryRecord:
    """Tracks a single retry event for a task step."""
    task_id: str
    step_name: str
    retry_count: int
    last_error: str
    next_attempt_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        d = {
            "task_id": self.task_id,
            "step_name": self.step_name,
            "retry_count": self.retry_count,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
        }
        if self.next_attempt_at:
            d["next_attempt_at"] = self.next_attempt_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "RetryRecord":
        dt_keys = ("next_attempt_at", "created_at")
        parsed = {}
        for k, v in d.items():
            if k in dt_keys and isinstance(v, str):
                parsed[k] = datetime.fromisoformat(v)
            else:
                parsed[k] = v
        return cls(**parsed)


# ---------------------------------------------------------------------------
# RetryPolicy class
# ---------------------------------------------------------------------------

class RetryPolicy:
    """Configurable retry logic with backoff strategies.

    Args:
        max_retries:      Maximum number of retry attempts per step.
        backoff_strategy:  How to compute delay between retries.
        base_delay:       Base delay in seconds (used differently per strategy).
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
    ) -> None:
        self.max_retries = max_retries
        self.backoff_strategy = backoff_strategy
        self.base_delay = base_delay
        # Track per-task attempt counts and last errors
        self._task_attempts: dict[str, int] = {}
        self._task_errors: dict[str, str | None] = {}

    def get_delay(self, retry_count: int) -> float:
        """Return the delay (in seconds) for the given retry count.

        Args:
            retry_count:  The current retry attempt number (0-based).

        Returns:
            Delay in seconds before the next retry.
        """
        if self.backoff_strategy == BackoffStrategy.FIXED:
            return self.base_delay

        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            return self.base_delay * (2 ** retry_count)

        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            return self.base_delay * (retry_count + 1)

        else:
            raise ValueError(f"Unknown backoff strategy: {self.backoff_strategy}")

    def should_retry(self, task_id: str, current_retry_count: int) -> bool:
        """Determine whether another retry is warranted.

        Args:
            task_id:              The task identifier.
            current_retry_count:  How many retries have already been attempted.

        Returns:
            True if another retry should be attempted, False otherwise.
        """
        return current_retry_count < self.max_retries

    def record_retry(
        self,
        task_id: str,
        step_name: str,
        error: str,
    ) -> RetryRecord:
        """Create a new retry record and compute next attempt time.

        Returns:
            A :class:`RetryRecord` with computed next_attempt_at.
        """
        record = RetryRecord(
            task_id=task_id,
            step_name=step_name,
            retry_count=0,  # will be set by caller
            last_error=error,
        )
        # Compute next attempt time
        record.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=self.get_delay(0))
        return record

    def update_retry_count(self, record: RetryRecord, increment: int = 1) -> RetryRecord:
        """Increment the retry count on a record."""
        record.retry_count += increment
        record.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=self.get_delay(record.retry_count))
        return record

    def get_backoff_info(self) -> dict:
        """Return a human-readable summary of the policy."""
        return {
            "max_retries": self.max_retries,
            "backoff_strategy": self.backoff_strategy.value,
            "base_delay": self.base_delay,
            "delays": [self.get_delay(i) for i in range(self.max_retries)],
        }

    # ---- Per-task tracking helpers (used by tests) ----

    def record_attempt(self, task_id: str, error: str) -> None:
        """Record an attempt for a task (increment its retry count and store the error)."""
        self._task_attempts[task_id] = self._task_attempts.get(task_id, 0) + 1
        self._task_errors[task_id] = error

    def attempt_count(self, task_id: str) -> int:
        """Return the number of recorded attempts for a task."""
        return self._task_attempts.get(task_id, 0)

    def last_error(self, task_id: str) -> str | None:
        """Return the last recorded error for a task."""
        return self._task_errors.get(task_id)

    def reset_task(self, task_id: str) -> None:
        """Reset all retry tracking for a task."""
        self._task_attempts.pop(task_id, None)
        self._task_errors.pop(task_id, None)

    def get_all_task_retries(self) -> dict[str, int]:
        """Return a copy of all task retry counts."""
        return dict(self._task_attempts)
