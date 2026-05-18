"""tests for resume_builder."""
from unittest.mock import patch
from resume_builder.builder import _fallback_resume, tailor_application, format_markdown

def test_fallback_resume():
    res = _fallback_resume("prof", "job")
    assert res["name"] == "Candidate"
    assert "cover_letter" in res

def test_tailor_application_fallback_on_failure():
    with patch("resume_builder.builder._call_ollama", return_value="invalid json"):
        res = tailor_application("prof", "job")
    assert res["name"] == "Candidate"

def test_format_markdown():
    data = _fallback_resume("prof", "job")
    md = format_markdown(data)
    assert "# Candidate" in md
    assert "# Cover Letter" in md
