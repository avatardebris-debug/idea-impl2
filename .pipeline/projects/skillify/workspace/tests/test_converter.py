"""Tests for skillify.converter — core conversion logic."""
import json
import pathlib
import sys
import tempfile
from datetime import datetime

import pytest

# Ensure workspace is on path (same as conftest.py)
_ws = pathlib.Path(__file__).resolve().parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from skillify.converter import convert, save_skill, load_skill, _to_skill_id, _infer_tags


# ── _to_skill_id ───────────────────────────────────────────────────────────

class TestToSkillId:
    def test_simple_title(self):
        assert _to_skill_id("Make Sourdough Bread") == "make_sourdough_bread"

    def test_already_snake_case(self):
        assert _to_skill_id("already_snake_case") == "already_snake_case"

    def test_special_chars(self):
        assert _to_skill_id("Hello, World! 123") == "hello_world_123"

    def test_empty_string(self):
        assert _to_skill_id("") == "unnamed_skill"

    def test_long_title_truncated(self):
        long = "a" * 100
        result = _to_skill_id(long)
        assert len(result) == 60

    def test_leading_trailing_dashes(self):
        assert _to_skill_id("---hello---") == "hello"


# ── _infer_tags ───────────────────────────────────────────────────────────

class TestInferTags:
    def test_steps_format(self):
        extraction = {"format": "steps"}
        tags = _infer_tags(extraction)
        assert "steps" in tags

    def test_components_format(self):
        extraction = {"format": "components"}
        tags = _infer_tags(extraction)
        assert "components" in tags

    def test_custom_tags_override(self):
        extraction = {"format": "steps", "tags": ["cooking", "bread"]}
        tags = _infer_tags(extraction)
        assert "cooking" in tags
        assert "bread" in tags

    def test_topic_keyword_inference(self):
        extraction = {"format": "steps", "topic": "cooking recipes"}
        tags = _infer_tags(extraction)
        assert "cooking" in tags

    def test_no_format_defaults_to_steps(self):
        extraction = {}
        tags = _infer_tags(extraction)
        assert "steps" in tags


# ── convert ───────────────────────────────────────────────────────────────

class TestConvert:
    def _sample_extraction(self):
        return {
            "title": "Make Sourdough Bread",
            "description": "A guide to making sourdough bread",
            "format": "steps",
            "metadata": {
                "model": "gpt-4",
                "extracted_at": "2024-01-01T00:00:00Z",
                "source_length": 1000
            },
            "steps": [
                {"step_number": 1, "action": "Mix", "detail": "Mix flour and water"},
                {"step_number": 2, "action": "Knead", "detail": "Knead the dough"}
            ],
            "components": [
                {"name": "starter", "description": "Sourdough starter"}
            ],
            "tips": ["Use warm water", "Let rise for 2 hours"],
            "tags": ["cooking", "bread"]
        }

    def test_convert_returns_dict(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert isinstance(result, dict)

    def test_convert_has_required_keys(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        required_keys = ["skill_id", "name", "version", "description", "tags",
                         "parameters", "steps", "components", "tips", "source", "created_at"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_convert_skill_id_from_title(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert result["skill_id"] == "make_sourdough_bread"

    def test_convert_name_from_title(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert result["name"] == "Make Sourdough Bread"

    def test_convert_version_default(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert result["version"] == "1.0.0"

    def test_convert_description(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert result["description"] == "A guide to making sourdough bread"

    def test_convert_tags(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert "cooking" in result["tags"]
        assert "bread" in result["tags"]

    def test_convert_parameters(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert "type" in result["parameters"]
        assert "properties" in result["parameters"]
        assert "required" in result["parameters"]
        assert "context" in result["parameters"]["properties"]
        assert "target_output" in result["parameters"]["properties"]

    def test_convert_steps(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert len(result["steps"]) == 2
        assert result["steps"][0]["action"] == "Mix"
        assert result["steps"][1]["action"] == "Knead"
        assert result["steps"][0]["step"] == 1
        assert result["steps"][1]["step"] == 2

    def test_convert_components(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert len(result["components"]) == 1
        assert result["components"][0]["name"] == "starter"

    def test_convert_tips(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert len(result["tips"]) == 2
        assert "Use warm water" in result["tips"]

    def test_convert_source(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        assert result["source"]["model"] == "gpt-4"
        assert result["source"]["extracted_at"] == "2024-01-01T00:00:00Z"
        assert result["source"]["format"] == "steps"
        assert result["source"]["topic"] == ""
        assert result["source"]["source_length"] == 1000

    def test_convert_created_at_is_string_iso(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        # created_at is an ISO string, not a datetime object
        assert isinstance(result["created_at"], str)
        # Should be parseable as ISO datetime
        datetime.fromisoformat(result["created_at"])

    def test_convert_minimal_extraction(self):
        minimal = {"title": "Minimal Skill"}
        result = convert(minimal)
        assert result["skill_id"] == "minimal_skill"
        assert result["name"] == "Minimal Skill"
        assert result["version"] == "1.0.0"
        assert result["description"] == ""
        assert "steps" in result["tags"]
        assert result["parameters"]["type"] == "object"
        assert result["steps"] == []
        assert result["components"] == []
        assert result["tips"] == []
        assert result["source"]["model"] == "unknown"

    def test_convert_with_custom_id(self):
        extraction = self._sample_extraction()
        result = convert(extraction, skill_id="custom_id")
        assert result["skill_id"] == "custom_id"

    def test_convert_json_serializable(self):
        extraction = self._sample_extraction()
        result = convert(extraction)
        # All values should be JSON-serializable (strings, lists, dicts)
        json_str = json.dumps(result)
        assert "make_sourdough_bread" in json_str


# ── save_skill / load_skill ───────────────────────────────────────────────

class TestSaveLoadSkill:
    def test_save_and_load_roundtrip(self):
        extraction = {
            "title": "Test Skill",
            "description": "A test",
            "tags": ["test"],
        }
        skill = convert(extraction)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "test_skill.json"
            save_skill(skill, path)
            assert path.exists()

            loaded = load_skill(path)
            assert loaded["skill_id"] == skill["skill_id"]
            assert loaded["name"] == skill["name"]
            assert loaded["description"] == skill["description"]
            assert loaded["tags"] == skill["tags"]

    def test_save_creates_parent_dirs(self):
        extraction = {"title": "Nested Skill"}
        skill = convert(extraction)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "a" / "b" / "c" / "skill.json"
            save_skill(skill, path)
            assert path.exists()

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            load_skill(pathlib.Path("/nonexistent/path/skill.json"))

    def test_save_writes_valid_json(self):
        extraction = {"title": "JSON Check"}
        skill = convert(extraction)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "skill.json"
            save_skill(skill, path)
            with open(path) as f:
                data = json.load(f)
            assert data["skill_id"] == "json_check"
