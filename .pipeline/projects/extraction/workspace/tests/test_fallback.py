"""
test_fallback.py — Unit tests for _fallback_extract (rule-based extraction).

Covers: numbered lists, bulleted lists, plain sentences, and empty input.
"""
import pytest
from extraction.extractor import _fallback_extract


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_valid(result: dict) -> None:
    """Assert that result has all required schema keys with correct types."""
    assert isinstance(result["title"], str) and result["title"]
    assert isinstance(result["topic"], str)
    assert result["format"] in ("recipe", "steps", "sop")
    assert isinstance(result["description"], str)
    assert isinstance(result["components"], list)
    assert isinstance(result["steps"], list)
    assert isinstance(result["tips"], list)
    assert isinstance(result["metadata"], dict)
    assert "source_length" in result["metadata"]
    assert "model" in result["metadata"]
    assert "extracted_at" in result["metadata"]


# ---------------------------------------------------------------------------
# Test: numbered list input
# ---------------------------------------------------------------------------

class TestFallbackNumberedList:
    def test_numbered_list_produces_steps(self):
        text = "1. Boil water\n2. Add salt\n3. Cook pasta for 10 minutes"
        result = _fallback_extract(text, "cooking pasta", "recipe")
        _assert_valid(result)
        assert len(result["steps"]) == 3
        assert result["steps"][0]["step_number"] == 1
        assert result["steps"][0]["action"] == "Boil water"
        assert result["steps"][1]["action"] == "Add salt"
        assert result["steps"][2]["action"] == "Cook pasta for 10 minutes"
        assert result["title"] == "cooking pasta"
        assert result["format"] == "recipe"

    def test_numbered_list_with_colon_delimiter(self):
        text = "1: Mix flour\n2: Add eggs\n3: Bake at 350F"
        result = _fallback_extract(text, "baking", "steps")
        _assert_valid(result)
        assert len(result["steps"]) == 3
        assert result["steps"][0]["action"] == "Mix flour"


# ---------------------------------------------------------------------------
# Test: bulleted list input
# ---------------------------------------------------------------------------

class TestFallbackBulletedList:
    def test_bullet_list_dash(self):
        text = "- Step one\n- Step two\n- Step three"
        result = _fallback_extract(text, "task list", "sop")
        _assert_valid(result)
        assert len(result["steps"]) == 3
        assert result["steps"][0]["action"] == "Step one"

    def test_bullet_list_asterisk(self):
        text = "* First item\n* Second item\n* Third item"
        result = _fallback_extract(text, "items", "steps")
        _assert_valid(result)
        assert len(result["steps"]) == 3

    def test_bullet_list_bullet_char(self):
        text = "• Item A\n• Item B\n• Item C"
        result = _fallback_extract(text, "bullets", "steps")
        _assert_valid(result)
        assert len(result["steps"]) == 3


# ---------------------------------------------------------------------------
# Test: plain sentences (no numbering or bullets)
# ---------------------------------------------------------------------------

class TestFallbackPlainSentences:
    def test_plain_sentences_split_into_steps(self):
        text = "First, boil the water. Then, add the pasta. Finally, drain the water."
        result = _fallback_extract(text, "cooking", "steps")
        _assert_valid(result)
        # Should have been split into multiple steps
        assert len(result["steps"]) >= 1
        # Each step should have a step_number starting from 1
        assert result["steps"][0]["step_number"] == 1

    def test_single_sentence(self):
        text = "Mix the ingredients together in a bowl."
        result = _fallback_extract(text, "mixing", "steps")
        _assert_valid(result)
        assert len(result["steps"]) == 1
        assert result["steps"][0]["action"] == "Mix the ingredients together in a bowl."


# ---------------------------------------------------------------------------
# Test: empty / edge-case input
# ---------------------------------------------------------------------------

class TestFallbackEmptyInput:
    def test_empty_string(self):
        result = _fallback_extract("", "topic", "steps")
        _assert_valid(result)
        assert len(result["steps"]) == 0
        assert result["description"] == ""

    def test_whitespace_only(self):
        result = _fallback_extract("   \n  \n  ", "topic", "steps")
        _assert_valid(result)
        assert len(result["steps"]) == 0

    def test_none_like_input(self):
        result = _fallback_extract("   ", "topic", "sop")
        _assert_valid(result)
        assert result["title"] == "topic"


# ---------------------------------------------------------------------------
# Test: metadata correctness
# ---------------------------------------------------------------------------

class TestFallbackMetadata:
    def test_metadata_source_length(self):
        text = "Hello world"
        result = _fallback_extract(text, "test", "steps")
        assert result["metadata"]["source_length"] == len(text)

    def test_metadata_model_is_fallback(self):
        text = "test"
        result = _fallback_extract(text, "test", "steps")
        assert result["metadata"]["model"] == "fallback"

    def test_metadata_has_timestamp(self):
        text = "test"
        result = _fallback_extract(text, "test", "steps")
        assert "extracted_at" in result["metadata"]
        assert len(result["metadata"]["extracted_at"]) > 0
