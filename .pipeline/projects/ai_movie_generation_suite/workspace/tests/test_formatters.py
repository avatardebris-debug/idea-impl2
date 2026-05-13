"""Tests for formatters."""

import json
import tempfile
from pathlib import Path

import pytest
from ai_movie_gen_suite.formatters.fdx_formatter import FDXFormatter
from ai_movie_gen_suite.formatters.json_formatter import JSONFormatter
from ai_movie_gen_suite.formatters.yaml_formatter import YAMLFormatter
from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    Script,
    SceneDescriptionCollection,
    Beat,
    BeatPhase,
    Character,
    CharacterRole,
    Scene,
    SceneDescription,
    DialogueLine,
)


class TestJSONFormatter:
    def test_save_json(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        character_registry.add_character(Character(name="Hero", role=CharacterRole.PROTAGONIST))
        scene_descriptions = SceneDescriptionCollection()

        formatter = JSONFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)
        assert Path(output_path).exists()

        with open(output_path) as f:
            data = json.load(f)
        assert "script" in data
        assert "beat_sheet" in data
        assert "characters" in data
        assert "scene_descriptions" in data

        Path(output_path).unlink()

    def test_json_contains_script_title(self):
        script = Script(title="My Script", logline="Test logline.", genre="drama")
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        scene_descriptions = SceneDescriptionCollection()

        formatter = JSONFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            data = json.load(f)
        assert data["script"]["title"] == "My Script"

        Path(output_path).unlink()

    def test_json_contains_characters(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        character_registry.add_character(Character(name="Hero", role=CharacterRole.PROTAGONIST))
        scene_descriptions = SceneDescriptionCollection()

        formatter = JSONFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            data = json.load(f)
        assert len(data["characters"]["characters"]) == 1
        assert data["characters"]["characters"][0]["name"] == "Hero"

        Path(output_path).unlink()

    def test_json_contains_script_scenes(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        script.add_scene(
            Scene(
                scene_heading="INT. COFFEE SHOP - DAY",
                action="A hero sits alone.",
                characters_present=["Hero"],
            )
        )
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        scene_descriptions = SceneDescriptionCollection()

        formatter = JSONFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            data = json.load(f)
        assert len(data["script"]["scenes"]) == 1
        assert data["script"]["scenes"][0]["scene_heading"] == "INT. COFFEE SHOP - DAY"

        Path(output_path).unlink()

    def test_json_format_method(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        scene_descriptions = SceneDescriptionCollection()

        formatter = JSONFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        output_dict = formatter.format()
        assert isinstance(output_dict, dict)
        assert output_dict["script"]["title"] == "Test"

    def test_json_empty_script(self):
        script = Script(title="Empty", logline="", genre="")
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        scene_descriptions = SceneDescriptionCollection()

        formatter = JSONFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)
        assert Path(output_path).exists()

        with open(output_path) as f:
            data = json.load(f)
        assert data["script"]["title"] == "Empty"
        assert data["script"]["scenes"] == []

        Path(output_path).unlink()


class TestYAMLFormatter:
    def test_save_yaml(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        character_registry.add_character(Character(name="Hero", role=CharacterRole.PROTAGONIST))
        scene_descriptions = SceneDescriptionCollection()

        formatter = YAMLFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)
        assert Path(output_path).exists()

        with open(output_path) as f:
            content = f.read()
        assert "title" in content

        Path(output_path).unlink()

    def test_yaml_contains_script_title(self):
        script = Script(title="My Script", logline="Test logline.", genre="drama")
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        scene_descriptions = SceneDescriptionCollection()

        formatter = YAMLFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            content = f.read()
        assert "My Script" in content

        Path(output_path).unlink()

    def test_yaml_format_method(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        beat_sheet = BeatSheet(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        scene_descriptions = SceneDescriptionCollection()

        formatter = YAMLFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        output_str = formatter.format()
        assert isinstance(output_str, str)
        assert "title" in output_str

    def test_yaml_contains_beat_sheet(self):
        beat_sheet = BeatSheet(title="My Beat Sheet", logline="Test logline.", genre="drama")
        script = Script(title="Test", logline="Test logline.", genre="drama")
        character_registry = CharacterRegistry()
        scene_descriptions = SceneDescriptionCollection()

        formatter = YAMLFormatter(
            script=script,
            beat_sheet=beat_sheet,
            characters=character_registry,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            content = f.read()
        assert "My Beat Sheet" in content

        Path(output_path).unlink()


class TestFDXFormatter:
    def test_save_fdx(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        scene_descriptions = SceneDescriptionCollection()

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".fdx", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)
        assert Path(output_path).exists()

        with open(output_path) as f:
            content = f.read()
        assert "FinalDraft" in content

        Path(output_path).unlink()

    def test_fdx_contains_script_title(self):
        script = Script(title="My Script", logline="Test logline.", genre="drama")
        scene_descriptions = SceneDescriptionCollection()

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".fdx", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            content = f.read()
        assert "My Script" in content

        Path(output_path).unlink()

    def test_fdx_contains_scene_heading(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        script.add_scene(
            Scene(
                scene_heading="INT. COFFEE SHOP - DAY",
                action="A hero sits alone.",
                characters_present=["Hero"],
            )
        )
        scene_descriptions = SceneDescriptionCollection()

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".fdx", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            content = f.read()
        assert "INT. COFFEE SHOP - DAY" in content

        Path(output_path).unlink()

    def test_fdx_contains_action(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        script.add_scene(
            Scene(
                scene_heading="INT. COFFEE SHOP - DAY",
                action="A hero sits alone.",
                characters_present=["Hero"],
            )
        )
        scene_descriptions = SceneDescriptionCollection()

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".fdx", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            content = f.read()
        assert "A hero sits alone." in content

        Path(output_path).unlink()

    def test_fdx_contains_dialogue(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        script.add_scene(
            Scene(
                scene_heading="INT. COFFEE SHOP - DAY",
                action="A hero sits alone.",
                characters_present=["Hero"],
                dialogue_lines=[
                    DialogueLine(
                        character_name="Hero",
                        character_id="hero-1",
                        text="Hello world.",
                    )
                ],
            )
        )
        scene_descriptions = SceneDescriptionCollection()

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".fdx", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            content = f.read()
        assert "Hello world." in content
        assert "Hero" in content

        Path(output_path).unlink()

    def test_fdx_format_method(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        scene_descriptions = SceneDescriptionCollection()

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        output_str = formatter.format()
        assert isinstance(output_str, str)
        assert "FinalDraft" in output_str
        assert '<?xml version="1.0" encoding="UTF-8"?>' in output_str

    def test_fdx_with_scene_descriptions(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        scene = Scene(
            scene_heading="INT. COFFEE SHOP - DAY",
            action="A hero sits alone.",
            characters_present=["Hero"],
        )
        script.add_scene(scene)

        scene_descriptions = SceneDescriptionCollection()
        scene_descriptions.add_description(
            scene.scene_id,
            SceneDescription(
                scene_id=scene.scene_id,
                mood="melancholy",
                lighting="dim",
                camera_notes="close-up",
            ),
        )

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".fdx", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            content = f.read()
        assert "melancholy" in content
        assert "dim" in content
        assert "close-up" in content

        Path(output_path).unlink()

    def test_fdx_multiple_scenes(self):
        script = Script(title="Test", logline="Test logline.", genre="drama")
        script.add_scene(
            Scene(
                scene_heading="INT. COFFEE SHOP - DAY",
                action="Scene 1 action.",
                characters_present=["Hero"],
            )
        )
        script.add_scene(
            Scene(
                scene_heading="EXT. PARK - NIGHT",
                action="Scene 2 action.",
                characters_present=["Hero", "Villain"],
            )
        )
        scene_descriptions = SceneDescriptionCollection()

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".fdx", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)

        with open(output_path) as f:
            content = f.read()
        assert "Scene 1 action." in content
        assert "Scene 2 action." in content
        assert "INT. COFFEE SHOP - DAY" in content
        assert "EXT. PARK - NIGHT" in content

        Path(output_path).unlink()

    def test_fdx_empty_script(self):
        script = Script(title="Empty", logline="", genre="")
        scene_descriptions = SceneDescriptionCollection()

        formatter = FDXFormatter(
            script=script,
            scene_descriptions=scene_descriptions,
        )

        with tempfile.NamedTemporaryFile(suffix=".fdx", delete=False) as f:
            output_path = f.name

        formatter.save(output_path)
        assert Path(output_path).exists()

        with open(output_path) as f:
            content = f.read()
        assert "Empty" in content
        assert "FinalDraft" in content

        Path(output_path).unlink()
