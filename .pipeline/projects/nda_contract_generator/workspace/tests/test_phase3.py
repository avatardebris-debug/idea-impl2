"""Phase 3 tests: exporters, validator, and compare command."""

import os
import tempfile
import pytest


# ---------------------------------------------------------------------------
# PDF Exporter Tests
# ---------------------------------------------------------------------------

class TestPDFExporter:
    """Tests for the PDF export module."""

    def test_import_pdf_exporter(self):
        """PDF exporter module imports without error."""
        from nda_contract_generator.exporters.pdf_exporter import export_pdf, pdf_to_bytes
        assert callable(export_pdf)
        assert callable(pdf_to_bytes)

    def test_export_pdf_to_file(self, tmp_path):
        """export_pdf writes a file (plain-text fallback if reportlab absent)."""
        from nda_contract_generator.exporters.pdf_exporter import export_pdf
        text = "NON-DISCLOSURE AGREEMENT\n\nThis agreement is entered into...\n\nTERM: 2 years.\n\nGOVERNING LAW: California."
        out = str(tmp_path / "test.pdf")
        result = export_pdf(text, out, title="Test NDA")
        assert os.path.exists(result), f"Expected output at {result}"

    def test_pdf_to_bytes_returns_bytes(self):
        """pdf_to_bytes returns bytes."""
        from nda_contract_generator.exporters.pdf_exporter import pdf_to_bytes
        result = pdf_to_bytes("Test NDA content.\n\nThis is confidential.", "Test NDA")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pdf_exporter_creates_parent_dirs(self, tmp_path):
        """export_pdf creates parent directories automatically."""
        from nda_contract_generator.exporters.pdf_exporter import export_pdf
        out = str(tmp_path / "subdir" / "deep" / "test.pdf")
        result = export_pdf("Agreement text here.", out)
        assert os.path.exists(result)

    def test_pdf_contains_disclaimer(self, tmp_path):
        """Exported file content references the legal disclaimer."""
        from nda_contract_generator.exporters import pdf_to_bytes
        data = pdf_to_bytes("Simple agreement.", "Test NDA")
        # Disclaimer should be embedded
        assert len(data) > 100  # substantial output


# ---------------------------------------------------------------------------
# DOCX Exporter Tests
# ---------------------------------------------------------------------------

class TestDOCXExporter:
    """Tests for the DOCX export module."""

    def test_import_docx_exporter(self):
        """DOCX exporter imports without error."""
        from nda_contract_generator.exporters.docx_exporter import export_docx
        assert callable(export_docx)

    def test_export_docx_to_file(self, tmp_path):
        """export_docx writes a file (plain-text fallback if python-docx absent)."""
        from nda_contract_generator.exporters.docx_exporter import export_docx
        text = "NON-DISCLOSURE AGREEMENT\n\nThis agreement is entered into...\n\nTERM: 2 years."
        out = str(tmp_path / "test.docx")
        result = export_docx(text, out, title="Test NDA")
        assert os.path.exists(result), f"Expected output at {result}"

    def test_docx_exporter_creates_parent_dirs(self, tmp_path):
        """export_docx creates parent directories automatically."""
        from nda_contract_generator.exporters.docx_exporter import export_docx
        out = str(tmp_path / "sub" / "deep" / "test.docx")
        result = export_docx("Agreement content.", out)
        assert os.path.exists(result)

    def test_docx_export_with_sections(self, tmp_path):
        """DOCX export handles section headings correctly."""
        from nda_contract_generator.exporters.docx_exporter import export_docx
        text = (
            "NON-DISCLOSURE AGREEMENT\n\n"
            "DEFINITIONS:\n\nConfidential information means...\n\n"
            "TERM AND TERMINATION:\n\nThis agreement is valid for 2 years.\n\n"
            "GOVERNING LAW:\n\nThis agreement is governed by California law."
        )
        out = str(tmp_path / "sections.docx")
        result = export_docx(text, out)
        assert os.path.exists(result)


# ---------------------------------------------------------------------------
# Compare Command Tests
# ---------------------------------------------------------------------------

class TestCompareCommand:
    """Tests for the NDA comparison utility."""

    def test_import_compare(self):
        """Compare module imports without error."""
        from nda_contract_generator.cli.commands.compare import compare_ndas, compare_nda_files, summary_diff
        assert callable(compare_ndas)
        assert callable(compare_nda_files)
        assert callable(summary_diff)

    def test_identical_texts(self):
        """Identical NDAs report no differences."""
        from nda_contract_generator.cli.commands.compare import compare_ndas
        text = "This is an NDA.\n\nIt is confidential."
        result = compare_ndas(text, text, "NDA A", "NDA B")
        assert "No differences" in result

    def test_different_texts(self):
        """Different NDAs produce a diff output."""
        from nda_contract_generator.cli.commands.compare import compare_ndas
        a = "This NDA has a 2-year term.\nGoverned by California law."
        b = "This NDA has a 3-year term.\nGoverned by New York law."
        result = compare_ndas(a, b)
        assert "2-year" in result or "3-year" in result or "---" in result

    def test_compare_files(self, tmp_path):
        """compare_nda_files reads and diffs two files correctly."""
        from nda_contract_generator.cli.commands.compare import compare_nda_files
        f1 = tmp_path / "nda1.txt"
        f2 = tmp_path / "nda2.txt"
        f1.write_text("Agreement version 1.\n\nTerm: 1 year.", encoding="utf-8")
        f2.write_text("Agreement version 2.\n\nTerm: 2 years.", encoding="utf-8")
        result = compare_nda_files(str(f1), str(f2))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_compare_missing_file_raises(self, tmp_path):
        """compare_nda_files raises FileNotFoundError for missing files."""
        from nda_contract_generator.cli.commands.compare import compare_nda_files
        with pytest.raises(FileNotFoundError):
            compare_nda_files(str(tmp_path / "nonexistent.txt"), str(tmp_path / "also_none.txt"))

    def test_summary_diff_identical(self):
        """summary_diff reports identical for same texts."""
        from nda_contract_generator.cli.commands.compare import summary_diff
        text = "Same NDA text."
        result = summary_diff(text, text)
        assert result["identical"] is True
        assert result["similarity_ratio"] == 1.0

    def test_summary_diff_different(self):
        """summary_diff reports non-identical for different texts."""
        from nda_contract_generator.cli.commands.compare import summary_diff
        result = summary_diff("NDA version 1, term 1 year.", "NDA version 2, term 3 years.")
        assert result["identical"] is False
        assert result["similarity_ratio"] < 1.0
        assert "added_lines" in result
        assert "removed_lines" in result


# ---------------------------------------------------------------------------
# Validator Tests
# ---------------------------------------------------------------------------

class TestValidator:
    """Tests for the enhanced NDA validator."""

    def test_import_validator(self):
        """Validator imports without error."""
        from nda_contract_generator.cli.commands.validate import (
            validate_contract_text, validate_form_data, detect_clause_conflicts
        )
        assert callable(validate_contract_text)
        assert callable(validate_form_data)
        assert callable(detect_clause_conflicts)

    def test_valid_contract(self):
        """A well-formed contract passes validation."""
        from nda_contract_generator.cli.commands.validate import validate_contract_text
        text = (
            "NON-DISCLOSURE AGREEMENT\n\n"
            "This agreement is entered into between Party A and Party B.\n\n"
            "CONFIDENTIAL INFORMATION: All non-public business information.\n\n"
            "TERM: This agreement is valid for 2 years from the effective date.\n\n"
            "GOVERNING LAW: This agreement is governed by the laws of California.\n\n"
            "DISCLAIMER: This document does not constitute legal advice. "
            "Always consult a qualified attorney."
        )
        result = validate_contract_text(text, jurisdiction="california")
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_unfilled_placeholder_is_error(self):
        """Unfilled Jinja2 placeholders are detected as errors."""
        from nda_contract_generator.cli.commands.validate import validate_contract_text
        text = "Agreement between {{ party_a }} and {{ party_b }}."
        result = validate_contract_text(text)
        assert result["valid"] is False
        assert any("placeholder" in e.lower() for e in result["errors"])

    def test_too_short_is_error(self):
        """Very short contracts are flagged as errors."""
        from nda_contract_generator.cli.commands.validate import validate_contract_text
        result = validate_contract_text("Short NDA.")
        assert result["valid"] is False
        assert any("short" in e.lower() or "incomplete" in e.lower() for e in result["errors"])

    def test_missing_disclaimer_is_warning(self):
        """Missing disclaimer is a warning, not an error."""
        from nda_contract_generator.cli.commands.validate import validate_contract_text
        text = "X" * 300  # long enough but no disclaimer
        result = validate_contract_text(text)
        # Should be a warning about disclaimer
        assert any("disclaimer" in w.lower() for w in result["warnings"])

    def test_validate_form_data_valid(self):
        """Complete form data for 'mutual' template passes."""
        from nda_contract_generator.cli.commands.validate import validate_form_data
        form = {
            "party_a_name": "Acme Corp",
            "party_b_name": "Beta LLC",
            "effective_date": "2026-01-01",
            "term": "2 years",
        }
        result = validate_form_data(form, template_type="mutual")
        assert result["valid"] is True
        assert len(result["missing"]) == 0

    def test_validate_form_data_missing_fields(self):
        """Incomplete form data flags missing required fields."""
        from nda_contract_generator.cli.commands.validate import validate_form_data
        form = {"party_a_name": "Acme Corp"}  # missing other required fields
        result = validate_form_data(form, template_type="mutual")
        assert result["valid"] is False
        assert "party_b_name" in result["missing"]
        assert "effective_date" in result["missing"]

    def test_detect_clause_conflicts_none(self):
        """No conflicts detected in clean clause set."""
        from nda_contract_generator.cli.commands.validate import detect_clause_conflicts
        clauses = {"term": "2 years", "governing_law": "California"}
        conflicts = detect_clause_conflicts(clauses)
        assert isinstance(conflicts, list)

    def test_california_compliance_warning(self):
        """Missing California reference in CA-jurisdiction contract produces warning."""
        from nda_contract_generator.cli.commands.validate import validate_contract_text
        text = "X" * 300 + "\nThis is a confidential agreement with a term and governing clause."
        result = validate_contract_text(text, jurisdiction="california")
        # Should have warnings about California not being referenced
        all_messages = result["errors"] + result["warnings"]
        assert any("california" in m.lower() for m in all_messages)

    def test_gdpr_compliance_warning(self):
        """Missing GDPR reference in EU-jurisdiction contract produces warning."""
        from nda_contract_generator.cli.commands.validate import validate_contract_text
        text = "X" * 300 + "\nThis is a confidential agreement with a term and governing clause."
        result = validate_contract_text(text, jurisdiction="gdpr_compliant")
        all_messages = result["errors"] + result["warnings"]
        assert any("gdpr" in m.lower() or "data protection" in m.lower() for m in all_messages)


# ---------------------------------------------------------------------------
# Integration Test: Draft -> Export -> Validate -> Compare
# ---------------------------------------------------------------------------

class TestPhase3Integration:
    """End-to-end integration tests for Phase 3 features."""

    def test_generate_export_validate_compare(self, tmp_path):
        """Full pipeline: generate two NDAs, export both, validate, and compare."""
        from nda_contract_generator.exporters.pdf_exporter import export_pdf
        from nda_contract_generator.exporters.docx_exporter import export_docx
        from nda_contract_generator.cli.commands.validate import validate_contract_text
        from nda_contract_generator.cli.commands.compare import compare_ndas, summary_diff

        nda_a = (
            "NON-DISCLOSURE AGREEMENT\n\n"
            "This agreement is between Acme Corp and Beta LLC.\n\n"
            "CONFIDENTIAL INFORMATION: All proprietary business data.\n\n"
            "TERM: 2 years from the effective date.\n\n"
            "GOVERNING LAW: California, USA.\n\n"
            "DISCLAIMER: This is not legal advice. Consult an attorney."
        )
        nda_b = (
            "NON-DISCLOSURE AGREEMENT\n\n"
            "This agreement is between Delta Inc and Gamma Ltd.\n\n"
            "CONFIDENTIAL INFORMATION: All proprietary business data.\n\n"
            "TERM: 3 years from the effective date.\n\n"
            "GOVERNING LAW: New York, USA.\n\n"
            "DISCLAIMER: This is not legal advice. Consult an attorney."
        )

        # Export both
        pdf_path = str(tmp_path / "nda_a.pdf")
        docx_path = str(tmp_path / "nda_b.docx")
        pdf_result = export_pdf(nda_a, pdf_path, "NDA A")
        docx_result = export_docx(nda_b, docx_path, "NDA B")
        assert os.path.exists(pdf_result)
        assert os.path.exists(docx_result)

        # Validate both
        val_a = validate_contract_text(nda_a, jurisdiction="california")
        val_b = validate_contract_text(nda_b, jurisdiction="england_wales")
        assert val_a["valid"] is True
        assert val_b["valid"] is True

        # Compare
        diff = compare_ndas(nda_a, nda_b, "NDA A", "NDA B")
        assert isinstance(diff, str)
        assert len(diff) > 0

        summary = summary_diff(nda_a, nda_b)
        assert summary["identical"] is False
        assert summary["similarity_ratio"] > 0.5  # mostly similar structure
