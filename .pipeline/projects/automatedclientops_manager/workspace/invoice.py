"""Invoice model for AutomatedClientOps Manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class InvoiceItem:
    """A single line item on an invoice.

    Attributes:
        description: What the item is for.
        quantity: Number of units.
        unit_price: Price per unit.
    """

    description: str
    quantity: float = 1.0
    unit_price: float = 0.0

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Invoice:
    """Represents an invoice for a client engagement.

    Attributes:
        invoice_id: Unique identifier for the invoice.
        client_id: The client this invoice is for.
        items: Line items on the invoice.
        status: Invoice status ('draft', 'sent', 'paid', 'overdue').
        due_date: Optional due date.
        notes: Optional free-form notes.
        created_at: When the invoice was created.
    """

    invoice_id: str
    client_id: str
    items: list[InvoiceItem] = field(default_factory=list)
    status: str = "pending"
    due_date: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def subtotal(self) -> float:
        return sum(item.total for item in self.items)

    @property
    def total(self) -> float:
        return self.subtotal

    def add_item(self, description: str, quantity: float = 1.0, unit_price: float = 0.0) -> None:
        """Add a line item to the invoice."""
        self.items.append(InvoiceItem(description=description, quantity=quantity, unit_price=unit_price))

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        return {
            "invoice_id": self.invoice_id,
            "client_id": self.client_id,
            "items": [
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total": item.total,
                }
                for item in self.items
            ],
            "subtotal": self.subtotal,
            "total": self.total,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Invoice":
        """Deserialize from a dictionary."""
        items = [
            InvoiceItem(
                description=item_data["description"],
                quantity=item_data.get("quantity", 1.0),
                unit_price=item_data.get("unit_price", 0.0),
            )
            for item_data in data.get("items", [])
        ]
        due_date = None
        if data.get("due_date"):
            due_date = datetime.fromisoformat(data["due_date"])
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        return cls(
            invoice_id=data["invoice_id"],
            client_id=data["client_id"],
            items=items,
            status=data.get("status", "draft"),
            due_date=due_date,
            notes=data.get("notes", ""),
            created_at=created_at,
        )
