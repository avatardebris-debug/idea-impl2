"""Tests for the SOP Engine (Task 6)."""

import os
import tempfile
import textwrap
import pytest
from supportagent.sop_engine import SOPEngine
from supportagent.models import (
    Ticket,
    TicketSource,
    SOPWorkflow,
    WorkflowExecution,
    WorkflowStep,
    StepType,
    GateType,
)


@pytest.fixture
def workflows_dir():
    """Create a temporary directory with workflow YAML files for testing."""
    temp_dir = tempfile.mkdtemp()

    # Technical workflow
    tech_yaml = textwrap.dedent("""\
        name: technical_flow
        version: "1.0"
        description: "Standard workflow for technical support tickets"
        steps:
          - id: step_1
            type: action
            action: classify_ticket
            description: "Classify the ticket"
          - id: step_2
            type: condition
            condition:
              field: category
              operator: "=="
              value: urgent
            then: step_3a
            else: step_3b
          - id: step_3a
            type: action
            action: escalate
            description: "Immediately escalate critical technical issues"
            params:
              target_team: escalation_team
              reason: "critical_technical_issue"
              notify_slack: true
          - id: step_3b
            type: action
            action: assign_team
            description: "Assign to technical team"
            params:
              team: technical_team
          - id: step_4
            type: action
            action: generate_draft
            description: "Generate a technical draft response"
            params:
              template: technical_response
              tone: professional
          - id: step_5
            type: gate
            gate_type: human_approval
            description: "Technical review before sending"
            auto_approve_after_hours: 12
          - id: step_6
            type: action
            action: send_response
            description: "Send the response"
    """)

    # General workflow
    general_yaml = textwrap.dedent("""\
        name: general_flow
        version: "1.0"
        description: "Default workflow for general support tickets"
        steps:
          - id: step_1
            type: action
            action: classify_ticket
            description: "Classify the ticket"
          - id: step_2
            type: condition
            condition:
              field: category
              operator: "=="
              value: general
            then: step_3
            else: step_4
          - id: step_3
            type: action
            action: assign_team
            description: "Assign to general team"
            params:
              team: general_team
          - id: step_4
            type: action
            action: assign_team
            description: "Fallback to general team"
            params:
              team: general_team
          - id: step_5
            type: action
            action: generate_draft
            description: "Generate a draft response"
            params:
              template: general_response
              tone: professional
          - id: step_6
            type: gate
            gate_type: human_approval
            description: "Await human approval"
            auto_approve_after_hours: 72
          - id: step_7
            type: action
            action: send_response
            description: "Send the approved response"
    """)

    # Account workflow
    account_yaml = textwrap.dedent("""\
        name: account_flow
        version: "1.0"
        description: "Standard workflow for account management tickets"
        steps:
          - id: step_1
            type: action
            action: classify_ticket
            description: "Classify the ticket"
          - id: step_2
            type: condition
            condition:
              field: category
              operator: "=="
              value: account
            then: step_3
            else: step_4
          - id: step_3
            type: action
            action: assign_team
            description: "Assign to account team"
            params:
              team: account_team
          - id: step_4
            type: action
            action: assign_team
            description: "Fallback to general team"
            params:
              team: general_team
          - id: step_5
            type: action
            action: generate_draft
            description: "Generate a draft response"
            params:
              template: account_response
              tone: professional
          - id: step_6
            type: gate
            gate_type: human_approval
            description: "Await human approval"
            auto_approve_after_hours: 48
          - id: step_7
            type: action
            action: send_response
            description: "Send the approved response"
    """)

    # Billing workflow
    billing_yaml = textwrap.dedent("""\
        name: billing_flow
        version: "1.0"
        description: "Standard workflow for billing tickets"
        steps:
          - id: step_1
            type: action
            action: classify_ticket
            description: "Classify the ticket"
          - id: step_2
            type: condition
            condition:
              field: category
              operator: "=="
              value: billing
            then: step_3
            else: step_4
          - id: step_3
            type: action
            action: assign_team
            description: "Assign to billing team"
            params:
              team: billing_team
          - id: step_4
            type: action
            action: assign_team
            description: "Fallback to general team"
            params:
              team: general_team
          - id: step_5
            type: action
            action: generate_draft
            description: "Generate a draft response"
            params:
              template: billing_response
              tone: professional
          - id: step_6
            type: gate
            gate_type: human_approval
            description: "Await human approval"
            auto_approve_after_hours: 24
          - id: step_7
            type: action
            action: send_response
            description: "Send the approved response"
    """)

    # Escalation workflow
    escalation_yaml = textwrap.dedent("""\
        name: escalation_flow
        version: "1.0"
        description: "Standard workflow for escalation tickets"
        steps:
          - id: step_1
            type: action
            action: classify_ticket
            description: "Classify the ticket"
          - id: step_2
            type: condition
            condition:
              field: category
              operator: "=="
              value: urgent
            then: step_3
            else: step_4
          - id: step_3
            type: action
            action: assign_team
            description: "Assign to escalation team"
            params:
              team: escalation_team
          - id: step_4
            type: action
            action: assign_team
            description: "Fallback to general team"
            params:
              team: general_team
          - id: step_5
            type: action
            action: generate_draft
            description: "Generate a draft response"
            params:
              template: escalation_response
              tone: urgent
          - id: step_6
            type: gate
            gate_type: human_approval
            description: "Await human approval"
            auto_approve_after_hours: 1
          - id: step_7
            type: action
            action: send_response
            description: "Send the approved response"
    """)

    # Write workflow files
    with open(os.path.join(temp_dir, "technical.yaml"), "w") as f:
        f.write(tech_yaml)
    with open(os.path.join(temp_dir, "general.yaml"), "w") as f:
        f.write(general_yaml)
    with open(os.path.join(temp_dir, "account.yaml"), "w") as f:
        f.write(account_yaml)
    with open(os.path.join(temp_dir, "billing.yaml"), "w") as f:
        f.write(billing_yaml)
    with open(os.path.join(temp_dir, "escalation.yaml"), "w") as f:
        f.write(escalation_yaml)

    yield temp_dir
    # Cleanup
    for f in os.listdir(temp_dir):
        os.unlink(os.path.join(temp_dir, f))
    os.rmdir(temp_dir)


@pytest.fixture
def sop_engine(workflows_dir):
    """Create an SOP Engine instance with the test workflows."""
    return SOPEngine(workflows_dir=workflows_dir)


class TestSOPEngineInitialization:
    def test_engine_loads_workflows(self, sop_engine):
        assert len(sop_engine.workflows) == 5

    def test_engine_loads_all_workflow_names(self, sop_engine):
        workflow_names = [w.name for w in sop_engine.workflows]
        assert "technical_flow" in workflow_names
        assert "general_flow" in workflow_names
        assert "account_flow" in workflow_names
        assert "billing_flow" in workflow_names
        assert "escalation_flow" in workflow_names

    def test_engine_loads_workflow_versions(self, sop_engine):
        for workflow in sop_engine.workflows:
            assert workflow.version == "1.0"

    def test_engine_loads_workflow_steps(self, sop_engine):
        for workflow in sop_engine.workflows:
            assert len(workflow.steps) >= 5

    def test_engine_invalid_dir_raises(self):
        with pytest.raises(Exception):  # Directory not found or invalid
            SOPEngine(workflows_dir="/nonexistent/path")

    def test_engine_empty_dir(self):
        temp_dir = tempfile.mkdtemp()
        try:
            engine = SOPEngine(workflows_dir=temp_dir)
            assert len(engine.workflows) == 0
        finally:
            os.rmdir(temp_dir)


class TestGetWorkflowByCategory:
    def test_get_workflow_technical(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        assert workflow is not None
        assert workflow.name == "technical_flow"

    def test_get_workflow_billing(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("billing")
        assert workflow is not None
        assert workflow.name == "billing_flow"

    def test_get_workflow_account(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("account")
        assert workflow is not None
        assert workflow.name == "account_flow"

    def test_get_workflow_urgent(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("urgent")
        assert workflow is not None
        assert workflow.name == "escalation_flow"

    def test_get_workflow_general(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("general")
        assert workflow is not None
        assert workflow.name == "general_flow"

    def test_get_workflow_unknown_category(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("unknown")
        assert workflow is None


class TestGetWorkflowByName:
    def test_get_workflow_by_name_technical(self, sop_engine):
        workflow = sop_engine.get_workflow_by_name("technical_flow")
        assert workflow is not None
        assert workflow.name == "technical_flow"

    def test_get_workflow_by_name_general(self, sop_engine):
        workflow = sop_engine.get_workflow_by_name("general_flow")
        assert workflow is not None
        assert workflow.name == "general_flow"

    def test_get_workflow_by_name_not_found(self, sop_engine):
        workflow = sop_engine.get_workflow_by_name("nonexistent_flow")
        assert workflow is None


class TestGetWorkflowForTicket:
    def test_get_workflow_for_technical_ticket(self, sop_engine):
        ticket = Ticket(
            ticket_id="T1",
            source=TicketSource.JSON,
            subject="Bug report",
            body="Application crashes",
            category="technical",
        )
        workflow = sop_engine.get_workflow_for_ticket(ticket)
        assert workflow is not None
        assert workflow.name == "technical_flow"

    def test_get_workflow_for_billing_ticket(self, sop_engine):
        ticket = Ticket(
            ticket_id="T2",
            source=TicketSource.EMAIL,
            subject="Billing issue",
            body="Wrong charge",
            category="billing",
        )
        workflow = sop_engine.get_workflow_for_ticket(ticket)
        assert workflow is not None
        assert workflow.name == "billing_flow"

    def test_get_workflow_for_account_ticket(self, sop_engine):
        ticket = Ticket(
            ticket_id="T3",
            source=TicketSource.WEB,
            subject="Account update",
            body="Change email",
            category="account",
        )
        workflow = sop_engine.get_workflow_for_ticket(ticket)
        assert workflow is not None
        assert workflow.name == "account_flow"

    def test_get_workflow_for_urgent_ticket(self, sop_engine):
        ticket = Ticket(
            ticket_id="T4",
            source=TicketSource.JSON,
            subject="Critical issue",
            body="System down",
            category="urgent",
        )
        workflow = sop_engine.get_workflow_for_ticket(ticket)
        assert workflow is not None
        assert workflow.name == "escalation_flow"

    def test_get_workflow_for_general_ticket(self, sop_engine):
        ticket = Ticket(
            ticket_id="T5",
            source=TicketSource.EMAIL,
            subject="General question",
            body="How do I reset password?",
            category="general",
        )
        workflow = sop_engine.get_workflow_for_ticket(ticket)
        assert workflow is not None
        assert workflow.name == "general_flow"

    def test_get_workflow_for_ticket_without_category(self, sop_engine):
        ticket = Ticket(
            ticket_id="T6",
            source=TicketSource.JSON,
            subject="No category",
            body="No category set",
        )
        workflow = sop_engine.get_workflow_for_ticket(ticket)
        assert workflow is None


class TestGetWorkflowSteps:
    def test_get_workflow_steps_technical(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        assert len(steps) >= 5
        assert steps[0].action == "classify_ticket"

    def test_get_workflow_steps_billing(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("billing")
        steps = sop_engine.get_workflow_steps(workflow)
        assert len(steps) >= 5

    def test_get_workflow_steps_for_none(self, sop_engine):
        steps = sop_engine.get_workflow_steps(None)
        assert steps == []


class TestGetNextStep:
    def test_get_next_step_first_step(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        next_step = sop_engine.get_next_step(workflow, steps, 0)
        assert next_step is not None
        assert next_step.id == "step_1"

    def test_get_next_step_second_step(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        next_step = sop_engine.get_next_step(workflow, steps, 1)
        assert next_step is not None
        assert next_step.id == "step_2"

    def test_get_next_step_last_step(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        next_step = sop_engine.get_next_step(workflow, steps, len(steps) - 1)
        assert next_step is None

    def test_get_next_step_for_none_workflow(self, sop_engine):
        next_step = sop_engine.get_next_step(None, [], 0)
        assert next_step is None

    def test_get_next_step_for_none_steps(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        next_step = sop_engine.get_next_step(workflow, None, 0)
        assert next_step is None


class TestExecuteWorkflow:
    def test_execute_workflow_technical(self, sop_engine):
        ticket = Ticket(
            ticket_id="T1",
            source=TicketSource.JSON,
            subject="Bug report",
            body="Application crashes",
            category="technical",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result is not None
        assert result.workflow_name == "technical_flow"
        assert result.status == "completed"
        assert len(result.executed_steps) > 0

    def test_execute_workflow_billing(self, sop_engine):
        ticket = Ticket(
            ticket_id="T2",
            source=TicketSource.EMAIL,
            subject="Billing issue",
            body="Wrong charge",
            category="billing",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result is not None
        assert result.workflow_name == "billing_flow"
        assert result.status == "completed"

    def test_execute_workflow_account(self, sop_engine):
        ticket = Ticket(
            ticket_id="T3",
            source=TicketSource.WEB,
            subject="Account update",
            body="Change email",
            category="account",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result is not None
        assert result.workflow_name == "account_flow"
        assert result.status == "completed"

    def test_execute_workflow_urgent(self, sop_engine):
        ticket = Ticket(
            ticket_id="T4",
            source=TicketSource.JSON,
            subject="Critical issue",
            body="System down",
            category="urgent",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result is not None
        assert result.workflow_name == "escalation_flow"
        assert result.status == "completed"

    def test_execute_workflow_general(self, sop_engine):
        ticket = Ticket(
            ticket_id="T5",
            source=TicketSource.EMAIL,
            subject="General question",
            body="How do I reset password?",
            category="general",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result is not None
        assert result.workflow_name == "general_flow"
        assert result.status == "completed"

    def test_execute_workflow_no_workflow(self, sop_engine):
        ticket = Ticket(
            ticket_id="T6",
            source=TicketSource.JSON,
            subject="No category",
            body="No category set",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result is None


class TestWorkflowStepTypes:
    def test_technical_workflow_has_condition_step(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        condition_steps = [s for s in steps if s.type == StepType.CONDITION]
        assert len(condition_steps) >= 1

    def test_technical_workflow_has_action_steps(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        action_steps = [s for s in steps if s.type == StepType.ACTION]
        assert len(action_steps) >= 3

    def test_technical_workflow_has_gate_step(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        gate_steps = [s for s in steps if s.type == StepType.GATE]
        assert len(gate_steps) >= 1

    def test_all_workflows_have_classification_step(self, sop_engine):
        for workflow in sop_engine.workflows:
            steps = sop_engine.get_workflow_steps(workflow)
            classification_steps = [s for s in steps if s.action == "classify_ticket"]
            assert len(classification_steps) >= 1

    def test_all_workflows_have_draft_generation_step(self, sop_engine):
        for workflow in sop_engine.workflows:
            steps = sop_engine.get_workflow_steps(workflow)
            draft_steps = [s for s in steps if s.action == "generate_draft"]
            assert len(draft_steps) >= 1

    def test_all_workflows_have_send_response_step(self, sop_engine):
        for workflow in sop_engine.workflows:
            steps = sop_engine.get_workflow_steps(workflow)
            send_steps = [s for s in steps if s.action == "send_response"]
            assert len(send_steps) >= 1


class TestWorkflowExecutionDetails:
    def test_execution_has_ticket_id(self, sop_engine):
        ticket = Ticket(
            ticket_id="T1",
            source=TicketSource.JSON,
            subject="Test",
            body="Test",
            category="technical",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result.ticket_id == "T1"

    def test_execution_has_workflow_name(self, sop_engine):
        ticket = Ticket(
            ticket_id="T1",
            source=TicketSource.JSON,
            subject="Test",
            body="Test",
            category="technical",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result.workflow_name == "technical_flow"

    def test_execution_has_status(self, sop_engine):
        ticket = Ticket(
            ticket_id="T1",
            source=TicketSource.JSON,
            subject="Test",
            body="Test",
            category="technical",
        )
        result = sop_engine.execute_workflow(ticket)
        assert result.status == "completed"

    def test_execution_has_executed_steps(self, sop_engine):
        ticket = Ticket(
            ticket_id="T1",
            source=TicketSource.JSON,
            subject="Test",
            body="Test",
            category="technical",
        )
        result = sop_engine.execute_workflow(ticket)
        assert len(result.executed_steps) > 0

    def test_execution_has_error_message_on_failure(self, sop_engine):
        # Create a workflow with an invalid step
        temp_dir = tempfile.mkdtemp()
        invalid_yaml = textwrap.dedent("""\
            name: invalid_flow
            version: "1.0"
            description: "Invalid workflow"
            steps:
              - id: step_1
                type: action
                action: nonexistent_action
                description: "Invalid action"
        """)
        with open(os.path.join(temp_dir, "invalid.yaml"), "w") as f:
            f.write(invalid_yaml)

        try:
            engine = SOPEngine(workflows_dir=temp_dir)
            ticket = Ticket(
                ticket_id="T1",
                source=TicketSource.JSON,
                subject="Test",
                body="Test",
                category="general",
            )
            result = engine.execute_workflow(ticket)
            # Should handle gracefully
            assert result is not None
        finally:
            os.unlink(os.path.join(temp_dir, "invalid.yaml"))
            os.rmdir(temp_dir)


class TestWorkflowTemplates:
    def test_technical_workflow_has_technical_template(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        draft_steps = [s for s in steps if s.action == "generate_draft"]
        assert len(draft_steps) >= 1
        assert draft_steps[0].params["template"] == "technical_response"

    def test_billing_workflow_has_billing_template(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("billing")
        steps = sop_engine.get_workflow_steps(workflow)
        draft_steps = [s for s in steps if s.action == "generate_draft"]
        assert len(draft_steps) >= 1
        assert draft_steps[0].params["template"] == "billing_response"

    def test_account_workflow_has_account_template(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("account")
        steps = sop_engine.get_workflow_steps(workflow)
        draft_steps = [s for s in steps if s.action == "generate_draft"]
        assert len(draft_steps) >= 1
        assert draft_steps[0].params["template"] == "account_response"

    def test_escalation_workflow_has_urgent_tone(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("urgent")
        steps = sop_engine.get_workflow_steps(workflow)
        draft_steps = [s for s in steps if s.action == "generate_draft"]
        assert len(draft_steps) >= 1
        assert draft_steps[0].params["tone"] == "urgent"

    def test_general_workflow_has_professional_tone(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("general")
        steps = sop_engine.get_workflow_steps(workflow)
        draft_steps = [s for s in steps if s.action == "generate_draft"]
        assert len(draft_steps) >= 1
        assert draft_steps[0].params["tone"] == "professional"


class TestWorkflowAutoApproveSettings:
    def test_technical_workflow_auto_approve_12_hours(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("technical")
        steps = sop_engine.get_workflow_steps(workflow)
        gate_steps = [s for s in steps if s.type == StepType.GATE]
        assert len(gate_steps) >= 1
        assert gate_steps[0].auto_approve_after_hours == 12

    def test_billing_workflow_auto_approve_24_hours(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("billing")
        steps = sop_engine.get_workflow_steps(workflow)
        gate_steps = [s for s in steps if s.type == StepType.GATE]
        assert len(gate_steps) >= 1
        assert gate_steps[0].auto_approve_after_hours == 24

    def test_account_workflow_auto_approve_48_hours(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("account")
        steps = sop_engine.get_workflow_steps(workflow)
        gate_steps = [s for s in steps if s.type == StepType.GATE]
        assert len(gate_steps) >= 1
        assert gate_steps[0].auto_approve_after_hours == 48

    def test_escalation_workflow_auto_approve_1_hour(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("urgent")
        steps = sop_engine.get_workflow_steps(workflow)
        gate_steps = [s for s in steps if s.type == StepType.GATE]
        assert len(gate_steps) >= 1
        assert gate_steps[0].auto_approve_after_hours == 1

    def test_general_workflow_auto_approve_72_hours(self, sop_engine):
        workflow = sop_engine.get_workflow_by_category("general")
        steps = sop_engine.get_workflow_steps(workflow)
        gate_steps = [s for s in steps if s.type == StepType.GATE]
        assert len(gate_steps) >= 1
        assert gate_steps[0].auto_approve_after_hours == 72
