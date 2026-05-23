"""Tests for video pipeline module (Phase 3)."""

import json
import tempfile
from pathlib import Path

import pytest

from video_recipe_mu.video_pipeline import (
    PipelineConfig,
    PipelineResult,
    _extract_key_frames,
    _run_video_scribe,
    run_pipeline,
    save_pipeline_result,
)


class TestExtractKeyFrames:
    """Tests for _extract_key_frames."""

    def test_synthetic_key_frames(self):
        """When no video is available, should return synthetic frames."""
        # Create a dummy file to test the fallback path
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            dummy_path = f.name

        try:
            frames = _extract_key_frames(dummy_path, num_frames=3)
            assert len(frames) == 3
            assert frames[0].frame_index == 0
            assert frames[0].timestamp_s == 0.0
        finally:
            Path(dummy_path).unlink()

    def test_synthetic_frame_count(self):
        """Should return exactly num_frames synthetic frames."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            dummy_path = f.name

        try:
            frames = _extract_key_frames(dummy_path, num_frames=10)
            assert len(frames) == 10
        finally:
            Path(dummy_path).unlink()


class TestRunVideoScribe:
    """Tests for _run_video_scribe."""

    def test_returns_valid_json(self):
        """Should return valid JSON string."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            dummy_path = f.name

        try:
            result = _run_video_scribe(dummy_path)
            data = json.loads(result)
            assert "scenes" in data
            assert len(data["scenes"]) > 0
        finally:
            Path(dummy_path).unlink()


class TestRunPipeline:
    """Tests for run_pipeline."""

    def test_pipeline_returns_result(self):
        """Pipeline should return a PipelineResult."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            dummy_path = f.name

        try:
            result = run_pipeline(dummy_path)
            assert isinstance(result, PipelineResult)
            assert isinstance(result.steps, list)
            assert result.scene_count > 0
            assert result.key_frame_count > 0
        finally:
            Path(dummy_path).unlink()

    def test_pipeline_with_spatial_grounding(self):
        """Pipeline should produce grounding results when enabled."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            dummy_path = f.name

        try:
            config = PipelineConfig(use_spatial_grounding=True)
            result = run_pipeline(dummy_path, config)
            assert result.grounding_results is not None
            assert len(result.grounding_results) > 0
        finally:
            Path(dummy_path).unlink()

    def test_pipeline_with_validation(self):
        """Pipeline should produce validation errors when enabled."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy")
            dummy_path = f.name

        try:
            config = PipelineConfig(validate=True)
            result = run_pipeline(dummy_path, config)
            assert result.validation_errors is not None
        finally:
            Path(dummy_path).unlink()


class TestSavePipelineResult:
    """Tests for save_pipeline_result."""

    def test_saves_to_file(self):
        """Should save result to a JSON file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        result = PipelineResult(
            steps=[{"step": 1, "description": "test"}],
            scene_count=1,
            key_frame_count=5,
        )
        save_pipeline_result(result, output_path)

        assert Path(output_path).exists()
        with open(output_path) as f:
            data = json.load(f)
        assert "steps" in data
        assert data["scene_count"] == 1
        assert data["key_frame_count"] == 5


class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = PipelineConfig()
        assert config.provider == "openai"
        assert config.llm_model == "gpt-4o"
        assert config.multi_scene is False
        assert config.use_spatial_grounding is False
        assert config.validate is False
        assert config.normalize is False


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_result_creation(self):
        """Should create a valid result."""
        result = PipelineResult(
            steps=[{"step": 1}],
            scene_count=3,
            key_frame_count=5,
        )
        assert result.steps == [{"step": 1}]
        assert result.scene_count == 3
        assert result.key_frame_count == 5
        assert result.grounding_results is None
        assert result.validation_errors is None
