"""Comprehensive unit tests for the invoice processor (Phase 2)."""

import csv
import os
import sys
import tempfile
import uuid
from datetime import date, datetime
from pathlib import Path

import pytest

# Ensure workspace is on path
_ws = Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from invoice_processor.models import Invoice, LineItem, Ledger, ValidationError
from invoice_processor.parsers.csv_parser import CSVParser
from invoice_processor.parsers.pdf_parser import PDFParser
from invoice_processor.ledger import LedgerExporter
from invoice_processor.exceptions import ParsingError, LedgerError
from invoice_processor.logging_config import setup_logger, get_logger
from invoice_processor.retry import retry


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_csv_path(tmp_path):
    """Create a temporary CSV file with sample invoice data."""
    csv_file = tmp_path / "sample_invoice.csv"
    csv_file.write_text(
        "Invoice Number,Vendor,Date,Total,Currency,Description,Quantity,Unit Price,Amount\n"
        "INV-001,Acme Corp,2024-01-15,150.00,USD,Widget A,10,10.00,100.00\n"
        "INV-001,Acme Corp,2024-01-15,150.00,USD,Widget B,5,10.00,50.00\n"
    )
    return str(csv_file)


@pytest.fixture
def multi_invoice_csv_path(tmp_path):
    """Create a CSV with multiple invoices."""
    csv_file = tmp_path / "multi_invoice.csv"
    csv_file.write_text(
        "inv_id,Invoice Number,Vendor,Date,Total,Currency,Description,Quantity,Unit Price,Amount\n"
        "1,INV-001,Acme Corp,2024-01-15,150.00,USD,Widget A,10,10.00,100.00\n"
        "1,INV-001,Acme Corp,2024-01-15,150.00,USD,Widget B,5,10.00,50.00\n"
        "2,INV-002,Beta LLC,2024-02-20,200.00,EUR,Gadget X,4,50.00,200.00\n"
    )
    return str(csv_file)


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Create a minimal valid PDF file."""
    pdf_file = tmp_path / "sample.pdf"
    # Minimal valid PDF
    pdf_content = (
        "%PDF-1.4\n"
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        "4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test) Tj ET\nendstream\nendobj\n"
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        "xref\n0 6\ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    )
    pdf_file.write_text(pdf_content)
    return str(pdf_file)


@pytest.fixture
def valid_invoice():
    """Create a valid Invoice instance."""
    return Invoice(
        vendor="Test Vendor",
        invoice_date=date(2024, 1, 1),
        total=100.0,
        currency="USD",
        line_items=[
            LineItem(description="Item 1", quantity=1, unit_price=100.0, amount=100.0),
        ],
    )


# ── Model Tests ───────────────────────────────────────────────────────────

class TestLineItem:
    def test_valid_line_item(self):
        item = LineItem(description="Test", quantity=1, unit_price=10.0, amount=10.0)
        assert item.description == "Test"
        assert item.quantity == 1
        assert item.unit_price == 10.0
        assert item.amount == 10.0

    def test_blank_description_raises(self):
        with pytest.raises(ValidationError, match="description"):
            LineItem(description="", quantity=1, unit_price=10.0, amount=10.0)

    def test_negative_quantity_raises(self):
        with pytest.raises(ValidationError, match="quantity"):
            LineItem(description="Test", quantity=-1, unit_price=10.0, amount=-10.0)

    def test_negative_unit_price_raises(self):
        with pytest.raises(ValidationError, match="unit_price"):
            LineItem(description="Test", quantity=1, unit_price=-10.0, amount=-10.0)

    def test_negative_amount_raises(self):
        with pytest.raises(ValidationError, match="amount"):
            LineItem(description="Test", quantity=1, unit_price=10.0, amount=-10.0)


class TestInvoice:
    def test_valid_invoice(self, valid_invoice):
        assert valid_invoice.vendor == "Test Vendor"
        assert valid_invoice.total == 100.0
        assert valid_invoice.currency == "USD"
        assert len(valid_invoice.line_items) == 1
        assert valid_invoice.invoice_id  # auto-generated

    def test_blank_vendor_raises(self):
        with pytest.raises(ValidationError, match="vendor"):
            Invoice(vendor="", invoice_date=date.today(), total=100.0)

    def test_negative_total_raises(self):
        with pytest.raises(ValidationError, match="total"):
            Invoice(vendor="Test", invoice_date=date.today(), total=-100.0)

    def test_blank_currency_raises(self):
        with pytest.raises(ValidationError, match="currency"):
            Invoice(vendor="Test", invoice_date=date.today(), total=100.0, currency="")

    def test_auto_invoice_id(self):
        inv1 = Invoice(vendor="A", invoice_date=date.today(), total=10.0)
        inv2 = Invoice(vendor="B", invoice_date=date.today(), total=20.0)
        assert inv1.invoice_id != inv2.invoice_id
        assert len(inv1.invoice_id) == 8


class TestLedger:
    def test_add_and_list(self, valid_invoice):
        ledger = Ledger()
        ledger.add_invoice(valid_invoice)
        assert len(ledger.list_invoices()) == 1

    def test_filter_by_vendor(self, valid_invoice):
        ledger = Ledger()
        ledger.add_invoice(Invoice(vendor="Acme Corp", invoice_date=date.today(), total=10.0))
        ledger.add_invoice(Invoice(vendor="Beta LLC", invoice_date=date.today(), total=20.0))
        results = ledger.filter_by_vendor("acme")
        assert len(results) == 1
        assert results[0].vendor == "Acme Corp"

    def test_filter_by_date_range(self):
        ledger = Ledger()
        ledger.add_invoice(Invoice(vendor="A", invoice_date=date(2024, 1, 1), total=10.0))
        ledger.add_invoice(Invoice(vendor="B", invoice_date=date(2024, 6, 1), total=20.0))
        ledger.add_invoice(Invoice(vendor="C", invoice_date=date(2024, 12, 1), total=30.0))
        results = ledger.filter_by_date_range(date(2024, 3, 1), date(2024, 9, 1))
        assert len(results) == 1
        assert results[0].vendor == "B"

    def test_clear(self, valid_invoice):
        ledger = Ledger()
        ledger.add_invoice(valid_invoice)
        ledger.clear()
        assert len(ledger.list_invoices()) == 0


# ── CSV Parser Tests ──────────────────────────────────────────────────────

class TestCSVParser:
    def test_parse_single_invoice(self, sample_csv_path):
        parser = CSVParser()
        result = parser.parse(sample_csv_path)
        assert isinstance(result, Invoice)
        assert result.vendor == "Acme Corp"
        assert result.total == 150.0
        assert len(result.line_items) == 2

    def test_parse_multi_invoice(self, multi_invoice_csv_path):
        parser = CSVParser()
        result = parser.parse(multi_invoice_csv_path)
        assert isinstance(result, list)
        assert len(result) == 2
        vendors = {inv.vendor for inv in result}
        assert "Acme Corp" in vendors
        assert "Beta LLC" in vendors

    def test_parse_nonexistent_file(self):
        parser = CSVParser()
        result = parser.parse("/nonexistent/file.csv")
        assert result == []

    def test_parse_non_csv_file(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")
        parser = CSVParser()
        result = parser.parse(str(txt_file))
        assert result == []

    def test_parse_empty_file(self, tmp_path):
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        parser = CSVParser()
        result = parser.parse(str(empty_file))
        assert result == []

    def test_parse_none_path(self):
        parser = CSVParser()
        result = parser.parse(None)  # type: ignore
        assert result == []

    def test_parse_empty_string_path(self):
        parser = CSVParser()
        result = parser.parse("")
        assert result == []


# ── PDF Parser Tests ──────────────────────────────────────────────────────

class TestPDFParser:
    def test_parse_valid_pdf(self, sample_pdf_path):
        parser = PDFParser()
        result = parser.parse(sample_pdf_path)
        # PDF parser returns an Invoice (may have default values)
        assert isinstance(result, Invoice)

    def test_parse_nonexistent_pdf(self):
        parser = PDFParser()
        with pytest.raises(ParsingError):
            parser.parse("/nonexistent/file.pdf")

    def test_parse_non_pdf_file(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")
        parser = PDFParser()
        result = parser.parse(str(txt_file))
        # PDF parser may return an Invoice with defaults for non-PDF files
        assert isinstance(result, Invoice)


# ── Ledger Exporter Tests ─────────────────────────────────────────────────

class TestLedgerExporter:
    def test_export_and_import_roundtrip(self, valid_invoice):
        exporter = LedgerExporter()
        ledger = Ledger()
        ledger.add_invoice(valid_invoice)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            exporter.export_to_csv(ledger, csv_path)
            imported_ledger = exporter.import_from_csv(csv_path)
            assert len(imported_ledger.list_invoices()) == 1
            imported_inv = imported_ledger.list_invoices()[0]
            assert imported_inv.vendor == valid_invoice.vendor
            assert imported_inv.total == valid_invoice.total
            assert len(imported_inv.line_items) == len(valid_invoice.line_items)
        finally:
            os.unlink(csv_path)

    def test_export_no_line_items(self, valid_invoice):
        # Create invoice without line items
        inv = Invoice(vendor="No Items", invoice_date=date.today(), total=50.0)
        exporter = LedgerExporter()
        ledger = Ledger()
        ledger.add_invoice(inv)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            exporter.export_to_csv(ledger, csv_path)
            imported_ledger = exporter.import_from_csv(csv_path)
            assert len(imported_ledger.list_invoices()) == 1
        finally:
            os.unlink(csv_path)


# ── Logging Tests ─────────────────────────────────────────────────────────

class TestLogging:
    def test_setup_logger_returns_logger(self):
        logger = setup_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_get_logger_returns_same(self):
        logger1 = get_logger("test_get")
        logger2 = get_logger("test_get")
        assert logger1 is logger2

    def test_logger_has_handlers(self):
        logger = setup_logger("test_handlers")
        assert len(logger.handlers) >= 1  # At least console handler


# ── Retry Tests ───────────────────────────────────────────────────────────

class TestRetry:
    def test_retry_succeeds_first_attempt(self):
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = retry(func, max_attempts=3)
        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failures(self):
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return "success"

        result = retry(func, max_attempts=3, delay=0.01)
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausts_attempts(self):
        def func():
            raise ValueError("permanent error")

        with pytest.raises(ValueError, match="permanent error"):
            retry(func, max_attempts=3, delay=0.01)

    def test_retry_custom_exceptions(self):
        def func():
            raise FileNotFoundError("not found")

        with pytest.raises(FileNotFoundError):
            retry(func, max_attempts=2, exceptions=(ValueError,), delay=0.01)


# ── Exception Tests ───────────────────────────────────────────────────────

class TestExceptions:
    def test_parsing_error_has_file_path(self):
        err = ParsingError("/path/to/file.pdf", "Bad format")
        assert err.file_path == "/path/to/file.pdf"
        assert "file.pdf" in str(err)

    def test_ledger_error(self):
        err = LedgerError("Operation failed")
        assert "Operation failed" in str(err)

    def test_validation_error(self):
        err = ValidationError("Invalid data")
        assert "Invalid data" in str(err)


# ── Integration / Edge Case Tests ─────────────────────────────────────────

class TestIntegration:
    def test_csv_parser_with_missing_columns(self, tmp_path):
        """Parser should handle CSVs with unexpected column layouts."""
        csv_file = tmp_path / "weird.csv"
        csv_file.write_text(
            "Name,Price\n"
            "Item A,10.00\n"
            "Item B,20.00\n"
        )
        parser = CSVParser()
        result = parser.parse(str(csv_file))
        # Should return empty or handle gracefully
        assert result is not None  # Doesn't crash

    def test_ledger_with_many_invoices(self):
        ledger = Ledger()
        for i in range(100):
            ledger.add_invoice(Invoice(
                vendor=f"Vendor {i}",
                invoice_date=date(2024, 1, 1),
                total=float(i),
            ))
        assert len(ledger.list_invoices()) == 100

    def test_invoice_id_uniqueness_across_many(self):
        ids = set()
        for _ in range(100):
            inv = Invoice(vendor="Test", invoice_date=date.today(), total=1.0)
            ids.add(inv.invoice_id)
        assert len(ids) == 100  # All unique

    def test_large_csv_import(self, tmp_path):
        """Test importing a large CSV."""
        csv_file = tmp_path / "large.csv"
        with open(csv_file, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["invoice_id", "Vendor", "Date", "Total", "Currency", "Description", "Quantity", "Unit Price", "Amount"])
            for i in range(1000):
                writer.writerow([
                    f"INV-{i // 10:04d}",  # 100 invoices, 10 items each
                    f"Vendor {i % 10}",
                    "2024-01-01",
                    "100.00",
                    "USD",
                    f"Item {i}",
                    "1",
                    "100.00",
                    "100.00",
                ])
        exporter = LedgerExporter()
        ledger = exporter.import_from_csv(str(csv_file))
        assert len(ledger.list_invoices()) == 100
