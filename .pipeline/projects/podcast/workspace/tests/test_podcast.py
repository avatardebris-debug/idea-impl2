"""tests for podcast — all offline, no LLM/audio calls."""
from __future__ import annotations
import json
import sys
import pathlib
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest

_TRANSCRIPT = """
Welcome to the show. Today we're discussing how to build a business.
The first key insight is that consistency beats intensity every single time.
You should show up every day, even when results aren't visible yet.
Successful entrepreneurs focus on systems, not goals. Goals are results you want.
Systems are the processes that lead to those results.
The second lesson is that your network determines your net worth.
Building relationships before you need them is the most powerful strategy.
Always provide value first without expecting anything in return.
Time management is the third pillar. You must protect your time ruthlessly.
Block your calendar for deep work. Say no to low-value meetings.
The fourth insight is that feedback is a gift. Seek criticism actively.
Your customers' complaints are your product roadmap. Listen carefully.
Finally, cash flow is more important than profit in early stages.
Many profitable businesses have failed due to cash flow problems.
Monitor your runway. Always know how many months of cash you have.
"""


class TestExtractor:
    def test_fallback_extracts_n_lessons(self):
        from podcast.extractor import _fallback_extract_lessons
        lessons = _fallback_extract_lessons(_TRANSCRIPT, 5)
        assert len(lessons) == 5

    def test_fallback_lesson_schema(self):
        from podcast.extractor import _fallback_extract_lessons
        lessons = _fallback_extract_lessons(_TRANSCRIPT, 3)
        for l in lessons:
            assert "number" in l
            assert "title" in l
            assert "detail" in l
            assert "quote" in l

    def test_fallback_sequential_numbers(self):
        from podcast.extractor import _fallback_extract_lessons
        lessons = _fallback_extract_lessons(_TRANSCRIPT, 4)
        assert [l["number"] for l in lessons] == list(range(1, 5))

    def test_extract_lessons_uses_fallback_on_llm_failure(self):
        from podcast.extractor import extract_lessons
        with patch("podcast.extractor._call_ollama", return_value="not valid json"):
            result = extract_lessons(_TRANSCRIPT, "Test Episode", n_lessons=5)
        assert len(result["lessons"]) == 5

    def test_extract_lessons_result_schema(self):
        from podcast.extractor import extract_lessons
        with patch("podcast.extractor._call_ollama", return_value=""):
            result = extract_lessons(_TRANSCRIPT, "Test Ep", n_lessons=3)
        assert "episode" in result
        assert "lessons" in result
        assert "summary" in result
        assert "metadata" in result

    def test_extract_lessons_metadata(self):
        from podcast.extractor import extract_lessons
        with patch("podcast.extractor._call_ollama", return_value=""):
            result = extract_lessons(_TRANSCRIPT, "Ep1", n_lessons=5, model="test-model")
        assert result["metadata"]["model"] == "test-model"
        assert result["metadata"]["transcript_length"] == len(_TRANSCRIPT)

    def test_llm_json_parsed_when_valid(self):
        from podcast.extractor import extract_lessons
        mock_lessons = json.dumps([
            {"number": i, "title": f"Lesson {i}", "detail": f"Detail {i}", "quote": f"Q{i}"}
            for i in range(1, 4)
        ])
        with patch("podcast.extractor._call_ollama", return_value=mock_lessons):
            result = extract_lessons(_TRANSCRIPT, "Ep", n_lessons=3)
        assert result["lessons"][0]["title"] == "Lesson 1"

    def test_parse_lessons_json_handles_markdown_fence(self):
        from podcast.extractor import _parse_lessons_json
        text = '```json\n[{"number":1,"title":"T","detail":"D","quote":"Q"}]\n```'
        items = _parse_lessons_json(text, 5)
        assert len(items) == 1

    def test_extract_empty_transcript(self):
        from podcast.extractor import extract_lessons
        with patch("podcast.extractor._call_ollama", return_value=""):
            result = extract_lessons("", "Empty", n_lessons=3)
        assert isinstance(result, dict)
        assert "lessons" in result


class TestFormatter:
    @pytest.fixture
    def sample_result(self):
        return {
            "episode": "Great Business Podcast",
            "summary": "This episode covers building a sustainable business.",
            "lessons": [
                {"number": 1, "title": "Consistency beats intensity",
                 "detail": "Show up every day.", "quote": "Consistency is key."},
                {"number": 2, "title": "Systems over goals",
                 "detail": "Build processes not just targets.", "quote": ""},
            ],
            "metadata": {"extracted_at": "2024-01-01T00:00:00Z", "model": "qwen3:6b",
                         "n_lessons": 2, "transcript_length": 500, "custom_prompt": ""},
        }

    def test_markdown_contains_episode_name(self, sample_result):
        from podcast.formatter import to_markdown
        md = to_markdown(sample_result)
        assert "Great Business Podcast" in md

    def test_markdown_contains_all_lessons(self, sample_result):
        from podcast.formatter import to_markdown
        md = to_markdown(sample_result)
        assert "Consistency beats intensity" in md
        assert "Systems over goals" in md

    def test_markdown_contains_summary(self, sample_result):
        from podcast.formatter import to_markdown
        md = to_markdown(sample_result)
        assert "sustainable business" in md

    def test_markdown_includes_quotes_by_default(self, sample_result):
        from podcast.formatter import to_markdown
        md = to_markdown(sample_result, include_quotes=True)
        assert "Consistency is key" in md

    def test_markdown_excludes_quotes_when_flag_set(self, sample_result):
        from podcast.formatter import to_markdown
        md = to_markdown(sample_result, include_quotes=False)
        assert "Consistency is key" not in md

    def test_plain_numbered_list(self, sample_result):
        from podcast.formatter import to_plain
        txt = to_plain(sample_result)
        assert "1." in txt
        assert "2." in txt
        assert "Consistency beats intensity" in txt

    def test_plain_contains_episode(self, sample_result):
        from podcast.formatter import to_plain
        txt = to_plain(sample_result)
        assert "Great Business Podcast" in txt
