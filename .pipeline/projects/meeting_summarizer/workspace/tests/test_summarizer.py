"""tests for meeting_summarizer."""
from unittest.mock import patch
from meeting_summarizer.summarizer import _fallback_summary, analyze_transcript, format_markdown

def test_fallback_summary():
    res = _fallback_summary("test transcript")
    assert "Fallback" in res["title"]
    assert len(res["action_items"]) > 0

def test_analyze_transcript_fallback_on_failure():
    with patch("meeting_summarizer.summarizer._call_ollama", return_value="invalid json"):
        res = analyze_transcript("Hello team")
    assert "Fallback" in res["title"]

def test_format_markdown():
    data = _fallback_summary("text")
    md = format_markdown(data)
    assert "# 📝 Meeting Summary" in md
    assert "| Task | Assignee | Deadline |" in md
