"""Tests for the Classifier (Task 3)."""

import pytest
from supportagent.classifier import Classifier
from supportagent.models import Ticket, TicketSource, Urgency


@pytest.fixture
def classifier():
    return Classifier()


class TestClassifier:
    def test_billing_category(self, classifier):
        t = Ticket(ticket_id="T1", source=TicketSource.JSON, subject="Billing issue", body="I was charged twice for my subscription")
        result = classifier.classify(t)
        assert result["category"] == "billing"
        assert result["urgency"] in ("medium", "high")
        assert result["priority_score"] >= 4

    def test_technical_category(self, classifier):
        t = Ticket(ticket_id="T2", source=TicketSource.JSON, subject="Error 500", body="The API is not working and keeps crashing")
        result = classifier.classify(t)
        assert result["category"] == "technical"
        assert result["priority_score"] >= 4

    def test_account_category(self, classifier):
        t = Ticket(ticket_id="T3", source=TicketSource.JSON, subject="Account settings", body="I need to update my email address")
        result = classifier.classify(t)
        assert result["category"] == "account"

    def test_urgent_category(self, classifier):
        t = Ticket(ticket_id="T4", source=TicketSource.JSON, subject="URGENT", body="Our production site is down, data loss imminent")
        result = classifier.classify(t)
        assert result["category"] == "urgent"
        assert result["urgency"] == "high"
        assert result["priority_score"] >= 7

    def test_general_category(self, classifier):
        t = Ticket(ticket_id="T5", source=TicketSource.JSON, subject="Random", body="Something unrelated to any specific category")
        result = classifier.classify(t)
        assert result["category"] == "general"
        assert result["urgency"] == "low"
        assert result["priority_score"] >= 1

    def test_classify_ticket_mutates(self, classifier):
        t = Ticket(ticket_id="T6", source=TicketSource.JSON, subject="Refund", body="Please refund my order")
        classifier.classify_ticket(t)
        assert t.category == "billing"
        assert t.urgency in (Urgency.MEDIUM, Urgency.HIGH)
        assert t.priority_score >= 4

    def test_empty_ticket_defaults_to_general(self, classifier):
        t = Ticket(ticket_id="T7", source=TicketSource.JSON, subject="", body="")
        result = classifier.classify(t)
        assert result["category"] == "general"
        assert result["urgency"] == "low"
        assert result["priority_score"] == 1

    def test_priority_capped_at_10(self, classifier):
        # Create a ticket with many billing keywords to test cap
        t = Ticket(ticket_id="T8", source=TicketSource.JSON,
                   subject="bill billing invoice payment charge subscription renewal plan pricing cost fee",
                   body="refund overcharge credit card")
        result = classifier.classify(t)
        assert result["priority_score"] <= 10
        assert result["category"] == "billing"

    def test_multiple_keyword_boost(self, classifier):
        t = Ticket(ticket_id="T9", source=TicketSource.JSON,
                   subject="bug error crash", body="not working broken issue")
        result = classifier.classify(t)
        assert result["category"] == "technical"
        # Multiple keywords should boost urgency
        assert result["priority_score"] >= 4

    def test_metadata_keywords_count(self, classifier):
        t = Ticket(ticket_id="T10", source=TicketSource.JSON, subject="", body="",
                   metadata={"subject_override": "billing invoice", "body_override": "refund charge"})
        result = classifier.classify(t)
        assert result["category"] == "billing"
