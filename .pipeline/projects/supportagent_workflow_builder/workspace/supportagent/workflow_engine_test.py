"""Tests for the workflow engine."""

import os
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from supportagent.models import (
    GateType,
    Ticket,
    TicketCategory,
    TicketSource,
    Urgency,
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStepType,
)
from supportagent.workflow_engine import WorkflowEngine, WorkflowEngineError


class TestWorkflowEngine(unittest.TestCase):
    """Tests for WorkflowEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = WorkflowEngine()

    def test_load_workflow_from_existing_file(self):
        """Test loading a workflow that exists."""
        workflow = self.engine.load_workflow("standard_triage_routing")
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.name, "standard_triage_routing")
        self.assertGreater(len(workflow.steps), 0)

    def test_load_workflow_caches_result(self):
        """Test that workflows are cached."""
        w1 = self.engine.load_workflow("standard_triage_routing")
        w2 = self.engine.load_workflow("standard_triage_routing")
        self.assertIs(w1, w2)

    def test_load_workflow_not_found(self):
        """Test loading a non-existent workflow raises an error."""
        with self.assertRaises(WorkflowEngineError):
            self.engine.load_workflow("nonexistent_workflow")

    def test_load_all_workflows(self):
        """Test loading all workflows from the directory."""
        workflows = self.engine.load_all_workflows()
        self.assertGreater(len(workflows), 0)
        self.assertIn("standard_triage_routing", workflows)

    def test_execute_workflow_basic(self):
        """Test basic workflow execution."""
        workflow = self.engine.load_workflow("standard_triage_routing")
        ticket = Ticket(
            ticket_id="test-001",
            source=TicketSource.EMAIL,
            subject="Test ticket",
            body="This is a test ticket",
        )

        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertIsNotNone(execution)
        self.assertFalse(execution.is_complete)

    def test_execute_workflow_assigns_team(self):
        """Test that workflow execution assigns teams correctly."""
        workflow = self.engine.load_workflow("standard_triage_routing")
        ticket = Ticket(
            ticket_id="test-002",
            source=TicketSource.EMAIL,
            subject="Test ticket",
            body="This is a test ticket",
        )

        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertEqual(ticket.assigned_team, "auto")

    def test_execute_workflow_with_condition(self):
        """Test workflow execution with condition branching."""
        workflow = self.engine.load_workflow("billing_flow")
        ticket = Ticket(
            ticket_id="test-003",
            source=TicketSource.EMAIL,
            subject="Billing issue",
            body="I was charged incorrectly",
            priority_score=8.0,
        )

        execution = self.engine.execute_workflow(workflow, ticket)
        # With priority_score >= 7, should take the escalation path
        self.assertIn("step_3a", execution.output)

    def test_execute_workflow_with_gate(self):
        """Test workflow execution with gate steps."""
        workflow = self.engine.load_workflow("technical_flow")
        ticket = Ticket(
            ticket_id="test-004",
            source=TicketSource.EMAIL,
            subject="Technical issue",
            body="My server is down",
        )

        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertIn("step_5", execution.output)
        gate_result = execution.output["step_5"]
        self.assertEqual(gate_result["gate_type"], "human_approval")

    def test_execute_workflow_with_escalation(self):
        """Test workflow execution with escalation."""
        workflow = self.engine.load_workflow("escalation_flow")
        ticket = Ticket(
            ticket_id="test-005",
            source=TicketSource.EMAIL,
            subject="Urgent issue",
            body="Critical problem",
            priority_score=9.5,
        )

        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertIn("step_3a", execution.output)
        self.assertTrue(ticket.workflow_state.get("escalated", False))

    def test_execute_workflow_with_notification(self):
        """Test workflow execution with notification."""
        workflow = self.engine.load_workflow("escalation_flow")
        ticket = Ticket(
            ticket_id="test-006",
            source=TicketSource.EMAIL,
            subject="Normal issue",
            body="Regular problem",
            priority_score=5.0,
        )

        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertIn("step_3b", execution.output)
        self.assertIn("notifications_sent", ticket.workflow_state)

    def test_execute_workflow_with_custom_dir(self):
        """Test loading workflows from a custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_yaml = textwrap.dedent("""\
                name: custom_workflow
                version: "1.0"
                description: "Test workflow"
                steps:
                  - id: step_1
                    type: action
                    action: classify_ticket
                    description: "Classify"
                  - id: step_2
                    type: action
                    action: assign_team
                    description: "Assign"
                    params:
                      team: custom_team
            """)
            workflow_path = os.path.join(tmpdir, "custom_workflow.yaml")
            with open(workflow_path, "w") as f:
                f.write(workflow_yaml)

            custom_engine = WorkflowEngine(workflow_dir=tmpdir)
            workflow = custom_engine.load_workflow("custom_workflow")
            self.assertEqual(workflow.name, "custom_workflow")
            self.assertEqual(len(workflow.steps), 2)

    def test_condition_equality(self):
        """Test equality condition evaluation."""
        ticket = Ticket(
            ticket_id="test-007",
            source=TicketSource.EMAIL,
            subject="Test",
            body="Test",
            category=TicketCategory.BILLING,
        )
        workflow = self.engine.load_workflow("account_management")
        execution = self.engine.execute_workflow(workflow, ticket)
        # Should take the 'then' branch for category == account
        # But since category is billing, it should take 'else'
        self.assertIn("step_4", execution.output)

    def test_condition_greater_than_or_equal(self):
        """Test >= condition evaluation."""
        ticket = Ticket(
            ticket_id="test-008",
            source=TicketSource.EMAIL,
            subject="Test",
            body="Test",
            priority_score=7.0,
        )
        workflow = self.engine.load_workflow("billing_flow")
        execution = self.engine.execute_workflow(workflow, ticket)
        # priority_score 7.0 >= 7 should be True
        self.assertIn("step_3a", execution.output)

    def test_condition_less_than(self):
        """Test < condition evaluation."""
        ticket = Ticket(
            ticket_id="test-009",
            source=TicketSource.EMAIL,
            subject="Test",
            body="Test",
            priority_score=5.0,
        )
        workflow = self.engine.load_workflow("billing_flow")
        execution = self.engine.execute_workflow(workflow, ticket)
        # priority_score 5.0 < 7 should be False, so take else branch
        self.assertIn("step_3b", execution.output)

    def test_workflow_state_persistence(self):
        """Test that workflow state is persisted through execution."""
        workflow = self.engine.load_workflow("billing_flow")
        ticket = Ticket(
            ticket_id="test-010",
            source=TicketSource.EMAIL,
            subject="Test",
            body="Test",
            priority_score=8.0,
        )

        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertIn("draft_template", ticket.workflow_state)
        self.assertIn("draft_tone", ticket.workflow_state)

    def test_execution_output_structure(self):
        """Test that execution output has correct structure."""
        workflow = self.engine.load_workflow("standard_triage_routing")
        ticket = Ticket(
            ticket_id="test-011",
            source=TicketSource.EMAIL,
            subject="Test",
            body="Test",
        )

        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertIsInstance(execution.output, dict)
        self.assertIn("step_1", execution.output)
        self.assertIn("step_2", execution.output)

    def test_empty_workflow(self):
        """Test handling of a workflow with no steps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_yaml = textwrap.dedent("""\
                name: empty_workflow
                version: "1.0"
                description: "Empty workflow"
                steps: []
            """)
            workflow_path = os.path.join(tmpdir, "empty_workflow.yaml")
            with open(workflow_path, "w") as f:
                f.write(workflow_yaml)

            custom_engine = WorkflowEngine(workflow_dir=tmpdir)
            workflow = custom_engine.load_workflow("empty_workflow")
            ticket = Ticket(
                ticket_id="test-012",
                source=TicketSource.EMAIL,
                subject="Test",
                body="Test",
            )

            execution = custom_engine.execute_workflow(workflow, ticket)
            self.assertTrue(execution.is_complete)

    def test_workflow_with_multiple_gate_types(self):
        """Test workflows with different gate types."""
        # Test human_approval gate
        workflow = self.engine.load_workflow("account_management")
        ticket = Ticket(
            ticket_id="test-013",
            source=TicketSource.EMAIL,
            subject="Test",
            body="Test",
            category=TicketCategory.ACCOUNT,
        )
        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertIn("step_6", execution.output)
        self.assertEqual(
            execution.output["step_6"]["gate_type"], "human_approval"
        )

    def test_workflow_with_immediate_response_gate(self):
        """Test immediate response gate."""
        workflow = self.engine.load_workflow("urgent_issue_handling")
        ticket = Ticket(
            ticket_id="test-014",
            source=TicketSource.EMAIL,
            subject="Urgent",
            body="Critical issue",
            priority_score=9.0,
        )
        execution = self.engine.execute_workflow(workflow, ticket)
        self.assertIn("step_6", execution.output)
        self.assertEqual(
            execution.output["step_6"]["gate_type"], "immediate_response"
        )


class TestWorkflowEngineParsing(unittest.TestCase):
    """Tests for workflow parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = WorkflowEngine()

    def test_parse_workflow_with_all_fields(self):
        """Test parsing a workflow with all fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_yaml = textwrap.dedent("""\
                name: full_workflow
                version: "2.0"
                description: "Full workflow test"
                author: "test"
                steps:
                  - id: step_1
                    type: action
                    action: classify_ticket
                    description: "Classify"
                  - id: step_2
                    type: condition
                    condition:
                      field: priority_score
                      operator: ">="
                      value: 8
                    then_step: step_3
                    else_step: step_4
                  - id: step_3
                    type: action
                    action: escalate
                    description: "Escalate"
                    params:
                      target_team: escalation_team
                      reason: "high_priority"
                  - id: step_4
                    type: action
                    action: assign_team
                    description: "Assign"
                    params:
                      team: general_team
                  - id: step_5
                    type: gate
                    gate_type: human_approval
                    description: "Approval"
                    params:
                      auto_approve_after_hours: 24
            """)
            workflow_path = os.path.join(tmpdir, "full_workflow.yaml")
            with open(workflow_path, "w") as f:
                f.write(workflow_yaml)

            custom_engine = WorkflowEngine(workflow_dir=tmpdir)
            workflow = custom_engine.load_workflow("full_workflow")

            self.assertEqual(workflow.name, "full_workflow")
            self.assertEqual(workflow.version, "2.0")
            self.assertEqual(workflow.description, "Full workflow test")
            self.assertEqual(workflow.metadata["author"], "test")
            self.assertEqual(len(workflow.steps), 5)

            # Check step types
            self.assertEqual(workflow.steps[0].step_type, WorkflowStepType.ACTION)
            self.assertEqual(workflow.steps[1].step_type, WorkflowStepType.CONDITION)
            self.assertEqual(workflow.steps[4].step_type, WorkflowStepType.GATE)

            # Check action steps
            self.assertEqual(
                workflow.steps[0].action, WorkflowAction.CLASSIFY_TICKET
            )
            self.assertEqual(
                workflow.steps[2].action, WorkflowAction.ESCALATE
            )

            # Check condition
            self.assertIsNotNone(workflow.steps[1].condition)
            self.assertEqual(
                workflow.steps[1].condition["field"], "priority_score"
            )

            # Check gate
            self.assertEqual(
                workflow.steps[4].gate_type, GateType.HUMAN_APPROVAL
            )


if __name__ == "__main__":
    unittest.main()
