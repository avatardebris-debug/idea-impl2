"""Task Queue — JSON-lines backed bulk SOP execution queue management.

Stores queue metadata and task records as JSON-lines files on disk so
that state survives process restarts.

Usage:
    from drop_servicing_tool.task_queue import TaskQueue, TaskStatus

    tq = TaskQueue()
    queue_id = tq.create_queue("blog_post", [{"topic": "AI"}, {"topic": "ML"}])
    queue = tq.get_queue(queue_id)
    print(queue["queue_id"], queue["total_tasks"])
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------------

_DEFAULT_QUEUE_DIR = Path(__file__).resolve().parent.parent / "bulk_queues"


def _get_queue_dir() -> Path:
    """Get the queue directory, respecting DST_BULK_BASE_DIR env var."""
    env_dir = os.environ.get("DST_BULK_BASE_DIR")
    if env_dir:
        return Path(env_dir)
    return _DEFAULT_QUEUE_DIR


# ---------------------------------------------------------------------------
# TaskStatus enum
# -----------------------------------------------------------------------------------

class TaskStatus(str, Enum):
    """Possible execution states for a single task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# TaskQueue class
# -----------------------------------------------------------------------------------

class TaskQueue:
    """Manages bulk SOP execution jobs backed by JSON-lines files.

    Each queue gets its own directory under *bulk_queues/* with two files:
        <queue_id>.jsonl          — task records
        <queue_id>_metadata.json  — queue-level metadata
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or _get_queue_dir()
        self._base.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_queue(self, sop_name: str, inputs: list[dict], max_retries: int = 3) -> str:
        """Create a new queue from a list of input dicts.

        Args:
            sop_name:      Name of the SOP this queue belongs to.
            inputs:        List of input dicts — one per task.
            max_retries:   Default max retries per task.

        Returns:
            A unique queue_id (UUID4 hex string).
        """
        queue_id = uuid.uuid4().hex[:12]
        ts = datetime.now(timezone.utc).isoformat()

        # Write metadata
        meta = {
            "queue_id": queue_id,
            "sop_name": sop_name,
            "max_retries": max_retries,
            "created_at": ts,
            "total_tasks": len(inputs),
        }
        (self._base / f"{queue_id}_metadata.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        # Write tasks (one JSON object per line)
        tasks_path = self._base / f"{queue_id}.jsonl"
        with open(tasks_path, "w", encoding="utf-8") as fh:
            for idx, inp in enumerate(inputs):
                task = {
                    "task_id": f"{queue_id}_t{idx:04d}",
                    "status": TaskStatus.PENDING,
                    "input_data": inp,
                    "retry_count": 0,
                    "created_at": ts,
                }
                fh.write(json.dumps(task, ensure_ascii=False) + "\n")

        return queue_id

    def get_queue(self, queue_id: str) -> dict:
        """Return queue metadata and task list."""
        meta_path = self._base / f"{queue_id}_metadata.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Queue not found: {queue_id}")

        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        tasks_path = self._base / f"{queue_id}.jsonl"
        tasks: list[dict] = []
        if tasks_path.exists():
            for line in tasks_path.read_text(encoding="utf-8").strip().splitlines():
                if line.strip():
                    tasks.append(json.loads(line))

        meta["tasks"] = tasks
        return meta

    def update_task_status(self, queue_id: str, task_id: str, status: str) -> None:
        """Update the status of a single task in-place on disk."""
        tasks_path = self._base / f"{queue_id}.jsonl"
        if not tasks_path.exists():
            raise FileNotFoundError(f"Queue not found: {queue_id}")

        updated = False
        lines = tasks_path.read_text(encoding="utf-8").strip().splitlines()
        new_lines: list[str] = []
        for line in lines:
            if not line.strip():
                continue
            task = json.loads(line)
            if task["task_id"] == task_id:
                task["status"] = status
                task["updated_at"] = datetime.now(timezone.utc).isoformat()
                updated = True
            new_lines.append(json.dumps(task, ensure_ascii=False))

        if not updated:
            raise ValueError(f"Task '{task_id}' not found in queue '{queue_id}'")

        tasks_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    def get_pending_tasks(self, queue_id: str) -> list[dict]:
        """Return all tasks that are still pending."""
        tasks = self._read_tasks(queue_id)
        return [t for t in tasks if t["status"] == TaskStatus.PENDING]

    def get_all_task_statuses(self, queue_id: str) -> dict:
        """Return {task_id: status} mapping for every task."""
        tasks = self._read_tasks(queue_id)
        return {t["task_id"]: t["status"] for t in tasks}

    def get_task_count_by_status(self, queue_id: str) -> dict:
        """Return counts of tasks grouped by status."""
        statuses = self.get_all_task_statuses(queue_id)
        counts: dict[str, int] = {}
        for s in statuses.values():
            counts[s] = counts.get(s, 0) + 1
        return counts

    def mark_all_completed(self, queue_id: str) -> None:
        """Mark every pending/running task as completed (useful for mock mode)."""
        tasks = self._read_tasks(queue_id)
        updated = False
        lines: list[str] = []
        for t in tasks:
            if t["status"] in (TaskStatus.PENDING, TaskStatus.RUNNING):
                t["status"] = TaskStatus.COMPLETED
                t["updated_at"] = datetime.now(timezone.utc).isoformat()
                updated = True
            lines.append(json.dumps(t, ensure_ascii=False))
        if updated:
            (self._base / f"{queue_id}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def delete_queue(self, queue_id: str) -> bool:
        """Remove a queue and all its files. Returns True if it existed."""
        meta_path = self._base / f"{queue_id}_metadata.json"
        task_path = self._base / f"{queue_id}.jsonl"
        result = False
        if meta_path.exists():
            meta_path.unlink()
            result = True
        if task_path.exists():
            task_path.unlink()
            result = True
        return result

    def get_sop(self, sop_name: str) -> dict:
        """Load an SOP by name from the SOP store.

        Returns:
            SOP dict (the raw parsed YAML content).
        """
        from .sop_store import get_sop as _get_sop
        sop = _get_sop(sop_name)
        return sop.model_dump()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_tasks(self, queue_id: str) -> list[dict]:
        tasks_path = self._base / f"{queue_id}.jsonl"
        if not tasks_path.exists():
            raise FileNotFoundError(f"Queue not found: {queue_id}")
        lines = tasks_path.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(l) for l in lines if l.strip()]
