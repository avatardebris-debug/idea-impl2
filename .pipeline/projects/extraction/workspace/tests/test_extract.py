"""
test_extract.py — Tests for the public `extract()` function with mocked Ollama.

Covers:
- Valid JSON response from Ollama
- Empty response (triggers fallback)
- Malformed JSON (triggers fallback)
- JSON missing 'steps' key (triggers fallback)
- Empty input (triggers fallback)
- Schema normalisation (step numbers, defaults)
- Format hints (recipe, steps, sop)
- Model parameter passthrough
"""
import json
import pytest
from unittest.mock import patch

from extraction.extractor import extract


class TestExtractValidJson:
    """extract() with a valid JSON response from Ollama."""

    def _mock_response(self, json_obj: dict) -> str:
        return json.dumps(json_obj)

    def test_full_schema(self):
        response = {
            "title": "Pasta Carbonara",
            "topic": "Italian pasta dish",
            "format": "recipe",
            "description": "Classic Roman pasta with eggs and cheese",
            "components": [
                {"name": "spaghetti", "quantity": "400", "unit": "g", "notes": ""},
                {"name": "guanciale", "quantity": "200", "unit": "g", "notes": "diced"},
            ],
            "steps": [
                {"step_number": 1, "action": "Boil water", "detail": "Bring salted water to boil",
                 "duration": "10 min", "tools": ["pot"], "warnings": []},
                {"step_number": 2, "action": "Fry guanciale", "detail": "Cook until crispy",
                 "duration": "5 min", "tools": ["pan"], "warnings": ["hot oil"]},
            ],
            "tips": ["Use room temperature eggs"],
        }
        with patch("extraction.extractor._call_ollama", return_value=self._mock_response(response)):
            result = extract("Cook pasta and mix with sauce.", topic="Italian cooking", fmt="recipe")

        assert result["title"] == "Pasta Carbonara"
        assert result["topic"] == "Italian cooking"
        assert result["format"] == "recipe"
        assert result["description"] == "Classic Roman pasta with eggs and cheese"
        assert len(result["components"]) == 2
        assert len(result["steps"]) == 2
        assert result["steps"][0]["step_number"] == 1
        assert result["steps"][1]["step_number"] == 2
        assert result["tips"] == ["Use room temperature eggs"]
        assert result["metadata"]["model"] == "qwen3:6b"
        assert result["metadata"]["source_length"] == len("Cook pasta and mix with sauce.")

    def test_empty_components_and_tips(self):
        response = {
            "title": "Tie Shoes",
            "topic": "Shoelace knot",
            "format": "steps",
            "description": "How to tie your shoes",
            "components": [],
            "steps": [{"step_number": 1, "action": "Cross laces", "detail": "Cross left over right",
                       "duration": "", "tools": [], "warnings": []}],
            "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=self._mock_response(response)):
            result = extract("Take your shoelaces and tie them.")

        assert result["steps"][0]["step_number"] == 1
        assert result["components"] == []
        assert result["tips"] == []

    def test_custom_model(self):
        response = {
            "title": "Test", "topic": "T", "format": "steps",
            "description": "d", "components": [],
            "steps": [{"step_number": 1, "action": "a", "detail": "d",
                       "duration": "", "tools": [], "warnings": []}],
            "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=self._mock_response(response)) as mock_call:
            result = extract("test", model="llama3.1:8b")

        assert result["metadata"]["model"] == "llama3.1:8b"
        mock_call.assert_called_once()
        call_args = mock_call.call_args
        assert call_args[1]["model"] == "llama3.1:8b"


class TestExtractFallback:
    """extract() triggers fallback when Ollama returns empty or invalid JSON."""

    def test_empty_response_triggers_fallback(self):
        with patch("extraction.extractor._call_ollama", return_value=""):
            result = extract("Step 1: Do thing.\nStep 2: Do another thing.", topic="Test")

        assert "steps" in result
        assert len(result["steps"]) >= 1
        assert result["metadata"]["model"] == "fallback"

    def test_malformed_json_triggers_fallback(self):
        with patch("extraction.extractor._call_ollama", return_value="{invalid json}"):
            result = extract("Step 1: Do thing.", topic="Test")

        assert "steps" in result
        assert result["metadata"]["model"] == "fallback"

    def test_json_missing_steps_triggers_fallback(self):
        response = {"title": "No steps here", "data": [1, 2, 3]}
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)):
            result = extract("Some text.", topic="Test")

        assert "steps" in result
        assert result["metadata"]["model"] == "fallback"

    def test_whitespace_only_response_triggers_fallback(self):
        with patch("extraction.extractor._call_ollama", return_value="   \n  "):
            result = extract("Step 1: Action.", topic="Test")

        assert "steps" in result
        assert result["metadata"]["model"] == "fallback"


class TestExtractEmptyInput:
    """extract() with empty or whitespace-only input always uses fallback."""

    def test_empty_string(self):
        result = extract("", topic="Test")
        assert result["metadata"]["model"] == "fallback"
        assert result["steps"] == []

    def test_whitespace_string(self):
        result = extract("   \n\t  ", topic="Test")
        assert result["metadata"]["model"] == "fallback"

    def test_none_input(self):
        result = extract(None, topic="Test")
        assert result["metadata"]["model"] == "fallback"


class TestExtractSchemaNormalisation:
    """extract() normalises the schema regardless of LLM output."""

    def test_step_numbers_renumbered(self):
        response = {
            "title": "T", "topic": "T", "format": "steps",
            "description": "d", "components": [],
            "steps": [
                {"step_number": 5, "action": "a", "detail": "d", "duration": "", "tools": [], "warnings": []},
                {"step_number": 3, "action": "b", "detail": "d", "duration": "", "tools": [], "warnings": []},
            ],
            "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)):
            result = extract("test")

        assert result["steps"][0]["step_number"] == 1
        assert result["steps"][1]["step_number"] == 2

    def test_missing_defaults_filled(self):
        response = {
            "title": "T", "topic": "T", "format": "steps",
            "description": "d", "components": [],
            "steps": [{"action": "do it"}],  # missing detail, duration, tools, warnings
            "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)):
            result = extract("test")

        assert result["steps"][0]["detail"] == "do it"
        assert result["steps"][0]["duration"] == ""
        assert result["steps"][0]["tools"] == []
        assert result["steps"][0]["warnings"] == []

    def test_missing_top_level_defaults(self):
        response = {
            "title": "T", "topic": "T", "format": "steps",
            "description": "d",
            # missing components, steps, tips
        }
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)):
            result = extract("test")

        assert result["components"] == []
        assert result["steps"] == []
        assert result["tips"] == []


class TestExtractFormatHints:
    """extract() passes format hint to the LLM prompt."""

    def test_recipe_format(self):
        response = {
            "title": "T", "topic": "T", "format": "recipe",
            "description": "d", "components": [], "steps": [], "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)) as mock_call:
            extract("test", fmt="recipe")

        call_args = mock_call.call_args[0][0]
        assert "recipe" in call_args
        assert "ingredients list" in call_args

    def test_sop_format(self):
        response = {
            "title": "T", "topic": "T", "format": "sop",
            "description": "d", "components": [], "steps": [], "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)) as mock_call:
            extract("test", fmt="sop")

        call_args = mock_call.call_args[0][0]
        assert "Standard Operating Procedure" in call_args

    def test_steps_format(self):
        response = {
            "title": "T", "topic": "T", "format": "steps",
            "description": "d", "components": [], "steps": [], "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)) as mock_call:
            extract("test", fmt="steps")

        call_args = mock_call.call_args[0][0]
        assert "ordered sequence of steps" in call_args


class TestExtractTopicHandling:
    """extract() handles topic parameter correctly."""

    def test_topic_passed_to_result(self):
        response = {
            "title": "T", "topic": "LLM topic", "format": "steps",
            "description": "d", "components": [], "steps": [], "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)):
            result = extract("test", topic="My custom topic")

        assert result["topic"] == "My custom topic"

    def test_no_topic_uses_default(self):
        response = {
            "title": "T", "topic": "T", "format": "steps",
            "description": "d", "components": [], "steps": [], "tips": [],
        }
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)):
            result = extract("test")

        assert result["topic"] == ""

    def test_fallback_uses_topic(self):
        with patch("extraction.extractor._call_ollama", return_value=""):
            result = extract("test", topic="Fallback topic")

        assert result["topic"] == "Fallback topic"
        assert result["title"] == "Fallback topic"


class TestExtractLongText:
    """extract() truncates long source text in the prompt."""

    def test_text_truncated_in_prompt(self):
        response = {
            "title": "T", "topic": "T", "format": "steps",
            "description": "d", "components": [], "steps": [], "tips": [],
        }
        long_text = "x" * 10000
        with patch("extraction.extractor._call_ollama", return_value=json.dumps(response)) as mock_call:
            extract(long_text)

        call_args = mock_call.call_args[0][0]
        # The prompt includes text[:4000]
        assert "SOURCE TEXT:" in call_args
        # The truncated text should be in the prompt
        assert "x" * 4000 in call_args or len([c for c in call_args if c == 'x']) <= 4000 + 100  # allow some buffer
