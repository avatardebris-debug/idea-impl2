#!/usr/bin/env python3
"""Smoke test for invoice processor - verifies core functionality."""

import csv
import os
import sys
import tempfile
from datetime import date

# Add workspace to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from invoice_processor.models import Invoice, LineItem, InvoiceLedger
from invoice_processor.exceptions import InvoiceProcessorError, ParsingError, LedgerError
from invoice_processor.parsers import get_parser, PDFParser, CSVParser
from invoice_processor.ledger import LedgerExporter
from invoice_processor.cli import process_directory


def test_models_importable():
    """Test that data models are importable and have correct fields."""
    item = LineItem(description="Test", quantity=1, unit_price=10.0, amount=10.0)
    assert item.description == "Test"
    assert item.quantity == 1
    assert item.unit_price == 10.0
    assert item.amount == 10.0

    inv = Invoice(vendor="Test Vendor", invoice_date=date(2024, 1, 1), total=100.0)
    assert inv.vendor == "Test Vendor"
    assert inv.invoice_date == date(2024, 1, 1)
    assert inv.total == 100.0
    assert inv.currency == "USD"
    assert inv.line_items == []
    assert inv.invoice_id != ""

    ledger = InvoiceLedger()
    assert ledger.invoices == []
    print("  [PASS] test_models_importable")


def test_ledger_operations():
    """Test Ledger add, list, filter operations."""
    ledger = InvoiceLedger()
    inv1 = Invoice(vendor="Acme Corp", invoice_date=date(2024, 1, 15), total=500.0)
    inv2 = Invoice(vendor="TechSupply Inc", invoice_date=date(2024, 2, 20), total=1200.0)
    inv3 = Invoice(vendor="Acme Solutions", invoice_date=date(2024, 3, 10), total=300.0)

    ledger.add_invoice(inv1)
    ledger.add_invoice(inv2)
    ledger.add_invoice(inv3)

    all_inv = ledger.list_invoices()
    assert len(all_inv) == 3

    filtered = ledger.filter_by_vendor("Acme")
    assert len(filtered) == 2

    filtered_date = ledger.filter_by_date_range(
        start_date=date(2024, 2, 1), end_date=date(2024, 3, 31)
    )
    assert len(filtered_date) == 2

    ledger.clear()
    assert len(ledger.list_invoices()) == 0
    print("  [PASS] test_ledger_operations")


def test_csv_parser():
    """Test CSV parser can parse invoice CSV files."""
    parser = CSVParser()
    assert parser.supports_file("test.csv")
    assert not parser.supports_file("test.pdf")

    sample_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_invoices", "acme_invoice.csv")
    if os.path.exists(sample_csv):
        invoice = parser.parse(sample_csv)
        assert invoice is not None
        assert invoice.vendor == "Acme Corp"
        assert invoice.total == 1500.0
        assert len(invoice.line_items) > 0
        print("  [PASS] test_csv_parser")
    else:
        print("  [SKIP] test_csv_parser (no sample CSV)")


def test_csv_export_import_roundtrip():
    """Test that CSV export and import produce the same data."""
    exporter = LedgerExporter()

    # Create a test ledger
    ledger = InvoiceLedger()
    inv1 = Invoice(
        vendor="Test Vendor",
        invoice_date=date(2024, 6, 15),
        total=999.99,
        currency="USD",
        invoice_number="TEST-001",
        source_file="test_source.pdf",
        line_items=[
            LineItem(description="Item A", quantity=2, unit_price=100.0, amount=200.0),
            LineItem(description="Item B", quantity=1, unit_price=799.99, amount=799.99),
        ],
    )
    ledger.add_invoice(inv1)

    # Export to temp CSV
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
        csv_path = f.name
    exporter.export_to_csv(ledger, csv_path)

    # Read back
    imported_ledger = exporter.import_from_csv(csv_path)
    imported_invoices = imported_ledger.list_invoices()

    assert len(imported_invoices) == 1
    imported_inv = imported_invoices[0]
    assert imported_inv.vendor == "Test Vendor"
    assert imported_inv.total == 999.99
    assert imported_inv.currency == "USD"
    assert imported_inv.invoice_number == "TEST-001"
    assert len(imported_inv.line_items) == 2
    assert imported_inv.line_items[0].description == "Item A"
    assert imported_inv.line_items[0].amount == 200.0

    os.unlink(csv_path)
    print("  [PASS] test_csv_export_import_roundtrip")


def test_cli_processes_files():
    """Test CLI processes sample files and produces CSV output."""
    sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_invoices")
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
        output_csv = f.name

    result = process_directory(sample_dir, output_csv)
    assert result == 0
    assert os.path.exists(output_csv)

    # Verify CSV content
    with open(output_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0

    os.unlink(output_csv)
    print("  [PASS] test_cli_processes_files")


def test_exceptions():
    """Test custom exceptions work correctly."""
    try:
        raise ParsingError("test.pdf", "Test error")
    except InvoiceProcessorError as e:
        assert "test.pdf" in str(e)

    try:
        raise LedgerError("Test ledger error")
    except InvoiceProcessorError as e:
        assert "Test ledger error" in str(e)
    print("  [PASS] test_exceptions")


def test_parser_getter():
    """Test get_parser returns correct parser types."""
    pdf_parser = get_parser("test.pdf")
    assert isinstance(pdf_parser, PDFParser)

    csv_parser = get_parser("test.csv")
    assert isinstance(csv_parser, CSVParser)

    try:
        get_parser("test.txt")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("  [PASS] test_parser_getter")


if __name__ == '__main__':
    print("Running smoke tests...\n")
    tests = [
        test_models_importable,
        test_ledger_operations,
        test_csv_parser,
        test_csv_export_import_roundtrip,
        test_cli_processes_files,
        test_exceptions,
        test_parser_getter,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
