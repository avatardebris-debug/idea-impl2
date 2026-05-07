"""SOP DSL engine — executes workflow steps defined in YAML."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import yaml

from supportagent.models import (
    SOPWorkflow,
    Ticket,
    WorkflowExecution,
    WorkflowStep,
    StepType,
    GateType,
)


class SOPEngine:
    """Executes SOP workflows defined in YAML files."""

    def __init__(self, workflows_dir: Optional[str] = None):
        """Initialize the SOP engine.

        Args:
            workflows_dir: Path to the directory containing workflow YAML files.
        """
        if workflows_dir is None:
            workflows_dir = os.path.join(
                os.path.dirname(__file__), "config", "sop_workflows"
            )
        self.workflows_dir = workflows_dir
        self.workflows: Dict[str, SOPWorkflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self._load_workflows()

    def _load_workflows(self) -> None:
        """Load all workflow YAML files from the workflows directory."""
        if not os.path.exists(self.workflows_dir):
            return
        for filename in os.listdir(self.workflows_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.workflows_dir, filename)
                with open(filepath, "r") as f:
                    workflow = SOPWorkflow.from_yaml(f.read())
                self.workflows[workflow.name] = workflow

    def get_workflow(self, name: str) -> Optional[SOPWorkflow]:
        """Get a workflow by name.

        Args:
            name: The workflow name.

        Returns:
            The SOPWorkflow object, or None if not found.
        """
        return self.workflows.get(name)

    def get_all_workflows(self) -> Dict[str, SOPWorkflow]:
        """Get all loaded workflows.

        Returns:
            Dict mapping workflow names to SOPWorkflow objects.
        """
        return self.workflows.copy()

    def execute(self, workflow_name: str, ticket: Ticket) -> WorkflowExecution:
        """Execute a workflow for a ticket.

        Args:
            workflow_name: The name of the workflow to execute.
            ticket: The ticket to process.

        Returns:
            The WorkflowExecution object tracking the execution.
        """
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found")

        execution = WorkflowExecution(
            execution_id=f"{workflow_name}_{ticket.ticket_id}",
            ticket_id=ticket.ticket_id,
            workflow_name=workflow_name,
        )
        self.executions[execution.execution_id] = execution

        step_index = 0
        while step_index < len(workflow.steps):
            step = workflow.steps[step_index]
            execution.current_step_index = step_index

            if step.type == StepType.ACTION:
                result = self._execute_action(step, ticket)
                execution.step_results[step.id] = result
                step_index += 1

            elif step.type == StepType.CONDITION:
                result = self._evaluate_condition(step, ticket)
                execution.step_results[step.id] = result
                if result:
                    next_step = step.then_step
                else:
                    next_step = step.else_step
                if next_step:
                    step_index = self._find_step_index(workflow, next_step)
                else:
                    step_index += 1

            elif step.type == StepType.GATE:
                execution.status = "paused"
                execution.paused_at = ticket.updated_at
                return execution

            if execution.status == "failed":
                break

        execution.status = "completed"
        execution.completed_at = ticket.updated_at
        return execution

    def _execute_action(self, step: WorkflowStep, ticket: Ticket) -> Dict[str, Any]:
        """Execute an action step.

        Args:
            step: The action step to execute.
            ticket: The current ticket.

        Returns:
            Result dictionary.
        """
        action = step.action
        params = step.params

        if action == "classify_ticket":
            # This is handled by the classifier, but we record it here
            return {"action": "classify_ticket", "status": "recorded"}

        elif action == "assign_team":
            team = params.get("team", "general_team")
            ticket.assigned_team = team
            ticket.status = "routed"
            return {"action": "assign_team", "team": team}

        elif action == "escalate":
            target = params.get("target_team", "escalation_team")
            reason = params.get("reason", "escalation")
            ticket.status = "routed"
            return {"action": "escalate", "target": target, "reason": reason}

        elif action == "generate_draft":
            template = params.get("template", "general_response")
            tone = params.get("tone", "professional")
            # This would call the response generator
            return {"action": "generate_draft", "template": template, "tone": tone}

        elif action == "send_response":
            ticket.status = "sent"
            return {"action": "send_response", "status": "sent"}

        elif action == "notify":
            channels = params.get("channels", [])
            recipients = params.get("recipients", [])
            return {"action": "notify", "channels": channels, "recipients": recipients}

        else:
            return {"action": action, "status": "unknown_action"}

    def _evaluate_condition(self, step: WorkflowStep, ticket: Ticket) -> bool:
        """Evaluate a condition step.

        Args:
            step: The condition step to evaluate.
            ticket: The current ticket.

        Returns:
            True if the condition is met, False otherwise.
        """
        condition = step.condition
        if not condition:
            return False

        field = condition.get("field", "")
        operator = condition.get("operator", "==")
        value = condition.get("value")

        ticket_value = getattr(ticket, field, None)
        if ticket_value is None:
            return False

        if operator == "==":
            return ticket_value == value
        elif operator == "!=":
            return ticket_value != value
        elif operator == ">":
            return ticket_value > value
        elif operator == ">=":
            return ticket_value >= value
        elif operator == "<":
            return ticket_value < value
        elif operator == "<=":
            return ticket_value <= value
        else:
            return False

    def _find_step_index(self, workflow: SOPWorkflow, step_id: str) -> int:
        """Find the index of a step by ID.

        Args:
            workflow: The workflow to search.
            step_id: The step ID to find.

        Returns:
            The index of the step, or -1 if not found.
        """
        for i, step in enumerate(workflow.steps):
            if step.id == step_id:
                return i
        return -1

    def add_workflow(self, workflow: SOPWorkflow) -> None:
        """Add or update a workflow.

        Args:
            workflow: The workflow to add or update.
        """
        self.workflows[workflow.name] = workflow

    def remove_workflow(self, name: str) -> None:
        """Remove a workflow.

        Args:
            name: The workflow name to remove.
        """
        self.workflows.pop(name, None)

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get an execution by ID.

        Args:
            execution_id: The execution ID.

        Returns:
            The WorkflowExecution object, or None if not found.
        """
        return self.executions.get(execution_id)

    def get_all_executions(self) -> Dict[str, WorkflowExecution]:
        """Get all executions.

        Returns:
            Dict mapping execution IDs to WorkflowExecution objects.
        """
        return self.executions.copy()

    def resume_execution(self, execution_id: str, ticket: Ticket) -> WorkflowExecution:
        """Resume a paused execution.

        Args:
            execution_id: The execution ID to resume.
            ticket: The updated ticket.

        Returns:
            The resumed WorkflowExecution object.
        """
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution '{execution_id}' not found")

        workflow = self.get_workflow(execution.workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{execution.workflow_name}' not found")

        execution.status = "running"
        execution.paused_at = None

        # Continue from the paused step
        step_index = execution.current_step_index
        while step_index < len(workflow.steps):
            step = workflow.steps[step_index]
            execution.current_step_index = step_index

            if step.type == StepType.ACTION:
                result = self._execute_action(step, ticket)
                execution.step_results[step.id] = result
                step_index += 1

            elif step.type == StepType.CONDITION:
                result = self._evaluate_condition(step, ticket)
                execution.step_results[step.id] = result
                if result:
                    next_step = step.then_step
                else:
                    next_step = step.else_step
                if next_step:
                    step_index = self._find_step_index(workflow, next_step)
                else:
                    step_index += 1

            elif step.type == StepType.GATE:
                execution.status = "paused"
                execution.paused_at = ticket.updated_at
                return execution

            if execution.status == "failed":
                break

        execution.status = "completed"
        execution.completed_at = ticket.updated_at
        return execution
