"""Tests for core data models."""

import pytest
from ai_movie_gen_suite.models import (
    Beat,
    BeatPhase,
    BeatSheet,
    Character,
    CharacterRegistry,
    CharacterRole,
    DialogueLine,
    Scene,
    Script,
    SceneDescription,
    SceneDescriptionCollection,
    Project,
)


class TestBeatPhase:
    def test_setup_value(self):
        assert BeatPhase.SETUP.value == "setup"

    def test_confrontation_value(self):
        assert BeatPhase.CONFRONTATION.value == "confrontation"

    def test_resolution_value(self):
        assert BeatPhase.RESOLUTION.value == "resolution"


class TestCharacterRole:
    def test_protagonist_value(self):
        assert CharacterRole.PROTAGONIST.value == "protagonist"

    def test_antagonist_value(self):
        assert CharacterRole.ANTAGONIST.value == "antagonist"

    def test_mentor_value(self):
        assert CharacterRole.MENTOR.value == "mentor"

    def test_supporting_value(self):
        assert CharacterRole.SUPPORTING.value == "supporting"


class TestBeat:
    def test_create_beat(self):
        beat = Beat(
            beat_name="Opening Image",
            beat_number=1,
            summary="The story begins.",
            phase=BeatPhase.SETUP,
            description="A detailed description.",
        )
        assert beat.phase == BeatPhase.SETUP
        assert beat.beat_name == "Opening Image"
        assert beat.beat_number == 1
        assert beat.summary == "The story begins."

    def test_beat_model_dump(self):
        beat = Beat(
            beat_name="Test Beat",
            beat_number=2,
            summary="Test summary",
            phase=BeatPhase.SETUP,
            description="Test description",
        )
        d = beat.model_dump()
        assert d["phase"] == "setup"
        assert d["beat_name"] == "Test Beat"
        assert d["summary"] == "Test summary"


class TestBeatSheet:
    def test_create_beatsheet(self):
        beatsheet = BeatSheet(
            logline="A test logline.",
            genre="drama",
        )
        assert beatsheet.logline == "A test logline."
        assert beatsheet.genre == "drama"
        assert len(beatsheet.beats) == 0

    def test_add_beat(self):
        beatsheet = BeatSheet(
            logline="A test logline.",
            genre="drama",
        )
        beat = Beat(
            beat_name="Test Beat",
            beat_number=1,
            summary="A summary",
            phase=BeatPhase.SETUP,
        )
        beatsheet.add_beat(beat)
        assert len(beatsheet.beats) == 1
        assert beatsheet.beats[0].beat_name == "Test Beat"

    def test_model_dump(self):
        beatsheet = BeatSheet(
            logline="A test logline.",
            genre="drama",
        )
        beatsheet.add_beat(Beat(beat_name="B1", beat_number=1, summary="S1", phase=BeatPhase.SETUP))
        d = beatsheet.model_dump()
        assert d["logline"] == "A test logline."
        assert len(d["beats"]) == 1


class TestCharacter:
    def test_create_character(self):
        char = Character(
            name="John Doe",
            role=CharacterRole.PROTAGONIST,
            physical_description="Tall and muscular",
            personality_traits=["brave", "determined"],
        )
        assert char.name == "John Doe"
        assert char.role == CharacterRole.PROTAGONIST
        assert char.physical_description == "Tall and muscular"
        assert char.personality_traits == ["brave", "determined"]

    def test_character_model_dump(self):
        char = Character(
            name="Jane Doe",
            role=CharacterRole.ANTAGONIST,
        )
        d = char.model_dump()
        assert d["name"] == "Jane Doe"
        assert d["role"] == "antagonist"


class TestCharacterRegistry:
    def test_add_character(self):
        registry = CharacterRegistry()
        char = Character(name="John", role=CharacterRole.PROTAGONIST)
        registry.add_character(char)
        assert len(registry.characters) == 1

    def test_get_by_id(self):
        registry = CharacterRegistry()
        char = Character(name="John", role=CharacterRole.PROTAGONIST)
        registry.add_character(char)
        found = registry.get_by_id(char.id)
        assert found is not None
        assert found.name == "John"

    def test_get_by_name(self):
        registry = CharacterRegistry()
        char = Character(name="John", role=CharacterRole.PROTAGONIST)
        registry.add_character(char)
        found = registry.get_by_name("John")
        assert found is not None
        assert found.name == "John"

    def test_get_by_name_case_insensitive(self):
        registry = CharacterRegistry()
        char = Character(name="John", role=CharacterRole.PROTAGONIST)
        registry.add_character(char)
        found = registry.get_by_name("john")
        assert found is not None
        assert found.name == "John"

    def test_get_by_id_not_found(self):
        registry = CharacterRegistry()
        found = registry.get_by_id("nonexistent")
        assert found is None

    def test_get_by_name_not_found(self):
        registry = CharacterRegistry()
        found = registry.get_by_name("Nobody")
        assert found is None


class TestDialogueLine:
    def test_create_dialogue_line(self):
        line = DialogueLine(
            character_name="John",
            character_id="char-1",
            text="Hello world!",
            parenthetical="(smiling)",
            delivery="warmly",
        )
        assert line.character_name == "John"
        assert line.text == "Hello world!"
        assert line.parenthetical == "(smiling)"
        assert line.delivery == "warmly"


class TestScene:
    def test_create_scene(self):
        scene = Scene(
            scene_heading="INT. COFFEE SHOP - DAY",
            action="John sits at a table.",
            characters_present=["John"],
        )
        assert scene.scene_heading == "INT. COFFEE SHOP - DAY"
        assert scene.action == "John sits at a table."
        assert len(scene.dialogue_lines) == 0

    def test_add_dialogue(self):
        scene = Scene(
            scene_heading="INT. COFFEE SHOP - DAY",
            action="John sits at a table.",
        )
        line = DialogueLine(
            character_name="John",
            character_id="char-1",
            text="Hello!",
        )
        scene.dialogue_lines.append(line)
        assert len(scene.dialogue_lines) == 1

    def test_scene_model_dump(self):
        scene = Scene(
            scene_heading="INT. COFFEE SHOP - DAY",
            action="John sits.",
        )
        d = scene.model_dump()
        assert d["scene_heading"] == "INT. COFFEE SHOP - DAY"
        assert "dialogue_lines" in d


class TestScript:
    def test_create_script(self):
        script = Script(
            title="Test Script",
            logline="A test logline.",
            genre="drama",
        )
        assert script.title == "Test Script"
        assert len(script.scenes) == 0

    def test_add_scene(self):
        script = Script(
            title="Test Script",
            logline="A test logline.",
            genre="drama",
        )
        scene = Scene(
            scene_heading="INT. ROOM - DAY",
            action="Action.",
        )
        script.add_scene(scene)
        assert len(script.scenes) == 1

    def test_script_model_dump(self):
        script = Script(
            title="Test Script",
            logline="A test logline.",
            genre="drama",
        )
        d = script.model_dump()
        assert d["title"] == "Test Script"
        assert "scenes" in d


class TestSceneDescription:
    def test_create_scene_description(self):
        desc = SceneDescription(
            scene_id="SC-001",
            setting="A dimly lit room",
            lighting="Low key",
            mood="Tense",
        )
        assert desc.scene_id == "SC-001"
        assert desc.setting == "A dimly lit room"
        assert desc.mood == "Tense"


class TestSceneDescriptionCollection:
    def test_add_description(self):
        collection = SceneDescriptionCollection()
        desc = SceneDescription(scene_id="SC-001", mood="Tense")
        collection.add_description("SC-001", desc)
        assert len(collection.descriptions) == 1

    def test_get_description(self):
        collection = SceneDescriptionCollection()
        desc = SceneDescription(scene_id="SC-001", mood="Tense")
        collection.add_description("SC-001", desc)
        found = collection.get_description("SC-001")
        assert found is not None
        assert found.mood == "Tense"

    def test_get_description_not_found(self):
        collection = SceneDescriptionCollection()
        found = collection.get_description("SC-999")
        assert found is None


class TestProject:
    def test_create_project(self):
        project = Project(
            title="Test Project",
            logline="A test logline.",
            genre="drama",
        )
        assert project.title == "Test Project"
        assert project.logline == "A test logline."
        assert project.genre == "drama"
        assert project.beat_sheet is None
        assert project.character_registry is None
        assert project.script is None
        assert project.scene_descriptions is None

    def test_project_model_dump(self):
        project = Project(
            title="Test Project",
            logline="A test logline.",
            genre="drama",
        )
        d = project.model_dump()
        assert d["title"] == "Test Project"
        assert "beat_sheet" in d
        assert "character_registry" in d
        assert "script" in d
        assert "scene_descriptions" in d
