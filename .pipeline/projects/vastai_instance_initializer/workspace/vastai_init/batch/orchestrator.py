"""Batch orchestrator engine.

Manages queuing, timing, concurrency, and instance state tracking for
multi-instance batch launches on VAST.ai.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import BatchConfig, BatchPresetRef
from .state import BatchState, InstanceState, save_batch_state


@dataclass
class LaunchTask:
    """A single instance launch task within a batch."""

    preset_ref: BatchPresetRef
    count_index: int  # 0-based index within the preset's count
    timing_offset: float  # seconds to wait before launching
    status: str = "pending"  # pending | launching | running | failed | stopped | skipped
    instance_id: str = ""
    error: str = ""
    started_at: float = 0.0
    stopped_at: float = 0.0


@dataclass
class BatchResult:
    """Results of a completed batch launch."""

    batch_name: str
    total_instances: int
    launched: int
    failed: int
    stopped: int
    skipped: int
    elapsed_seconds: float
    errors: list[str] = field(default_factory=list)


class BatchOrchestrator:
    """Orchestrates batch instance launches with timing and concurrency control."""

    def __init__(
        self,
        config: BatchConfig,
        *,
        dry_run: bool = False,
        state_path: str | None = None,
        on_instance_status: Callable[[str, str, str], None] | None = None,
    ):
        """Initialize the orchestrator.

        Args:
            config: The batch configuration.
            dry_run: If True, do not actually launch instances.
            state_path: Path to save/load batch state for pause/resume.
            on_instance_status: Callback for instance status updates.
        """
        self.config = config
        self.dry_run = dry_run
        self.state_path = state_path
        self.on_instance_status = on_instance_status or self._noop_callback

        # Build the task list from config
        self.tasks: list[LaunchTask] = self._build_tasks(config)

        # State tracking
        self.batch_state: BatchState | None = None
        self._result: BatchResult | None = None
        self._started_at: float = 0.0
        self._completed_at: float = 0.0

    @staticmethod
    def _noop_callback(*args: Any, **kwargs: Any) -> None:
        pass

    def _build_tasks(self, config: BatchConfig) -> list[LaunchTask]:
        """Build the list of launch tasks from the batch config."""
        tasks: list[LaunchTask] = []

        for preset_ref in config.presets:
            for i in range(preset_ref.count):
                tasks.append(LaunchTask(
                    preset_ref=preset_ref,
                    count_index=i,
                    timing_offset=0.0,
                ))

        # Apply timing offsets
        if config.timing.delay_seconds > 0:
            # All tasks start after the initial delay
            for task in tasks:
                task.timing_offset = config.timing.delay_seconds

        if config.timing.stagger_percent > 0:
            # Distribute stagger offsets across tasks
            total_tasks = len(tasks)
            if total_tasks > 1:
                stagger_range = config.timing.delay_seconds or 60.0  # default range
                stagger_step = stagger_range / (total_tasks - 1)
                for idx, task in enumerate(tasks):
                    task.timing_offset = stagger_step * idx

        return tasks

    def _update_status(self, task: LaunchTask, status: str, instance_id: str = "", error: str = "") -> None:
        """Update task status and notify callback."""
        task.status = status
        if instance_id:
            task.instance_id = instance_id
        if error:
            task.error = error

        if status in ("launched", "running"):
            task.started_at = time.time()
        elif status in ("failed", "stopped", "skipped"):
            task.stopped_at = time.time()

        self.on_instance_status(task.preset_ref.preset_path, task.count_index, status, instance_id, error)

    def _save_state(self) -> None:
        """Save current batch state for pause/resume."""
        if not self.state_path or not self.batch_state:
            return

        # Update instances from tasks
        self.batch_state.instances = [
            InstanceState(
                instance_id=t.instance_id,
                preset_path=t.preset_ref.preset_path,
                count_index=t.count_index,
                status=t.status,
                error=t.error,
                started_at=t.started_at,
                stopped_at=t.stopped_at,
                timing_offset=t.timing_offset,
            )
            for t in self.tasks
        ]
        self.batch_state.status = self._get_batch_status()
        save_batch_state(self.batch_state, self.state_path)

    def _get_batch_status(self) -> str:
        """Determine overall batch status from task statuses."""
        if not self.tasks:
            return "completed"

        statuses = {t.status for t in self.tasks}
        if "pending" in statuses or "launching" in statuses or "running" in statuses:
            return "running"
        if all(t.status in ("completed", "stopped", "skipped") for t in self.tasks):
            return "completed"
        if "failed" in statuses:
            return "failed"
        return "running"

    async def launch(self) -> BatchResult:
        """Execute the batch launch.

        Returns:
            BatchResult with launch statistics.
        """
        self._started_at = time.time()

        if self.state_path:
            # Try to load existing state for resume
            try:
                from .state import load_batch_state
                self.batch_state = load_batch_state(self.state_path)
                # Restore task states from saved state
                for task, inst in zip(self.tasks, self.batch_state.instances):
                    task.status = inst.status
                    task.instance_id = inst.instance_id
                    task.error = inst.error
                    task.started_at = inst.started_at
                    task.stopped_at = inst.stopped_at
            except FileNotFoundError:
                self.batch_state = BatchState(
                    batch_name=self.config.name,
                    source_path=str(self.state_path),
                    presets=[p.to_dict() for p in self.config.presets],
                    timing={"delay_seconds": self.config.timing.delay_seconds,
                            "stagger_percent": self.config.timing.stagger_percent},
                    concurrency=self.config.concurrency,
                    timeout=self.config.timeout,
                )

        # Filter out already-completed tasks
        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        if not pending_tasks:
            self._completed_at = time.time()
            self._result = BatchResult(
                batch_name=self.config.name,
                total_instances=len(self.tasks),
                launched=sum(1 for t in self.tasks if t.status in ("completed", "stopped")),
                failed=sum(1 for t in self.tasks if t.status == "failed"),
                stopped=sum(1 for t in self.tasks if t.status == "stopped"),
                skipped=sum(1 for t in self.tasks if t.status == "skipped"),
                elapsed_seconds=self._completed_at - self._started_at,
            )
            return self._result

        # Launch tasks with concurrency control
        semaphore = asyncio.Semaphore(self.config.concurrency)
        errors: list[str] = []

        async def launch_single(task: LaunchTask) -> None:
            """Launch a single instance with timing delay."""
            # Wait for timing offset
            if task.timing_offset > 0:
                await asyncio.sleep(task.timing_offset)

            async with semaphore:
                self._update_status(task, "launching")

                if self.dry_run:
                    # Simulate launch
                    task.instance_id = f"dry-run-{task.preset_ref.preset_path}-{task.count_index}"
                    await asyncio.sleep(0.01)  # Simulate network delay
                    task.status = "completed"
                    self._update_status(task, "completed", task.instance_id)
                else:
                    # TODO: Actually launch on VAST.ai
                    # For now, simulate
                    task.instance_id = f"sim-{task.preset_ref.preset_path}-{task.count_index}"
                    await asyncio.sleep(0.01)
                    task.status = "completed"
                    self._update_status(task, "completed", task.instance_id)

                self._save_state()

        # Execute all pending tasks
        launch_coros = [launch_single(t) for t in pending_tasks]
        await asyncio.gather(*launch_coros, return_exceptions=True)

        # Collect errors
        for task in self.tasks:
            if task.status == "failed":
                errors.append(f"{task.preset_ref.preset_path}[{task.count_index}]: {task.error}")

        self._completed_at = time.time()
        self._result = BatchResult(
            batch_name=self.config.name,
            total_instances=len(self.tasks),
            launched=sum(1 for t in self.tasks if t.status in ("completed", "stopped")),
            failed=sum(1 for t in self.tasks if t.status == "failed"),
            stopped=sum(1 for t in self.tasks if t.status == "stopped"),
            skipped=sum(1 for t in self.tasks if t.status == "skipped"),
            elapsed_seconds=self._completed_at - self._started_at,
            errors=errors,
        )

        return self._result

    def get_result(self) -> BatchResult | None:
        """Get the batch launch result."""
        return self._result

    def get_tasks(self) -> list[LaunchTask]:
        """Get all launch tasks."""
        return self.tasks

    def get_task_count(self) -> int:
        """Get total number of tasks."""
        return len(self.tasks)

    def get_pending_count(self) -> int:
        """Get number of pending tasks."""
        return sum(1 for t in self.tasks if t.status == "pending")

    def get_completed_count(self) -> int:
        """Get number of completed tasks."""
        return sum(1 for t in self.tasks if t.status in ("completed", "stopped"))

    def get_failed_count(self) -> int:
        """Get number of failed tasks."""
        return sum(1 for t in self.tasks if t.status == "failed")
