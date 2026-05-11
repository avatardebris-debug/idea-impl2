"""Comprehensive tests for ai_movie_gen_suite.models module.

Tests cover all Pydantic models: Beat, BeatSheet, CharacterProfile,
CharacterRegistry, DialogueLine, Scene, Script, SceneDescription, Project,
and the JSON schema helpers.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

import pytest
from pydantic import ValidationError

# Ensure local imports work
import sys, pathlib
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from ai_movie_gen_suite.models import (
    Beat,
    BeatSheet,
    CharacterProfile,
    CharacterRegistry,
    DialogueLine,
    Project,
    Scene,
    SceneDescription,
    Script,
    DialogueLine,
    get_json_schema,
    validate_json_with_schema,
)


# ========================
# Beat Tests
# ========================

class TestBeat:
    """Tests for the Beat model."""

    def test_create_valid_beat(self):
        beat = Beat(
            number=1,
            name="Opening Image",
            description="The story begins with a striking visual.",
            scene_numbers=[1],
        )
        assert beat.number == 1
        assert beat.name == "Opening Image"
        assert beat.description == "The story begins with a striking visual."
        assert beat.scene_numbers == [1]

    def test_beat_default_scene_numbers(self):
        beat = Beat(number=1, name="Test", description="desc")
        assert beat.scene_numbers == []

    def test_beat_number_validation_min(self):
        with pytest.raises(ValidationError):
            Beat(number=0, name="Test", description="desc")

    def test_beat_number_validation_max(self):
        with pytest.raises(ValidationError):
            Beat(number=16, name="Test", description="desc")

    def test_beat_name_not_empty(self):
        with pytest.raises(ValidationError):
            Beat(number=1, name="", description="desc")

    def test_beat_name_strips_whitespace(self):
        beat = Beat(number=1, name="  Test  ", description="desc")
        assert beat.name == "Test"

    def test_beat_description_not_empty(self):
        with pytest.raises(ValidationError):
            Beat(number=1, name="Test", description="")

    def test_beat_to_dict(self):
        beat = Beat(number=5, name="Midpoint", description="A major twist occurs.", scene_numbers=[10, 11])
        d = beat.to_dict()
        assert d == {
            "number": 5,
            "name": "Midpoint",
            "description": "A major twist occurs.",
            "scene_numbers": [10, 11],
        }

    def test_beat_to_json(self):
        beat = Beat(number=1, name="Test", description="desc")
        j = beat.to_json()
        parsed = json.loads(j)
        assert parsed["number"] == 1
        assert parsed["name"] == "Test"

    def test_beat_to_json_indent(self):
        beat = Beat(number=1, name="Test", description="desc")
        j = beat.to_json(indent=4)
        assert "\n" in j  # Pretty-printed

    def test_beat_edge_number_15(self):
        beat = Beat(number=15, name="Final Image", description="The end.")
        assert beat.number == 15


# ========================
# BeatSheet Tests
# ========================

class TestBeatSheet:
    """Tests for the BeatSheet model."""

    def test_create_valid_beatsheet(self):
        beats = [
            Beat(number=1, name="Opening Image", description="Start."),
            Beat(number=2, name="Theme Stated", description="Theme introduced."),
        ]
        bs = BeatSheet(
            title="My Film",
            logline="A short logline.",
            beats=beats,
            genre="Sci-Fi",
            tone="Dark",
        )
        assert bs.title == "My Film"
        assert bs.genre == "Sci-Fi"
        assert bs.tone == "Dark"
        assert len(bs.beats) == 2

    def test_beatsheet_defaults(self):
        bs = BeatSheet(title="T", logline="L", beats=[Beat(number=1, name="N", description="d")])
        assert bs.genre == "Drama"
        assert bs.tone == "Serious"

    def test_beatsheet_title_not_empty(self):
        with pytest.raises(ValidationError):
            BeatSheet(title="", logline="L", beats=[Beat(number=1, name="N", description="d")])

    def test_beatsheet_title_strips(self):
        bs = BeatSheet(title="  T  ", logline="L", beats=[Beat(number=1, name="N", description="d")])
        assert bs.title == "T"

    def test_beatsheet_logline_not_empty(self):
        with pytest.raises(ValidationError):
            BeatSheet(title="T", logline="", beats=[Beat(number=1, name="N", description="d")])

    def test_beatsheet_beats_not_empty(self):
        with pytest.raises(ValidationError):
            BeatSheet(title="T", logline="L", beats=[])

    def test_beatsheet_to_dict(self):
        beats = [Beat(number=1, name="N", description="d")]
        bs = BeatSheet(title="T", logline="L", beats=beats)
        d = bs.to_dict()
        assert d["title"] == "T"
        assert d["logline"] == "L"
        assert d["genre"] == "Drama"
        assert d["tone"] == "Serious"
        assert len(d["beats"]) == 1

    def test_beatsheet_to_json(self):
        beats = [Beat(number=1, name="N", description="d")]
        bs = BeatSheet(title="T", logline="L", beats=beats)
        j = bs.to_json()
        parsed = json.loads(j)
        assert parsed["title"] == "T"


# ========================
# CharacterProfile Tests
# ========================

class TestCharacterProfile:
    """Tests for the CharacterProfile model."""

    def test_create_valid_character(self):
        char = CharacterProfile(
            name="John Doe",
            role="Protagonist",
            age=30,
            gender="Male",
            description="A brave hero.",
            motivation="Save the world.",
            arc="From coward to hero.",
            relationships={"Jane": "Love interest"},
        )
        assert char.name == "John Doe"
        assert char.role == "Protagonist"
        assert char.age == 30
        assert char.gender == "Male"
        assert char.motivation == "Save the world."

    def test_character_optional_fields(self):
        char = CharacterProfile(
            name="Jane",
            role="Supporting",
            description="Mysterious.",
            motivation="Find truth.",
            arc="Discovery.",
        )
        assert char.age is None
        assert char.gender is None
        assert char.relationships == {}

    def test_character_age_validation_min(self):
        with pytest.raises(ValidationError):
            CharacterProfile(
                name="X", role="R", description="d", motivation="m", arc="a", age=-1
            )

    def test_character_age_validation_max(self):
        with pytest.raises(ValidationError):
            CharacterProfile(
                name="X", role="R", description="d", motivation="m", arc="a", age=151
            )

    def test_character_name_not_empty(self):
        with pytest.raises(ValidationError):
            CharacterProfile(name="", role="R", description="d", motivation="m", arc="a")

    def test_character_name_strips(self):
        char = CharacterProfile(name="  Bob  ", role="R", description="d", motivation="m", arc="a")
        assert char.name == "Bob"

    def test_character_to_dict(self):
        char = CharacterProfile(
            name="Bob", role="Hero", description="d", motivation="m", arc="a", age=25
        )
        d = char.to_dict()
        assert d["name"] == "Bob"
        assert d["age"] == 25
        assert d["relationships"] == {}

    def test_character_to_json(self):
        char = CharacterProfile(name="Bob", role="Hero", description="d", motivation="m", arc="a")
        j = char.to_json()
        parsed = json.loads(j)
        assert parsed["name"] == "Bob"


# ========================
# CharacterRegistry Tests
# ========================

class TestCharacterRegistry:
    """Tests for the CharacterRegistry model."""

    def test_create_registry(self):
        chars = [
            CharacterProfile(name="A", role="Hero", description="d", motivation="m", arc="a"),
            CharacterProfile(name="B", role="Villain", description="d", motivation="m", arc="a"),
        ]
        reg = CharacterRegistry(characters=chars)
        assert len(reg.characters) == 2

    def test_registry_characters_not_empty(self):
        with pytest.raises(ValidationError):
            CharacterRegistry(characters=[])

    def test_registry_to_dict(self):
        chars = [CharacterProfile(name="A", role="Hero", description="d", motivation="m", arc="a")]
        reg = CharacterRegistry(characters=chars)
        d = reg.to_dict()
        assert "characters" in d
        assert len(d["characters"]) == 1

    def test_registry_to_json(self):
        chars = [CharacterProfile(name="A", role="Hero", description="d", motivation="m", arc="a")]
        reg = CharacterRegistry(characters=chars)
        j = reg.to_json()
        parsed = json.loads(j)
        assert parsed["characters"][0]["name"] == "A"

    def test_get_character_case_insensitive(self):
        chars = [CharacterProfile(name="Alice", role="Hero", description="d", motivation="m", arc="a")]
        reg = CharacterRegistry(characters=chars)
        found = reg.get_character("alice")
        assert found is not None
        assert found.name == "Alice"

    def test_get_character_not_found(self):
        chars = [CharacterProfile(name="Alice", role="Hero", description="d", motivation="m", arc="a")]
        reg = CharacterRegistry(characters=chars)
        found = reg.get_character("Bob")
        assert found is None

    def test_get_character_partial_match(self):
        chars = [CharacterProfile(name="Alice", role="Hero", description="d", motivation="m", arc="a")]
        reg = CharacterRegistry(characters=chars)
        # Partial match should NOT find it (exact match only)
        found = reg.get_character("Ali")
        assert found is None


# ========================
# DialogueLine Tests
# ========================

class TestDialogueLine:
    """Tests for the DialogueLine model."""

    def test_create_valid_dialogue(self):
        dl = DialogueLine(character="Bob", dialogue="Hello, world!", action="smiling")
        assert dl.character == "Bob"
        assert dl.dialogue == "Hello, world!"
        assert dl.action == "smiling"

    def test_dialogue_default_action(self):
        dl = DialogueLine(character="Bob", dialogue="Hello")
        assert dl.action is None

    def test_dialogue_character_not_empty(self):
        with pytest.raises(ValidationError):
            DialogueLine(character="", dialogue="Hello")

    def test_dialogue_dialogue_not_empty(self):
        with pytest.raises(ValidationError):
            DialogueLine(character="Bob", dialogue="")

    def test_dialogue_to_dict(self):
        dl = DialogueLine(character="Bob", dialogue="Hi", action="waves")
        d = dl.to_dict()
        assert d == {"character": "Bob", "dialogue": "Hi", "action": "waves"}

    def test_dialogue_to_json(self):
        dl = DialogueLine(character="Bob", dialogue="Hi")
        j = dl.to_json()
        parsed = json.loads(j)
        assert parsed["character"] == "Bob"


# ========================
# Scene Tests
# ========================

class TestScene:
    """Tests for the Scene model."""

    def test_create_valid_scene(self):
        scene = Scene(
            number=1,
            location="INT. COFFEE SHOP - DAY",
            description="Bob walks in.",
            dialogue=[DialogueLine(character="Bob", dialogue="Coffee, please.")],
            characters_present=["Bob"],
        )
        assert scene.number == 1
        assert scene.location == "INT. COFFEE SHOP - DAY"
        assert len(scene.dialogue) == 1
        assert scene.characters_present == ["Bob"]

    def test_scene_defaults(self):
        scene = Scene(number=1, location="INT. ROOM - DAY", description="Empty room.")
        assert scene.dialogue == []
        assert scene.characters_present == []

    def test_scene_number_validation(self):
        with pytest.raises(ValidationError):
            Scene(number=0, location="INT. ROOM - DAY", description="desc")

    def test_scene_location_not_empty(self):
        with pytest.raises(ValidationError):
            Scene(number=1, location="", description="desc")

    def test_scene_location_strips(self):
        scene = Scene(number=1, location="  INT. ROOM - DAY  ", description="desc")
        assert scene.location == "INT. ROOM - DAY"

    def test_scene_description_not_empty(self):
        with pytest.raises(ValidationError):
            Scene(number=1, location="INT. ROOM - DAY", description="")

    def test_scene_to_dict(self):
        scene = Scene(number=1, location="INT. ROOM - DAY", description="desc")
        d = scene.to_dict()
        assert d["number"] == 1
        assert d["location"] == "INT. ROOM - DAY"
        assert d["description"] == "desc"
        assert d["dialogue"] == []
        assert d["characters_present"] == []

    def test_scene_to_json(self):
        scene = Scene(number=1, location="INT. ROOM - DAY", description="desc")
        j = scene.to_json()
        parsed = json.loads(j)
        assert parsed["number"] == 1


# ========================
# Script Tests
# ========================

class TestScript:
    """Tests for the Script model."""

    def test_create_valid_script(self):
        scenes = [
            Scene(number=1, location="INT. ROOM - DAY", description="Start."),
            Scene(number=2, location="EXT. PARK - DAY", description="End."),
        ]
        script = Script(title="My Script", genre="Comedy", tone="Light", scenes=scenes)
        assert script.title == "My Script"
        assert script.genre == "Comedy"
        assert script.tone == "Light"
        assert len(script.scenes) == 2

    def test_script_defaults(self):
        scenes = [Scene(number=1, location="INT. ROOM - DAY", description="desc")]
        script = Script(title="T", scenes=scenes)
        assert script.genre == "Drama"
        assert script.tone == "Serious"

    def test_script_title_not_empty(self):
        with pytest.raises(ValidationError):
            Script(title="", scenes=[])

    def test_script_title_strips(self):
        scenes = [Scene(number=1, location="INT. ROOM - DAY", description="desc")]
        script = Script(title="  T  ", scenes=scenes)
        assert script.title == "T"

    def test_script_scenes_not_empty(self):
        with pytest.raises(ValidationError):
            Script(title="T", scenes=[])

    def test_script_to_dict(self):
        scenes = [Scene(number=1, location="INT. ROOM - DAY", description="desc")]
        script = Script(title="T", scenes=scenes)
        d = script.to_dict()
        assert d["title"] == "T"
        assert d["genre"] == "Drama"
        assert d["tone"] == "Serious"
        assert len(d["scenes"]) == 1

    def test_script_to_json(self):
        scenes = [Scene(number=1, location="INT. ROOM - DAY", description="desc")]
        script = Script(title="T", scenes=scenes)
        j = script.to_json()
        parsed = json.loads(j)
        assert parsed["title"] == "T"


# ========================
# SceneDescription Tests
# ========================

class TestSceneDescription:
    """Tests for the SceneDescription model."""

    def test_create_valid_scene_description(self):
        sd = SceneDescription(
            scene_number=1,
            location="INT. COFFEE SHOP - DAY",
            visual_description="Warm lighting, cozy atmosphere.",
            camera_directions="Slow pan across the room.",
            lighting="Soft natural light from windows.",
            color_palette="Warm browns and creams.",
            mood="Relaxed and inviting.",
            props_and_set_design="Wooden tables, espresso machine.",
        )
        assert sd.scene_number == 1
        assert sd.visual_description == "Warm lighting, cozy atmosphere."
        assert sd.camera_directions == "Slow pan across the room."

    def test_scene_description_scene_number_validation(self):
        with pytest.raises(ValidationError):
            SceneDescription(
                scene_number=0,
                location="INT. ROOM - DAY",
                visual_description="desc",
                camera_directions="desc",
                lighting="desc",
                color_palette="desc",
                mood="desc",
                props_and_set_design="desc",
            )

    def test_scene_description_all_fields_required(self):
        # Each field should raise ValidationError if empty
        base = {
            "scene_number": 1,
            "location": "INT. ROOM - DAY",
            "visual_description": "desc",
            "camera_directions": "desc",
            "lighting": "desc",
            "color_palette": "desc",
            "mood": "desc",
            "props_and_set_design": "desc",
        }
        for field in base:
            test_data = base.copy()
            test_data[field] = ""
            with pytest.raises(ValidationError):
                SceneDescription(**test_data)

    def test_scene_description_to_dict(self):
        sd = SceneDescription(
            scene_number=1,
            location="INT. ROOM - DAY",
            visual_description="desc",
            camera_directions="desc",
            lighting="desc",
            color_palette="desc",
            mood="desc",
            props_and_set_design="desc",
        )
        d = sd.to_dict()
        assert d["scene_number"] == 1
        assert d["location"] == "INT. ROOM - DAY"
        assert all(k in d for k in [
            "visual_description", "camera_directions", "lighting",
            "color_palette", "mood", "props_and_set_design",
        ])

    def test_scene_description_to_json(self):
        sd = SceneDescription(
            scene_number=1,
            location="INT. ROOM - DAY",
            visual_description="desc",
            camera_directions="desc",
            lighting="desc",
            color_palette="desc",
            mood="desc",
            props_and_set_design="desc",
        )
        j = sd.to_json()
        parsed = json.loads(j)
        assert parsed["scene_number"] == 1


# ========================
# Project Tests
# ========================

class TestProject:
    """Tests for the Project model."""

    def test_create_valid_project(self):
        project = Project(
            title="My Movie",
            logline="A hero saves the world.",
            genre="Sci-Fi",
            tone="Dark",
        )
        assert project.title == "My Movie"
        assert project.logline == "A hero saves the world."
        assert project.genre == "Sci-Fi"
        assert project.tone == "Dark"
        assert project.status == "initialized"
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_project_defaults(self):
        project = Project(title="T", logline="L")
        assert project.genre == "Drama"
        assert project.tone == "Serious"
        assert project.status == "initialized"
        assert project.beat_sheet is None
        assert project.characters is None
        assert project.script is None
        assert project.scene_descriptions is None
        assert project.summary is None
        assert project.music is None
        assert project.post_production is None
        assert project.marketing is None
        assert project.distribution is None

    def test_project_title_not_empty(self):
        with pytest.raises(ValidationError):
            Project(title="", logline="L")

    def test_project_title_strips(self):
        project = Project(title="  T  ", logline="L")
        assert project.title == "T"

    def test_project_logline_not_empty(self):
        with pytest.raises(ValidationError):
            Project(title="T", logline="")

    def test_project_update_status(self):
        project = Project(title="T", logline="L")
        old_updated = project.updated_at
        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)
        project.update_status("beat_sheet_complete")
        assert project.status == "beat_sheet_complete"
        assert project.updated_at != old_updated

    def test_project_to_dict(self):
        project = Project(title="T", logline="L")
        d = project.to_dict()
        assert d["title"] == "T"
        assert d["logline"] == "L"
        assert d["status"] == "initialized"
        assert d["beat_sheet"] is None
        assert d["characters"] is None

    def test_project_to_json(self):
        project = Project(title="T", logline="L")
        j = project.to_json()
        parsed = json.loads(j)
        assert parsed["title"] == "T"
        assert parsed["status"] == "initialized"

    def test_project_with_all_fields(self):
        project = Project(
            title="Full Project",
            logline="A full project.",
            genre="Action",
            tone="Intense",
            beat_sheet={"beats": []},
            characters={"characters": []},
            script={"title": "T", "scenes": []},
            scene_descriptions=[{"scene_number": 1}],
            summary={"summary": "done"},
            music={"track": "theme"},
            post_production={"editing": "done"},
            marketing={"plan": "social"},
            distribution={"platform": "streaming"},
        )
        d = project.to_dict()
        assert d["beat_sheet"] == {"beats": []}
        assert d["characters"] == {"characters": []}
        assert d["script"] == {"title": "T", "scenes": []}
        assert d["scene_descriptions"] == [{"scene_number": 1}]
        assert d["summary"] == {"summary": "done"}
        assert d["music"] == {"track": "theme"}
        assert d["post_production"] == {"editing": "done"}
        assert d["marketing"] == {"plan": "social"}
        assert d["distribution"] == {"platform": "streaming"}


# ========================
# JSON Schema Helpers Tests
# ========================

class TestJsonSchemaHelpers:
    """Tests for get_json_schema and validate_json_with_schema."""

    def test_get_json_schema_returns_dict(self):
        schema = get_json_schema(Project)
        assert isinstance(schema, dict)
        assert "$defs" in schema or "properties" in schema

    def test_get_json_schema_has_required_fields(self):
        schema = get_json_schema(Project)
        props = schema.get("properties", {})
        assert "title" in props
        assert "logline" in props
        assert "genre" in props
        assert "tone" in props
        assert "status" in props

    def test_validate_json_with_schema_valid(self):
        data = {"title": "T", "logline": "L"}
        project = validate_json_with_schema(data, Project)
        assert isinstance(project, Project)
        assert project.title == "T"

    def test_validate_json_with_schema_invalid(self):
        data = {"title": "", "logline": "L"}
        with pytest.raises(ValueError, match="Validation failed"):
            validate_json_with_schema(data, Project)

    def test_validate_json_with_schema_missing_required(self):
        data = {"logline": "L"}
        with pytest.raises(ValueError, match="Validation failed"):
            validate_json_with_schema(data, Project)

    def test_validate_json_with_schema_extra_fields(self):
        data = {"title": "T", "logline": "L", "extra_field": "ignored"}
        project = validate_json_with_schema(data, Project)
        assert project.title == "T"

    def test_get_json_schema_character_profile(self):
        schema = get_json_schema(CharacterProfile)
        props = schema.get("properties", {})
        assert "name" in props
        assert "role" in props
        assert "age" in props
        assert "gender" in props
        assert "description" in props
        assert "motivation" in props
        assert "arc" in props
        assert "relationships" in props

    def test_get_json_schema_scene(self):
        schema = get_json_schema(Scene)
        props = schema.get("properties", {})
        assert "number" in props
        assert "location" in props
        assert "description" in props
        assert "dialogue" in props
        assert "characters_present" in props

    def test_get_json_schema_beat_sheet(self):
        schema = get_json_schema(BeatSheet)
        props = schema.get("properties", {})
        assert "title" in props
        assert "logline" in props
        assert "beats" in props
        assert "genre" in props
        assert "tone" in props

    def test_validate_json_with_schema_beat_sheet(self):
        data = {
            "title": "T",
            "logline": "L",
            "beats": [{"number": 1, "name": "N", "description": "d"}],
        }
        bs = validate_json_with_schema(data, BeatSheet)
        assert isinstance(bs, BeatSheet)
        assert bs.title == "T"

    def test_validate_json_with_schema_script(self):
        data = {
            "title": "T",
            "scenes": [{"number": 1, "location": "INT. ROOM - DAY", "description": "desc"}],
        }
        script = validate_json_with_schema(data, Script)
        assert isinstance(script, Script)
        assert script.title == "T"

    def test_validate_json_with_schema_scene_description(self):
        data = {
            "scene_number": 1,
            "location": "INT. ROOM - DAY",
            "visual_description": "desc",
            "camera_directions": "desc",
            "lighting": "desc",
            "color_palette": "desc",
            "mood": "desc",
            "props_and_set_design": "desc",
        }
        sd = validate_json_with_schema(data, SceneDescription)
        assert isinstance(sd, SceneDescription)
        assert sd.scene_number == 1


# ========================
# Integration / Round-trip Tests
# ========================

class TestRoundTrip:
    """Test serialization/deserialization round-trips."""

    def test_beat_round_trip(self):
        beat = Beat(number=1, name="Test", description="desc", scene_numbers=[1, 2])
        j = beat.to_json()
        parsed = json.loads(j)
        beat2 = Beat(**parsed)
        assert beat2.number == beat.number
        assert beat2.name == beat.name
        assert beat2.description == beat.description
        assert beat2.scene_numbers == beat.scene_numbers

    def test_character_round_trip(self):
        char = CharacterProfile(
            name="Bob", role="Hero", age=30, gender="Male",
            description="d", motivation="m", arc="a",
            relationships={"Alice": "Friend"},
        )
        j = char.to_json()
        parsed = json.loads(j)
        char2 = CharacterProfile(**parsed)
        assert char2.name == char.name
        assert char2.age == char.age
        assert char2.relationships == char.relationships

    def test_dialogue_round_trip(self):
        dl = DialogueLine(character="Bob", dialogue="Hi", action="waves")
        j = dl.to_json()
        parsed = json.loads(j)
        dl2 = DialogueLine(**parsed)
        assert dl2.character == dl.character
        assert dl2.action == dl.action

    def test_scene_round_trip(self):
        scene = Scene(
            number=1, location="INT. ROOM - DAY", description="desc",
            dialogue=[DialogueLine(character="Bob", dialogue="Hi")],
            characters_present=["Bob"],
        )
        j = scene.to_json()
        parsed = json.loads(j)
        scene2 = Scene(**parsed)
        assert scene2.number == scene.number
        assert scene2.location == scene.location
        assert len(scene2.dialogue) == 1
        assert scene2.characters_present == scene.characters_present

    def test_script_round_trip(self):
        scenes = [Scene(number=1, location="INT. ROOM - DAY", description="desc")]
        script = Script(title="T", genre="Comedy", tone="Light", scenes=scenes)
        j = script.to_json()
        parsed = json.loads(j)
        script2 = Script(**parsed)
        assert script2.title == script.title
        assert script2.genre == script.genre
        assert len(script2.scenes) == 1

    def test_project_round_trip(self):
        project = Project(
            title="T", logline="L", genre="Sci-Fi", tone="Dark",
            beat_sheet={"beats": []},
            characters={"characters": []},
        )
        j = project.to_json()
        parsed = json.loads(j)
        project2 = Project(**parsed)
        assert project2.title == project.title
        assert project2.genre == project.genre
        assert project2.beat_sheet == project.beat_sheet

    def test_beatsheet_round_trip(self):
        beats = [Beat(number=1, name="N", description="d")]
        bs = BeatSheet(title="T", logline="L", beats=beats, genre="Action")
        j = bs.to_json()
        parsed = json.loads(j)
        bs2 = BeatSheet(**parsed)
        assert bs2.title == bs.title
        assert bs2.genre == bs.genre
        assert len(bs2.beats) == 1

    def test_character_registry_round_trip(self):
        chars = [CharacterProfile(name="A", role="Hero", description="d", motivation="m", arc="a")]
        reg = CharacterRegistry(characters=chars)
        j = reg.to_json()
        parsed = json.loads(j)
        reg2 = CharacterRegistry(**parsed)
        assert len(reg2.characters) == 1
        assert reg2.characters[0].name == "A"

    def test_scene_description_round_trip(self):
        sd = SceneDescription(
            scene_number=1, location="INT. ROOM - DAY",
            visual_description="desc", camera_directions="desc",
            lighting="desc", color_palette="desc",
            mood="desc", props_and_set_design="desc",
        )
        j = sd.to_json()
        parsed = json.loads(j)
        sd2 = SceneDescription(**parsed)
        assert sd2.scene_number == sd.scene_number
        assert sd2.location == sd.location


# ========================
# Edge Cases
# ========================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_beat_number_boundary_1(self):
        beat = Beat(number=1, name="N", description="d")
        assert beat.number == 1

    def test_beat_number_boundary_15(self):
        beat = Beat(number=15, name="N", description="d")
        assert beat.number == 15

    def test_character_age_boundary_0(self):
        char = CharacterProfile(name="A", role="R", description="d", motivation="m", arc="a", age=0)
        assert char.age == 0

    def test_character_age_boundary_150(self):
        char = CharacterProfile(name="A", role="R", description="d", motivation="m", arc="a", age=150)
        assert char.age == 150

    def test_scene_number_boundary_1(self):
        scene = Scene(number=1, location="INT. ROOM - DAY", description="desc")
        assert scene.number == 1

    def test_project_status_transition(self):
        project = Project(title="T", logline="L")
        statuses = ["initialized", "beat_sheet_complete", "characters_complete",
                     "script_complete", "scene_descriptions_complete", "summary_complete",
                     "music_complete", "post_production_complete", "marketing_complete",
                     "distribution_complete", "finalized"]
        for status in statuses:
            project.update_status(status)
            assert project.status == status

    def test_empty_relationships_dict(self):
        char = CharacterProfile(name="A", role="R", description="d", motivation="m", arc="a")
        assert char.relationships == {}
        assert isinstance(char.relationships, dict)

    def test_empty_dialogue_list(self):
        scene = Scene(number=1, location="INT. ROOM - DAY", description="desc")
        assert scene.dialogue == []
        assert isinstance(scene.dialogue, list)

    def test_empty_characters_present_list(self):
        scene = Scene(number=1, location="INT. ROOM - DAY", description="desc")
        assert scene.characters_present == []

    def test_project_timestamps_are_iso_format(self):
        project = Project(title="T", logline="L")
        # Should not raise
        datetime.fromisoformat(project.created_at)
        datetime.fromisoformat(project.updated_at)

    def test_project_timestamps_update_on_status_change(self):
        project = Project(title="T", logline="L")
        old_updated = project.updated_at
        import time
        time.sleep(0.01)
        project.update_status("new_status")
        assert project.updated_at > old_updated

    def test_validate_json_with_schema_beat(self):
        data = {"number": 1, "name": "N", "description": "d"}
        beat = validate_json_with_schema(data, Beat)
        assert isinstance(beat, Beat)

    def test_validate_json_with_schema_dialogue(self):
        data = {"character": "Bob", "dialogue": "Hi"}
        dl = validate_json_with_schema(data, DialogueLine)
        assert isinstance(dl, DialogueLine)

    def test_validate_json_with_schema_character_registry(self):
        data = {
            "characters": [
                {"name": "A", "role": "Hero", "description": "d", "motivation": "m", "arc": "a"}
            ]
        }
        reg = validate_json_with_schema(data, CharacterRegistry)
        assert isinstance(reg, CharacterRegistry)
        assert len(reg.characters) == 1
