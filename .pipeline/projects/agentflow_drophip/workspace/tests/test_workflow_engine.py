"""Tests for the WorkflowEngine."""

import pytest
from unittest.mock import MagicMock, patch

from agentflow_drophip.workflow.engine import WorkflowEngine, WorkflowResult
from agentflow_drophip.workflow.task import Task, TaskResult, TaskStatus
from agentflow_drophip.workflow.dag import DAG, Node
from agentflow_drophip.exceptions import CycleDetectedError


class TestWorkflowResult:
    """Tests for WorkflowResult."""

    def test_workflow_result_creation(self):
        """Test creating a WorkflowResult."""
        result = WorkflowResult(
            success=True,
            task_results={"task1": TaskResult(success=True)},
            duration=1.5,
        )
        assert result.success is True
        assert result.task_results == {"task1": TaskResult(success=True)}
        assert result.duration == 1.5
        assert result.error is None

    def test_workflow_result_failure(self):
        """Test creating a failed WorkflowResult."""
        result = WorkflowResult(
            success=False,
            error="Workflow failed",
        )
        assert result.success is False
        assert result.error == "Workflow failed"

    def test_workflow_result_to_dict(self):
        """Test serialization to dict."""
        result = WorkflowResult(
            success=True,
            task_results={"task1": TaskResult(success=True)},
            duration=1.5,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["duration"] == 1.5
        assert "task_results" in d

    def test_workflow_result_str(self):
        """Test string representation."""
        result = WorkflowResult(
            success=True,
            task_results={"task1": TaskResult(success=True)},
            duration=1.5,
        )
        s = str(result)
        assert "success=True" in s
        assert "1.5" in s


class TestWorkflowEngine:
    """Tests for WorkflowEngine."""

    def test_engine_creation(self):
        """Test creating a WorkflowEngine."""
        engine = WorkflowEngine()
        assert engine.dag is not None
        assert engine.tasks == {}
        assert engine.workflow_result is None

    def test_engine_with_config(self):
        """Test creating a WorkflowEngine with config."""
        engine = WorkflowEngine(config={"max_retries": 5})
        assert engine.config["max_retries"] == 5

    def test_add_task(self):
        """Test adding a task to the engine."""
        engine = WorkflowEngine()
        task = Task(id="task1", name="Task 1", agent_type="test")
        engine.add_task(task)
        assert "task1" in engine.tasks
        assert len(engine.dag) == 1

    def test_add_task_with_dependencies(self):
        """Test adding a task with dependencies."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        engine.add_task(task1)
        engine.add_task(task2)
        assert "task1" in engine.tasks["task2"].dependencies

    def test_add_duplicate_task_raises_error(self):
        """Test that adding a duplicate task raises ValueError."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        engine.add_task(task1)
        task2 = Task(id="task1", name="Task 1 duplicate", agent_type="test")
        with pytest.raises(ValueError, match="already exists"):
            engine.add_task(task2)

    def test_execute_workflow(self):
        """Test executing a simple workflow."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        engine.add_task(task1)
        engine.add_task(task2)

        # Mock the execute_task method
        with patch.object(engine, 'execute_task') as mock_execute:
            mock_execute.return_value = TaskResult(success=True, data={"output": "result"})
            result = engine.execute_workflow()

        assert result.success is True
        assert len(result.task_results) == 2

    def test_execute_workflow_with_failure(self):
        """Test executing a workflow where a task fails."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        engine.add_task(task1)
        engine.add_task(task2)

        def side_effect(task):
            if task.id == "task1":
                return TaskResult(success=True)
            return TaskResult(success=False, error="Task 2 failed")

        with patch.object(engine, 'execute_task', side_effect=side_effect):
            result = engine.execute_workflow()

        assert result.success is False
        assert result.error is not None

    def test_execute_workflow_with_cycle_raises_error(self):
        """Test that executing a workflow with a cycle raises CycleDetectedError."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        task3 = Task(id="task3", name="Task 3", agent_type="test", dependencies=["task2"])
        engine.add_task(task1)
        engine.add_task(task2)
        engine.add_task(task3)

        # Create a cycle
        engine.dag.add_edge("task3", "task1")

        with pytest.raises(CycleDetectedError):
            engine.execute_workflow()

    def test_execute_task_success(self):
        """Test executing a single task successfully."""
        engine = WorkflowEngine()
        task = Task(id="task1", name="Task 1", agent_type="test")
        result = TaskResult(success=True, data={"output": "result"})

        with patch.object(engine, '_execute_task_impl', return_value=result):
            executed_task = engine.execute_task(task)

        assert executed_task.status == TaskStatus.COMPLETED
        assert executed_task.result == result

    def test_execute_task_failure(self):
        """Test executing a single task that fails."""
        engine = WorkflowEngine()
        task = Task(id="task1", name="Task 1", agent_type="test")
        result = TaskResult(success=False, error="Task failed")

        with patch.object(engine, '_execute_task_impl', return_value=result):
            executed_task = engine.execute_task(task)

        assert executed_task.status == TaskStatus.FAILED
        assert executed_task.error == "Task failed"

    def test_execute_task_with_retry(self):
        """Test executing a task with retry logic."""
        engine = WorkflowEngine()
        task = Task(id="task1", name="Task 1", agent_type="test", max_retries=2)
        call_count = [0]

        def side_effect(task):
            call_count[0] += 1
            if call_count[0] < 2:
                return TaskResult(success=False, error="Temporary error")
            return TaskResult(success=True, data={"output": "result"})

        with patch.object(engine, '_execute_task_impl', side_effect=side_effect):
            executed_task = engine.execute_task(task)

        assert executed_task.status == TaskStatus.COMPLETED
        assert executed_task.result is not None
        assert call_count[0] == 2

    def test_execute_task_exceeds_max_retries(self):
        """Test that exceeding max retries results in failure."""
        engine = WorkflowEngine()
        task = Task(id="task1", name="Task 1", agent_type="test", max_retries=1)
        call_count = [0]

        def side_effect(task):
            call_count[0] += 1
            return TaskResult(success=False, error="Persistent error")

        with patch.object(engine, '_execute_task_impl', side_effect=side_effect):
            executed_task = engine.execute_task(task)

        assert executed_task.status == TaskStatus.FAILED
        assert call_count[0] == 2  # Initial + 1 retry

    def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        engine.add_task(task1)
        engine.add_task(task2)

        ready = engine.get_ready_tasks()
        assert "task1" in ready
        assert "task2" not in ready

        # Complete task1
        engine.tasks["task1"].complete(TaskResult(success=True))
        ready = engine.get_ready_tasks()
        assert "task1" not in ready
        assert "task2" in ready

    def test_get_dependent_tasks(self):
        """Test getting dependent tasks."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        task3 = Task(id="task3", name="Task 3", agent_type="test", dependencies=["task2"])
        engine.add_task(task1)
        engine.add_task(task2)
        engine.add_task(task3)

        dependents = engine.get_dependent_tasks("task1")
        assert "task2" in dependents
        assert "task3" in dependents

    def test_get_dependencies(self):
        """Test getting dependencies."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        engine.add_task(task1)
        engine.add_task(task2)

        dependencies = engine.get_dependencies("task2")
        assert "task1" in dependencies

    def test_validate_workflow_valid(self):
        """Test validating a valid workflow."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        engine.add_task(task1)
        engine.add_task(task2)
        assert engine.validate_workflow() is True

    def test_validate_workflow_invalid(self):
        """Test validating an invalid workflow."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["nonexistent"])
        engine.add_task(task1)
        engine.add_task(task2)
        assert engine.validate_workflow() is False

    def test_validate_workflow_with_cycle(self):
        """Test validating a workflow with a cycle."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test", dependencies=["task1"])
        engine.add_task(task1)
        engine.add_task(task2)
        engine.dag.add_edge("task2", "task1")
        assert engine.validate_workflow() is False

    def test_get_workflow_status(self):
        """Test getting workflow status."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test")
        engine.add_task(task1)
        engine.add_task(task2)

        status = engine.get_workflow_status()
        assert status["total"] == 2
        assert status["pending"] == 2
        assert status["completed"] == 0
        assert status["failed"] == 0

    def test_get_workflow_status_with_completed_tasks(self):
        """Test getting workflow status with completed tasks."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        task2 = Task(id="task2", name="Task 2", agent_type="test")
        engine.add_task(task1)
        engine.add_task(task2)

        task1.complete(TaskResult(success=True))
        task2.fail("Error")

        status = engine.get_workflow_status()
        assert status["total"] == 2
        assert status["completed"] == 1
        assert status["failed"] == 1

    def test_reset(self):
        """Test resetting the engine."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        engine.add_task(task1)
        task1.complete(TaskResult(success=True))
        engine.workflow_result = WorkflowResult(success=True)

        engine.reset()
        assert len(engine.tasks) == 0
        assert engine.workflow_result is None

    def test_execute_workflow_with_error_handling(self):
        """Test that workflow handles errors gracefully."""
        engine = WorkflowEngine()
        task1 = Task(id="task1", name="Task 1", agent_type="test")
        engine.add_task(task1)

        with patch.object(engine, 'execute_task', side_effect=Exception("Unexpected error")):
            result = engine.execute_workflow()
            assert result.success is False
            assert result.error is not None
