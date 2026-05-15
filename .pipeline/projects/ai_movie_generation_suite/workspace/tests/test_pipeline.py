"""Tests for the AI Movie Generation Suite pipeline."""

import pytest
from ai_movie_gen_suite.config import LLMConfig, ProjectConfig, SuiteConfig
from ai_movie_gen_suite.models import (
    Beat,
    BeatPhase,
    BeatSheet,
    Character,
    CharacterRegistry,
    CharacterRole,
    DialogueLine,
    Project,
    Scene,
    SceneDescription,
    SceneDescriptionCollection,
    Script,
)
from ai_movie_gen_suite.stages.beat_generator import BeatGenerator
from ai_movie_gen_suite.stages.character_generator import CharacterGenerator
from ai_movie_gen_suite.stages.scene_description_engine import SceneDescriptionEngine
from ai_movie_gen_suite.stages.script_writer import ScriptWriter


class TestModels:
    """Test core data models."""

    def test_beat_creation(self):
        beat = Beat(
            beat_name="Catalyst",
            beat_number=4,
            summary="The inciting incident.",
            phase=BeatPhase.SETUP,
        )
        assert beat.beat_name == "Catalyst"
        assert beat.beat_number == 4
        assert beat.phase == BeatPhase.SETUP

    def test_beat_sheet_creation(self):
        sheet = BeatSheet(logline="A test logline.", genre="Drama")
        assert sheet.logline == "A test logline."
        assert sheet.genre == "Drama"
        assert len(sheet.beats) == 0

    def test_beat_sheet_add_beat(self):
        sheet = BeatSheet(logline="A test logline.", genre="Drama")
        beat = Beat(beat_name="Setup", beat_number=3, summary="Setup.")
        sheet.add_beat(beat)
        assert len(sheet.beats) == 1
        assert sheet.beats[0].beat_name == "Setup"

    def test_character_creation(self):
        char = Character(
            name="Hero",
            role=CharacterRole.PROTAGONIST,
            physical_description="Tall and brave.",
        )
        assert char.name == "Hero"
        assert char.role == CharacterRole.PROTAGONIST

    def test_character_registry(self):
        registry = CharacterRegistry()
        char1 = Character(name="Hero", role=CharacterRole.PROTAGONIST)
        char2 = Character(name="Villain", role=CharacterRole.ANTAGONIST)
        registry.add_character(char1)
        registry.add_character(char2)
        assert len(registry.characters) == 2
        assert registry.get_by_name("Hero") == char1
        assert registry.get_by_name("villain") == char2

    def test_scene_creation(self):
        scene = Scene(
            scene_id="SC-001",
            scene_heading="INT. COFFEE SHOP - DAY",
            action="A person orders coffee.",
        )
        assert scene.scene_heading == "INT. COFFEE SHOP - DAY"
        assert len(scene.dialogue_lines) == 0

    def test_script_creation(self):
        script = Script(title="Test", logline="Test logline.", genre="Drama")
        scene = Scene(scene_id="SC-001", scene_heading="INT. ROOM - DAY", action="Action.")
        script.add_scene(scene)
        assert len(script.scenes) == 1

    def test_scene_description_collection(self):
        collection = SceneDescriptionCollection()
        desc = SceneDescription(scene_id="SC-001", mood="tense")
        collection.add_description("SC-001", desc)
        assert collection.get_description("SC-001") == desc

    def test_project_creation(self):
        project = Project(title="Test Film", logline="Test logline.", genre="Drama")
        assert project.title == "Test Film"
        assert project.beat_sheet is None
        assert project.character_registry is None
        assert project.script is None
        assert project.scene_descriptions is None

    def test_model_dump_serialization(self):
        project = Project(title="Test", logline="Test.", genre="Drama")
        d = project.model_dump()
        assert d["title"] == "Test"
        assert "beat_sheet" not in d or d["beat_sheet"] is None


class TestBeatGenerator:
    """Test beat sheet generation."""

    def test_generate_beat_sheet(self):
        generator = BeatGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        sheet = generator.generate_beat_sheet()
        assert sheet.logline == "A hero saves the world."
        assert sheet.genre == "Action"
        assert len(sheet.beats) == 15

    def test_beat_phases(self):
        generator = BeatGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        sheet = generator.generate_beat_sheet()
        phases = [b.phase for b in sheet.beats if b.phase]
        assert BeatPhase.SETUP in phases
        assert BeatPhase.CONFRONTATION in phases
        assert BeatPhase.RESOLUTION in phases

    def test_beat_names(self):
        generator = BeatGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        sheet = generator.generate_beat_sheet()
        names = [b.beat_name for b in sheet.beats]
        assert "Opening Image" in names
        assert "Catalyst" in names
        assert "Finale" in names
        assert "Final Image" in names


class TestCharacterGenerator:
    """Test character generation."""

    def test_generate_characters(self):
        generator = CharacterGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        registry = generator.generate_characters()
        assert len(registry.characters) == 5
        roles = [c.role for c in registry.characters]
        assert CharacterRole.PROTAGONIST in roles
        assert CharacterRole.ANTAGONIST in roles
        assert CharacterRole.MENTOR in roles
        assert CharacterRole.ALLY in roles
        assert CharacterRole.SIDEKICK in roles

    def test_generate_custom_character(self):
        generator = CharacterGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        char = generator.generate_custom_character(
            name="Custom Hero",
            role=CharacterRole.PROTAGONIST,
            physical_description="Brave and strong.",
        )
        assert char.name == "Custom Hero"
        assert char.role == CharacterRole.PROTAGONIST


class TestScriptWriter:
    """Test script writing."""

    def test_write_script_from_beat_sheet(self):
        generator = BeatGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        beat_sheet = generator.generate_beat_sheet()

        writer = ScriptWriter(
            title="Test Film",
            logline="A hero saves the world.",
            genre="Action",
            beat_sheet=beat_sheet,
        )
        script = writer.write_script()
        assert script.title == "Test Film"
        assert len(script.scenes) == 15  # One scene per beat

    def test_write_script_without_beat_sheet(self):
        writer = ScriptWriter(
            title="Test Film",
            logline="A hero saves the world.",
            genre="Action",
        )
        script = writer.write_script()
        assert len(script.scenes) == 1  # Placeholder scene


class TestSceneDescriptionEngine:
    """Test scene description generation."""

    def test_generate_descriptions(self):
        generator = BeatGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        beat_sheet = generator.generate_beat_sheet()

        writer = ScriptWriter(
            title="Test Film",
            logline="A hero saves the world.",
            genre="Action",
            beat_sheet=beat_sheet,
        )
        script = writer.write_script()

        engine = SceneDescriptionEngine(
            script=script,
            tone="Exciting",
        )
        descriptions = engine.generate_descriptions()
        assert len(descriptions.descriptions) == 15

    def test_mood_inference(self):
        engine = SceneDescriptionEngine(tone="Exciting")

        night_scene = Scene(scene_id="SC-001", scene_heading="INT. DARK ROOM - NIGHT", action="Action.")
        assert engine._infer_mood(night_scene) == "tense, mysterious"

        day_scene = Scene(scene_id="SC-002", scene_heading="EXT. PARK - DAY", action="Action.")
        assert engine._infer_mood(day_scene) == "bright, hopeful"

    def test_lighting_inference(self):
        engine = SceneDescriptionEngine(tone="Exciting")

        night_scene = Scene(scene_id="SC-001", scene_heading="INT. DARK ROOM - NIGHT", action="Action.")
        assert "low-key" in engine._infer_lighting(night_scene)

        day_scene = Scene(scene_id="SC-002", scene_heading="EXT. PARK - DAY", action="Action.")
        assert "natural" in engine._infer_lighting(day_scene)


class TestPipelineIntegration:
    """Test the full pipeline."""

    def test_full_pipeline(self):
        """Test the complete pipeline from logline to scene descriptions."""
        # Step 1: Generate beat sheet
        beat_gen = BeatGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        beat_sheet = beat_gen.generate_beat_sheet()
        assert len(beat_sheet.beats) == 15

        # Step 2: Generate characters
        char_gen = CharacterGenerator(
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
        )
        character_registry = char_gen.generate_characters()
        assert len(character_registry.characters) == 5

        # Step 3: Write script
        writer = ScriptWriter(
            title="Test Film",
            logline="A hero saves the world.",
            genre="Action",
            beat_sheet=beat_sheet,
            character_registry=character_registry,
        )
        script = writer.write_script()
        assert len(script.scenes) == 15

        # Step 4: Generate scene descriptions
        engine = SceneDescriptionEngine(
            script=script,
            beat_sheet=beat_sheet,
            character_registry=character_registry,
            tone="Exciting",
        )
        scene_descriptions = engine.generate_descriptions()
        assert len(scene_descriptions.descriptions) == 15

        # Step 5: Create project
        project = Project(
            title="Test Film",
            logline="A hero saves the world.",
            genre="Action",
            tone="Exciting",
            beat_sheet=beat_sheet,
            character_registry=character_registry,
            script=script,
            scene_descriptions=scene_descriptions,
        )
        assert project.title == "Test Film"
        assert project.beat_sheet is not None
        assert project.character_registry is not None
        assert project.script is not None
        assert project.scene_descriptions is not None

        # Verify serialization
        d = project.model_dump()
        assert d["title"] == "Test Film"
        assert "beat_sheet" in d
        assert "character_registry" in d
        assert "script" in d
        assert "scene_descriptions" in d


class TestConfig:
    """Test configuration classes."""

    def test_llm_config(self):
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4o"

    def test_project_config(self):
        config = ProjectConfig(
            project_dir="/tmp/test",
            title="Test Film",
            logline="Test logline.",
            genre="Drama",
        )
        assert config.title == "Test Film"

    def test_suite_config(self):
        config = SuiteConfig()
        assert config.output_format == "json"
        assert config.scenes_dir == "scenes"
