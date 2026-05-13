"""Tests for pipeline orchestrator."""

import tempfile
from pathlib import Path

import pytest
from ai_movie_gen_suite.pipeline.orchestrator import MovieGenerationPipeline, PipelineConfig


class TestPipelineConfig:
    def test_default_config(self):
        config = PipelineConfig(
            logline="A test logline.",
            title="Test Title",
            genre="drama",
        )
        assert config.logline == "A test logline."
        assert config.title == "Test Title"
        assert config.genre == "drama"
        assert config.tone == ""
        assert config.output_format == "json"
        assert config.use_llm is False

    def test_config_with_all_options(self):
        config = PipelineConfig(
            logline="A test logline.",
            title="Test Title",
            genre="action",
            tone="dark",
            output_format="yaml",
            output_dir="/tmp/test",
            use_llm=True,
        )
        assert config.tone == "dark"
        assert config.output_format == "yaml"
        assert config.output_dir == "/tmp/test"
        assert config.use_llm is True


class TestMovieGenerationPipeline:
    def test_pipeline_runs(self):
        config = PipelineConfig(
            logline="A hero saves the world.",
            title="Test Script",
            genre="action",
            output_dir=tempfile.mkdtemp(),
        )
        pipeline = MovieGenerationPipeline(config)
        results = pipeline.run()

        assert results is not None
        assert "beat_sheet" in results
        assert "characters" in results
        assert "script" in results
        assert "scene_descriptions" in results

    def test_pipeline_creates_output_files(self):
        output_dir = tempfile.mkdtemp()
        config = PipelineConfig(
            logline="A hero saves the world.",
            title="Test Script",
            genre="action",
            output_format="json",
            output_dir=output_dir,
        )
        pipeline = MovieGenerationPipeline(config)
        results = pipeline.run()

        # Check that output file was created
        output_file = Path(output_dir) / "test_script.json"
        assert output_file.exists()

    def test_pipeline_with_yaml_format(self):
        output_dir = tempfile.mkdtemp()
        config = PipelineConfig(
            logline="A hero saves the world.",
            title="Test Script",
            genre="action",
            output_format="yaml",
            output_dir=output_dir,
        )
        pipeline = MovieGenerationPipeline(config)
        results = pipeline.run()

        output_file = Path(output_dir) / "test_script.yaml"
        assert output_file.exists()

    def test_pipeline_with_fdx_format(self):
        output_dir = tempfile.mkdtemp()
        config = PipelineConfig(
            logline="A hero saves the world.",
            title="Test Script",
            genre="action",
            output_format="fdx",
            output_dir=output_dir,
        )
        pipeline = MovieGenerationPipeline(config)
        results = pipeline.run()

        output_file = Path(output_dir) / "test_script.fdx"
        assert output_file.exists()

    def test_pipeline_stages_run_in_order(self):
        config = PipelineConfig(
            logline="A hero saves the world.",
            title="Test Script",
            genre="action",
            output_dir=tempfile.mkdtemp(),
        )
        pipeline = MovieGenerationPipeline(config)
        results = pipeline.run()

        # Verify that each stage produced output
        assert results["beat_sheet"] is not None
        assert len(results["beat_sheet"]["beats"]) > 0

        assert results["characters"] is not None
        assert len(results["characters"]["characters"]) > 0

        assert results["script"] is not None
        assert len(results["script"].scenes) > 0

        assert results["scene_descriptions"] is not None
        assert len(results["scene_descriptions"].descriptions) > 0
