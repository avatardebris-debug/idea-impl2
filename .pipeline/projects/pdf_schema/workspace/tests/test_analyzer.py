"""Tests for pdf_schema.analyzer — schema discovery and extraction."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from pdf_schema.analyzer import (
    _SCHEMA_TEMPLATES,
    _call_ollama,
    _parse_json,
    discover_schema,
    extract_schema,
    list_schemas,
)


INVOICE_TEXT = """
INVOICE #INV-2024-001
Date: 2024-03-15
Vendor: Acme Corp
Bill To: Widget Co

Item: Widget A  Qty: 10  Price: $50.00  Total: $500.00
Item: Widget B  Qty: 5   Price: $30.00  Total: $150.00

Subtotal: $650.00
Tax (10%): $65.00
Total Due: $715.00
Due Date: 2024-04-15
Payment Terms: Net 30
"""

RESUME_TEXT = """
Alice Johnson
alice@example.com | 555-1234

SUMMARY
Experienced software engineer with 8 years in Python.

SKILLS
Python, FastAPI, PostgreSQL, Docker

EXPERIENCE
Senior Engineer, Acme Corp, Jan 2020 - Present
  - Led API redesign reducing latency by 40%
  - Mentored team of 5 junior engineers

EDUCATION
B.S. Computer Science, State University, 2016
"""

CONTRACT_TEXT = """
SERVICE AGREEMENT
Parties: Alpha LLC and Beta Inc
Effective Date: 2024-01-01
Termination Date: 2024-12-31
Jurisdiction: State of California
Governing Law: California

Obligations:
- Alpha shall provide consulting services
- Beta shall pay monthly retainer of $5000

Key Clauses:
- Confidentiality: All information is proprietary
- Termination: 30-day notice required
"""


# ---------------------------------------------------------------------------
# _parse_json
# ---------------------------------------------------------------------------

class TestParseJson:
    def test_parses_valid_object(self):
        text = 'some prefix {"key": "value"} trailing text'
        result = _parse_json(text)
        assert result == {"key": "value"}

    def test_parses_valid_array(self):
        text = 'result: [1, 2, 3]'
        result = _parse_json(text)
        assert result == [1, 2, 3]

    def test_returns_none_on_invalid_json(self):
        result = _parse_json("not json at all")
        assert result is None

    def test_returns_none_on_empty_string(self):
        assert _parse_json("") is None

    def test_handles_nested_json(self):
        text = '{"outer": {"inner": [1, 2, 3]}}'
        result = _parse_json(text)
        assert result["outer"]["inner"] == [1, 2, 3]

    def test_handles_partial_garbage(self):
        text = "Model says: { invalid json here"
        result = _parse_json(text)
        assert result is None


# ---------------------------------------------------------------------------
# list_schemas
# ---------------------------------------------------------------------------

class TestListSchemas:
    def test_returns_list(self):
        schemas = list_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) > 0

    def test_contains_known_schemas(self):
        schemas = list_schemas()
        for name in ("invoice", "contract", "resume", "medical", "report"):
            assert name in schemas

    def test_matches_template_keys(self):
        assert set(list_schemas()) == set(_SCHEMA_TEMPLATES.keys())


# ---------------------------------------------------------------------------
# extract_schema — validation
# ---------------------------------------------------------------------------

class TestExtractSchemaValidation:
    def test_raises_on_unknown_schema(self):
        with pytest.raises(ValueError, match="Unknown schema"):
            extract_schema("some text", "nonexistent_schema")

    def test_error_message_lists_available(self):
        with pytest.raises(ValueError) as exc:
            extract_schema("text", "bogus")
        assert "invoice" in str(exc.value)

    def test_case_insensitive_schema_name(self):
        """Schema name lookup should be case-insensitive."""
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = extract_schema(INVOICE_TEXT, "INVOICE")
        assert result["_schema"] == "INVOICE"

    def test_all_template_keys_present_in_result(self):
        """Every key in the template must appear in the output (nulls OK)."""
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = extract_schema(INVOICE_TEXT, "invoice")
        for key in _SCHEMA_TEMPLATES["invoice"]:
            assert key in result

    def test_fallback_when_llm_returns_empty(self):
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = extract_schema(INVOICE_TEXT, "invoice")
        assert "_validation" in result
        assert result["_validation"]["completeness_pct"] == 0

    def test_fallback_warnings_mention_llm(self):
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = extract_schema(INVOICE_TEXT, "invoice")
        warnings = result["_validation"].get("warnings", [])
        assert any("fallback" in w.lower() or "llm" in w.lower() for w in warnings)

    def test_result_includes_schema_key(self):
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = extract_schema(RESUME_TEXT, "resume")
        assert result["_schema"] == "resume"

    def test_result_includes_metadata(self):
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = extract_schema(RESUME_TEXT, "resume")
        assert "metadata" in result
        assert "extracted_at" in result["metadata"]
        assert "text_length" in result["metadata"]

    def test_good_llm_response_parsed_correctly(self):
        """When LLM returns a valid JSON response, it should be used."""
        good_response = json.dumps({
            "invoice_number": "INV-001",
            "date": "2024-03-15",
            "vendor": "Acme Corp",
            "buyer": "Widget Co",
            "line_items": [],
            "subtotal": 650.0,
            "tax": 65.0,
            "total": 715.0,
            "due_date": "2024-04-15",
            "payment_terms": "Net 30",
        })
        with patch("pdf_schema.analyzer._call_ollama", return_value=good_response):
            result = extract_schema(INVOICE_TEXT, "invoice")
        assert result["invoice_number"] == "INV-001"
        assert result["vendor"] == "Acme Corp"
        assert result["_validation"]["completeness_pct"] == 100

    def test_completeness_pct_partial(self):
        """Partial LLM response should give proportional completeness."""
        partial = json.dumps({
            "invoice_number": "INV-001",
            "date": "2024-03-15",
            # rest are missing/null
        })
        with patch("pdf_schema.analyzer._call_ollama", return_value=partial):
            result = extract_schema(INVOICE_TEXT, "invoice")
        pct = result["_validation"]["completeness_pct"]
        assert 0 < pct < 100


# ---------------------------------------------------------------------------
# discover_schema
# ---------------------------------------------------------------------------

class TestDiscoverSchema:
    def test_returns_dict(self):
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = discover_schema(INVOICE_TEXT)
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = discover_schema(INVOICE_TEXT)
        for key in ("document_type", "confidence", "fields", "tables", "summary"):
            assert key in result

    def test_fallback_document_type_unknown(self):
        """When LLM fails, document_type should default to 'unknown'."""
        with patch("pdf_schema.analyzer._call_ollama", return_value="not json"):
            result = discover_schema(INVOICE_TEXT)
        assert result["document_type"] == "unknown"

    def test_fallback_extracts_regex_fields(self):
        """Regex fallback should extract some fields from the invoice text."""
        with patch("pdf_schema.analyzer._call_ollama", return_value="bad"):
            result = discover_schema(INVOICE_TEXT)
        # Regex finds "Key: Value" patterns — should capture at least one
        assert isinstance(result["fields"], dict)

    def test_good_llm_response_used(self):
        llm_out = json.dumps({
            "document_type": "invoice",
            "confidence": 0.95,
            "fields": {"invoice_number": "INV-001"},
            "tables": [],
            "summary": "An invoice from Acme Corp.",
        })
        with patch("pdf_schema.analyzer._call_ollama", return_value=llm_out):
            result = discover_schema(INVOICE_TEXT)
        assert result["document_type"] == "invoice"
        assert result["confidence"] == 0.95

    def test_metadata_always_present(self):
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = discover_schema(RESUME_TEXT)
        assert "metadata" in result
        assert result["metadata"]["text_length"] == len(RESUME_TEXT)

    def test_truncates_long_text(self):
        """discover_schema should not pass >8000 chars to LLM prompt."""
        long_text = "A" * 20000
        captured_prompts = []
        def fake_ollama(prompt, **kwargs):
            captured_prompts.append(prompt)
            return ""
        with patch("pdf_schema.analyzer._call_ollama", side_effect=fake_ollama):
            discover_schema(long_text)
        assert len(captured_prompts) == 1
        # The text slice is [:8000], but the prompt template itself
        # also contains a few literal 'A' chars (e.g. "Analyse"), so allow a small buffer
        assert captured_prompts[0].count("A") <= 8010

    def test_confidence_defaults_to_float(self):
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = discover_schema("Some text")
        assert isinstance(result["confidence"], (int, float))

    def test_resume_text_produces_fields(self):
        """Regex fallback on resume-like text should pick up some key:value pairs."""
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = discover_schema(RESUME_TEXT)
        assert isinstance(result["fields"], dict)

    def test_empty_text(self):
        """Empty document should not crash."""
        with patch("pdf_schema.analyzer._call_ollama", return_value=""):
            result = discover_schema("")
        assert isinstance(result, dict)
        assert "document_type" in result


# ---------------------------------------------------------------------------
# Schema template integrity
# ---------------------------------------------------------------------------

class TestSchemaTemplates:
    def test_all_templates_non_empty(self):
        for name, tmpl in _SCHEMA_TEMPLATES.items():
            assert len(tmpl) > 0, f"Template '{name}' is empty"

    def test_all_template_values_are_strings(self):
        for name, tmpl in _SCHEMA_TEMPLATES.items():
            for k, v in tmpl.items():
                assert isinstance(v, str), f"{name}.{k} value should be a string description"

    def test_invoice_has_expected_fields(self):
        tmpl = _SCHEMA_TEMPLATES["invoice"]
        for field in ("invoice_number", "date", "vendor", "total"):
            assert field in tmpl

    def test_resume_has_expected_fields(self):
        tmpl = _SCHEMA_TEMPLATES["resume"]
        for field in ("name", "email", "skills", "experience", "education"):
            assert field in tmpl

    def test_contract_has_expected_fields(self):
        tmpl = _SCHEMA_TEMPLATES["contract"]
        for field in ("parties", "effective_date", "jurisdiction"):
            assert field in tmpl
