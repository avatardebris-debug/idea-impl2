"""Tests for skillify package imports and public API."""
import sys
import pathlib

_ws = pathlib.Path(__file__).resolve().parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))


class TestImports:
    def test_import_skillify(self):
        import skillify
        assert hasattr(skillify, "convert")
        assert hasattr(skillify, "save_skill")
        assert hasattr(skillify, "load_skill")

    def test_import_converter(self):
        from skillify import converter
        assert hasattr(converter, "convert")
        assert hasattr(converter, "save_skill")
        assert hasattr(converter, "load_skill")

    def test_import_cli(self):
        from skillify import cli
        assert hasattr(cli, "main")

    def test_convert_callable(self):
        from skillify import convert
        assert callable(convert)

    def test_save_skill_callable(self):
        from skillify import save_skill
        assert callable(save_skill)

    def test_load_skill_callable(self):
        from skillify import load_skill
        assert callable(load_skill)


class TestPublicAPI:
    def test_convert_signature(self):
        from skillify import convert
        extraction = {"title": "API Test"}
        result = convert(extraction)
        assert isinstance(result, dict)
        assert "skill_id" in result
        assert "name" in result

    def test_convert_with_all_options(self):
        from skillify import convert
        extraction = {
            "title": "Full Test",
            "description": "Full test extraction",
            "format": "steps",
            "parameters": {"type": "object", "properties": {}},
            "steps": [{"title": "A", "description": "B"}],
            "components": [{"name": "C", "description": "D"}],
            "tips": ["tip1"],
            "source": {"model": "test"},
            "tags": ["test"],
        }
        result = convert(extraction, skill_id="full_test")
        assert result["skill_id"] == "full_test"
        assert result["name"] == "Full Test"
        assert result["description"] == "Full test extraction"
        assert result["version"] == "1.0.0"
        assert "test" in result["tags"]
        assert len(result["steps"]) == 1
        assert len(result["components"]) == 1
        assert len(result["tips"]) == 1
