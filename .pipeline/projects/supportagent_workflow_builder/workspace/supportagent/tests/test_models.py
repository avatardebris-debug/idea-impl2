"""Tests for supportagent.models — Ticket, PipelineResult, Workflow, etc."""

import json
from unittest import TestCase

from supportagent.models import (
    DraftResponse,
    GateType,
    PipelineResult,
    Priority,
    Priority as TicketPriority,
    RoutingResult,
    Ticket,
    TicketCategory,
    TicketSource,
    TicketStatus,
    TriageResult,
    Urgency,
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStepType,
)


class TestTicketSourceEnum(TestCase):
    def test_enum_values(self):
        self.assertEqual(TicketSource.EMAIL.value, "email")
        self.assertEqual(TicketSource.JSON.value, "json")
        self.assertEqual(TicketSource.WEB.value, "web")
        self.assertEqual(TicketSource.API.value, "api")


class TestUrgencyEnum(TestCase):
    def test_enum_values(self):
        self.assertEqual(Urgency.LOW.value, "low")
        self.assertEqual(Urgency.MEDIUM.value, "medium")
        self.assertEqual(Urgency.HIGH.value, "high")
        self.assertEqual(Urgency.CRITICAL.value, "critical")


class TestTicketStatusEnum(TestCase):
    def test_enum_values(self):
        self.assertEqual(TicketStatus.NEW.value, "new")
        self.assertEqual(TicketStatus.ROUTED.value, "routed")
        self.assertEqual(TicketStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(TicketStatus.AWAITING_CUSTOMER.value, "awaiting_customer")
        self.assertEqual(TicketStatus.RESOLVED.value, "resolved")
        self.assertEqual(TicketStatus.CLOSED.value, "closed")


class TestPriorityEnum(TestCase):
    def test_enum_values(self):
        self.assertEqual(Priority.P1.value, "p1")
        self.assertEqual(Priority.P2.value, "p2")
        self.assertEqual(Priority.P3.value, "p3")
        self.assertEqual(Priority.P4.value, "p4")


class TestTicketCategoryEnum(TestCase):
    def test_enum_values(self):
        self.assertEqual(TicketCategory.URGENT.value, "urgent")
        self.assertEqual(TicketCategory.BILLING.value, "billing")
        self.assertEqual(TicketCategory.TECHNICAL.value, "technical")
        self.assertEqual(TicketCategory.ACCOUNT.value, "account")
        self.assertEqual(TicketCategory.GENERAL.value, "general")


class TestWorkflowStepTypeEnum(TestCase):
    def test_enum_values(self):
        self.assertEqual(WorkflowStepType.ACTION.value, "action")
        self.assertEqual(WorkflowStepType.CONDITION.value, "condition")
        self.assertEqual(WorkflowStepType.GATE.value, "gate")


class TestWorkflowActionEnum(TestCase):
    def test_enum_values(self):
        self.assertEqual(WorkflowAction.CLASSIFY_TICKET.value, "classify_ticket")
        self.assertEqual(WorkflowAction.ASSIGN_TEAM.value, "assign_team")
        self.assertEqual(WorkflowAction.ESCALATE.value, "escalate")
        self.assertEqual(WorkflowAction.GENERATE_DRAFT.value, "generate_draft")
        self.assertEqual(WorkflowAction.SEND_RESPONSE.value, "send_response")
        self.assertEqual(WorkflowAction.NOTIFY.value, "notify")


class TestGateTypeEnum(TestCase):
    def test_enum_values(self):
        self.assertEqual(GateType.HUMAN_APPROVAL.value, "human_approval")
        self.assertEqual(GateType.HUMAN_REVIEW.value, "human_review")
        self.assertEqual(GateType.IMMEDIATE_RESPONSE.value, "immediate_response")


class TestTicket(TestCase):
    def test_create_ticket_defaults(self):
        ticket = Ticket(
            ticket_id="T1",
            source=TicketSource.EMAIL,
            subject="Test",
            body="Test body",
        )
        self.assertEqual(ticket.ticket_id, "T1")
        self.assertEqual(ticket.source, TicketSource.EMAIL)
        self.assertEqual(ticket.subject, "Test")
        self.assertEqual(ticket.body, "Test body")
        self.assertEqual(ticket.status, TicketStatus.NEW)
        self.assertEqual(ticket.priority_score, 0.0)
        self.assertIsNone(ticket.category)
        self.assertIsNone(ticket.urgency)
        self.assertIsNone(ticket.priority)
        self.assertIsNone(ticket.assigned_team)
        self.assertIsNone(ticket.sentiment)
        self.assertIsNone(ticket.draft_response)
        self.assertEqual(ticket.metadata, {})
        self.assertEqual(ticket.workflow_state, {})
        self.assertTrue(len(ticket.created_at) > 0)

    def test_ticket_post_init_status_conversion(self):
        ticket = Ticket(
            ticket_id="T2",
            source=TicketSource.WEB,
            subject="S",
            body="B",
            status="resolved",
        )
        self.assertEqual(ticket.status, TicketStatus.RESOLVED)

    def test_ticket_to_dict(self):
        ticket = Ticket(
            ticket_id="T3",
            source=TicketSource.API,
            subject="Subject",
            body="Body",
            category=TicketCategory.BILLING,
            urgency=Urgency.HIGH,
            priority=Priority.P1,
            status=TicketStatus.IN_PROGRESS,
            assigned_team="billing_team",
            sentiment="negative",
            draft_response="Draft",
            metadata={"key": "val"},
            workflow_state={"step": 1},
        )
        d = ticket.to_dict()
        self.assertEqual(d["ticket_id"], "T3")
        self.assertEqual(d["source"], "api")
        self.assertEqual(d["subject"], "Subject")
        self.assertEqual(d["body"], "Body")
        self.assertEqual(d["category"], "billing")
        self.assertEqual(d["urgency"], "high")
        self.assertEqual(d["priority"], "p1")
        self.assertEqual(d["status"], "in_progress")
        self.assertEqual(d["assigned_team"], "billing_team")
        self.assertEqual(d["sentiment"], "negative")
        self.assertEqual(d["draft_response"], "Draft")
        self.assertEqual(d["metadata"], {"key": "val"})
        self.assertEqual(d["workflow_state"], {"step": 1})

    def test_ticket_to_json_and_from_json(self):
        ticket = Ticket(
            ticket_id="T4",
            source=TicketSource.EMAIL,
            subject="JSON Test",
            body="JSON Body",
            category=TicketCategory.TECHNICAL,
            urgency=Urgency.CRITICAL,
            priority=Priority.P2,
            status=TicketStatus.ROUTED,
            assigned_team="tech_team",
            sentiment="neutral",
            draft_response="Draft JSON",
            metadata={"a": 1},
            workflow_state={"x": 2},
        )
        json_str = ticket.to_json()
        ticket2 = Ticket.from_json(json_str)
        self.assertEqual(ticket2.ticket_id, "T4")
        self.assertEqual(ticket2.source, TicketSource.EMAIL)
        self.assertEqual(ticket2.subject, "JSON Test")
        self.assertEqual(ticket2.body, "JSON Body")
        self.assertEqual(ticket2.category, TicketCategory.TECHNICAL)
        self.assertEqual(ticket2.urgency, Urgency.CRITICAL)
        self.assertEqual(ticket2.priority, Priority.P2)
        self.assertEqual(ticket2.status, TicketStatus.ROUTED)
        self.assertEqual(ticket2.assigned_team, "tech_team")
        self.assertEqual(ticket2.sentiment, "neutral")
        self.assertEqual(ticket2.draft_response, "Draft JSON")
        self.assertEqual(ticket2.metadata, {"a": 1})
        self.assertEqual(ticket2.workflow_state, {"x": 2})

    def test_ticket_from_dict_with_string_enums(self):
        data = {
            "ticket_id": "T5",
            "source": "web",
            "subject": "Dict Test",
            "body": "Dict Body",
            "category": "urgent",
            "urgency": "medium",
            "priority": "p3",
            "status": "new",
            "assigned_team": None,
            "sentiment": None,
            "draft_response": None,
            "metadata": {},
            "workflow_state": {},
        }
        ticket = Ticket.from_dict(data)
        self.assertEqual(ticket.ticket_id, "T5")
        self.assertEqual(ticket.source, TicketSource.WEB)
        self.assertEqual(ticket.category, TicketCategory.URGENT)
        self.assertEqual(ticket.urgency, Urgency.MEDIUM)
        self.assertEqual(ticket.priority, Priority.P3)
        self.assertEqual(ticket.status, TicketStatus.NEW)

    def test_ticket_from_dict_missing_optional_fields(self):
        data = {
            "ticket_id": "T6",
            "source": "json",
            "subject": "Minimal",
            "body": "Minimal body",
        }
        ticket = Ticket.from_dict(data)
        self.assertEqual(ticket.ticket_id, "T6")
        self.assertEqual(ticket.source, TicketSource.JSON)
        self.assertEqual(ticket.category, None)
        self.assertEqual(ticket.urgency, None)
        self.assertEqual(ticket.priority, None)
        self.assertEqual(ticket.status, TicketStatus.NEW)
        self.assertEqual(ticket.metadata, {})
        self.assertEqual(ticket.workflow_state, {})


class TestPipelineResult(TestCase):
    def test_create_pipeline_result_defaults(self):
        result = PipelineResult(ticket_id="P1")
        self.assertEqual(result.ticket_id, "P1")
        self.assertEqual(result.category, "general")
        self.assertEqual(result.urgency, "low")
        self.assertEqual(result.priority_score, 1)
        self.assertEqual(result.assigned_team, "general_inbox")
        self.assertEqual(result.draft_response, "")
        self.assertEqual(result.status, "new")

    def test_create_pipeline_result_with_values(self):
        result = PipelineResult(
            ticket_id="P2",
            category="billing",
            urgency="high",
            priority_score=0.9,
            assigned_team="billing_team",
            draft_response="Hello",
            status="resolved",
        )
        self.assertEqual(result.category, "billing")
        self.assertEqual(result.urgency, "high")
        self.assertEqual(result.priority_score, 0.9)
        self.assertEqual(result.assigned_team, "billing_team")
        self.assertEqual(result.draft_response, "Hello")
        self.assertEqual(result.status, "resolved")

    def test_pipeline_result_to_dict(self):
        result = PipelineResult(
            ticket_id="P3",
            category="technical",
            urgency="critical",
            priority_score=0.95,
            assigned_team="tech_team",
            draft_response="Hi there",
            status="in_progress",
        )
        d = result.to_dict()
        self.assertEqual(d["ticket_id"], "P3")
        self.assertEqual(d["category"], "technical")
        self.assertEqual(d["urgency"], "critical")
        self.assertEqual(d["priority_score"], 0.95)
        self.assertEqual(d["assigned_team"], "tech_team")
        self.assertEqual(d["draft_response"], "Hi there")
        self.assertEqual(d["status"], "in_progress")

    def test_pipeline_result_from_dict(self):
        data = {
            "ticket_id": "P4",
            "category": "account",
            "urgency": "low",
            "priority_score": 0.5,
            "assigned_team": "account_team",
            "draft_response": "Thanks",
            "status": "closed",
        }
        result = PipelineResult.from_dict(data)
        self.assertEqual(result.ticket_id, "P4")
        self.assertEqual(result.category, "account")
        self.assertEqual(result.urgency, "low")
        self.assertEqual(result.priority_score, 0.5)
        self.assertEqual(result.assigned_team, "account_team")
        self.assertEqual(result.draft_response, "Thanks")
        self.assertEqual(result.status, "closed")

    def test_pipeline_result_from_dict_defaults(self):
        data = {"ticket_id": "P5"}
        result = PipelineResult.from_dict(data)
        self.assertEqual(result.ticket_id, "P5")
        self.assertEqual(result.category, "general")
        self.assertEqual(result.urgency, "low")
        self.assertEqual(result.priority_score, 1)
        self.assertEqual(result.assigned_team, "general_inbox")
        self.assertEqual(result.draft_response, "")
        self.assertEqual(result.status, "new")

    def test_pipeline_result_from_ticket(self):
        ticket = Ticket(
            ticket_id="T7",
            source=TicketSource.EMAIL,
            subject="S",
            body="B",
            category=TicketCategory.URGENT,
            urgency=Urgency.HIGH,
            priority=Priority.P1,
            status=TicketStatus.IN_PROGRESS,
            assigned_team="urgent_team",
            draft_response="Draft response",
        )
        result = PipelineResult.from_ticket(ticket)
        self.assertEqual(result.ticket_id, "T7")
        self.assertEqual(result.category, "urgent")
        self.assertEqual(result.urgency, "high")
        self.assertEqual(result.priority_score, 0.0)  # priority_score was 0.0
        self.assertEqual(result.assigned_team, "urgent_team")
        self.assertEqual(result.draft_response, "Draft response")
        self.assertEqual(result.status, "in_progress")


class TestWorkflowStep(TestCase):
    def test_create_workflow_step_defaults(self):
        step = WorkflowStep(id="S1", step_type=WorkflowStepType.ACTION)
        self.assertEqual(step.id, "S1")
        self.assertEqual(step.step_type, WorkflowStepType.ACTION)
        self.assertIsNone(step.action)
        self.assertIsNone(step.condition)
        self.assertIsNone(step.gate_type)
        self.assertEqual(step.params, {})
        self.assertEqual(step.description, "")
        self.assertIsNone(step.then_step)
        self.assertIsNone(step.else_step)

    def test_create_workflow_step_with_all_fields(self):
        step = WorkflowStep(
            id="S2",
            step_type=WorkflowStepType.CONDITION,
            action=WorkflowAction.CLASSIFY_TICKET,
            condition={"key": "val"},
            gate_type=GateType.HUMAN_APPROVAL,
            params={"p": 1},
            description="Test step",
            then_step="S3",
            else_step="S4",
        )
        self.assertEqual(step.id, "S2")
        self.assertEqual(step.step_type, WorkflowStepType.CONDITION)
        self.assertEqual(step.action, WorkflowAction.CLASSIFY_TICKET)
        self.assertEqual(step.condition, {"key": "val"})
        self.assertEqual(step.gate_type, GateType.HUMAN_APPROVAL)
        self.assertEqual(step.params, {"p": 1})
        self.assertEqual(step.description, "Test step")
        self.assertEqual(step.then_step, "S3")
        self.assertEqual(step.else_step, "S4")


class TestWorkflow(TestCase):
    def test_create_workflow_defaults(self):
        wf = Workflow(name="Test Workflow")
        self.assertEqual(wf.name, "Test Workflow")
        self.assertEqual(wf.version, "1.0")
        self.assertEqual(wf.description, "")
        self.assertEqual(wf.steps, [])
        self.assertEqual(wf.metadata, {})

    def test_create_workflow_with_steps(self):
        step = WorkflowStep(id="S1", step_type=WorkflowStepType.ACTION)
        wf = Workflow(name="WF with steps", steps=[step])
        self.assertEqual(len(wf.steps), 1)
        self.assertEqual(wf.steps[0].id, "S1")


class TestWorkflowExecution(TestCase):
    def test_create_workflow_execution_defaults(self):
        wf = Workflow(name="Test")
        ticket = Ticket(ticket_id="T1", source=TicketSource.EMAIL, subject="S", body="B")
        exec_state = WorkflowExecution(workflow=wf, ticket=ticket)
        self.assertEqual(exec_state.workflow, wf)
        self.assertEqual(exec_state.ticket, ticket)
        self.assertIsNone(exec_state.current_step_id)
        self.assertEqual(exec_state.completed_steps, [])
        self.assertEqual(exec_state.failed_steps, [])
        self.assertEqual(exec_state.output, {})
        self.assertIsNone(exec_state.error)
        self.assertFalse(exec_state.is_complete)

    def test_create_workflow_execution_with_values(self):
        wf = Workflow(name="Test")
        ticket = Ticket(ticket_id="T2", source=TicketSource.EMAIL, subject="S", body="B")
        exec_state = WorkflowExecution(
            workflow=wf,
            ticket=ticket,
            current_step_id="S1",
            completed_steps=["S1"],
            failed_steps=["S2"],
            output={"result": "ok"},
            error=None,
            is_complete=True,
        )
        self.assertEqual(exec_state.current_step_id, "S1")
        self.assertEqual(exec_state.completed_steps, ["S1"])
        self.assertEqual(exec_state.failed_steps, ["S2"])
        self.assertEqual(exec_state.output, {"result": "ok"})
        self.assertIsNone(exec_state.error)
        self.assertTrue(exec_state.is_complete)


class TestTriageResult(TestCase):
    def test_create_triaqe_result_defaults(self):
        ticket = Ticket(ticket_id="T1", source=TicketSource.EMAIL, subject="S", body="B")
        result = TriageResult(
            ticket=ticket,
            category=TicketCategory.BILLING,
            priority_score=0.8,
            urgency=Urgency.HIGH,
            priority=Priority.P2,
            sentiment="negative",
        )
        self.assertEqual(result.ticket, ticket)
        self.assertEqual(result.category, TicketCategory.BILLING)
        self.assertEqual(result.priority_score, 0.8)
        self.assertEqual(result.urgency, Urgency.HIGH)
        self.assertEqual(result.priority, Priority.P2)
        self.assertEqual(result.sentiment, "negative")
        self.assertEqual(result.confidence, 0.0)

    def test_create_triaqe_result_with_confidence(self):
        ticket = Ticket(ticket_id="T1", source=TicketSource.EMAIL, subject="S", body="B")
        result = TriageResult(
            ticket=ticket,
            category=TicketCategory.TECHNICAL,
            priority_score=0.5,
            urgency=Urgency.MEDIUM,
            priority=Priority.P3,
            sentiment="neutral",
            confidence=0.95,
        )
        self.assertEqual(result.confidence, 0.95)


class TestRoutingResult(TestCase):
    def test_create_routing_result_defaults(self):
        ticket = Ticket(ticket_id="T1", source=TicketSource.EMAIL, subject="S", body="B")
        result = RoutingResult(
            ticket=ticket,
            assigned_team="tech_team",
            team_label="Technical Support",
            sla_hours=24.0,
        )
        self.assertEqual(result.ticket, ticket)
        self.assertEqual(result.assigned_team, "tech_team")
        self.assertEqual(result.team_label, "Technical Support")
        self.assertEqual(result.sla_hours, 24.0)
        self.assertFalse(result.escalation_required)
        self.assertIsNone(result.escalation_reason)

    def test_create_routing_result_with_escalation(self):
        ticket = Ticket(ticket_id="T1", source=TicketSource.EMAIL, subject="S", body="B")
        result = RoutingResult(
            ticket=ticket,
            assigned_team="escalation_team",
            team_label="Escalation",
            sla_hours=4.0,
            escalation_required=True,
            escalation_reason="SLA breach risk",
        )
        self.assertTrue(result.escalation_required)
        self.assertEqual(result.escalation_reason, "SLA breach risk")


class TestDraftResponse(TestCase):
    def test_create_draft_response_defaults(self):
        ticket = Ticket(ticket_id="T1", source=TicketSource.EMAIL, subject="S", body="B")
        response = DraftResponse(
            ticket=ticket,
            content="Hello",
            tone="professional",
            template_used="welcome",
            team="general",
        )
        self.assertEqual(response.ticket, ticket)
        self.assertEqual(response.content, "Hello")
        self.assertEqual(response.tone, "professional")
        self.assertEqual(response.template_used, "welcome")
        self.assertEqual(response.team, "general")
        self.assertEqual(response.metadata, {})

    def test_create_draft_response_with_metadata(self):
        ticket = Ticket(ticket_id="T1", source=TicketSource.EMAIL, subject="S", body="B")
        response = DraftResponse(
            ticket=ticket,
            content="Hi there",
            tone="friendly",
            template_used="greeting",
            team="sales",
            metadata={"key": "val"},
        )
        self.assertEqual(response.metadata, {"key": "val"})
