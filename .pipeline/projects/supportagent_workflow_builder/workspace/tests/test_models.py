"""Tests for core data models (Task 1)."""

import json
import pytest
from supportagent.models import (
    Ticket,
    PipelineResult,
    TicketSource,
    TicketStatus,
    Urgency,
)


# ---- Ticket construction ----

class TestTicketConstruction:
    def test_create_ticket_defaults(self):
        t = Ticket(ticket_id="T1", source=TicketSource.JSON, subject="Hi", body="Body")
        assert t.ticket_id == "T1"
        assert t.source == TicketSource.JSON
        assert t.category is None
        assert t.urgency is None
        assert t.status == TicketStatus.NEW
        assert t.metadata == {}

    def test_create_ticket_with_all_fields(self):
        t = Ticket(
            ticket_id="T2",
            source=TicketSource.EMAIL,
            subject="Refund",
            body="I want a refund",
            metadata={"sender": "a@b.com"},
            category="refund",
            urgency=Urgency.HIGH,
            priority_score=8,
            assigned_team="refunds",
            draft_response="Hi",
            status=TicketStatus.ROUTED,
        )
        assert t.category == "refund"
        assert t.urgency == Urgency.HIGH
        assert t.priority_score == 8
        assert t.assigned_team == "refunds"


# ---- Serialization ----

class TestTicketSerialization:
    def test_to_dict(self):
        t = Ticket(ticket_id="T1", source=TicketSource.WEB, subject="S", body="B")
        d = t.to_dict()
        assert d["ticket_id"] == "T1"
        assert d["source"] == "web"
        assert d["status"] == "new"
        assert d["urgency"] is None

    def test_to_dict_with_urgency(self):
        t = Ticket(ticket_id="T1", source=TicketSource.JSON, subject="S", body="B", urgency=Urgency.CRITICAL)
        d = t.to_dict()
        assert d["urgency"] == "critical"

    def test_to_json_roundtrip(self):
        t = Ticket(ticket_id="T1", source=TicketSource.EMAIL, subject="Subj", body="Body", metadata={"k": "v"})
        j = t.to_json()
        t2 = Ticket.from_json(j)
        assert t2.ticket_id == t.ticket_id
        assert t2.source == t.source
        assert t2.subject == t.subject
        assert t2.body == t.body
        assert t2.metadata == t.metadata

    def test_from_dict(self):
        data = {
            "ticket_id": "T1",
            "source": "json",
            "subject": "Hello",
            "body": "World",
            "metadata": {"x": 1},
            "category": "billing",
            "urgency": "high",
            "priority_score": 7,
            "assigned_team": "billing_team",
            "draft_response": "Hi",
            "status": "routed",
        }
        t = Ticket.from_dict(data)
        assert t.ticket_id == "T1"
        assert t.source == TicketSource.JSON
        assert t.category.value == "billing"
        assert t.urgency == Urgency.HIGH
        assert t.priority_score == 7
        assert t.assigned_team == "billing_team"
        assert t.status == TicketStatus.ROUTED


# ---- PipelineResult ----

class TestPipelineResult:
    def test_create(self):
        p = PipelineResult(
            ticket_id="T1",
            category="billing",
            urgency="high",
            priority_score=8,
            assigned_team="billing_team",
            draft_response="Hi",
            status="routed",
        )
        assert p.ticket_id == "T1"

    def test_to_dict(self):
        p = PipelineResult(
            ticket_id="T1",
            category="billing",
            urgency="high",
            priority_score=8,
            assigned_team="billing_team",
            draft_response="Hi",
            status="routed",
        )
        d = p.to_dict()
        assert d["ticket_id"] == "T1"
        assert d["category"] == "billing"

    def test_from_dict(self):
        data = {
            "ticket_id": "T1",
            "category": "billing",
            "urgency": "high",
            "priority_score": 8,
            "assigned_team": "billing_team",
            "draft_response": "Hi",
            "status": "routed",
        }
        p = PipelineResult.from_dict(data)
        assert p.ticket_id == "T1"
        assert p.category == "billing"

    def test_from_ticket(self):
        t = Ticket(
            ticket_id="T1",
            source=TicketSource.JSON,
            subject="S",
            body="B",
            category="billing",
            urgency=Urgency.HIGH,
            priority_score=8,
            assigned_team="billing_team",
            draft_response="Hi",
            status=TicketStatus.ROUTED,
        )
        p = PipelineResult.from_ticket(t)
        assert p.ticket_id == "T1"
        assert p.category == "billing"
        assert p.urgency == "high"
        assert p.priority_score == 8
        assert p.assigned_team == "billing_team"
        assert p.draft_response == "Hi"
        assert p.status == "routed"

    def test_from_ticket_defaults(self):
        t = Ticket(ticket_id="T1", source=TicketSource.JSON, subject="S", body="B")
        p = PipelineResult.from_ticket(t)
        assert p.category == "general"
        assert p.urgency == "low"
        assert p.priority_score == 1
        assert p.assigned_team == "general_inbox"
        assert p.draft_response == ""
