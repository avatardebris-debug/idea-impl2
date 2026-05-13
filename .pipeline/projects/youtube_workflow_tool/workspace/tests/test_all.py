"""Tests for the YouTube Workflow Tool."""

import pytest
import json
import os
from pathlib import Path

from youtube_workflow_tool.config import Config, DEFAULT_CONFIG
from youtube_workflow_tool.templates import Template, TemplateEngine, BUILTIN_TEMPLATES
from youtube_workflow_tool.metadata_generator import Metadata, generate_metadata, _extract_keywords, _expand_keywords
from youtube_workflow_tool.optimizer import (
    ScoreResult, evaluate_metadata, ctr_prediction, keyword_density_report,
    _score_title, _score_description, _score_tags, _score_hashtags
)
from youtube_workflow_tool.cli import cli, _load_config


class TestConfig:
    """Tests for the Config class."""

    def test_default_config(self):
        """Test that default config has correct values."""
        config = Config()
        assert config.min_tags == 5
        assert config.min_hashtags == 3
        assert config.max_tags == 15
        assert config.max_hashtags == 10
        assert config.min_title_length == 10
        assert config.max_title_length == 100
        assert config.min_description_length == 100
        assert config.default_niche == "general"
        assert config.default_tone == "informative"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {"min_tags": 10, "max_tags": 20}
        config = Config.from_dict(data)
        assert config.min_tags == 10
        assert config.max_tags == 20
        assert config.default_niche == "general"  # default preserved

    def test_config_to_dict(self):
        """Test serializing config to dictionary."""
        config = Config(min_tags=10, max_tags=20)
        data = config.to_dict()
        assert data["min_tags"] == 10
        assert data["max_tags"] == 20

    def test_config_from_file(self, tmp_path):
        """Test loading config from file."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"min_tags": 10}))
        
        config = Config.from_file(str(config_path))
        assert config.min_tags == 10

    def test_config_load_method(self, tmp_path):
        """Test the load class method."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"min_tags": 10}))
        
        config = Config.load(str(config_path))
        assert config.min_tags == 10

    def test_config_from_env(self, monkeypatch):
        """Test loading config from environment variables."""
        monkeypatch.setenv("YW_MIN_TAGS", "10")
        monkeypatch.setenv("YW_MAX_TAGS", "20")
        
        config = Config.from_env()
        assert config.min_tags == 10
        assert config.max_tags == 20


class TestTemplates:
    """Tests for the Template and TemplateEngine classes."""

    def test_template_creation(self):
        """Test creating a template."""
        template = Template(
            name="test_template",
            category="tutorial",
            pattern="How to {topic} in 2024",
        )
        assert template.name == "test_template"
        assert template.category == "tutorial"
        assert template.pattern == "How to {topic} in 2024"

    def test_template_rendering(self):
        """Test rendering a template with variables."""
        template = Template(
            name="test",
            category="tutorial",
            pattern="How to {topic} in {year}",
        )
        
        rendered = template.fill_in(topic="Python", year="2024")
        assert "Python" in rendered
        assert "2024" in rendered

    def test_template_engine_initialization(self):
        """Test that engine loads built-in templates."""
        engine = TemplateEngine()
        assert len(engine.templates) > 0  # built-in templates loaded
        assert "tutorial" in engine.get_categories()

    def test_template_engine_get_categories(self):
        """Test listing categories."""
        engine = TemplateEngine()
        categories = engine.get_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0

    def test_template_engine_generate_titles(self):
        """Test generating titles from templates."""
        engine = TemplateEngine()
        titles = engine.generate_titles(
            topic="Python",
            categories=["tutorial"],
        )
        
        assert len(titles) >= 1
        assert all(isinstance(t, str) for t in titles)
        assert "Python" in titles[0]

    def test_template_engine_generate_titles_limit(self):
        """Test that we get limited titles."""
        engine = TemplateEngine()
        titles = engine.generate_titles(
            topic="Test",
            categories=["tutorial"],
        )
        # The engine returns all matching templates, so we check it's reasonable
        assert len(titles) >= 1
        assert len(titles) <= 10


class TestMetadataGenerator:
    """Tests for the metadata generator."""

    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "This is a test about Python programming and coding"
        keywords = _extract_keywords(text)
        assert "python" in keywords
        assert "programming" in keywords
        assert "coding" in keywords
        assert "this" not in keywords  # stop word

    def test_expand_keywords(self):
        """Test keyword expansion."""
        keywords = ["python", "coding"]
        topic = "Python programming tutorial"
        expanded = _expand_keywords(keywords, topic)
        
        assert "python" in expanded
        assert "coding" in expanded
        assert "tutorial" in expanded  # from extras

    def test_generate_metadata_basic(self):
        """Test basic metadata generation."""
        metadata = generate_metadata(
            topic="Python Programming",
            niche="tech",
            tone="informative",
        )
        
        assert isinstance(metadata, Metadata)
        assert len(metadata.titles) >= 5
        assert len(metadata.tags) >= 5
        assert len(metadata.hashtags) >= 3
        assert "Python" in metadata.topic

    def test_generate_metadata_with_config(self, tmp_path):
        """Test metadata generation with custom config."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({
            "min_tags": 10,
            "max_tags": 20,
            "min_hashtags": 5,
            "max_hashtags": 15,
        }))
        
        config = Config.from_file(str(config_path))
        metadata = generate_metadata(
            topic="Test Topic",
            niche="general",
            tone="informative",
            config=config,
        )
        
        assert len(metadata.tags) >= 10
        assert len(metadata.hashtags) >= 5

    def test_metadata_serialization(self):
        """Test metadata serialization."""
        metadata = generate_metadata(
            topic="Test",
            niche="general",
            tone="informative",
        )
        
        data = metadata.to_dict()
        assert "titles" in data
        assert "description" in data
        assert "tags" in data
        assert "hashtags" in data
        
        restored = Metadata.from_dict(data)
        assert restored.topic == metadata.topic
        assert len(restored.titles) == len(metadata.titles)


class TestOptimizer:
    """Tests for the optimizer module."""

    def test_ctr_prediction_basic(self):
        """Test CTR prediction with known patterns."""
        # High CTR pattern
        score = ctr_prediction("How to Python in 10 Minutes")
        assert score > 0.1
        
        # Low CTR pattern
        score = ctr_prediction("Random Title")
        assert score < 0.1

    def test_ctr_prediction_patterns(self):
        """Test specific CTR patterns."""
        patterns = [
            ("How to learn Python", 0.15),
            ("Ultimate Guide to Python", 0.12),
            ("Top 10 Python Tips", 0.10),
            ("Best Python Tutorial", 0.10),
        ]
        
        for title, expected_min in patterns:
            score = ctr_prediction(title)
            assert score >= expected_min, f"Expected >= {expected_min} for '{title}', got {score}"

    def test_ctr_prediction_length_bonus(self):
        """Test that optimal length titles get bonus."""
        # Optimal length (50-70 chars)
        long_title = "A" * 60
        score = ctr_prediction(long_title)
        assert score > 0.02
        
        # Too short
        short_title = "A" * 10
        score_short = ctr_prediction(short_title)
        assert score_short < score

    def test_keyword_density_report(self):
        """Test keyword density analysis."""
        text = "Python Python Python is great. Python programming is fun."
        report = keyword_density_report(text)
        
        assert report.total_words > 0
        assert "python" in report.keyword_density
        assert report.keyword_density["python"] > 0

    def test_score_title(self):
        """Test title scoring."""
        config = Config()
        
        # Good title
        score = _score_title("How to Python in 10 Minutes", config)
        assert score > 30
        
        # Bad title
        score = _score_title("A", config)
        assert score < 30

    def test_score_description(self):
        """Test description scoring."""
        config = Config()
        
        # Good description
        desc = """
        Welcome to this video!
        
        What You'll Learn:
        - Introduction
        - Main content
        
        Don't forget to LIKE and SUBSCRIBE!
        
        #python #tutorial
        """
        score = _score_description(desc, config)
        assert score > 30
        
        # Empty description
        score = _score_description("", config)
        assert score == 0

    def test_score_tags(self):
        """Test tag scoring."""
        # Good tags
        tags = ["python", "programming", "tutorial", "coding", "beginner"]
        score = _score_tags(tags, "Python Programming")
        assert score > 30
        
        # Empty tags
        score = _score_tags([], "Python")
        assert score == 0

    def test_score_hashtags(self):
        """Test hashtag scoring."""
        # Good hashtags
        hashtags = ["#python", "#programming", "#tutorial", "#coding"]
        score = _score_hashtags(hashtags, "Python Programming")
        assert score > 30
        
        # Empty hashtags
        score = _score_hashtags([], "Python")
        assert score == 0

    def test_evaluate_metadata(self):
        """Test full metadata evaluation."""
        metadata = generate_metadata(
            topic="Python Programming",
            niche="tech",
            tone="informative",
        )
        
        result = evaluate_metadata(metadata)
        
        assert isinstance(result, ScoreResult)
        assert 0 <= result.overall_score <= 100
        assert "title" in result.breakdown
        assert "description" in result.breakdown
        assert "tags" in result.breakdown
        assert "hashtags" in result.breakdown
        assert len(result.recommendations) > 0

    def test_score_result_serialization(self):
        """Test ScoreResult serialization."""
        result = ScoreResult(
            overall_score=85.5,
            title_score=90.0,
            description_score=80.0,
            tag_score=85.0,
            hashtag_score=85.0,
            breakdown={"title": 90, "description": 80},
            recommendations=["Test recommendation"],
        )
        
        data = result.to_dict()
        assert data["overall_score"] == 85.5
        assert len(data["recommendations"]) == 1


class TestCLI:
    """Tests for the CLI module."""

    def test_cli_help(self, capsys):
        """Test CLI help output."""
        with pytest.raises(SystemExit):
            cli(["--help"])
        
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    def test_cli_generate_command(self, capsys):
        """Test generate command."""
        with pytest.raises(SystemExit):
            cli(["generate", "Python Programming", "--num-titles", "3", "--format", "json"])
        captured = capsys.readouterr()
        assert "metadata" in captured.out
        assert "score" in captured.out


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self):
        """Test complete metadata generation and evaluation workflow."""
        # Generate metadata
        metadata = generate_metadata(
            topic="Python Programming for Beginners",
            niche="education",
            tone="educational",
        )
        
        # Evaluate metadata
        result = evaluate_metadata(metadata)
        
        # Verify results
        assert len(metadata.titles) >= 5
        assert len(metadata.tags) >= 5
        assert len(metadata.hashtags) >= 3
        assert result.overall_score >= 0
        assert result.overall_score <= 100

    def test_different_niches(self):
        """Test metadata generation for different niches."""
        niches = ["tech", "gaming", "education", "fitness", "cooking"]
        
        for niche in niches:
            metadata = generate_metadata(
                topic="Test Topic",
                niche=niche,
                tone="informative",
            )
            assert len(metadata.titles) >= 5
            assert metadata.niche == niche

    def test_different_tones(self):
        """Test metadata generation for different tones."""
        tones = ["informative", "entertaining", "professional", "casual", "educational"]
        
        for tone in tones:
            metadata = generate_metadata(
                topic="Test Topic",
                niche="general",
                tone=tone,
            )
            assert len(metadata.titles) >= 5
            assert metadata.tone == tone

    def test_metadata_variations(self):
        """Test that generated titles are varied."""
        metadata = generate_metadata(
            topic="Python Programming",
            niche="tech",
            tone="informative",
        )
        
        # Check for variety
        unique_titles = set(metadata.titles)
        assert len(unique_titles) == len(metadata.titles)
        
        # Check that titles are different
        assert len(metadata.titles) >= 5
        for i in range(1, len(metadata.titles)):
            assert metadata.titles[i] != metadata.titles[i-1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
