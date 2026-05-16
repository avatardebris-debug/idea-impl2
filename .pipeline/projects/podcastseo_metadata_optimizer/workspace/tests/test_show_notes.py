"""Tests for show_notes_generator.py."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from podcastseo.show_notes_generator import ShowNotesConfig, ShowNotesGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_keywords():
    return [
        {"keyword": "machine learning", "score": 0.95, "category": "technical", "occurrences": 12},
        {"keyword": "neural networks", "score": 0.88, "category": "technical", "occurrences": 8},
        {"keyword": "deep learning", "score": 0.82, "category": "technical", "occurrences": 6},
        {"keyword": "healthcare AI", "score": 0.75, "category": "health", "occurrences": 5},
        {"keyword": "data privacy", "score": 0.70, "category": "business", "occurrences": 4},
        {"keyword": "cloud computing", "score": 0.65, "category": "technical", "occurrences": 3},
        {"keyword": "startup funding", "score": 0.60, "category": "business", "occurrences": 2},
    ]


@pytest.fixture
def sample_transcript():
    return (
        "Welcome to today's episode. We're going to talk about machine learning "
        "and how it's transforming healthcare. Neural networks are at the heart "
        "of deep learning, which has seen tremendous progress in recent years. "
        "Data privacy remains a critical concern as healthcare AI systems process "
        "sensitive patient information. Cloud computing enables scalable infrastructure "
        "for these models. Meanwhile, startup funding for AI companies has reached "
        "record levels."
    )


@pytest.fixture
def empty_keywords():
    return []


@pytest.fixture
def empty_transcript():
    return ""


@pytest.fixture
def generator():
    return ShowNotesGenerator()


@pytest.fixture
def professional_generator():
    config = ShowNotesConfig(tone="professional", length="medium")
    return ShowNotesGenerator(config)


@pytest.fixture
def casual_generator():
    config = ShowNotesConfig(tone="casual", length="short")
    return ShowNotesGenerator(config)


# ---------------------------------------------------------------------------
# ShowNotesConfig tests
# ---------------------------------------------------------------------------

class TestShowNotesConfig:
    """Tests for the ShowNotesConfig dataclass."""

    def test_default_tone(self):
        config = ShowNotesConfig()
        assert config.tone == "professional"

    def test_default_length(self):
        config = ShowNotesConfig()
        assert config.length == "medium"

    def test_default_section_order(self):
        config = ShowNotesConfig()
        assert config.section_order == [
            "summary",
            "key_takeaways",
            "timestamps",
            "related_topics",
            "cta",
        ]

    def test_default_max_takeaways(self):
        config = ShowNotesConfig()
        assert config.max_takeaways == 5

    def test_default_max_timestamps(self):
        config = ShowNotesConfig()
        assert config.max_timestamps == 10

    def test_default_max_summary_words(self):
        config = ShowNotesConfig()
        assert config.max_summary_words == 150

    def test_custom_tone(self):
        config = ShowNotesConfig(tone="casual")
        assert config.tone == "casual"

    def test_custom_section_order(self):
        config = ShowNotesConfig(section_order=["cta", "summary"])
        assert config.section_order == ["cta", "summary"]

    def test_custom_max_takeaways(self):
        config = ShowNotesConfig(max_takeaways=10)
        assert config.max_takeaways == 10


# ---------------------------------------------------------------------------
# ShowNotesGenerator - generate() tests
# ---------------------------------------------------------------------------

class TestShowNotesGenerate:
    """Tests for the generate() method."""

    def test_generate_returns_string(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert isinstance(result, str)

    def test_generate_markdown_format(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert "## Episode Summary" in result
        assert "## Key Takeaways" in result
        assert "## Timestamps" in result
        assert "## Related Topics" in result
        assert "## Call to Action" in result

    def test_generate_html_format(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="html")
        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "<head>" in result
        assert "<body>" in result
        assert "</html>" in result

    def test_generate_text_format(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="text")
        # Text format uses === as section headers
        assert "EPISODE SUMMARY" in result or "Episode Summary" in result

    def test_generate_unsupported_format_raises(self, generator, sample_keywords, sample_transcript):
        with pytest.raises(ValueError, match="Unsupported format"):
            generator.generate(sample_keywords, sample_transcript, format="xml")

    def test_generate_with_empty_keywords(self, generator, sample_transcript):
        result = generator.generate([], sample_transcript, format="markdown")
        assert isinstance(result, str)
        assert "No key takeaways available" in result

    def test_generate_with_empty_transcript(self, generator, sample_keywords):
        result = generator.generate(sample_keywords, "", format="markdown")
        assert isinstance(result, str)
        assert "No timestamps available" in result

    def test_generate_with_both_empty(self, generator):
        result = generator.generate([], "", format="markdown")
        assert isinstance(result, result)

    def test_generate_includes_top_keywords(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert "machine learning" in result
        assert "neural networks" in result
        assert "deep learning" in result

    def test_generate_includes_scores(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert "0.95" in result
        assert "0.88" in result

    def test_generate_includes_occurrences(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert "12 occurrences" in result
        assert "8 occurrences" in result


# ---------------------------------------------------------------------------
# ShowNotesGenerator - _generate_summary() tests
# ---------------------------------------------------------------------------

class TestShowNotesGenerateSummary:
    """Tests for the _generate_summary() method."""

    def test_summary_contains_keywords(self, generator, sample_keywords, sample_transcript):
        summary = generator._generate_summary(sample_keywords, sample_transcript)
        assert "machine learning" in summary.lower()

    def test_summary_length_respects_config(self):
        config = ShowNotesConfig(max_summary_words=10)
        gen = ShowNotesGenerator(config)
        summary = gen._generate_summary([], "This is a test sentence with some words.")
        words = summary.split()
        assert len(words) <= 10

    def test_summary_with_empty_input(self, generator):
        summary = generator._generate_summary([], "")
        assert summary == "No summary available."

    def test_summary_with_empty_keywords(self, generator, sample_transcript):
        summary = generator._generate_summary([], sample_transcript)
        assert "No summary available." in summary


# ---------------------------------------------------------------------------
# ShowNotesGenerator - _generate_takeaways() tests
# ---------------------------------------------------------------------------

class TestShowNotesGenerateTakeaways:
    """Tests for the _generate_takeaways() method."""

    def test_takeaways_from_keywords(self, generator, sample_keywords, sample_transcript):
        takeaways = generator._generate_takeaways(sample_keywords, sample_transcript)
        assert "machine learning" in takeaways

    def test_takeaways_respects_max_count(self):
        config = ShowNotesConfig(max_takeaways=2)
        gen = ShowNotesGenerator(config)
        takeaways = gen._generate_takeaways(sample_keywords, sample_transcript)
        # Count bullet points
        bullet_count = takeaways.count("-")
        assert bullet_count <= 2

    def test_takeaways_with_empty_keywords(self, generator, sample_transcript):
        takeaways = generator._generate_takeaways([], sample_transcript)
        assert "No key takeaways available" in takeaways

    def test_takeaways_with_empty_transcript(self, generator, sample_keywords):
        takeaways = generator._generate_takeaways(sample_keywords, "")
        assert "No key takeaways available" in takeaways


# ---------------------------------------------------------------------------
# ShowNotesGenerator - _generate_timestamps() tests
# ---------------------------------------------------------------------------

class TestShowNotesGenerateTimestamps:
    """Tests for the _generate_timestamps() method."""

    def test_timestamps_from_transcript(self, generator, sample_transcript):
        timestamps = generator._generate_timestamps(sample_transcript)
        assert "00:00" in timestamps

    def test_timestamps_respects_max_count(self):
        config = ShowNotesConfig(max_timestamps=3)
        gen = ShowNotesGenerator(config)
        timestamps = gen._generate_timestamps(sample_transcript)
        # Count lines that look like timestamps
        lines = [l for l in timestamps.split("\n") if l.strip() and ":" in l]
        assert len(lines) <= 3

    def test_timestamps_with_empty_transcript(self, generator):
        timestamps = generator._generate_timestamps("")
        assert "No timestamps available" in timestamps

    def test_timestamps_format(self, generator, sample_transcript):
        timestamps = generator._generate_timestamps(sample_transcript)
        # Check that timestamps have HH:MM format
        import re
        matches = re.findall(r"\d{2}:\d{2}", timestamps)
        assert len(matches) > 0


# ---------------------------------------------------------------------------
# ShowNotesGenerator - _generate_related_topics() tests
# ---------------------------------------------------------------------------

class TestShowNotesGenerateRelatedTopics:
    """Tests for the _generate_related_topics() method."""

    def test_related_topics_from_keywords(self, generator, sample_keywords, sample_transcript):
        topics = generator._generate_related_topics(sample_keywords, sample_transcript)
        assert "machine learning" in topics

    def test_related_topics_with_empty_keywords(self, generator, sample_transcript):
        topics = generator._generate_related_topics([], sample_transcript)
        assert "No related topics available" in topics

    def test_related_topics_with_empty_transcript(self, generator, sample_keywords):
        topics = generator._generate_related_topics(sample_keywords, "")
        assert "No related topics available" in topics


# ---------------------------------------------------------------------------
# ShowNotesGenerator - _generate_cta() tests
# ---------------------------------------------------------------------------

class TestShowNotesGenerateCTA:
    """Tests for the _generate_cta() method."""

    def test_cta_contains_default_text(self, generator, sample_keywords, sample_transcript):
        cta = generator._generate_cta(sample_keywords, sample_transcript)
        assert "Subscribe" in cta or "follow" in cta.lower()

    def test_cta_with_custom_text(self, generator, sample_keywords, sample_transcript):
        cta = generator._generate_cta(sample_keywords, sample_transcript, custom_cta="Check out our website!")
        assert "Check out our website!" in cta

    def test_cta_with_empty_input(self, generator):
        cta = generator._generate_cta([], "")
        assert "Subscribe" in cta or "follow" in cta.lower()


# ---------------------------------------------------------------------------
# ShowNotesGenerator - _apply_tone() tests
# ---------------------------------------------------------------------------

class TestShowNotesApplyTone:
    """Tests for the _apply_tone() method."""

    def test_professional_tone(self, professional_generator, sample_keywords, sample_transcript):
        result = professional_generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert "machine learning" in result

    def test_casual_tone(self, casual_generator, sample_keywords, sample_transcript):
        result = casual_generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert "machine learning" in result

    def test_tone_affects_language(self, professional_generator, casual_generator, sample_keywords, sample_transcript):
        pro_result = professional_generator.generate(sample_keywords, sample_transcript, format="markdown")
        cas_result = casual_generator.generate(sample_keywords, sample_transcript, format="markdown")
        # The outputs should differ due to tone
        assert pro_result != cas_result


# ---------------------------------------------------------------------------
# ShowNotesGenerator - _apply_length() tests
# ---------------------------------------------------------------------------

class TestShowNotesApplyLength:
    """Tests for the _apply_length() method."""

    def test_short_length(self, casual_generator, sample_keywords, sample_transcript):
        result = casual_generator.generate(sample_keywords, sample_transcript, format="markdown")
        # Short length should have fewer sections or shorter content
        assert len(result) < len(
            ShowNotesGenerator().generate(sample_keywords, sample_transcript, format="markdown")
        )

    def test_medium_length(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert len(result) > 0

    def test_long_length(self, sample_keywords, sample_transcript):
        config = ShowNotesConfig(length="long")
        gen = ShowNotesGenerator(config)
        result = gen.generate(sample_keywords, sample_transcript, format="markdown")
        assert len(result) > len(
            ShowNotesGenerator().generate(sample_keywords, sample_transcript, format="markdown")
        )


# ---------------------------------------------------------------------------
# ShowNotesGenerator - _render_template() tests
# ---------------------------------------------------------------------------

class TestShowNotesRenderTemplate:
    """Tests for the _render_template() method."""

    def test_render_markdown_template(self, generator, sample_keywords, sample_transcript):
        sections = {
            "summary": "Test summary",
            "key_takeaways": "Test takeaways",
            "timestamps": "Test timestamps",
            "related_topics": "Test topics",
            "cta": "Test CTA",
        }
        result = generator._render_template(sections, "markdown")
        assert "## Episode Summary" in result
        assert "Test summary" in result

    def test_render_html_template(self, generator, sample_keywords, sample_transcript):
        sections = {
            "summary": "Test summary",
            "key_takeaways": "Test takeaways",
            "timestamps": "Test timestamps",
            "related_topics": "Test topics",
            "cta": "Test CTA",
        }
        result = generator._render_template(sections, "html")
        assert "<!DOCTYPE html>" in result
        assert "Test summary" in result

    def test_render_text_template(self, generator, sample_keywords, sample_transcript):
        sections = {
            "summary": "Test summary",
            "key_takeaways": "Test takeaways",
            "timestamps": "Test timestamps",
            "related_topics": "Test topics",
            "cta": "Test CTA",
        }
        result = generator._render_template(sections, "text")
        assert "EPISODE SUMMARY" in result
        assert "Test summary" in result

    def test_render_with_partial_sections(self, generator):
        sections = {
            "summary": "Test summary",
        }
        result = generator._render_template(sections, "markdown")
        assert "## Episode Summary" in result
        assert "## Key Takeaways" not in result

    def test_render_with_empty_sections(self, generator):
        sections = {}
        result = generator._render_template(sections, "markdown")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# ShowNotesGenerator - save() tests
# ---------------------------------------------------------------------------

class TestShowNotesSave:
    """Tests for the save() method."""

    def test_save_markdown_file(self, generator, sample_keywords, sample_transcript, tmp_path):
        output_file = tmp_path / "show_notes.md"
        generator.save(
            sample_keywords,
            sample_transcript,
            str(output_file),
            format="markdown",
        )
        assert output_file.exists()
        content = output_file.read_text()
        assert "## Episode Summary" in content

    def test_save_html_file(self, generator, sample_keywords, sample_transcript, tmp_path):
        output_file = tmp_path / "show_notes.html"
        generator.save(
            sample_keywords,
            sample_transcript,
            str(output_file),
            format="html",
        )
        assert output_file.exists()
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content

    def test_save_text_file(self, generator, sample_keywords, sample_transcript, tmp_path):
        output_file = tmp_path / "show_notes.txt"
        generator.save(
            sample_keywords,
            sample_transcript,
            str(output_file),
            format="text",
        )
        assert output_file.exists()
        content = output_file.read_text()
        assert "EPISODE SUMMARY" in content

    def test_save_creates_directory(self, generator, sample_keywords, sample_transcript, tmp_path):
        output_dir = tmp_path / "output" / "subdir"
        output_file = output_dir / "show_notes.md"
        generator.save(
            sample_keywords,
            sample_transcript,
            str(output_file),
            format="markdown",
        )
        assert output_file.exists()

    def test_save_overwrites_existing_file(self, generator, sample_keywords, sample_transcript, tmp_path):
        output_file = tmp_path / "show_notes.md"
        output_file.write_text("old content")
        generator.save(
            sample_keywords,
            sample_transcript,
            str(output_file),
            format="markdown",
        )
        content = output_file.read_text()
        assert "old content" not in content
        assert "## Episode Summary" in content


# ---------------------------------------------------------------------------
# ShowNotesGenerator - Integration tests
# ---------------------------------------------------------------------------

class TestShowNotesIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_markdown(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="markdown")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "## Episode Summary" in result
        assert "## Key Takeaways" in result
        assert "## Timestamps" in result
        assert "## Related Topics" in result
        assert "## Call to Action" in result

    def test_full_pipeline_html(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="html")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "<!DOCTYPE html>" in result
        assert "<h1>" in result
        assert "<h2>" in result

    def test_full_pipeline_text(self, generator, sample_keywords, sample_transcript):
        result = generator.generate(sample_keywords, sample_transcript, format="text")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_save_and_read_back(self, generator, sample_keywords, sample_transcript, tmp_path):
        output_file = tmp_path / "show_notes.md"
        generator.save(
            sample_keywords,
            sample_transcript,
            str(output_file),
            format="markdown",
        )
        content = output_file.read_text()
        assert "machine learning" in content
        assert "neural networks" in content
        assert "deep learning" in content

    def test_different_tones_produce_different_output(self, sample_keywords, sample_transcript):
        pro_gen = ShowNotesGenerator(ShowNotesConfig(tone="professional"))
        cas_gen = ShowNotesGenerator(ShowNotesConfig(tone="casual"))
        pro_result = pro_gen.generate(sample_keywords, sample_transcript, format="markdown")
        cas_result = cas_gen.generate(sample_keywords, sample_transcript, format="markdown")
        assert pro_result != cas_result

    def test_different_lengths_produce_different_output(self, sample_keywords, sample_transcript):
        short_gen = ShowNotesGenerator(ShowNotesConfig(length="short"))
        long_gen = ShowNotesGenerator(ShowNotesConfig(length="long"))
        short_result = short_gen.generate(sample_keywords, sample_transcript, format="markdown")
        long_result = long_gen.generate(sample_keywords, sample_transcript, format="markdown")
        assert len(short_result) < len(long_result)
