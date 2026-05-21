"""Tests for Phase 2 visual planning (storyboard prompts, mood boards, character sheets)."""

import json
from pathlib import Path

import pytest

from ai_movie_gen_suite.models import ImageModelTarget, SceneDescription, SceneDescriptionCollection
from ai_movie_gen_suite.pipeline.project_exporter import ProjectExporter
from ai_movie_gen_suite.stages.animatic_builder import AnimaticTimelineBuilder
from ai_movie_gen_suite.stages.character_consistency import CharacterConsistencyEngine
from ai_movie_gen_suite.stages.mood_board_generator import MoodBoardGenerator
from ai_movie_gen_suite.stages.storyboard_prompt_generator import StoryboardPromptGenerator
from ai_movie_gen_suite.stages.beat_generator import BeatGenerator
from ai_movie_gen_suite.stages.character_generator import CharacterGenerator
from ai_movie_gen_suite.stages.scene_description_engine import SceneDescriptionEngine
from ai_movie_gen_suite.stages.script_writer import ScriptWriter


@pytest.fixture
def pipeline_artifacts():
    """Minimal full pipeline output for visual planning tests."""
    beat_sheet = BeatGenerator(
        logline="A detective solves a murder where everyone lies.",
        genre="Noir",
        tone="dark",
    ).generate_beat_sheet()
    registry = CharacterGenerator(
        logline="A detective solves a murder where everyone lies.",
        genre="Noir",
        tone="dark",
    ).generate_characters()
    script = ScriptWriter(
        title="The Lying City",
        logline="A detective solves a murder where everyone lies.",
        genre="Noir",
        beat_sheet=beat_sheet,
        character_registry=registry,
    ).write_script()
    descriptions = SceneDescriptionEngine(
        script=script,
        beat_sheet=beat_sheet,
        character_registry=registry,
        tone="dark",
    ).generate_descriptions()
    return script, registry, descriptions


class TestCharacterConsistency:
    def test_enrich_and_character_sheets(self, pipeline_artifacts):
        _, registry, _ = pipeline_artifacts
        engine = CharacterConsistencyEngine(registry, tone="dark")
        sheets = engine.generate_all_sheets()
        assert len(sheets) == len(registry.characters)
        for sheet in sheets:
            assert sheet.prompt
            assert sheet.negative_prompt
            assert sheet.target_model == ImageModelTarget.SDXL


class TestStoryboardPromptGenerator:
    def test_generates_one_to_three_prompts_per_scene(self, pipeline_artifacts):
        script, registry, descriptions = pipeline_artifacts
        gen = StoryboardPromptGenerator(
            script=script,
            scene_descriptions=descriptions,
            character_registry=registry,
            tone="dark",
        )
        all_prompts = gen.generate_all()
        assert len(all_prompts) == len(script.scenes)
        for scene_id, sb in all_prompts.items():
            assert 1 <= len(sb.prompts) <= 3
            assert sb.scene_id == scene_id
            assert sb.prompts[0].prompt


class TestMoodBoardGenerator:
    def test_character_and_scene_boards(self, pipeline_artifacts):
        script, registry, descriptions = pipeline_artifacts
        consistency = CharacterConsistencyEngine(registry, script=script, tone="dark")
        sheets = consistency.generate_all_sheets()
        storyboards = StoryboardPromptGenerator(
            script=script,
            scene_descriptions=descriptions,
            character_registry=registry,
            tone="dark",
        ).generate_all()
        mood_gen = MoodBoardGenerator(registry, sheets, storyboards, tone="dark")
        char_boards = mood_gen.generate_character_boards()
        scene_boards = mood_gen.generate_scene_boards()
        assert len(char_boards) == len(registry.characters)
        assert len(scene_boards) == len(script.scenes)
        for board in char_boards.values():
            assert board.character_sheet_prompt
            assert board.references


class TestProjectExporterPhase2:
    def test_writes_deliverable_directories(self, pipeline_artifacts, tmp_path):
        script, registry, descriptions = pipeline_artifacts
        exporter = ProjectExporter(
            project_dir=tmp_path,
            script=script,
            character_registry=registry,
            scene_descriptions=descriptions,
            tone="dark",
        )
        storyboards, _ = exporter.export_phase2()

        assert (tmp_path / "characters.json").exists()
        assert (tmp_path / "storyboard_prompts").is_dir()
        assert len(list((tmp_path / "storyboard_prompts").glob("*.json"))) == len(storyboards)
        assert (tmp_path / "mood_boards" / "characters").is_dir()
        assert (tmp_path / "mood_boards" / "scenes").is_dir()

        chars = json.loads((tmp_path / "characters.json").read_text(encoding="utf-8"))
        for char in chars["characters"]:
            assert "character_sheet_prompt" in char


class TestAnimaticBuilder:
    def test_timeline_and_audio_cues(self, pipeline_artifacts, tmp_path):
        script, registry, descriptions = pipeline_artifacts
        exporter = ProjectExporter(
            project_dir=tmp_path,
            script=script,
            character_registry=registry,
            scene_descriptions=descriptions,
            tone="dark",
        )
        storyboards, _ = exporter.export_phase2()
        phase4 = exporter.export_phase4(storyboards)

        timeline = phase4["timeline"]
        assert len(timeline.segments) >= len(script.scenes)
        for seg in timeline.segments:
            assert seg.duration_ms > 0
            assert seg.scene_id in storyboards

        audio = phase4["audio_cues"]
        assert len(audio.cues) == len(timeline.segments)

        builder = AnimaticTimelineBuilder(script, storyboards, tone="dark")
        preview = builder.build_preview_manifest(timeline)
        assert preview["frame_count"] == len(timeline.segments)

    def test_manual_timing_override_preserved(self, pipeline_artifacts):
        script, registry, descriptions = pipeline_artifacts
        storyboards = StoryboardPromptGenerator(
            script=script,
            scene_descriptions=descriptions,
            character_registry=registry,
        ).generate_all()
        first_scene = script.scenes[0].scene_id
        overrides = {f"{first_scene}:1": 9999}
        builder = AnimaticTimelineBuilder(
            script, storyboards, manual_overrides=overrides
        )
        timeline = builder.build_timeline()
        match = [s for s in timeline.segments if s.scene_id == first_scene and s.frame_index == 1]
        assert match[0].duration_ms == 9999
