"""tests for startup_compliance."""
from unittest.mock import patch
from startup_compliance.scanner import _fallback_checklist, generate_checklist, format_markdown

def test_fallback_checklist():
    res = _fallback_checklist("Acme", "desc")
    assert res["company_name"] == "Acme"
    assert len(res["checklist"]) > 0

def test_generate_checklist_fallback_on_failure():
    with patch("startup_compliance.scanner._call_ollama", return_value="invalid json"):
        res = generate_checklist("Test", "test")
    assert res["company_name"] == "Test"

def test_format_markdown():
    data = _fallback_checklist("Acme", "desc")
    md = format_markdown(data)
    assert "# 🛡️ Compliance Checklist: Acme" in md
    assert "- [ ] **Enforce MFA" in md
