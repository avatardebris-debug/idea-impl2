"""WorkflowEngine — executes DAG-based workflows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from agentflow_drophip.exceptions import WorkflowError
from agentflow_drophip.models.business_spec import BusinessSpec
from agentflow_drophip.workflow.dag import DAG, Node
from agentflow_drophip.workflow.task import Task, TaskResult, TaskStatus


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    workflow_id: str
    status: str  # completed, failed, partial
    tasks: Dict[str, Task] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    @property
    def is_success(self) -> bool:
        return self.status == "completed"

    @property
    def is_failure(self) -> bool:
        return self.status == "failed"

    @property
    def is_partial(self) -> bool:
        return self.status == "partial"


class WorkflowEngine:
    """Executes DAG-based workflows with task management and error handling."""

    def __init__(self, dag: DAG):
        """Initialize the workflow engine.

        Args:
            dag: The DAG defining the workflow structure.
        """
        self.dag = dag
        self.tasks: Dict[str, Task] = {}
        self.workflow_id = str(uuid.uuid4())
        self.result: Optional[WorkflowResult] = None

    def initialize_tasks(self) -> None:
        """Initialize tasks from the DAG nodes."""
        for node_id, node in self.dag.nodes.items():
            self.tasks[node_id] = Task(
                id=node_id,
                name=node.label,
                agent_type=node_id,  # Default agent type
                status=TaskStatus.PENDING,
                dependencies=node.dependencies,
                data=node.data,
            )

    def execute(self, task_handlers: Dict[str, Callable[[Task], TaskResult]]) -> WorkflowResult:
        """Execute the workflow using the provided task handlers.

        Args:
            task_handlers: Mapping of task_id to handler function.

        Returns:
            WorkflowResult with execution status.
        """
        self.initialize_tasks()
        self.result = WorkflowResult(
            workflow_id=self.workflow_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Get execution order
            execution_order = self.dag.topological_sort()

            # Execute tasks in order
            for task_id in execution_order:
                task = self.tasks[task_id]

                # Check if dependencies are met
                if not self._are_dependencies_met(task):
                    task.skip()
                    continue

                # Execute task
                task.start()
                try:
                    handler = task_handlers.get(task_id)
                    if not handler:
                        raise WorkflowError(
                            f"No handler for task '{task_id}'",
                            task_id=task_id,
                        )

                    result = handler(task)
                    task.complete(result)

                    # If task failed, mark dependents as skipped
                    if not result.success:
                        self._handle_task_failure(task, result.error or "Unknown error")

                except Exception as e:
                    task.fail(str(e))
                    self._handle_task_failure(task, str(e))

            # Determine final status
            completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
            failed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]

            if failed_tasks:
                self.result.status = "partial" if completed_tasks else "failed"
                self.result.errors = [t.error for t in failed_tasks if t.error]
            else:
                self.result.status = "completed"

        except Exception as e:
            self.result.status = "failed"
            self.result.errors.append(str(e))
            raise WorkflowError(
                f"Workflow execution failed: {e}",
                workflow_id=self.workflow_id,
            ) from e

        finally:
            self.result.completed_at = datetime.now(timezone.utc)
            if self.result.started_at:
                self.result.duration_seconds = (
                    self.result.completed_at - self.result.started_at
                ).total_seconds()

        return self.result

    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if all dependencies for a task are completed."""
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
        return True

    def _handle_task_failure(self, task: Task, error: str) -> None:
        """Handle task failure by marking dependents as skipped."""
        dependents = self.dag.get_dependents(task.id)
        for dep_id in dependents:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if dep_task.status == TaskStatus.PENDING:
                    dep_task.skip()
                    self.result.errors.append(
                        f"Task '{dep_id}' skipped due to failure in '{task.id}': {error}"
                    )

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a specific task."""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None

    def get_all_task_statuses(self) -> Dict[str, str]:
        """Get status of all tasks."""
        return {task_id: task.status.value for task_id, task in self.tasks.items()}

    def retry_failed_tasks(self, task_handlers: Dict[str, Callable[[Task], TaskResult]]) -> WorkflowResult:
        """Retry all failed tasks.

        Args:
            task_handlers: Mapping of task_id to handler function.

        Returns:
            Updated WorkflowResult.
        """
        if not self.result:
            raise WorkflowError("No workflow result available")

        failed_tasks = [
            task_id
            for task_id, task in self.tasks.items()
            if task.status == TaskStatus.FAILED and task.retries < task.max_retries
        ]

        for task_id in failed_tasks:
            task = self.tasks[task_id]
            task.retry()
            try:
                handler = task_handlers.get(task_id)
                if handler:
                    result = handler(task)
                    task.complete(result)
                else:
                    task.fail("No handler available for retry")
            except Exception as e:
                task.fail(str(e))

        # Update result status
        remaining_failed = [
            task_id
            for task_id, task in self.tasks.items()
            if task.status == TaskStatus.FAILED
        ]

        if remaining_failed:
            self.result.status = "partial" if any(
                task.status == TaskStatus.COMPLETED
                for task in self.tasks.values()
            ) else "failed"
        else:
            self.result.status = "completed"

        return self.result
