"""tests for extraction, skillify, and skill_ninja — all offline."""
from __future__ import annotations
import json
import pathlib
import sys
from unittest.mock import patch

# Add all three workspace paths
_base = pathlib.Path(__file__).parent
for pkg in ["extraction", "skillify", "skill_ninja"]:
    ws = _base.parent.parent.parent / pkg / "workspace"
    if ws.exists():
        sys.path.insert(0, str(ws))

import pytest


# ─────────────────────────────────────────────
# EXTRACTION tests
# ─────────────────────────────────────────────

_HOWTO_TEXT = """
How to make sourdough bread.
First, mix 500g flour with 375ml water and 100g active starter.
Second, let it rest for 30 minutes (autolyse).
Third, add 10g salt, fold the dough 4 times over 2 hours.
Fourth, shape the dough and place in a proofing basket.
Fifth, refrigerate overnight for 12-16 hours.
Finally, bake at 230°C for 20 minutes covered, then 25 minutes uncovered.
"""


class TestExtractor:
    def test_fallback_extracts_steps(self):
        from extraction.extractor import _fallback_extract
        result = _fallback_extract(_HOWTO_TEXT, "sourdough", "recipe")
        assert len(result["steps"]) > 0

    def test_fallback_schema_keys(self):
        from extraction.extractor import _fallback_extract
        result = _fallback_extract(_HOWTO_TEXT, "sourdough", "steps")
        required = {"title","topic","format","description","components","steps","tips","metadata"}
        assert required.issubset(set(result.keys()))

    def test_fallback_step_schema(self):
        from extraction.extractor import _fallback_extract
        result = _fallback_extract(_HOWTO_TEXT, "bread", "steps")
        for step in result["steps"]:
            assert "step_number" in step
            assert "action" in step
            assert "detail" in step

    def test_extract_uses_fallback_when_llm_fails(self):
        from extraction.extractor import extract
        with patch("extraction.extractor._call_ollama", return_value="not json at all"):
            result = extract(_HOWTO_TEXT, topic="sourdough", fmt="recipe")
        assert len(result["steps"]) > 0

    def test_extract_empty_text(self):
        from extraction.extractor import extract
        with patch("extraction.extractor._call_ollama", return_value=""):
            result = extract("", topic="test", fmt="steps")
        assert isinstance(result, dict)

    def test_extract_step_numbers_sequential(self):
        from extraction.extractor import extract
        with patch("extraction.extractor._call_ollama", return_value=""):
            result = extract(_HOWTO_TEXT, fmt="steps")
        numbers = [s["step_number"] for s in result["steps"]]
        assert numbers == list(range(1, len(numbers)+1))

    def test_metadata_present(self):
        from extraction.extractor import extract
        with patch("extraction.extractor._call_ollama", return_value=""):
            result = extract(_HOWTO_TEXT, fmt="steps", model="test-model")
        assert "metadata" in result
        assert "extracted_at" in result["metadata"]

    def test_parse_json_from_response(self):
        from extraction.extractor import _parse_json_from_response
        text = 'Some preamble {"key": "value", "num": 42} trailing'
        assert _parse_json_from_response(text) == {"key": "value", "num": 42}

    def test_parse_json_invalid_returns_empty(self):
        from extraction.extractor import _parse_json_from_response
        assert _parse_json_from_response("no json here") == {}


# ─────────────────────────────────────────────
# SKILLIFY tests
# ─────────────────────────────────────────────

@pytest.fixture
def sample_extraction():
    return {
        "title": "Make Sourdough Bread",
        "topic": "sourdough bread baking",
        "format": "recipe",
        "description": "Classic sourdough loaf from starter to bake.",
        "components": [
            {"name": "flour", "quantity": "500", "unit": "g", "notes": "bread flour"},
            {"name": "water", "quantity": "375", "unit": "ml", "notes": "room temp"},
        ],
        "steps": [
            {"step_number": 1, "action": "Mix ingredients", "detail": "Combine flour, water, starter",
             "duration": "5 min", "tools": ["bowl"], "warnings": []},
            {"step_number": 2, "action": "Autolyse", "detail": "Rest 30 minutes",
             "duration": "30 min", "tools": [], "warnings": []},
        ],
        "tips": ["Use a dutch oven for better crust"],
        "metadata": {"model": "qwen3:6b", "extracted_at": "2024-01-01T00:00:00Z", "source_length": 500},
    }


class TestSkillify:
    def test_convert_returns_skill_dict(self, sample_extraction):
        from skillify.converter import convert
        skill = convert(sample_extraction)
        assert "skill_id" in skill
        assert "steps" in skill
        assert "parameters" in skill

    def test_skill_id_generated_from_title(self, sample_extraction):
        from skillify.converter import convert
        skill = convert(sample_extraction)
        assert "sourdough" in skill["skill_id"] or "make" in skill["skill_id"]

    def test_skill_id_override(self, sample_extraction):
        from skillify.converter import convert
        skill = convert(sample_extraction, skill_id="my_custom_id")
        assert skill["skill_id"] == "my_custom_id"

    def test_steps_count_preserved(self, sample_extraction):
        from skillify.converter import convert
        skill = convert(sample_extraction)
        assert len(skill["steps"]) == 2

    def test_step_schema(self, sample_extraction):
        from skillify.converter import convert
        skill = convert(sample_extraction)
        for step in skill["steps"]:
            assert "step" in step
            assert "action" in step
            assert "detail" in step

    def test_components_preserved(self, sample_extraction):
        from skillify.converter import convert
        skill = convert(sample_extraction)
        assert len(skill["components"]) == 2

    def test_tags_include_format(self, sample_extraction):
        from skillify.converter import convert
        skill = convert(sample_extraction)
        assert "recipe" in skill["tags"] or "cooking" in skill["tags"]

    def test_source_metadata_present(self, sample_extraction):
        from skillify.converter import convert
        skill = convert(sample_extraction)
        assert "source" in skill
        assert "extracted_at" in skill["source"]

    def test_save_and_load(self, sample_extraction, tmp_path):
        from skillify.converter import convert, save_skill, load_skill
        skill = convert(sample_extraction)
        out = tmp_path / "skill.json"
        save_skill(skill, out)
        loaded = load_skill(out)
        assert loaded["skill_id"] == skill["skill_id"]
        assert len(loaded["steps"]) == len(skill["steps"])

    def test_to_skill_id(self):
        from skillify.converter import _to_skill_id
        assert _to_skill_id("Make Sourdough Bread!") == "make_sourdough_bread"
        assert _to_skill_id("") == "unnamed_skill"


# ─────────────────────────────────────────────
# SKILL NINJA dispatcher tests
# ─────────────────────────────────────────────

@pytest.fixture
def skill_file(tmp_path):
    skill = {
        "skill_id": "test_skill",
        "name": "Test Skill",
        "version": "1.0.0",
        "description": "A test skill.",
        "tags": ["test"],
        "parameters": {},
        "steps": [
            {"step": 1, "action": "Do thing one", "detail": "Details for step one",
             "duration": "1 min", "tools": [], "warnings": []},
            {"step": 2, "action": "Do thing two", "detail": "Details for step two",
             "duration": "", "tools": ["hammer"], "warnings": ["be careful"]},
        ],
        "components": [],
        "tips": ["Tip one"],
        "source": {"format": "steps", "extracted_at": "2024-01-01T00:00:00Z"},
        "created_at": "2024-01-01T00:00:00Z",
    }
    path = tmp_path / "test_skill.json"
    path.write_text(json.dumps(skill), encoding="utf-8")
    return path


class TestDispatcher:
    def test_load_skill(self, skill_file):
        from skill_ninja.dispatcher import load_skill
        skill = load_skill(skill_file)
        assert skill["skill_id"] == "test_skill"
        assert len(skill["steps"]) == 2

    def test_list_skills_finds_file(self, skill_file):
        from skill_ninja.dispatcher import list_skills
        skills = list_skills(skill_file.parent)
        assert any(s["skill_id"] == "test_skill" for s in skills)

    def test_list_skills_empty_dir(self, tmp_path):
        from skill_ninja.dispatcher import list_skills
        skills = list_skills(tmp_path)
        assert skills == []

    def test_format_summary(self, skill_file):
        from skill_ninja.dispatcher import load_skill, format_skill_summary
        skill = load_skill(skill_file)
        summary = format_skill_summary(skill)
        assert "test_skill" in summary
        assert "Test Skill" in summary
        assert "2 steps" in summary

    def test_list_skills_path_added(self, skill_file):
        from skill_ninja.dispatcher import list_skills
        skills = list_skills(skill_file.parent)
        assert "_path" in skills[0]
