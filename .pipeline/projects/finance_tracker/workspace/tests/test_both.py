"""Tests for pdf_schema and finance_tracker — all offline, no PDF/LLM/network calls."""
from __future__ import annotations
import json
import sys
import pathlib
from unittest.mock import patch

_base = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_base.parent.parent / "pdf_schema" / "workspace"))
sys.path.insert(0, str(_base))

import pytest


# ─────────────────────────────────────────────
# pdf_schema tests
# ─────────────────────────────────────────────

_INVOICE_TEXT = """
INVOICE

Invoice Number: INV-2024-0042
Date: 2024-01-15
Due Date: 2024-02-15

From: Acme Corp
      123 Business St, New York, NY 10001

To: ClientCo Inc
    456 Client Ave, San Francisco, CA 94102

Line Items:
  - Web Development Services    40 hrs @ $150.00   $6,000.00
  - Design Consultation         10 hrs @ $120.00   $1,200.00
  - Server Setup (one-time)      1 unit @ $500.00  $  500.00

Subtotal: $7,700.00
Tax (8%): $  616.00
Total:    $8,316.00

Payment Terms: Net 30
"""

_CONTRACT_TEXT = """
SERVICE AGREEMENT

This agreement is made between Acme Corp ("Service Provider") and ClientCo Inc ("Client"),
effective January 15, 2024, and terminating December 31, 2024.

Governing Law: State of New York
Jurisdiction: New York County

Obligations:
- Service Provider shall deliver monthly progress reports.
- Client shall pay invoices within 30 days of receipt.

Confidentiality: Both parties agree to maintain strict confidentiality.
"""


class TestPdfSchemaAnalyzer:
    def test_discover_fallback_extracts_fields(self):
        from pdf_schema.analyzer import discover_schema
        with patch("pdf_schema.analyzer._call_ollama", return_value="not json"):
            result = discover_schema(_INVOICE_TEXT)
        assert "fields" in result
        assert "document_type" in result
        assert "metadata" in result

    def test_extract_schema_returns_all_keys(self):
        from pdf_schema.analyzer import extract_schema
        mock_resp = json.dumps({
            "invoice_number": "INV-2024-0042",
            "date": "2024-01-15",
            "vendor": "Acme Corp",
            "buyer": "ClientCo Inc",
            "line_items": [],
            "subtotal": 7700.0,
            "tax": 616.0,
            "total": 8316.0,
            "due_date": "2024-02-15",
            "payment_terms": "Net 30",
        })
        with patch("pdf_schema.analyzer._call_ollama", return_value=mock_resp):
            result = extract_schema(_INVOICE_TEXT, "invoice")
        assert result["invoice_number"] == "INV-2024-0042"
        assert result["vendor"] == "Acme Corp"
        assert "_validation" in result

    def test_extract_schema_fallback_on_llm_failure(self):
        from pdf_schema.analyzer import extract_schema
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = extract_schema(_INVOICE_TEXT, "invoice")
        assert "_validation" in result
        assert result["_validation"]["completeness_pct"] == 0

    def test_extract_schema_unknown_raises(self):
        from pdf_schema.analyzer import extract_schema
        with pytest.raises(ValueError, match="Unknown schema"):
            extract_schema("text", "nonexistent_schema")

    def test_list_schemas(self):
        from pdf_schema.analyzer import list_schemas
        schemas = list_schemas()
        assert "invoice" in schemas
        assert "contract" in schemas
        assert "resume" in schemas

    def test_validation_completeness_filled(self):
        from pdf_schema.analyzer import extract_schema
        # All fields populated → high completeness
        template_fill = json.dumps({
            "invoice_number": "X", "date": "2024-01-01", "vendor": "V",
            "buyer": "B", "line_items": [], "subtotal": 100.0, "tax": 10.0,
            "total": 110.0, "due_date": "2024-02-01", "payment_terms": "Net 30",
        })
        with patch("pdf_schema.analyzer._call_ollama", return_value=template_fill):
            result = extract_schema(_INVOICE_TEXT, "invoice")
        assert result["_validation"]["completeness_pct"] >= 80

    def test_parse_json_handles_prefix(self):
        from pdf_schema.analyzer import _parse_json
        text = 'Here: {"a": 1, "b": 2} end'
        assert _parse_json(text) == {"a": 1, "b": 2}

    def test_parse_json_returns_none_on_failure(self):
        from pdf_schema.analyzer import _parse_json
        assert _parse_json("no json here") is None

    def test_discover_schema_metadata_present(self):
        from pdf_schema.analyzer import discover_schema
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = discover_schema(_INVOICE_TEXT)
        assert "metadata" in result
        assert "text_length" in result["metadata"]


# ─────────────────────────────────────────────
# finance_tracker tests
# ─────────────────────────────────────────────

_CSV_SIMPLE = """Date,Description,Amount
2024-01-05,Whole Foods Market,-87.43
2024-01-06,Starbucks Coffee,-6.50
2024-01-08,PAYROLL DEPOSIT,3500.00
2024-01-10,Netflix Subscription,-15.99
2024-01-12,Shell Gas Station,-55.00
2024-01-15,Amazon.com Purchase,-120.00
2024-01-20,Uber Ride,-18.50
2024-01-22,Walgreens Pharmacy,-45.00
2024-01-25,Whole Foods Market,-94.10
2024-01-28,Chipotle Mexican Grill,-14.75
"""

_CSV_DEBIT_CREDIT = """Date,Description,Debit,Credit
2024-02-01,Walmart Grocery,65.00,
2024-02-03,Direct Deposit,,3500.00
2024-02-10,ExxonMobil Gas,45.00,
2024-02-15,Hulu Streaming,14.99,
2024-02-20,CVS Pharmacy,32.00,
"""


class TestCategorizer:
    def test_parse_csv_simple(self):
        from finance_tracker.categorizer import parse_csv
        txns = parse_csv(_CSV_SIMPLE)
        assert len(txns) == 10

    def test_parse_csv_debit_credit(self):
        from finance_tracker.categorizer import parse_csv
        txns = parse_csv(_CSV_DEBIT_CREDIT)
        assert len(txns) == 5

    def test_categorize_groceries(self):
        from finance_tracker.categorizer import categorize
        assert categorize("Whole Foods Market") == "groceries"
        assert categorize("Kroger") == "groceries"
        assert categorize("WALMART SUPERCENTER") == "groceries"

    def test_categorize_dining(self):
        from finance_tracker.categorizer import categorize
        assert categorize("Starbucks Coffee") == "dining"
        assert categorize("Chipotle Mexican Grill") == "dining"
        assert categorize("DoorDash") == "dining"

    def test_categorize_subscriptions(self):
        from finance_tracker.categorizer import categorize
        assert categorize("Netflix") == "subscriptions"
        assert categorize("Spotify Premium") == "subscriptions"

    def test_categorize_income(self):
        from finance_tracker.categorizer import categorize
        assert categorize("PAYROLL DEPOSIT") == "income"
        assert categorize("Direct Deposit") == "income"

    def test_categorize_fuel(self):
        from finance_tracker.categorizer import categorize
        assert categorize("Shell Gas Station") == "fuel"
        assert categorize("ExxonMobil Gas Station") == "fuel"

    def test_categorize_health(self):
        from finance_tracker.categorizer import categorize
        assert categorize("Walgreens Pharmacy") == "health"
        assert categorize("CVS") == "health"

    def test_categorize_unknown_returns_other(self):
        from finance_tracker.categorizer import categorize
        assert categorize("XYZZY FROBNICATE LLC") == "other"

    def test_parse_amount_handles_parens(self):
        from finance_tracker.categorizer import _parse_amount
        assert _parse_amount("(100.00)") == -100.0
        assert _parse_amount("$1,234.56") == 1234.56
        assert _parse_amount("-50.00") == -50.0

    def test_income_positive_debit_negative(self):
        from finance_tracker.categorizer import parse_csv
        txns = parse_csv(_CSV_SIMPLE)
        income_txns  = [t for t in txns if t.amount > 0]
        expense_txns = [t for t in txns if t.amount < 0]
        assert len(income_txns) > 0
        assert len(expense_txns) > 0


class TestReporter:
    @pytest.fixture
    def transactions(self):
        from finance_tracker.categorizer import parse_csv
        return parse_csv(_CSV_SIMPLE)

    def test_summarize_by_month(self, transactions):
        from finance_tracker.reporter import summarize_by_month
        summaries = summarize_by_month(transactions)
        assert len(summaries) >= 1
        s = summaries[0]
        assert s.month == "2024-01"
        assert s.income > 0
        assert s.expenses > 0

    def test_net_calculation(self, transactions):
        from finance_tracker.reporter import summarize_by_month
        s = summarize_by_month(transactions)[0]
        assert abs(s.net - (s.income - s.expenses)) < 0.01

    def test_by_category_populated(self, transactions):
        from finance_tracker.reporter import summarize_by_month
        s = summarize_by_month(transactions)[0]
        assert len(s.by_category) > 0

    def test_detect_anomalies_flags_outliers(self):
        from finance_tracker.categorizer import parse_csv
        from finance_tracker.reporter import detect_anomalies
        # Need 3+ grocery transactions. CSV has 2. Add a third normal + one huge outlier.
        extra = (
            "\n2024-01-29,Whole Foods Market,-91.00"
            "\n2024-01-30,Whole Foods Market,-1000.00"
        )
        txns = parse_csv(_CSV_SIMPLE + extra)
        anomalies = detect_anomalies(txns, z_threshold=1.0)
        grocery_anomaly = [a for a in anomalies if a["category"] == "groceries"]
        assert len(grocery_anomaly) > 0
        assert grocery_anomaly[0]["amount"] >= 900.0

    def test_detect_anomalies_empty(self):
        from finance_tracker.reporter import detect_anomalies
        from finance_tracker.categorizer import parse_csv
        # Only 2 transactions per category — no anomalies (need >= 3)
        txns = parse_csv("Date,Description,Amount\n2024-01-01,Starbucks,-6.00\n2024-01-02,Starbucks,-7.00\n")
        assert detect_anomalies(txns) == []

    def test_format_report_contains_month(self, transactions):
        from finance_tracker.reporter import summarize_by_month, format_report
        summaries = summarize_by_month(transactions)
        report = format_report(summaries)
        assert "2024-01" in report

    def test_format_report_contains_income(self, transactions):
        from finance_tracker.reporter import summarize_by_month, format_report
        summaries = summarize_by_month(transactions)
        report = format_report(summaries)
        assert "3,500.00" in report or "Income" in report
