"""Tests for the AI Movie Gen Suite."""

import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

from ai_movie_gen_suite.formatters.fdx_formatter import FDXFormatter
from ai_movie_gen_suite.formatters.json_formatter import JSONFormatter
from ai_movie_gen_suite.formatters.yaml_formatter import YAMLFormatter
from ai_movie_gen_suite.models import (
    Beat,
    BeatPhase,
    BeatSheet,
    Character,
    CharacterRegistry,
    CharacterRole,
    DialogueLine,
    Scene,
    SceneDescription,
    SceneDescriptionCollection,
    Script,
)
from ai_movie_gen_suite.pipeline.orchestrator import MovieGenerationPipeline, PipelineConfig
from ai_movie_gen_suite.stages.beat_generator import BeatGenerator
from ai_movie_gen_suite.stages.character_generator import CharacterGenerator
from ai_movie_gen_suite.stages.script_writer import ScriptWriter
from ai_movie_gen_suite.stages.scene_description_engine import SceneDescriptionEngine


class TestBeatSheet(unittest.TestCase):
    """Test BeatSheet model."""

    def test_add_beat(self):
        beat_sheet = BeatSheet(logline="Test logline", genre="Drama")
        beat = Beat(beat_name="Test Beat", beat_number=1, summary="Test summary")
        beat_sheet.add_beat(beat)
        self.assertEqual(len(beat_sheet.beats), 1)
        self.assertEqual(beat_sheet.beats[0].beat_name, "Test Beat")

    def test_model_dump(self):
        beat_sheet = BeatSheet(logline="Test logline", genre="Drama")
        beat = Beat(beat_name="Test Beat", beat_number=1, summary="Test summary")
        beat_sheet.add_beat(beat)
        data = beat_sheet.model_dump()
        self.assertEqual(data["logline"], "Test logline")
        self.assertEqual(data["genre"], "Drama")
        self.assertEqual(len(data["beats"]), 1)


class TestCharacterRegistry(unittest.TestCase):
    """Test CharacterRegistry model."""

    def test_add_character(self):
        registry = CharacterRegistry()
        char = Character(name="Test", role=CharacterRole.PROTAGONIST)
        registry.add_character(char)
        self.assertEqual(len(registry.characters), 1)
        self.assertEqual(registry.characters[0].name, "Test")

    def test_model_dump(self):
        registry = CharacterRegistry()
        char = Character(name="Test", role=CharacterRole.PROTAGONIST)
        registry.add_character(char)
        data = registry.model_dump()
        self.assertEqual(len(data["characters"]), 1)


class TestScript(unittest.TestCase):
    """Test Script model."""

    def test_add_scene(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        scene = Scene(scene_id="SC-001", scene_heading="INT. TEST - DAY", action="Test action")
        script.add_scene(scene)
        self.assertEqual(len(script.scenes), 1)
        self.assertEqual(script.scenes[0].scene_id, "SC-001")

    def test_model_dump(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        scene = Scene(scene_id="SC-001", scene_heading="INT. TEST - DAY", action="Test action")
        script.add_scene(scene)
        data = script.model_dump()
        self.assertEqual(data["title"], "Test")
        self.assertEqual(len(data["scenes"]), 1)


class TestSceneDescriptionCollection(unittest.TestCase):
    """Test SceneDescriptionCollection model."""

    def test_add_description(self):
        collection = SceneDescriptionCollection()
        desc = SceneDescription(scene_id="SC-001", setting="INT. TEST - DAY", mood="bright")
        collection.add_description("SC-001", desc)
        self.assertEqual(len(collection.descriptions), 1)

    def test_get_description(self):
        collection = SceneDescriptionCollection()
        desc = SceneDescription(scene_id="SC-001", setting="INT. TEST - DAY", mood="bright")
        collection.add_description("SC-001", desc)
        retrieved = collection.get_description("SC-001")
        self.assertEqual(retrieved.mood, "bright")

    def test_get_missing_description(self):
        collection = SceneDescriptionCollection()
        retrieved = collection.get_description("SC-999")
        self.assertIsNone(retrieved)


class TestBeatGenerator(unittest.TestCase):
    """Test BeatGenerator stage."""

    def test_generate_beat_sheet(self):
        generator = BeatGenerator(logline="Test logline", genre="Drama")
        beat_sheet = generator.generate_beat_sheet()
        self.assertEqual(len(beat_sheet.beats), 15)  # Save-the-Cat has 15 beats
        self.assertEqual(beat_sheet.beats[0].beat_name, "Opening Image")
        self.assertEqual(beat_sheet.beats[-1].beat_name, "Final Image")

    def test_phase_assignment(self):
        generator = BeatGenerator(logline="Test logline", genre="Drama")
        beat_sheet = generator.generate_beat_sheet()
        phases = [b.phase for b in beat_sheet.beats if b.phase]
        self.assertTrue(any(p == BeatPhase.SETUP for p in phases))
        self.assertTrue(any(p == BeatPhase.CONFRONTATION for p in phases))
        self.assertTrue(any(p == BeatPhase.RESOLUTION for p in phases))


class TestCharacterGenerator(unittest.TestCase):
    """Test CharacterGenerator stage."""

    def test_generate_characters(self):
        generator = CharacterGenerator(logline="Test logline", genre="Drama")
        registry = generator.generate_characters()
        self.assertEqual(len(registry.characters), 5)
        roles = [c.role for c in registry.characters]
        self.assertIn(CharacterRole.PROTAGONIST, roles)
        self.assertIn(CharacterRole.ANTAGONIST, roles)


class TestScriptWriter(unittest.TestCase):
    """Test ScriptWriter stage."""

    def test_write_script(self):
        beat_sheet = BeatGenerator(logline="Test logline", genre="Drama").generate_beat_sheet()
        characters = CharacterGenerator(logline="Test logline", genre="Drama").generate_characters()
        writer = ScriptWriter(
            title="Test",
            logline="Test logline",
            genre="Drama",
            beat_sheet=beat_sheet,
            character_registry=characters,
        )
        script = writer.write_script()
        self.assertEqual(len(script.scenes), 15)
        self.assertEqual(script.title, "Test")

    def test_scene_count_matches_beats(self):
        beat_sheet = BeatGenerator(logline="Test logline", genre="Drama").generate_beat_sheet()
        characters = CharacterGenerator(logline="Test logline", genre="Drama").generate_characters()
        writer = ScriptWriter(
            title="Test",
            logline="Test logline",
            genre="Drama",
            beat_sheet=beat_sheet,
            character_registry=characters,
        )
        script = writer.write_script()
        self.assertEqual(len(script.scenes), len(beat_sheet.beats))


class TestSceneDescriptionEngine(unittest.TestCase):
    """Test SceneDescriptionEngine stage."""

    def test_generate_descriptions(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        script.add_scene(Scene(scene_id="SC-001", scene_heading="INT. TEST - DAY", action="Test action"))
        engine = SceneDescriptionEngine(script=script)
        collection = engine.generate_descriptions()
        self.assertEqual(len(collection.descriptions), 1)
        desc = collection.get_description("SC-001")
        self.assertIsNotNone(desc)
        self.assertIn("bright", desc.mood)


class TestJSONFormatter(unittest.TestCase):
    """Test JSONFormatter."""

    def test_format(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        script.add_scene(Scene(scene_id="SC-001", scene_heading="INT. TEST - DAY", action="Test action"))
        formatter = JSONFormatter(script=script)
        data = formatter.format()
        self.assertIn("script", data)
        self.assertEqual(data["script"]["title"], "Test")

    def test_format_string(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        formatter = JSONFormatter(script=script)
        json_str = formatter.format_string()
        data = json.loads(json_str)
        self.assertIn("script", data)

    def test_save(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        formatter = JSONFormatter(script=script)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        try:
            formatter.save(filepath)
            self.assertTrue(os.path.exists(filepath))
            with open(filepath) as f:
                data = json.load(f)
            self.assertIn("script", data)
        finally:
            os.unlink(filepath)


class TestYAMLFormatter(unittest.TestCase):
    """Test YAMLFormatter."""

    def test_format(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        formatter = YAMLFormatter(script=script)
        yaml_str = formatter.format()
        self.assertIn("script", yaml_str)
        self.assertIn("title", yaml_str)


class TestFDXFormatter(unittest.TestCase):
    """Test FDXFormatter."""

    def test_format(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        script.add_scene(Scene(scene_id="SC-001", scene_heading="INT. TEST - DAY", action="Test action"))
        formatter = FDXFormatter(script=script)
        xml_str = formatter.format()
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, "FinalDraft")
        doc = root.find("Document")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.get("Title"), "Test")

    def test_save(self):
        script = Script(title="Test", logline="Test logline", genre="Drama")
        formatter = FDXFormatter(script=script)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fdx", delete=False) as f:
            filepath = f.name
        try:
            formatter.save(filepath)
            self.assertTrue(os.path.exists(filepath))
            with open(filepath) as f:
                content = f.read()
            self.assertIn("FinalDraft", content)
        finally:
            os.unlink(filepath)


class TestPipeline(unittest.TestCase):
    """Test MovieGenerationPipeline."""

    def test_run_pipeline(self):
        config = PipelineConfig(
            logline="Test logline",
            title="Test Movie",
            genre="Drama",
            output_format="json",
            output_dir=tempfile.gettempdir(),
        )
        pipeline = MovieGenerationPipeline(config)
        results = pipeline.run()

        self.assertIsNotNone(pipeline.beat_sheet)
        self.assertIsNotNone(pipeline.character_registry)
        self.assertIsNotNone(pipeline.script)
        self.assertIsNotNone(pipeline.scene_descriptions)
        self.assertIn("output_path", results)
        self.assertTrue(os.path.exists(results["output_path"]))

    def test_run_pipeline_fdx(self):
        config = PipelineConfig(
            logline="Test logline",
            title="Test Movie",
            genre="Drama",
            output_format="fdx",
            output_dir=tempfile.gettempdir(),
        )
        pipeline = MovieGenerationPipeline(config)
        results = pipeline.run()

        self.assertTrue(results["output_path"].endswith(".fdx"))
        self.assertTrue(os.path.exists(results["output_path"]))

    def test_get_results(self):
        config = PipelineConfig(
            logline="Test logline",
            title="Test Movie",
            genre="Drama",
            output_format="json",
            output_dir=tempfile.gettempdir(),
        )
        pipeline = MovieGenerationPipeline(config)
        pipeline.run()
        results = pipeline.get_results()
        self.assertIn("beat_sheet", results)
        self.assertIn("characters", results)
        self.assertIn("script", results)


if __name__ == "__main__":
    unittest.main()
