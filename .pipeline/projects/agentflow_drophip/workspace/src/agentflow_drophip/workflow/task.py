"""Task model for workflow execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Status of a workflow task."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """Result of a task execution."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return self.success


@dataclass
class Task:
    """A single task in a workflow DAG."""

    id: str
    name: str
    agent_type: str  # e.g., "sourcing", "listing", "fulfillment"
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    result: Optional[TaskResult] = None
    retries: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def start(self) -> None:
        """Mark the task as running."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def complete(self, result: TaskResult) -> None:
        """Mark the task as completed with a result."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        """Mark the task as failed."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc)

    def retry(self) -> None:
        """Increment retry count and mark as retrying."""
        self.retries += 1
        self.status = TaskStatus.RETRYING
        self.started_at = datetime.now(timezone.utc)

    def skip(self) -> None:
        """Mark the task as skipped."""
        self.status = TaskStatus.SKIPPED
        self.completed_at = datetime.now(timezone.utc)

    @property
    def is_done(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)

    @property
    def is_ready(self) -> bool:
        """Check if all dependencies are completed."""
        if not self.dependencies:
            return self.status == TaskStatus.PENDING
        return False  # Handled by WorkflowEngine

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "data": self.data,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Deserialize task from dictionary."""
        task = cls(
            id=data["id"],
            name=data["name"],
            agent_type=data["agent_type"],
            status=TaskStatus(data.get("status", "pending")),
            dependencies=data.get("dependencies", []),
            data=data.get("data", {}),
            retries=data.get("retries", 0),
            max_retries=data.get("max_retries", 3),
        )
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            task.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])
        if data.get("error"):
            task.error = data["error"]
        return task
