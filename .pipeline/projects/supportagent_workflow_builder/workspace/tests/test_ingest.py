"""Tests for the Ingestor (Task 2)."""

import pytest
from supportagent.ingest import Ingestor, IngestorError
from supportagent.models import Ticket, TicketSource


# ===================== JSON =====================

class TestIngestorFromJson:
    def test_from_json_dict(self):
        payload = {
            "ticket_id": "J1",
            "subject": "Cannot login",
            "body": "I get an error 500",
            "sender": "a@b.com",
            "customer_name": "Alice",
        }
        t = Ingestor.from_json(payload)
        assert t.ticket_id == "J1"
        assert t.source == TicketSource.JSON
        assert t.subject == "Cannot login"
        assert t.body == "I get an error 500"
        assert t.metadata["sender"] == "a@b.com"
        assert t.metadata["customer_name"] == "Alice"

    def test_from_json_string(self):
        payload = '{"ticket_id":"J2","subject":"Refund","body":"Please refund"}'
        t = Ingestor.from_json(payload)
        assert t.ticket_id == "J2"
        assert t.subject == "Refund"

    def test_from_json_flexible_keys(self):
        payload = {"title": "Feature request", "message": "Add dark mode"}
        t = Ingestor.from_json(payload)
        assert t.subject == "Feature request"
        assert t.body == "Add dark mode"

    def test_from_json_minimal(self):
        payload = {}
        t = Ingestor.from_json(payload)
        assert t.ticket_id is not None  # auto-generated UUID
        assert t.source == TicketSource.JSON
        assert t.subject == ""
        assert t.body == ""

    def test_from_json_custom_ticket_id(self):
        payload = {"subject": "S", "body": "B"}
        t = Ingestor.from_json(payload, ticket_id="CUSTOM")
        assert t.ticket_id == "CUSTOM"

    def test_from_json_malformed_raises(self):
        with pytest.raises(Exception):  # json.JSONDecodeError
            Ingestor.from_json("{bad json")


# ===================== MIME =====================

class TestIngestorFromMime:
    def test_from_mime_text_plain(self):
        mime = (
            "From: alice@example.com\r\n"
            "To: support@company.com\r\n"
            "Subject: Order not received\r\n"
            "Date: Mon, 1 Jan 2024 12:00:00 +0000\r\n"
            "\r\n"
            "My order #12345 has not arrived. Please help."
        )
        t = Ingestor.from_mime(mime)
        assert t.source == TicketSource.EMAIL
        assert t.subject == "Order not received"
        assert "My order #12345" in t.body
        assert t.metadata["sender"] == "alice@example.com"
        assert t.metadata["date"] == "Mon, 1 Jan 2024 12:00:00 +0000"

    def test_from_mime_multipart(self):
        mime = (
            "From: bob@example.com\r\n"
            "Subject: Bug report\r\n"
            "MIME-Version: 1.0\r\n"
            "Content-Type: multipart/alternative; boundary=BOUNDARY\r\n"
            "\r\n"
            "--BOUNDARY\r\n"
            "Content-Type: text/html\r\n"
            "\r\n"
            "<html><body>Bug in production</body></html>\r\n"
            "--BOUNDARY\r\n"
            "Content-Type: text/plain\r\n"
            "\r\n"
            "Bug in production\r\n"
            "--BOUNDARY--\r\n"
        )
        t = Ingestor.from_mime(mime)
        assert t.source == TicketSource.EMAIL
        assert "Bug in production" in t.body

    def test_from_mime_no_subject(self):
        mime = "From: a@b.com\r\n\r\nHello world"
        t = Ingestor.from_mime(mime)
        assert t.subject == "(no subject)"
        assert t.body == "Hello world"

    def test_from_mime_custom_ticket_id(self):
        mime = "From: a@b.com\r\nSubject: S\r\n\r\nB"
        t = Ingestor.from_mime(mime, ticket_id="EMAIL1")
        assert t.ticket_id == "EMAIL1"


# ===================== Web Form =====================

class TestIngestorFromWebform:
    def test_from_webform_dict(self):
        payload = {
            "ticket_id": "W1",
            "subject": "Billing question",
            "body": "How do I change my plan?",
            "name": "Charlie",
            "email": "charlie@x.com",
        }
        t = Ingestor.from_webform(payload)
        assert t.ticket_id == "W1"
        assert t.source == TicketSource.WEB
        assert t.subject == "Billing question"
        assert t.metadata["customer_name"] == "Charlie"
        assert t.metadata["sender_email"] == "charlie@x.com"

    def test_from_webform_url_encoded(self):
        payload = "subject=Password%20reset&body=I%20forgot%20my%20password&name=Dave"
        t = Ingestor.from_webform(payload)
        assert t.source == TicketSource.WEB
        assert t.subject == "Password reset"
        assert t.body == "I forgot my password"
        assert t.metadata["customer_name"] == "Dave"

    def test_from_webform_minimal(self):
        payload = {}
        t = Ingestor.from_webform(payload)
        assert t.ticket_id is not None
        assert t.source == TicketSource.WEB

    def test_from_webform_custom_ticket_id(self):
        payload = {"subject": "S", "body": "B"}
        t = Ingestor.from_webform(payload, ticket_id="WEB1")
        assert t.ticket_id == "WEB1"
