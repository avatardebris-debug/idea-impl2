"""Tests for the Task model."""

import pytest
from datetime import datetime, timezone

from agentflow_drophip.workflow.task import Task, TaskResult, TaskStatus


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRYING.value == "retrying"
        assert TaskStatus.SKIPPED.value == "skipped"


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_task_result_creation(self):
        """Test creating a TaskResult."""
        result = TaskResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.warnings == []
        assert result.is_success is True

    def test_task_result_failure(self):
        """Test creating a failed TaskResult."""
        result = TaskResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.is_success is False

    def test_task_result_defaults(self):
        """Test default values for TaskResult."""
        result = TaskResult(success=True)
        assert result.data == {}
        assert result.error is None
        assert result.warnings == []


class TestTask:
    """Tests for Task dataclass."""

    def test_task_creation(self):
        """Test creating a Task."""
        task = Task(
            id="test-1",
            name="Test Task",
            agent_type="test",
        )
        assert task.id == "test-1"
        assert task.name == "Test Task"
        assert task.agent_type == "test"
        assert task.status == TaskStatus.PENDING
        assert task.dependencies == []
        assert task.data == {}
        assert task.result is None
        assert task.retries == 0
        assert task.max_retries == 3
        assert task.created_at is not None
        assert task.started_at is None
        assert task.completed_at is None
        assert task.error is None

    def test_task_start(self):
        """Test starting a task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        task.start()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        assert task.completed_at is None

    def test_task_complete(self):
        """Test completing a task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        result = TaskResult(success=True, data={"output": "value"})
        task.complete(result)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task.completed_at is not None

    def test_task_fail(self):
        """Test failing a task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        task.fail("Error occurred")
        assert task.status == TaskStatus.FAILED
        assert task.error == "Error occurred"
        assert task.completed_at is not None

    def test_task_retry(self):
        """Test retrying a task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        task.retry()
        assert task.status == TaskStatus.RETRYING
        assert task.retries == 1
        assert task.started_at is not None

    def test_task_skip(self):
        """Test skipping a task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        task.skip()
        assert task.status == TaskStatus.SKIPPED
        assert task.completed_at is not None

    def test_task_is_done_completed(self):
        """Test is_done property for completed task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        task.complete(TaskResult(success=True))
        assert task.is_done is True

    def test_task_is_done_failed(self):
        """Test is_done property for failed task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        task.fail("Error")
        assert task.is_done is True

    def test_task_is_done_skipped(self):
        """Test is_done property for skipped task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        task.skip()
        assert task.is_done is True

    def test_task_is_done_pending(self):
        """Test is_done property for pending task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        assert task.is_done is False

    def test_task_is_done_running(self):
        """Test is_done property for running task."""
        task = Task(id="test-1", name="Test", agent_type="test")
        task.start()
        assert task.is_done is False

    def test_task_to_dict(self):
        """Test serialization to dict."""
        task = Task(
            id="test-1",
            name="Test",
            agent_type="test",
            status=TaskStatus.COMPLETED,
            dependencies=["dep1"],
            data={"key": "value"},
            retries=1,
            max_retries=3,
        )
        task.start()
        task.complete(TaskResult(success=True))
        d = task.to_dict()
        assert d["id"] == "test-1"
        assert d["name"] == "Test"
        assert d["agent_type"] == "test"
        assert d["status"] == "completed"
        assert d["dependencies"] == ["dep1"]
        assert d["data"] == {"key": "value"}
        assert d["retries"] == 1
        assert d["max_retries"] == 3
        assert d["created_at"] is not None
        assert d["started_at"] is not None
        assert d["completed_at"] is not None
        assert d["error"] is None

    def test_task_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "id": "test-1",
            "name": "Test",
            "agent_type": "test",
            "status": "completed",
            "dependencies": ["dep1"],
            "data": {"key": "value"},
            "retries": 1,
            "max_retries": 3,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
        task = Task.from_dict(data)
        assert task.id == "test-1"
        assert task.name == "Test"
        assert task.agent_type == "test"
        assert task.status == TaskStatus.COMPLETED
        assert task.dependencies == ["dep1"]
        assert task.data == {"key": "value"}
        assert task.retries == 1
        assert task.max_retries == 3
        assert task.created_at is not None
        assert task.started_at is not None
        assert task.completed_at is not None
        assert task.error is None

    def test_task_from_dict_defaults(self):
        """Test from_dict with minimal data."""
        data = {
            "id": "test-1",
            "name": "Test",
            "agent_type": "test",
        }
        task = Task.from_dict(data)
        assert task.id == "test-1"
        assert task.status == TaskStatus.PENDING
        assert task.dependencies == []
        assert task.data == {}
        assert task.retries == 0
        assert task.max_retries == 3

    def test_task_from_dict_with_error(self):
        """Test from_dict with error."""
        data = {
            "id": "test-1",
            "name": "Test",
            "agent_type": "test",
            "status": "failed",
            "error": "Something went wrong",
        }
        task = Task.from_dict(data)
        assert task.status == TaskStatus.FAILED
        assert task.error == "Something went wrong"
