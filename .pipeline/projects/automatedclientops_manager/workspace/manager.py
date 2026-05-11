"""ClientOpsManager — Main orchestrator for AutomatedClientOps Manager.

Provides the high-level interface for managing clients, generating invoices,
sending emails, and executing SOPs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from models import Client
from invoice import Invoice, InvoiceItem
from email_tool import EmailSender, EmailMessage
from sop_executor import SOP, SOPExecutor, SOPStep, create_sop

logger = logging.getLogger(__name__)


class ClientOpsManager:
    """Main orchestrator for automated client operations.

    Manages clients, invoices, email communication, and SOP execution.

    Attributes:
        clients: Dict of client_id -> Client.
        invoices: Dict of invoice_id -> Invoice.
        email_sender: Optional EmailSender instance.
    """

    def __init__(self, email_sender: Optional[EmailSender] = None):
        self.clients: dict[str, Client] = {}
        self.invoices: dict[str, Invoice] = {}
        self.email_sender = email_sender

    # ── Client Management ────────────────────────────────────────

    def add_client(
        self,
        client_id: str,
        name: str,
        email: str,
        status: str = "pending",
        metadata: Optional[dict] = None,
    ) -> Client:
        """Add or update a client.

        Args:
            client_id: Unique client identifier.
            name: Client name.
            email: Client email.
            status: Client status.
            metadata: Optional metadata dict.

        Returns:
            The Client instance.
        """
        client = Client(
            client_id=client_id,
            name=name,
            email=email,
            status=status,
            metadata=metadata or {},
        )
        self.clients[client_id] = client
        logger.info(f"Client added: {client_id} ({name})")
        return client

    def get_client(self, client_id: str) -> Optional[Client]:
        """Get a client by ID."""
        return self.clients.get(client_id)

    def remove_client(self, client_id: str) -> bool:
        """Remove a client by ID. Returns True if removed."""
        if client_id in self.clients:
            del self.clients[client_id]
            return True
        return False

    def list_clients(self) -> list[Client]:
        """List all clients."""
        return list(self.clients.values())

    # ── Invoice Management ───────────────────────────────────────

    def create_invoice(
        self,
        invoice_id: str,
        client_id: str,
        items: Optional[list[dict]] = None,
        due_date: Optional[str] = None,
        notes: str = "",
    ) -> Invoice:
        """Create an invoice for a client.

        Args:
            invoice_id: Unique invoice identifier.
            client_id: Client ID the invoice is for.
            items: List of item dicts with 'description', 'quantity', 'unit_price'.
            due_date: Optional due date string (ISO format).
            notes: Optional notes.

        Returns:
            The created Invoice.
        """
        from datetime import datetime

        if client_id not in self.clients:
            raise ValueError(f"Client '{client_id}' not found")

        item_objects = []
        if items:
            for item_data in items:
                item_objects.append(
                    InvoiceItem(
                        description=item_data["description"],
                        quantity=item_data.get("quantity", 1),
                        unit_price=item_data.get("unit_price", 0),
                    )
                )

        invoice = Invoice(
            invoice_id=invoice_id,
            client_id=client_id,
            items=item_objects,
            notes=notes,
        )
        self.invoices[invoice_id] = invoice
        logger.info(f"Invoice created: {invoice_id} for client {client_id} (${invoice.total:.2f})")
        return invoice

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get an invoice by ID."""
        return self.invoices.get(invoice_id)

    def mark_invoice_paid(self, invoice_id: str) -> bool:
        """Mark an invoice as paid."""
        invoice = self.invoices.get(invoice_id)
        if invoice:
            invoice.status = "paid"
            logger.info(f"Invoice {invoice_id} marked as paid")
            return True
        return False

    # ── Email Operations ─────────────────────────────────────────

    def send_invoice_email(
        self,
        invoice_id: str,
        client_email: Optional[str] = None,
        attachments: Optional[list[str]] = None,
    ) -> bool:
        """Send an invoice notification email.

        Args:
            invoice_id: Invoice to send.
            client_email: Override client email.
            attachments: Optional file attachments.

        Returns:
            True if sent successfully.
        """
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice '{invoice_id}' not found")

        email = client_email or self.clients[invoice.client_id].email
        if not self.email_sender:
            raise RuntimeError("EmailSender not configured")

        msg = self.email_sender.compose_invoice_email(
            client_email=email,
            invoice_id=invoice_id,
            total=invoice.total,
            attachments=attachments,
        )
        return self.email_sender.send(msg)

    def send_file_delivery_email(
        self,
        client_id: str,
        project_name: str,
        attachments: list[str],
        client_email: Optional[str] = None,
    ) -> bool:
        """Send a file delivery email.

        Args:
            client_id: Client to send to.
            project_name: Project/deliverable name.
            attachments: List of file paths to attach.
            client_email: Override client email.

        Returns:
            True if sent successfully.
        """
        client = self.clients.get(client_id)
        if not client:
            raise ValueError(f"Client '{client_id}' not found")

        email = client_email or client.email
        if not self.email_sender:
            raise RuntimeError("EmailSender not configured")

        msg = self.email_sender.compose_file_delivery_email(
            client_email=email,
            project_name=project_name,
            attachments=attachments,
        )
        return self.email_sender.send(msg)

    # ── SOP Execution ────────────────────────────────────────────

    def execute_sop(
        self,
        sop: SOP,
        inputs: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Execute an SOP.

        Args:
            sop: The SOP to execute.
            inputs: Input data for the SOP.

        Returns:
            The execution result.
        """
        executor = SOPExecutor(sop)
        result = executor.execute(inputs)
        if result.success:
            logger.info(f"SOP '{sop.name}' executed successfully")
        else:
            logger.error(f"SOP '{sop.name}' failed: {result.errors}")
        return result

    def run_standard_onboarding(
        self,
        client_id: str,
        client_name: str,
        client_email: str,
        project_name: str,
        deliverables: Optional[list[str]] = None,
        invoice_items: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """Run a standard client onboarding SOP.

        This is a convenience method that creates and executes a complete
        onboarding workflow: add client, create invoice, send invoice email,
        and prepare for file delivery.

        Args:
            client_id: Unique client identifier.
            client_name: Client name.
            client_email: Client email.
            project_name: Project name.
            deliverables: Optional list of deliverable file paths.
            invoice_items: Optional list of invoice item dicts.

        Returns:
            Dict with results of each step.
        """
        deliverables = deliverables or []
        invoice_items = invoice_items or []

        # Step 1: Add client
        client = self.add_client(client_id, client_name, client_email, status="active")

        # Step 2: Create invoice
        invoice_id = f"INV-{client_id.upper()}-001"
        invoice = self.create_invoice(
            invoice_id=invoice_id,
            client_id=client_id,
            items=invoice_items,
            notes=f"Initial invoice for {project_name}",
        )

        # Step 3: Send invoice email
        invoice_sent = False
        if self.email_sender:
            try:
                invoice_sent = self.send_invoice_email(invoice_id, attachments=deliverables)
            except Exception as e:
                logger.error(f"Failed to send invoice email: {e}")

        # Step 4: Prepare file delivery SOP
        delivery_sop = create_sop(
            name=f"deliver_{project_name.replace(' ', '_')}",
            description=f"Deliver files for {project_name}",
            steps=[
                {
                    "name": "deliver_files",
                    "action": "deliver_file",
                    "params": {"files": deliverables},
                    "description": "Prepare files for delivery",
                },
                {
                    "name": "send_delivery_email",
                    "action": "send_email",
                    "params": {
                        "to": client_email,
                        "subject": f"Deliverable Ready: {project_name}",
                        "body": f"Your deliverable for '{project_name}' is ready!",
                        "attachments": deliverables,
                    },
                    "description": "Send delivery email",
                },
            ],
        )

        delivery_result = self.execute_sop(delivery_sop)

        return {
            "client": client.to_dict(),
            "invoice": invoice.to_dict(),
            "invoice_sent": invoice_sent,
            "delivery_sop": delivery_sop.to_dict(),
            "delivery_result": delivery_result.step_results,
        }

    def save_state(self, path: str | Path) -> None:
        """Save the current state to a JSON file.

        Args:
            path: Path to save to.
        """
        path = Path(path)
        state = {
            "clients": {cid: c.to_dict() for cid, c in self.clients.items()},
            "invoices": {iid: inv.to_dict() for iid, inv in self.invoices.items()},
        }
        path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        logger.info(f"State saved to {path}")

    def load_state(self, path: str | Path) -> None:
        """Load state from a JSON file.

        Args:
            path: Path to load from.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")

        state = json.loads(path.read_text(encoding="utf-8"))
        self.clients = {cid: Client.from_dict(c) for cid, c in state.get("clients", {}).items()}
        self.invoices = {iid: Invoice.from_dict(inv) for iid, inv in state.get("invoices", {}).items()}
        logger.info(f"State loaded from {path}")
