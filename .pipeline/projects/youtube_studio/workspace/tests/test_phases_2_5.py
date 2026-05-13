"""
Tests for phases 2-5 of YouTube Studio.

Phase 2: Transcript import + search
Phase 3: Story generator
Phase 4: Template versioning + A/B testing
Phase 5: Production pipeline + project management
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure workspace root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcript_builder import TranscriptBuilder
from transcript_importer import TranscriptImporter
from story_generator import StoryGenerator, VideoFormat, StoryTone
from template_versioning import TemplateVersionManager
from production_pipeline import (
    ProductionPipeline, ProjectManager, ProjectStatus, VideoProject,
)


# ═══════════════════════════════════════════════════════════════════
# Phase 2 — Transcript Import & Search
# ═══════════════════════════════════════════════════════════════════

class TestTranscriptImporter:
    def test_import_srt(self, tmp_path):
        srt = (
            "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"
            "2\n00:00:05,000 --> 00:00:10,000\nSecond line.\n"
        )
        f = tmp_path / "test.srt"
        f.write_text(srt, encoding="utf-8")
        builder = TranscriptImporter.import_file(str(f))
        sections = builder.get_sections()
        assert len(sections) == 2
        assert sections[0].content == "Hello world."
        assert sections[0].start_time == 0.0
        assert sections[0].end_time == 5.0

    def test_import_vtt(self, tmp_path):
        vtt = "WEBVTT\n\n00:00:00.000 --> 00:00:03.500\nFirst cue.\n\n00:00:04.000 --> 00:00:08.000\nSecond cue.\n"
        f = tmp_path / "test.vtt"
        f.write_text(vtt, encoding="utf-8")
        builder = TranscriptImporter.import_file(str(f))
        sections = builder.get_sections()
        assert len(sections) == 2
        assert sections[1].content == "Second cue."

    def test_import_json(self, tmp_path):
        data = {"title": "My Video", "sections": [
            {"title": "Intro", "content": "Welcome!", "start_time": 0, "end_time": 5},
            {"title": "Body", "content": "Main content here.", "start_time": 5, "end_time": 20},
        ]}
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        builder = TranscriptImporter.import_file(str(f))
        assert builder.title == "My Video"
        assert len(builder.get_sections()) == 2

    def test_import_txt(self, tmp_path):
        txt = "First paragraph of text.\n\nSecond paragraph of text.\n\nThird paragraph."
        f = tmp_path / "test.txt"
        f.write_text(txt, encoding="utf-8")
        builder = TranscriptImporter.import_file(str(f))
        assert len(builder.get_sections()) == 3

    def test_import_unsupported_format(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("whatever", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported"):
            TranscriptImporter.import_file(str(f))

    def test_import_missing_file(self):
        with pytest.raises(FileNotFoundError):
            TranscriptImporter.import_file("/nonexistent/file.srt")

    def test_search_case_insensitive(self):
        builder = TranscriptBuilder(title="Test")
        builder.add_section("S1", "The quick brown fox jumps over.")
        builder.add_section("S2", "Another section with no match.")
        builder.add_section("S3", "The FOX appears again here.")
        results = TranscriptImporter.search(builder, "fox")
        assert len(results) == 2
        assert results[0]["section_index"] == 0
        assert results[1]["section_index"] == 2

    def test_search_case_sensitive(self):
        builder = TranscriptBuilder(title="Test")
        builder.add_section("S1", "The FOX is here.")
        builder.add_section("S2", "the fox is here.")
        results = TranscriptImporter.search(builder, "FOX", case_sensitive=True)
        assert len(results) == 1

    def test_roundtrip_srt(self, tmp_path):
        builder = TranscriptBuilder(title="RT")
        builder.add_section("A", "First.", start_time=0, end_time=5)
        builder.add_section("B", "Second.", start_time=5, end_time=10)
        srt_path = str(tmp_path / "rt.srt")
        builder.export_to_srt(srt_path)
        reimported = TranscriptImporter.import_file(srt_path)
        assert len(reimported.get_sections()) == 2


# ═══════════════════════════════════════════════════════════════════
# Phase 3 — Story Generator
# ═══════════════════════════════════════════════════════════════════

class TestStoryGenerator:
    def test_generate_short_form(self):
        gen = StoryGenerator()
        story = gen.generate("AI in healthcare", format=VideoFormat.SHORT_FORM)
        assert story.format == VideoFormat.SHORT_FORM
        assert len(story.beats) == 4  # Hook, Problem, Payoff, CTA
        assert story.title
        assert story.logline

    def test_generate_long_form(self):
        gen = StoryGenerator()
        story = gen.generate("Climate change", format=VideoFormat.LONG_FORM, tone=StoryTone.EDUCATIONAL)
        assert len(story.beats) == 10
        assert story.tone == StoryTone.EDUCATIONAL

    def test_generate_save_the_cat(self):
        gen = StoryGenerator()
        story = gen.generate("A detective's journey", format=VideoFormat.SAVE_THE_CAT, tone=StoryTone.DRAMATIC)
        assert len(story.beats) == 15
        beat_names = [b.name for b in story.beats]
        assert "Opening Image" in beat_names
        assert "Finale" in beat_names

    def test_generate_commercial(self):
        gen = StoryGenerator()
        story = gen.generate("Our new product", format=VideoFormat.COMMERCIAL)
        assert len(story.beats) == 5

    def test_generate_movie_outline(self):
        gen = StoryGenerator()
        story = gen.generate("Space exploration", format=VideoFormat.MOVIE_OUTLINE)
        assert len(story.beats) == 8
        assert "90-120 minutes" in story.estimated_duration

    def test_full_script_generated(self):
        gen = StoryGenerator()
        story = gen.generate("Cooking tutorial")
        assert story.full_script
        assert "===" in story.full_script

    def test_to_json(self):
        gen = StoryGenerator()
        story = gen.generate("Test topic", format=VideoFormat.SHORT_FORM)
        j = story.to_json()
        data = json.loads(j)
        assert data["format"] == "short_form"
        assert len(data["beats"]) == 4

    def test_list_formats(self):
        gen = StoryGenerator()
        formats = gen.list_formats()
        assert len(formats) == 5
        names = [f["format"] for f in formats]
        assert "save_the_cat" in names


# ═══════════════════════════════════════════════════════════════════
# Phase 4 — Template Versioning & A/B Testing
# ═══════════════════════════════════════════════════════════════════

class TestTemplateVersioning:
    def test_create_and_get(self):
        mgr = TemplateVersionManager()
        v = mgr.create_template("intro", {"text": "Hello {name}"})
        assert v.version == 1
        latest = mgr.get_latest("intro")
        assert latest["text"] == "Hello {name}"

    def test_save_new_version(self):
        mgr = TemplateVersionManager()
        mgr.create_template("intro", {"text": "v1"})
        v2 = mgr.save_version("intro", {"text": "v2"}, changelog="Updated greeting")
        assert v2.version == 2
        assert mgr.get_latest("intro")["text"] == "v2"

    def test_get_specific_version(self):
        mgr = TemplateVersionManager()
        mgr.create_template("t", {"v": 1})
        mgr.save_version("t", {"v": 2})
        mgr.save_version("t", {"v": 3})
        v1 = mgr.get_version("t", 1)
        assert v1.content["v"] == 1

    def test_version_history(self):
        mgr = TemplateVersionManager()
        mgr.create_template("t", {"v": 1})
        mgr.save_version("t", {"v": 2})
        history = mgr.get_history("t")
        assert len(history) == 2
        assert history[0]["version"] == 1

    def test_rollback(self):
        mgr = TemplateVersionManager()
        mgr.create_template("t", {"v": 1})
        mgr.save_version("t", {"v": 2})
        rb = mgr.rollback("t", 1)
        assert rb.version == 3
        assert mgr.get_latest("t")["v"] == 1

    def test_delete_template(self):
        mgr = TemplateVersionManager()
        mgr.create_template("t", {"v": 1})
        assert mgr.delete_template("t")
        assert mgr.get_latest("t") is None

    def test_list_templates(self):
        mgr = TemplateVersionManager()
        mgr.create_template("a", {})
        mgr.create_template("b", {})
        listing = mgr.list_templates()
        assert len(listing) == 2

    def test_persistence(self, tmp_path):
        mgr = TemplateVersionManager(storage_dir=str(tmp_path))
        mgr.create_template("persist_test", {"hello": "world"})
        mgr.save_version("persist_test", {"hello": "v2"})
        # Create new manager from same dir
        mgr2 = TemplateVersionManager(storage_dir=str(tmp_path))
        assert mgr2.get_latest("persist_test")["hello"] == "v2"
        assert len(mgr2.get_history("persist_test")) == 2

    def test_ab_test(self):
        mgr = TemplateVersionManager()
        mgr.create_template("t", {"v": 1})
        mgr.save_version("t", {"v": 2})
        test = mgr.create_ab_test("t", 1, 2)
        assert test.version_a == 1
        result = mgr.record_ab_result(0, winner=2, metrics={"ctr": 0.15})
        assert result.winner == 2

    def test_duplicate_create_raises(self):
        mgr = TemplateVersionManager()
        mgr.create_template("t", {})
        with pytest.raises(ValueError):
            mgr.create_template("t", {})


# ═══════════════════════════════════════════════════════════════════
# Phase 5 — Production Pipeline & Project Management
# ═══════════════════════════════════════════════════════════════════

class TestProductionPipeline:
    def test_full_pipeline(self):
        pipeline = ProductionPipeline()
        project = pipeline.produce("How to learn Python", format=VideoFormat.LONG_FORM)
        assert project.title
        assert project.story is not None
        assert len(project.keywords) >= 5
        assert project.quality_report is not None
        assert project.quality_report.score > 0

    def test_pipeline_short_form(self):
        pipeline = ProductionPipeline()
        project = pipeline.produce("Quick cooking tip", format=VideoFormat.SHORT_FORM)
        assert project.format == VideoFormat.SHORT_FORM
        assert project.story.format == VideoFormat.SHORT_FORM

    def test_quality_check_passes(self):
        pipeline = ProductionPipeline()
        gen = StoryGenerator()
        story = gen.generate("test", format=VideoFormat.LONG_FORM)
        qr = pipeline.quality_check(
            title="A Good Title For Testing",
            keywords=["python", "coding", "tutorial", "learn", "beginner"],
            story=story,
            transcript_sections=5,
        )
        assert qr.passed
        assert qr.score >= 60

    def test_quality_check_fails_short_title(self):
        pipeline = ProductionPipeline()
        gen = StoryGenerator()
        story = gen.generate("test")
        qr = pipeline.quality_check(
            title="Hi",  # Too short
            keywords=["a"],  # Too few
            story=story,
            transcript_sections=1,
        )
        assert len(qr.issues) > 0

    def test_export_project(self, tmp_path):
        pipeline = ProductionPipeline()
        project = pipeline.produce("Export test topic")
        path = pipeline.export_project(project, str(tmp_path))
        assert Path(path).exists()
        assert (tmp_path / f"{project.id}.srt").exists()
        assert (tmp_path / f"{project.id}.vtt").exists()
        assert project.status == ProjectStatus.EXPORTED


class TestProjectManager:
    def test_add_and_get(self):
        mgr = ProjectManager()
        proj = VideoProject(id="p1", title="Test", topic="Testing")
        mgr.add_project(proj)
        assert mgr.get_project("p1") is not None

    def test_list_projects(self):
        mgr = ProjectManager()
        mgr.add_project(VideoProject(id="p1", title="A", topic="a"))
        mgr.add_project(VideoProject(id="p2", title="B", topic="b"))
        listing = mgr.list_projects()
        assert len(listing) == 2

    def test_filter_by_status(self):
        mgr = ProjectManager()
        mgr.add_project(VideoProject(id="p1", title="A", topic="a", status=ProjectStatus.DRAFT))
        mgr.add_project(VideoProject(id="p2", title="B", topic="b", status=ProjectStatus.EXPORTED))
        drafts = mgr.list_projects(status=ProjectStatus.DRAFT)
        assert len(drafts) == 1

    def test_update_status(self):
        mgr = ProjectManager()
        mgr.add_project(VideoProject(id="p1", title="A", topic="a"))
        assert mgr.update_status("p1", ProjectStatus.APPROVED)
        assert mgr.get_project("p1").status == ProjectStatus.APPROVED

    def test_delete_project(self):
        mgr = ProjectManager()
        mgr.add_project(VideoProject(id="p1", title="A", topic="a"))
        assert mgr.delete_project("p1")
        assert mgr.get_project("p1") is None
