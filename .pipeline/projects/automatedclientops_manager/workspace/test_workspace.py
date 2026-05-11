"""Comprehensive test suite for AutomatedClientOps Manager."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from models import Client
from invoice import Invoice, InvoiceItem
from email_tool import EmailSender, EmailMessage
from sop_executor import (
    SOP,
    SOPExecutor,
    SOPStep,
    ExecutionResult,
    create_sop,
)
from manager import ClientOpsManager


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def sample_client():
    return Client(
        client_id="client-001",
        name="Acme Corp",
        email="billing@acme.com",
        status="active",
        metadata={"industry": "tech"},
    )


@pytest.fixture
def sample_invoice():
    items = [
        InvoiceItem(description="Web Design", quantity=1, unit_price=5000),
        InvoiceItem(description="Hosting", quantity=12, unit_price=50),
    ]
    return Invoice(
        invoice_id="INV-001",
        client_id="client-001",
        items=items,
        notes="Monthly hosting",
    )


@pytest.fixture
def sample_sop():
    return create_sop(
        name="test_sop",
        description="Test SOP",
        steps=[
            {
                "name": "step1",
                "action": "set_context",
                "params": {"key": "value"},
                "description": "Set context",
            },
            {
                "name": "step2",
                "action": "log",
                "params": {"message": "Test log", "level": "info"},
                "description": "Log message",
            },
        ],
    )


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ── Client Tests ──────────────────────────────────────────────────

class TestClient:
    def test_create_client(self, sample_client):
        assert sample_client.client_id == "client-001"
        assert sample_client.name == "Acme Corp"
        assert sample_client.status == "active"

    def test_client_to_dict(self, sample_client):
        d = sample_client.to_dict()
        assert d["client_id"] == "client-001"
        assert d["name"] == "Acme Corp"
        assert d["metadata"]["industry"] == "tech"

    def test_client_from_dict(self):
        d = {
            "client_id": "client-002",
            "name": "Beta Inc",
            "email": "info@beta.com",
            "status": "pending",
            "metadata": {},
        }
        c = Client.from_dict(d)
        assert c.client_id == "client-002"
        assert c.name == "Beta Inc"

    def test_client_str(self, sample_client):
        s = str(sample_client)
        assert "Acme Corp" in s
        assert "client-001" in s


# ── Invoice Tests ─────────────────────────────────────────────────

class TestInvoice:
    def test_create_invoice(self, sample_invoice):
        assert sample_invoice.invoice_id == "INV-001"
        assert sample_invoice.total == 5600.0
        assert sample_invoice.status == "pending"

    def test_invoice_to_dict(self, sample_invoice):
        d = sample_invoice.to_dict()
        assert d["invoice_id"] == "INV-001"
        assert d["total"] == 5600.0
        assert len(d["items"]) == 2

    def test_invoice_from_dict(self):
        d = {
            "invoice_id": "INV-002",
            "client_id": "client-001",
            "items": [
                {"description": "Service", "quantity": 1, "unit_price": 100}
            ],
            "status": "paid",
            "notes": "Test",
        }
        inv = Invoice.from_dict(d)
        assert inv.invoice_id == "INV-002"
        assert inv.total == 100.0
        assert inv.status == "paid"

    def test_mark_paid(self, sample_invoice):
        sample_invoice.status = "paid"
        assert sample_invoice.status == "paid"

    def test_empty_invoice(self):
        inv = Invoice(invoice_id="INV-000", client_id="client-001", items=[])
        assert inv.total == 0.0


# ── Email Tests ───────────────────────────────────────────────────

class TestEmailMessage:
    def test_create_message(self):
        msg = EmailMessage(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )
        assert msg.to == "test@example.com"
        assert msg.subject == "Test Subject"
        assert msg.body == "Test Body"

    def test_message_with_attachments(self):
        msg = EmailMessage(
            to="test@example.com",
            subject="Test",
            body="Test",
            attachments=["/path/to/file.pdf"],
        )
        assert len(msg.attachments) == 1

    def test_message_build_mime(self):
        msg = EmailMessage(
            to="test@example.com",
            subject="Test",
            body="Test Body",
        )
        mime_msg = msg.build_mime()
        assert mime_msg["To"] == "test@example.com"
        assert mime_msg["Subject"] == "Test"
        payload = mime_msg.get_payload()
        if isinstance(payload, list):
            payload_str = "\n".join(p.get_payload() if hasattr(p, "get_payload") else str(p) for p in payload)
        else:
            payload_str = payload
        assert "Test Body" in payload_str


class TestEmailSender:
    @mock.patch("email_tool.smtplib.SMTP")
    @mock.patch("email_tool.ssl.create_default_context")
    def test_send_email_success(self, mock_ssl, mock_smtp):
        mock_server = mock.MagicMock()
        mock_smtp.return_value.__enter__ = mock.MagicMock(return_value=mock_server)

        sender = EmailSender(
            smtp_server="smtp.test.com",
            smtp_port=587,
            sender_email="sender@test.com",
            sender_password="password",
        )

        msg = EmailMessage(
            to="recipient@test.com",
            subject="Test",
            body="Test Body",
        )

        result = sender.send(msg)
        assert result is True
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    def test_send_email_no_credentials(self):
        sender = EmailSender()
        msg = EmailMessage(to="test@test.com", subject="Test", body="Test")
        with pytest.raises(ValueError):
            sender.send(msg)

    def test_compose_invoice_email(self):
        sender = EmailSender()
        msg = sender.compose_invoice_email(
            client_email="client@test.com",
            invoice_id="INV-001",
            total=1000.0,
        )
        assert "INV-001" in msg.subject
        assert "$1000.00" in msg.subject
        assert "invoice" in msg.body.lower()

    def test_compose_file_delivery_email(self):
        sender = EmailSender()
        msg = sender.compose_file_delivery_email(
            client_email="client@test.com",
            project_name="Website Redesign",
            attachments=["/path/design.pdf", "/path/code.zip"],
        )
        assert "Website Redesign" in msg.subject
        assert "design.pdf" in msg.body
        assert "code.zip" in msg.body


# ── SOP Executor Tests ────────────────────────────────────────────

class TestSOPStep:
    def test_step_to_dict(self):
        step = SOPStep(name="test", action="log", params={"msg": "hi"})
        d = step.to_dict()
        assert d["name"] == "test"
        assert d["action"] == "log"

    def test_step_from_dict(self):
        d = {"name": "test", "action": "log", "params": {"msg": "hi"}}
        step = SOPStep.from_dict(d)
        assert step.name == "test"
        assert step.params["msg"] == "hi"


class TestSOP:
    def test_sop_to_dict(self, sample_sop):
        d = sample_sop.to_dict()
        assert d["name"] == "test_sop"
        assert len(d["steps"]) == 2

    def test_sop_from_dict(self):
        d = {
            "name": "test",
            "description": "Test SOP",
            "steps": [
                {"name": "s1", "action": "log", "params": {}}
            ],
            "inputs": [],
        }
        sop = SOP.from_dict(d)
        assert sop.name == "test"
        assert len(sop.steps) == 1

    def test_sop_from_yaml(self, temp_dir):
        yaml_content = """
name: yaml_test
description: Test from YAML
steps:
  - name: step1
    action: log
    params:
      message: "Hello"
      level: info
inputs: []
"""
        yaml_path = temp_dir / "test_sop.yaml"
        yaml_path.write_text(yaml_content)

        sop = SOP.from_yaml(yaml_path)
        assert sop.name == "yaml_test"
        assert len(sop.steps) == 1

    def test_sop_from_yaml_missing_file(self, temp_dir):
        with pytest.raises(FileNotFoundError):
            SOP.from_yaml(temp_dir / "nonexistent.yaml")


class TestSOPExecutor:
    def test_execute_success(self, sample_sop):
        executor = SOPExecutor(sample_sop)
        result = executor.execute()
        assert result.success is True
        assert len(result.step_results) == 2

    def test_execute_with_inputs(self, sample_sop):
        executor = SOPExecutor(sample_sop)
        result = executor.execute(inputs={"key": "value"})
        assert result.success is True

    def test_execute_invalid_action(self):
        sop = create_sop(
            name="bad_sop",
            description="Bad SOP",
            steps=[{"name": "step1", "action": "invalid_action", "params": {}}],
        )
        executor = SOPExecutor(sop)
        result = executor.execute()
        assert result.success is False
        assert len(result.errors) > 0

    def test_set_context(self):
        sop = create_sop(
            name="context_test",
            description="Test context",
            steps=[
                {
                    "name": "set",
                    "action": "set_context",
                    "params": {"my_key": "my_value"},
                }
            ],
        )
        executor = SOPExecutor(sop)
        result = executor.execute()
        assert result.success is True
        assert executor.context["my_key"] == "my_value"


class TestCreateSOP:
    def test_create_sop(self):
        sop = create_sop(
            name="test",
            description="Test",
            steps=[{"name": "s1", "action": "log", "params": {}}],
        )
        assert sop.name == "test"
        assert len(sop.steps) == 1


# ── Manager Tests ─────────────────────────────────────────────────

class TestClientOpsManager:
    @pytest.fixture
    def manager(self):
        return ClientOpsManager()

    def test_add_client(self, manager):
        client = manager.add_client("c1", "Test", "test@test.com")
        assert client.client_id == "c1"
        assert len(manager.clients) == 1

    def test_get_client(self, manager):
        manager.add_client("c1", "Test", "test@test.com")
        client = manager.get_client("c1")
        assert client is not None
        assert client.name == "Test"

    def test_get_client_not_found(self, manager):
        assert manager.get_client("nonexistent") is None

    def test_remove_client(self, manager):
        manager.add_client("c1", "Test", "test@test.com")
        assert manager.remove_client("c1") is True
        assert len(manager.clients) == 0

    def test_list_clients(self, manager):
        manager.add_client("c1", "Test1", "t1@test.com")
        manager.add_client("c2", "Test2", "t2@test.com")
        clients = manager.list_clients()
        assert len(clients) == 2

    def test_create_invoice(self, manager):
        manager.add_client("c1", "Test", "test@test.com")
        invoice = manager.create_invoice(
            invoice_id="INV-001",
            client_id="c1",
            items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
        )
        assert invoice.invoice_id == "INV-001"
        assert invoice.total == 100.0
        assert len(manager.invoices) == 1

    def test_create_invoice_invalid_client(self, manager):
        with pytest.raises(ValueError):
            manager.create_invoice(
                invoice_id="INV-001",
                client_id="nonexistent",
                items=[],
            )

    def test_mark_invoice_paid(self, manager):
        manager.add_client("c1", "Test", "test@test.com")
        manager.create_invoice(
            invoice_id="INV-001",
            client_id="c1",
            items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
        )
        assert manager.mark_invoice_paid("INV-001") is True
        assert manager.invoices["INV-001"].status == "paid"

    def test_save_load_state(self, manager, temp_dir):
        manager.add_client("c1", "Test", "test@test.com")
        manager.create_invoice(
            invoice_id="INV-001",
            client_id="c1",
            items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
        )

        state_path = temp_dir / "state.json"
        manager.save_state(state_path)

        new_manager = ClientOpsManager()
        new_manager.load_state(state_path)

        assert len(new_manager.clients) == 1
        assert len(new_manager.invoices) == 1
        assert new_manager.clients["c1"].name == "Test"

    def test_save_load_state_missing_file(self, manager, temp_dir):
        with pytest.raises(FileNotFoundError):
            manager.load_state(temp_dir / "nonexistent.json")

    @mock.patch("email_tool.EmailSender")
    def test_send_invoice_email(self, mock_sender_class, manager):
        mock_sender = mock.MagicMock()
        mock_sender.send.return_value = True
        manager.email_sender = mock_sender

        manager.add_client("c1", "Test", "test@test.com")
        manager.create_invoice(
            invoice_id="INV-001",
            client_id="c1",
            items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
        )

        result = manager.send_invoice_email("INV-001")
        assert result is True
        mock_sender.send.assert_called_once()

    def test_send_invoice_email_no_sender(self, manager):
        manager.add_client("c1", "Test", "test@test.com")
        manager.create_invoice(
            invoice_id="INV-001",
            client_id="c1",
            items=[{"description": "Service", "quantity": 1, "unit_price": 100}],
        )
        with pytest.raises(RuntimeError):
            manager.send_invoice_email("INV-001")

    def test_execute_sop(self, manager, sample_sop):
        result = manager.execute_sop(sample_sop)
        assert result.success is True

    def test_run_standard_onboarding(self, manager, temp_dir):
        # Create a mock email sender
        mock_sender = mock.MagicMock()
        mock_sender.send.return_value = True
        manager.email_sender = mock_sender

        result = manager.run_standard_onboarding(
            client_id="c1",
            client_name="Test Client",
            client_email="test@test.com",
            project_name="Test Project",
            invoice_items=[{"description": "Service", "quantity": 1, "unit_price": 500}],
        )

        assert "client" in result
        assert "invoice" in result
        assert result["client"]["name"] == "Test Client"
        assert result["invoice"]["total"] == 500.0
        assert result["invoice_sent"] is True


# ── Integration Tests ─────────────────────────────────────────────

class TestIntegration:
    def test_full_workflow(self, temp_dir):
        """Test complete client onboarding workflow."""
        manager = ClientOpsManager()

        # Add client
        client = manager.add_client(
            client_id="client-001",
            name="Acme Corp",
            email="billing@acme.com",
            status="active",
        )

        # Create invoice
        invoice = manager.create_invoice(
            invoice_id="INV-001",
            client_id="client-001",
            items=[
                {"description": "Web Design", "quantity": 1, "unit_price": 5000},
                {"description": "Hosting", "quantity": 12, "unit_price": 50},
            ],
        )

        # Verify
        assert client.client_id == "client-001"
        assert invoice.total == 5600.0
        assert len(manager.clients) == 1
        assert len(manager.invoices) == 1

        # Save state
        state_path = temp_dir / "state.json"
        manager.save_state(state_path)
        assert state_path.exists()

        # Load state
        new_manager = ClientOpsManager()
        new_manager.load_state(state_path)
        assert len(new_manager.clients) == 1
        assert len(new_manager.invoices) == 1

    def test_sop_execution_chain(self):
        """Test executing multiple SOPs in sequence."""
        manager = ClientOpsManager()

        # Create first SOP
        sop1 = create_sop(
            name="sop1",
            description="First SOP",
            steps=[
                {
                    "name": "log1",
                    "action": "log",
                    "params": {"message": "Step 1", "level": "info"},
                }
            ],
        )

        # Create second SOP
        sop2 = create_sop(
            name="sop2",
            description="Second SOP",
            steps=[
                {
                    "name": "log2",
                    "action": "log",
                    "params": {"message": "Step 2", "level": "info"},
                }
            ],
        )

        # Execute both
        result1 = manager.execute_sop(sop1)
        result2 = manager.execute_sop(sop2)

        assert result1.success is True
        assert result2.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
