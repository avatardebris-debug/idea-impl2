"""tests for contract_extractor."""
from unittest.mock import patch
from contract_extractor.extractor import _fallback_extract, extract_clauses, format_markdown

_TEXT = "This agreement is confidential. Liability is strictly limited. Termination requires 30 days notice."

def test_fallback_extract():
    res = _fallback_extract(_TEXT)
    types = [c["type"] for c in res["clauses"]]
    assert "Termination" in types
    assert "Confidentiality" in types
    assert "Liability" in types

def test_extract_clauses_fallback_on_failure():
    with patch("contract_extractor.extractor._call_ollama", return_value="invalid json"):
        res = extract_clauses(_TEXT)
    assert len(res["clauses"]) == 3

def test_format_markdown():
    data = _fallback_extract(_TEXT)
    md = format_markdown(data)
    assert "# 📜 Contract Analysis" in md
    assert "Termination" in md
