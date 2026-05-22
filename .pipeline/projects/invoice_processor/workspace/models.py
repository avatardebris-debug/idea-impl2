"""Core data models for the invoice processor."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


def _validate_positive(value: float, name: str) -> float:
    """Ensure a numeric field is non-negative."""
    if value < 0:
        raise ValidationError(f"{name} must be non-negative, got {value}")
    return value


def _validate_non_empty(value: str, name: str) -> str:
    """Ensure a string field is not blank."""
    if not value or not value.strip():
        raise ValidationError(f"{name} must not be blank")
    return value.strip()


@dataclass
class LineItem:
    """A single line item on an invoice."""
    description: str
    quantity: float
    unit_price: float
    amount: float
    source_file: str = ""

    def __post_init__(self):
        _validate_positive(self.quantity, "quantity")
        _validate_positive(self.unit_price, "unit_price")
        _validate_positive(self.amount, "amount")
        _validate_non_empty(self.description, "description")


@dataclass
class Invoice:
    """A parsed invoice."""
    vendor: str
    invoice_date: date
    total: float
    currency: str = "USD"
    line_items: List[LineItem] = field(default_factory=list)
    source_file: str = ""
    invoice_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    invoice_number: str = ""

    def __post_init__(self):
        _validate_non_empty(self.vendor, "vendor")
        _validate_positive(self.total, "total")
        _validate_non_empty(self.currency, "currency")


@dataclass
class Ledger:
    """A collection of invoices."""
    invoices: List[Invoice] = field(default_factory=list)

    def add_invoice(self, invoice: Invoice) -> None:
        """Add an invoice to the ledger."""
        self.invoices.append(invoice)

    def list_invoices(self) -> List[Invoice]:
        """Return all invoices in the ledger."""
        return list(self.invoices)

    def filter_by_vendor(self, vendor: str) -> List[Invoice]:
        """Filter invoices by vendor name (case-insensitive partial match)."""
        vendor_lower = vendor.lower()
        return [inv for inv in self.invoices if vendor_lower in inv.vendor.lower()]

    def filter_by_date_range(self, start_date: Optional[date] = None,
                             end_date: Optional[date] = None) -> List[Invoice]:
        """Filter invoices by date range (inclusive)."""
        result = []
        for inv in self.invoices:
            if start_date and inv.invoice_date < start_date:
                continue
            if end_date and inv.invoice_date > end_date:
                continue
            result.append(inv)
        return result

    def clear(self) -> None:
        """Remove all invoices from the ledger."""
        self.invoices.clear()


# Alias for convenience
InvoiceLedger = Ledger
