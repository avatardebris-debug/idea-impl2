"""Tests for meeting_summarizer.summarizer — transcript analysis engine."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure package importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meeting_summarizer.summarizer import (
    _fallback_summary,
    _parse_json,
    analyze_transcript,
    format_markdown,
)


SAMPLE_TRANSCRIPT = """
[09:00] Alice: Good morning everyone. Let's kick off our sprint planning.
[09:01] Bob: Sure. I'll take the API redesign ticket — I can finish by Wednesday.
[09:02] Carol: I'll handle the database migrations. Target Friday.
[09:05] Alice: Great. We also decided to drop the old authentication module.
[09:06] Bob: Agreed. And we should add monitoring dashboards by next sprint.
[09:10] Alice: Okay. Action items summary:
         - Bob: complete API redesign by Wednesday
         - Carol: finish database migrations by Friday
         - Everyone: review new monitoring proposal by end of week
[09:12] Alice: Meeting adjourned.
"""

SHORT_TRANSCRIPT = "Quick sync. No decisions. Bob to send report by Monday."

EMPTY_TRANSCRIPT = ""


# ---------------------------------------------------------------------------
# _parse_json
# ---------------------------------------------------------------------------

class TestParseJson:
    def test_parses_valid_json_object(self):
        text = '{"title": "Sprint Planning", "date": "2024-03-15"}'
        result = _parse_json(text)
        assert result["title"] == "Sprint Planning"

    def test_returns_empty_dict_on_bad_input(self):
        result = _parse_json("not json")
        assert result == {}

    def test_returns_empty_dict_on_empty_string(self):
        assert _parse_json("") == {}

    def test_ignores_prefix_garbage(self):
        text = "Here is the result: {\"key\": \"value\"}"
        result = _parse_json(text)
        assert result["key"] == "value"

    def test_handles_nested_structures(self):
        text = '{"action_items": [{"task": "Send report", "assignee": "Bob"}]}'
        result = _parse_json(text)
        assert result["action_items"][0]["assignee"] == "Bob"


# ---------------------------------------------------------------------------
# _fallback_summary
# ---------------------------------------------------------------------------

class TestFallbackSummary:
    def test_returns_dict(self):
        result = _fallback_summary(SAMPLE_TRANSCRIPT)
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = _fallback_summary(SAMPLE_TRANSCRIPT)
        for key in ("title", "date", "executive_summary", "key_topics",
                    "action_items", "decisions", "metadata"):
            assert key in result

    def test_action_items_is_list(self):
        result = _fallback_summary(SAMPLE_TRANSCRIPT)
        assert isinstance(result["action_items"], list)
        assert len(result["action_items"]) > 0

    def test_metadata_has_model_fallback(self):
        result = _fallback_summary(SAMPLE_TRANSCRIPT)
        assert result["metadata"]["model"] == "fallback"

    def test_metadata_includes_text_length(self):
        result = _fallback_summary(SAMPLE_TRANSCRIPT)
        assert result["metadata"]["text_length"] == len(SAMPLE_TRANSCRIPT)

    def test_empty_transcript_doesnt_crash(self):
        result = _fallback_summary("")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# analyze_transcript
# ---------------------------------------------------------------------------

class TestAnalyzeTranscript:
    def test_uses_fallback_when_llm_returns_empty(self):
        with patch("meeting_summarizer.summarizer._call_ollama", return_value=""):
            result = analyze_transcript(SAMPLE_TRANSCRIPT)
        assert result["metadata"]["model"] == "fallback"

    def test_uses_fallback_when_llm_returns_bad_json(self):
        with patch("meeting_summarizer.summarizer._call_ollama", return_value="Sure! Here's the summary."):
            result = analyze_transcript(SAMPLE_TRANSCRIPT)
        assert "title" in result

    def test_uses_fallback_when_action_items_missing(self):
        """If JSON is valid but missing action_items, fallback is used."""
        incomplete = json.dumps({"title": "Meeting", "date": "2024-01-01"})
        with patch("meeting_summarizer.summarizer._call_ollama", return_value=incomplete):
            result = analyze_transcript(SAMPLE_TRANSCRIPT)
        assert result["metadata"]["model"] == "fallback"

    def test_uses_llm_result_when_valid(self):
        good_response = json.dumps({
            "title": "Sprint Planning",
            "date": "2024-03-15",
            "executive_summary": "Team planned the next sprint.",
            "key_topics": ["API redesign", "Database migrations"],
            "action_items": [
                {"task": "API redesign", "assignee": "Bob", "deadline": "Wednesday"},
                {"task": "DB migrations", "assignee": "Carol", "deadline": "Friday"},
            ],
            "decisions": ["Drop old authentication module"],
        })
        with patch("meeting_summarizer.summarizer._call_ollama", return_value=good_response):
            result = analyze_transcript(SAMPLE_TRANSCRIPT)
        assert result["title"] == "Sprint Planning"
        assert len(result["action_items"]) == 2
        assert result["decisions"][0] == "Drop old authentication module"

    def test_adds_metadata_on_success(self):
        good_response = json.dumps({
            "title": "Sync",
            "date": "2024-01-01",
            "executive_summary": "Quick sync.",
            "key_topics": ["Status"],
            "action_items": [{"task": "Send report", "assignee": "Bob", "deadline": "Monday"}],
            "decisions": [],
        })
        with patch("meeting_summarizer.summarizer._call_ollama", return_value=good_response):
            result = analyze_transcript(SHORT_TRANSCRIPT)
        assert "metadata" in result
        assert "generated_at" in result["metadata"]
        assert result["metadata"]["text_length"] == len(SHORT_TRANSCRIPT)

    def test_empty_transcript_doesnt_crash(self):
        with patch("meeting_summarizer.summarizer._call_ollama", return_value=""):
            result = analyze_transcript(EMPTY_TRANSCRIPT)
        assert isinstance(result, dict)

    def test_long_transcript_truncated_in_prompt(self):
        """LLM prompt should cap at 16000 chars of transcript."""
        long_transcript = "Speaker: " + "word " * 5000  # >16k chars
        captured = []
        def fake_call(prompt, **kwargs):
            captured.append(prompt)
            return ""
        with patch("meeting_summarizer.summarizer._call_ollama", side_effect=fake_call):
            analyze_transcript(long_transcript)
        assert len(captured) == 1
        # The slice [:16000] means transcript chars in prompt <= 16000
        assert captured[0].count("word") <= 3200  # 16000/5 chars per "word "

    def test_model_param_passed_through(self):
        """Custom model name should be forwarded to _call_ollama."""
        calls = []
        def fake_call(prompt, model="qwen3:6b", **kwargs):
            calls.append(model)
            return ""
        with patch("meeting_summarizer.summarizer._call_ollama", side_effect=fake_call):
            analyze_transcript(SHORT_TRANSCRIPT, model="llama3:8b")
        assert calls[0] == "llama3:8b"


# ---------------------------------------------------------------------------
# format_markdown
# ---------------------------------------------------------------------------

class TestFormatMarkdown:
    def setup_method(self):
        self.data = {
            "title": "Sprint Planning",
            "date": "2024-03-15",
            "executive_summary": "Team planned the sprint.",
            "key_topics": ["API redesign", "DB migrations"],
            "action_items": [
                {"task": "API redesign", "assignee": "Bob", "deadline": "Wednesday"},
                {"task": "DB migrations", "assignee": "Carol", "deadline": "Friday"},
            ],
            "decisions": ["Drop old auth module"],
        }

    def test_returns_string(self):
        assert isinstance(format_markdown(self.data), str)

    def test_contains_title(self):
        md = format_markdown(self.data)
        assert "Sprint Planning" in md

    def test_contains_date(self):
        md = format_markdown(self.data)
        assert "2024-03-15" in md

    def test_contains_executive_summary(self):
        md = format_markdown(self.data)
        assert "Team planned the sprint." in md

    def test_contains_action_items(self):
        md = format_markdown(self.data)
        assert "API redesign" in md
        assert "Bob" in md
        assert "Wednesday" in md

    def test_contains_decisions(self):
        md = format_markdown(self.data)
        assert "Drop old auth module" in md

    def test_contains_key_topics(self):
        md = format_markdown(self.data)
        assert "DB migrations" in md

    def test_action_items_in_table_format(self):
        """Action items should be rendered as a markdown table."""
        md = format_markdown(self.data)
        assert "| Task" in md or "|Task" in md or "Task |" in md

    def test_empty_data_doesnt_crash(self):
        md = format_markdown({})
        assert isinstance(md, str)

    def test_missing_action_items_doesnt_crash(self):
        data = {**self.data, "action_items": []}
        md = format_markdown(data)
        assert isinstance(md, str)

    def test_multiple_action_items_all_rendered(self):
        md = format_markdown(self.data)
        assert "Carol" in md
        assert "Friday" in md
