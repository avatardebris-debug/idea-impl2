"""Bulk Runner — orchestrates parallel execution of SOP tasks.

Uses ThreadPoolExecutor to process multiple tasks concurrently with
configurable rate limiting and token budgets.

Usage:
    from drop_servicing_tool.bulk_runner import BulkRunner

    runner = BulkRunner(
        sop_name="blog_post",
        queue_id="abc123",
        max_workers=4,
        rate_limit_per_second=2.0,
        token_budget=10000,
        use_mock_llm=True,
    )
    summary = runner.run()
    print(summary["completed_tasks"], summary["failed_tasks"])
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from .executor import MockLLMClient, SOPExecutor
from .retry_policy import RetryPolicy
from .sop_schema import SOP
from .task_queue import TaskQueue, TaskStatus
from .results_store import ResultsStore


# ---------------------------------------------------------------------------
# Task result dataclass
# ---------------------------------------------------------------------------

@dataclass
class TaskResult:
    """Result of executing a single task."""
    task_id: str
    status: str
    result_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    tokens_used: int = 0
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# BulkRunner class
# ---------------------------------------------------------------------------

class BulkRunner:
    """Orchestrates parallel execution of SOP tasks with rate limiting.

    Args:
        sop_name:              Name of the SOP to execute.
        queue_id:              Queue ID from TaskQueue.
        max_workers:           Maximum parallel tasks (default 4).
        rate_limit_per_second: Requests per second (default 1.0).
        token_budget:          Total token budget (default None = unlimited).
        use_mock_llm:          Use MockLLMClient (default False).
        retry_policy:          RetryPolicy instance (default: 3 retries, exponential).
        base_dir:              Override base directory for TaskQueue/ResultsStore.
    """

    def __init__(
        self,
        sop_name: str,
        queue_id: str,
        max_workers: int = 4,
        rate_limit_per_second: float = 1.0,
        token_budget: Optional[int] = None,
        use_mock_llm: bool = False,
        retry_policy: Optional[RetryPolicy] = None,
        base_dir: Optional[Path] = None,
    ) -> None:
        self.sop_name = sop_name
        self.queue_id = queue_id
        self.max_workers = max_workers
        self.rate_limit = rate_limit_per_second
        self.token_budget = token_budget
        self.use_mock_llm = use_mock_llm
        self.retry_policy = retry_policy or RetryPolicy()
        self._base_dir = base_dir
        self._task_queue = TaskQueue(base_dir=base_dir)
        self._results_store = ResultsStore(base_dir=base_dir)
        self._sop: Optional[SOP] = None
        self._lock = Lock()
        self._tokens_used = 0
        self._completed_count = 0
        self._failed_count = 0

    def _get_sop(self) -> SOP:
        """Load SOP (cached after first load)."""
        if self._sop is None:
            from .sop_store import get_sop
            self._sop = get_sop(self.sop_name)
        return self._sop

    def _get_llm_client(self) -> Any:
        """Get the LLM client (mock or real)."""
        if self.use_mock_llm:
            return MockLLMClient()
        # For real LLM, you'd instantiate your client here
        raise RuntimeError("Real LLM client not implemented. Set use_mock_llm=True for testing.")

    def _execute_task(self, task: dict) -> TaskResult:
        """Execute a single task with retry logic."""
        task_id = task["task_id"]
        input_data = task["input_data"]
        max_retries = task.get("max_retries", self.retry_policy.max_retries)

        last_error: Optional[str] = None
        for attempt in range(max_retries + 1):
            if attempt > 0:
                delay = self.retry_policy.get_delay(attempt - 1)
                time.sleep(delay)

            try:
                llm_client = self._get_llm_client()
                executor = SOPExecutor(self._get_sop(), llm_client)
                result = executor.run(input_data)

                # Extract tokens from result
                tokens = result.get("tokens_used", 0)
                with self._lock:
                    self._tokens_used += tokens
                    self._completed_count += 1

                log = executor.get_execution_log()
                duration = log[-1].duration_seconds if log else 0.0
                return TaskResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED.value,
                    result_data=result,
                    tokens_used=tokens,
                    duration_seconds=duration,
                    metadata={"attempts": attempt + 1},
                )

            except Exception as exc:
                last_error = str(exc)
                if attempt == max_retries:
                    break
                if not self.retry_policy.should_retry(task_id, attempt):
                    break

        with self._lock:
            self._failed_count += 1

        return TaskResult(
            task_id=task_id,
            status=TaskStatus.FAILED.value,
            error=last_error,
            metadata={"attempts": max_retries + 1},
        )

    def _rate_limit(self) -> None:
        """Throttle execution to meet rate limit."""
        if self.rate_limit <= 0:
            return
        interval = 1.0 / self.rate_limit
        time.sleep(interval)

    def _check_token_budget(self) -> bool:
        """Check if token budget is exceeded."""
        if self.token_budget is None:
            return True
        return self._tokens_used < self.token_budget

    def run(self) -> Dict[str, Any]:
        """Execute all tasks in the queue.

        Returns:
            Summary dict with execution statistics.
        """
        queue = self._task_queue.get_queue(self.queue_id)
        tasks = queue.get("tasks", [])

        if not tasks:
            return {
                "completed_tasks": 0,
                "failed_tasks": 0,
                "total_tasks": 0,
                "total_tokens": 0,
                "total_duration": 0.0,
            }

        # Execute tasks with thread pool
        start_time = time.time()
        futures = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for task in tasks:
                if not self._check_token_budget():
                    # Mark remaining tasks as skipped
                    self._task_queue.update_task_status(
                        self.queue_id, task["task_id"], TaskStatus.FAILED.value
                    )
                    continue

                future = executor.submit(self._execute_task, task)
                futures[future] = task

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()

                    # Store result
                    self._results_store.store_result(
                        self.queue_id,
                        result.task_id,
                        result.result_data,
                        tokens_used=result.tokens_used,
                        duration_seconds=result.duration_seconds,
                        status=result.status,
                        error=result.error,
                        metadata=result.metadata,
                    )

                    # Update task status
                    self._task_queue.update_task_status(
                        self.queue_id, result.task_id, result.status
                    )

                    # Rate limiting
                    self._rate_limit()

                except Exception as exc:
                    self._results_store.store_result(
                        self.queue_id,
                        task["task_id"],
                        {},
                        status=TaskStatus.FAILED.value,
                        error=str(exc),
                    )
                    self._task_queue.update_task_status(
                        self.queue_id, task["task_id"], TaskStatus.FAILED.value
                    )

        elapsed = time.time() - start_time

        summary = {
            "completed_tasks": self._completed_count,
            "failed_tasks": self._failed_count,
            "total_tasks": len(tasks),
            "total_tokens": self._tokens_used,
            "total_duration": elapsed,
            "sop_name": self.sop_name,
            "queue_id": self.queue_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save summary
        self._results_store._update_summary(self.queue_id)

        return summary

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary (calls run() if not yet executed)."""
        summary_file = self._base_dir / self.queue_id / "summary.json" if self._base_dir else None
        if summary_file and summary_file.exists():
            return json.loads(summary_file.read_text(encoding="utf-8"))
        return self.run()

    def get_all_results(self) -> List[Dict[str, Any]]:
        """Get all task results."""
        return self._results_store.get_all_results(self.queue_id)

    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Get a single task result."""
        return self._results_store.get_result(self.queue_id, task_id)

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending tasks."""
        return self._task_queue.get_pending_tasks(self.queue_id)

    def get_queue(self) -> Dict[str, Any]:
        """Get queue information."""
        return self._task_queue.get_queue(self.queue_id)
