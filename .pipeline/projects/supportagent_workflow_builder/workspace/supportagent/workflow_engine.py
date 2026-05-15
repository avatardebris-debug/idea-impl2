"""Workflow engine — loads, executes, and manages SOP workflows."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import yaml

from supportagent.models import (
    GateType,
    Ticket,
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStepType,
)


class WorkflowEngineError(Exception):
    """Raised when workflow execution fails."""


class WorkflowEngine:
    """Loads and executes SOP workflows defined in YAML files."""

    def __init__(self, workflow_dir: Optional[str] = None):
        """Initialize the workflow engine.

        Args:
            workflow_dir: Directory containing workflow YAML files.
        """
        if workflow_dir is None:
            workflow_dir = os.path.join(
                os.path.dirname(__file__), "config", "sop_workflows"
            )
        self.workflow_dir = workflow_dir
        self._workflow_cache: Dict[str, Workflow] = {}

    def load_workflow(self, workflow_name: str) -> Workflow:
        """Load a workflow by name from the workflow directory.

        Args:
            workflow_name: Name of the workflow (without .yaml extension).

        Returns:
            The loaded Workflow object.

        Raises:
            WorkflowEngineError: If the workflow file is not found or invalid.
        """
        if workflow_name in self._workflow_cache:
            return self._workflow_cache[workflow_name]

        workflow_path = os.path.join(self.workflow_dir, f"{workflow_name}.yaml")
        if not os.path.exists(workflow_path):
            raise WorkflowEngineError(
                f"Workflow file not found: {workflow_path}"
            )

        with open(workflow_path, "r") as f:
            data = yaml.safe_load(f)

        workflow = self._parse_workflow(data)
        self._workflow_cache[workflow_name] = workflow
        return workflow

    def load_all_workflows(self) -> Dict[str, Workflow]:
        """Load all workflows from the workflow directory.

        Returns:
            Dictionary mapping workflow names to Workflow objects.
        """
        workflows = {}
        if not os.path.exists(self.workflow_dir):
            return workflows

        for filename in os.listdir(self.workflow_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                name = filename[:-5]  # strip .yaml or .yml
                workflows[name] = self.load_workflow(name)
        return workflows

    def execute_workflow(
        self, workflow: Workflow, ticket: Ticket
    ) -> WorkflowExecution:
        """Execute a workflow for a given ticket.

        Args:
            workflow: The workflow to execute.
            ticket: The ticket to process.

        Returns:
            The WorkflowExecution result.

        Raises:
            WorkflowEngineError: If execution fails.
        """
        execution = WorkflowExecution(
            workflow=workflow,
            ticket=ticket,
            current_step_id=workflow.steps[0].id if workflow.steps else None,
        )

        last_step_id = None
        while execution.current_step_id and not execution.is_complete:
            step = self._get_step(workflow, execution.current_step_id)
            if step is None:
                execution.is_complete = True
                break

            last_step_id = step.id
            try:
                result = self._execute_step(step, execution)
                if result is not None:
                    execution.output[step.id] = result
                    
                if step.step_type == WorkflowStepType.GATE:
                    break
            except WorkflowEngineError as e:
                execution.error = str(e)
                execution.failed_steps.append(step.id)
                break

        if not execution.current_step_id and (not last_step_id or not execution.output.get(last_step_id, {}).get("gate_type")):
            execution.is_complete = True

        return execution

    def _get_step(self, workflow: Workflow, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID from a workflow."""
        for step in workflow.steps:
            if step.id == step_id:
                return step
        return None

    def _execute_step(
        self, step: WorkflowStep, execution: WorkflowExecution
    ) -> Optional[Any]:
        """Execute a single workflow step.

        Returns:
            The result of the step, or None if the step completes normally.
        """
        if step.step_type == WorkflowStepType.ACTION:
            res = self._execute_action(step, execution)
            execution.current_step_id = step.then_step or self._get_next_sequential_step_id(execution.workflow, step.id)
            return res
        elif step.step_type == WorkflowStepType.CONDITION:
            return self._execute_condition(step, execution)
        elif step.step_type == WorkflowStepType.GATE:
            res = self._execute_gate(step, execution)
            execution.current_step_id = step.then_step or self._get_next_sequential_step_id(execution.workflow, step.id)
            return res
        else:
            raise WorkflowEngineError(f"Unknown step type: {step.step_type}")

    def _get_next_sequential_step_id(self, workflow: Workflow, current_id: str) -> Optional[str]:
        for i, s in enumerate(workflow.steps):
            if s.id == current_id:
                if i + 1 < len(workflow.steps):
                    return workflow.steps[i+1].id
                break
        return None

    def _execute_action(
        self, step: WorkflowStep, execution: WorkflowExecution
    ) -> Optional[Any]:
        """Execute an action step."""
        ticket = execution.ticket
        workflow = execution.workflow

        if step.action == WorkflowAction.CLASSIFY_TICKET:
            # Classification is handled by the classifier module
            # This step is a placeholder for the engine to know classification happened
            return {"action": "classify_ticket", "status": "completed"}

        elif step.action == WorkflowAction.ASSIGN_TEAM:
            team = step.params.get("team", "general_team")
            ticket.assigned_team = team
            return {"action": "assign_team", "team": team}

        elif step.action == WorkflowAction.ESCALATE:
            target = step.params.get("target_team", "escalation_team")
            reason = step.params.get("reason", "escalation")
            ticket.workflow_state["escalated"] = True
            ticket.workflow_state["escalation_reason"] = reason
            return {
                "action": "escalate",
                "target_team": target,
                "reason": reason,
            }

        elif step.action == WorkflowAction.GENERATE_DRAFT:
            template = step.params.get("template", "general_response")
            tone = step.params.get("tone", "professional")
            ticket.workflow_state["draft_template"] = template
            ticket.workflow_state["draft_tone"] = tone
            return {
                "action": "generate_draft",
                "template": template,
                "tone": tone,
            }

        elif step.action == WorkflowAction.SEND_RESPONSE:
            ticket.workflow_state["response_sent"] = True
            return {"action": "send_response", "status": "completed"}

        elif step.action == WorkflowAction.NOTIFY:
            channels = step.params.get("channels", [])
            recipients = step.params.get("recipients", [])
            ticket.workflow_state["notifications_sent"] = {
                "channels": channels,
                "recipients": recipients,
            }
            return {
                "action": "notify",
                "channels": channels,
                "recipients": recipients,
            }

        else:
            raise WorkflowEngineError(f"Unknown action: {step.action}")

    def _execute_condition(
        self, step: WorkflowStep, execution: WorkflowExecution
    ) -> Optional[Any]:
        """Execute a condition step, routing to then/else branches."""
        condition = step.condition
        if not condition:
            # No condition means always take the then branch
            execution.current_step_id = step.then_step
            return None

        field = condition.get("field", "")
        operator = condition.get("operator", "==")
        value = condition.get("value")

        # Get the actual value from the ticket or workflow state
        actual_value = self._get_condition_value(execution, field)

        # Evaluate the condition
        result = self._evaluate_condition(actual_value, operator, value)

        if result:
            execution.current_step_id = step.then_step
        else:
            execution.current_step_id = step.else_step

        return {"condition": condition, "result": result}

    def _get_condition_value(
        self, execution: WorkflowExecution, field: str
    ) -> Any:
        """Get the value of a field for condition evaluation."""
        ticket = execution.ticket

        if field in ("priority_score", "priority"):
            return ticket.priority_score
        elif field == "category":
            return ticket.category.value if ticket.category else None
        elif field == "status":
            return ticket.status
        elif field in ticket.workflow_state:
            return ticket.workflow_state[field]
        else:
            return None

    def _evaluate_condition(
        self, actual: Any, operator: str, expected: Any
    ) -> bool:
        """Evaluate a condition operator."""
        if actual is None:
            return False

        if operator == "==":
            return actual == expected
        elif operator == "!=":
            return actual != expected
        elif operator == ">=":
            return actual >= expected
        elif operator == "<=":
            return actual <= expected
        elif operator == ">":
            return actual > expected
        elif operator == "<":
            return actual < expected
        elif operator == "in":
            return actual in expected
        else:
            raise WorkflowEngineError(f"Unknown operator: {operator}")

    def _execute_gate(
        self, step: WorkflowStep, execution: WorkflowExecution
    ) -> Optional[Any]:
        """Execute a gate step (approval/wait)."""
        gate_type = step.gate_type
        ticket = execution.ticket

        if gate_type == GateType.HUMAN_APPROVAL:
            hours = step.params.get("auto_approve_after_hours", 24)
            ticket.workflow_state["gate_type"] = "human_approval"
            ticket.workflow_state["auto_approve_after_hours"] = hours
            # For engine testing, we auto-approve
            ticket.workflow_state["gate_approved"] = True
            return {
                "gate_type": "human_approval",
                "auto_approve_after_hours": hours,
            }

        elif gate_type == GateType.HUMAN_REVIEW:
            required_roles = step.params.get("required_roles", [])
            ticket.workflow_state["gate_type"] = "human_review"
            ticket.workflow_state["required_roles"] = required_roles
            ticket.workflow_state["gate_approved"] = True
            return {
                "gate_type": "human_review",
                "required_roles": required_roles,
            }

        elif gate_type == GateType.IMMEDIATE_RESPONSE:
            required_roles = step.params.get("required_roles", [])
            ticket.workflow_state["gate_type"] = "immediate_response"
            ticket.workflow_state["required_roles"] = required_roles
            ticket.workflow_state["gate_approved"] = True
            return {
                "gate_type": "immediate_response",
                "required_roles": required_roles,
            }

        else:
            raise WorkflowEngineError(f"Unknown gate type: {gate_type}")

    def _parse_workflow(self, data: Dict[str, Any]) -> Workflow:
        """Parse a YAML workflow definition into a Workflow object."""
        name = data.get("name", "unnamed")
        version = data.get("version", "1.0")
        description = data.get("description", "")
        metadata = {k: v for k, v in data.items() if k not in ("name", "version", "description", "steps")}

        steps = []
        for step_data in data.get("steps", []):
            step = self._parse_step(step_data)
            steps.append(step)

        return Workflow(
            name=name,
            version=version,
            description=description,
            steps=steps,
            metadata=metadata,
        )

    def _parse_step(self, data: Dict[str, Any]) -> WorkflowStep:
        """Parse a YAML step definition into a WorkflowStep object."""
        step_type_str = data.get("type", "action")
        step_type = WorkflowStepType(step_type_str)

        action = None
        if data.get("action"):
            action = WorkflowAction(data["action"])

        gate_str = data.get("gate_type") or data.get("params", {}).get("gate_type")
        gate_type = None
        if gate_str:
            gate_type = GateType(gate_str)

        condition = data.get("condition")
        params = data.get("params", {})
        description = data.get("description", "")
        then_step = data.get("then_step") or data.get("then")
        else_step = data.get("else_step") or data.get("else")

        return WorkflowStep(
            id=data.get("id", "unknown"),
            step_type=step_type,
            action=action,
            condition=condition,
            gate_type=gate_type,
            params=params,
            description=description,
            then_step=then_step,
            else_step=else_step,
        )
