"""Tests for pipeline stages."""

import pytest
from ai_movie_gen_suite.stages.beat_generator import BeatGenerator
from ai_movie_gen_suite.stages.character_generator import CharacterGenerator
from ai_movie_gen_suite.stages.script_writer import ScriptWriter
from ai_movie_gen_suite.stages.scene_description_engine import SceneDescriptionEngine
from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    Script,
    BeatPhase,
    CharacterRole,
)


class TestBeatGenerator:
    def test_generate_beat_sheet(self):
        generator = BeatGenerator(
            logline="A hero saves the world.",
            genre="action",
            tone="exciting",
        )
        beatsheet = generator.generate_beat_sheet()
        assert beatsheet is not None
        assert beatsheet.title == "Untitled"
        assert len(beatsheet.beats) > 0
        # Verify beats are in order
        phases = [b.phase for b in beatsheet.beats]
        # All setup beats should come before confrontation, which should come before resolution
        setup_indices = [i for i, p in enumerate(phases) if p == BeatPhase.SETUP]
        confrontation_indices = [i for i, p in enumerate(phases) if p == BeatPhase.CONFRONTATION]
        resolution_indices = [i for i, p in enumerate(phases) if p == BeatPhase.RESOLUTION]
        if setup_indices and confrontation_indices:
            assert max(setup_indices) < min(confrontation_indices)
        if confrontation_indices and resolution_indices:
            assert max(confrontation_indices) < min(resolution_indices)

    def test_generate_beat_sheet_with_title(self):
        generator = BeatGenerator(
            logline="A hero saves the world.",
            genre="action",
            tone="exciting",
        )
        beatsheet = generator.generate_beat_sheet()
        assert beatsheet.logline == "A hero saves the world."
        assert beatsheet.genre == "action"


class TestCharacterGenerator:
    def test_generate_characters(self):
        generator = CharacterGenerator(
            logline="A hero saves the world.",
            genre="action",
            tone="exciting",
        )
        registry = generator.generate_characters()
        assert registry is not None
        assert len(registry.characters) > 0
        # Should have at least a protagonist
        roles = [c.role for c in registry.characters]
        assert CharacterRole.PROTAGONIST in roles

    def test_character_has_required_fields(self):
        generator = CharacterGenerator(
            logline="A hero saves the world.",
            genre="action",
            tone="exciting",
        )
        registry = generator.generate_characters()
        for char in registry.characters:
            assert char.name
            assert char.role
            assert char.motivation


class TestScriptWriter:
    def test_write_script(self):
        beat_sheet = BeatSheet(
            title="Test Story",
            logline="A hero saves the world.",
            genre="action",
        )
        beat_sheet.add_beat(
            pytest.importorskip("ai_movie_gen_suite.models").Beat(
                phase=BeatPhase.SETUP,
                title="Test Beat",
                description="Test description",
            )
        )
        character_registry = CharacterRegistry()
        character_registry.add_character(
            pytest.importorskip("ai_movie_gen_suite.models").Character(
                name="Hero",
                role=CharacterRole.PROTAGONIST,
                motivation="Save the world",
            )
        )

        writer = ScriptWriter(
            title="Test Script",
            logline="A hero saves the world.",
            genre="action",
            beat_sheet=beat_sheet,
            character_registry=character_registry,
        )
        script = writer.write_script()
        assert script is not None
        assert script.title == "Test Script"
        assert len(script.scenes) > 0

    def test_script_has_scenes(self):
        beat_sheet = BeatSheet(
            title="Test Story",
            logline="A hero saves the world.",
            genre="action",
        )
        beat_sheet.add_beat(
            pytest.importorskip("ai_movie_gen_suite.models").Beat(
                phase=BeatPhase.SETUP,
                title="Test Beat",
                description="Test description",
            )
        )
        character_registry = CharacterRegistry()
        character_registry.add_character(
            pytest.importorskip("ai_movie_gen_suite.models").Character(
                name="Hero",
                role=CharacterRole.PROTAGONIST,
                motivation="Save the world",
            )
        )

        writer = ScriptWriter(
            title="Test Script",
            logline="A hero saves the world.",
            genre="action",
            beat_sheet=beat_sheet,
            character_registry=character_registry,
        )
        script = writer.write_script()
        for scene in script.scenes:
            assert scene.scene_heading
            assert scene.action


class TestSceneDescriptionEngine:
    def test_generate_descriptions(self):
        script = Script(
            title="Test Script",
            logline="A hero saves the world.",
            genre="action",
        )
        script.add_scene(
            pytest.importorskip("ai_movie_gen_suite.models").Scene(
                scene_heading="INT. ROOM - DAY",
                action="Action.",
            )
        )

        beat_sheet = BeatSheet(
            title="Test Story",
            logline="A hero saves the world.",
            genre="action",
        )
        character_registry = CharacterRegistry()
        character_registry.add_character(
            pytest.importorskip("ai_movie_gen_suite.models").Character(
                name="Hero",
                role=CharacterRole.PROTAGONIST,
                motivation="Save the world",
            )
        )

        engine = SceneDescriptionEngine(
            script=script,
            beat_sheet=beat_sheet,
            character_registry=character_registry,
            tone="exciting",
        )
        descriptions = engine.generate_descriptions()
        assert descriptions is not None
        assert len(descriptions.descriptions) > 0

    def test_descriptions_have_required_fields(self):
        script = Script(
            title="Test Script",
            logline="A hero saves the world.",
            genre="action",
        )
        script.add_scene(
            pytest.importorskip("ai_movie_gen_suite.models").Scene(
                scene_heading="INT. ROOM - DAY",
                action="Action.",
            )
        )

        beat_sheet = BeatSheet(
            title="Test Story",
            logline="A hero saves the world.",
            genre="action",
        )
        character_registry = CharacterRegistry()
        character_registry.add_character(
            pytest.importorskip("ai_movie_gen_suite.models").Character(
                name="Hero",
                role=CharacterRole.PROTAGONIST,
                motivation="Save the world",
            )
        )

        engine = SceneDescriptionEngine(
            script=script,
            beat_sheet=beat_sheet,
            character_registry=character_registry,
            tone="exciting",
        )
        descriptions = engine.generate_descriptions()
        for desc in descriptions.descriptions.values():
            assert desc.scene_id
            assert desc.mood
            assert desc.lighting
