"""Tests for the pipeline module — end-to-end video generation."""

import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from videopow.pipeline import generate_video


def _create_test_video(tmp_path, width=640, height=480, frames=10, fps=30, name="test_input.mp4"):
    """Helper to create a test video file."""
    video_path = tmp_path / name
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
    for i in range(frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                frame[y, x] = [
                    int(255 * x / width),
                    int(255 * y / height),
                    int(128 + 127 * np.sin(i * 0.5)),
                ]
        writer.write(frame)
    writer.release()
    return video_path


class TestGenerateVideo:
    """Test the generate_video pipeline function."""

    def test_basic_generation(self, tmp_path):
        """Basic video generation works."""
        video_path = _create_test_video(tmp_path)
        result = generate_video(
            description="grayscale",
            input_video_path=str(video_path),
        )
        assert "output_path" in result
        assert "frames_processed" in result
        assert result["frames_processed"] > 0
        assert result["effect_applied"] == "grayscale"
        assert os.path.exists(result["output_path"])

    def test_empty_description_raises(self, tmp_path):
        """Empty description raises ValueError."""
        video_path = _create_test_video(tmp_path)
        with pytest.raises(ValueError, match="Description cannot be empty"):
            generate_video(
                description="",
                input_video_path=str(video_path),
            )

    def test_whitespace_description_raises(self, tmp_path):
        """Whitespace-only description raises ValueError."""
        video_path = _create_test_video(tmp_path)
        with pytest.raises(ValueError, match="Description cannot be empty"):
            generate_video(
                description="   ",
                input_video_path=str(video_path),
            )

    def test_nonexistent_input_raises(self, tmp_path):
        """Nonexistent input file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            generate_video(
                description="grayscale",
                input_video_path="/nonexistent/video.mp4",
            )

    def test_grayscale_pipeline(self, tmp_path):
        """Grayscale pipeline produces correct output."""
        video_path = _create_test_video(tmp_path)
        result = generate_video(
            description="grayscale",
            input_video_path=str(video_path),
        )
        assert result["effect_applied"] == "grayscale"
        assert result["width"] == 640
        assert result["height"] == 480

    def test_sepia_pipeline(self, tmp_path):
        """Sepia pipeline produces correct output."""
        video_path = _create_test_video(tmp_path)
        result = generate_video(
            description="sepia tone",
            input_video_path=str(video_path),
        )
        assert result["effect_applied"] == "sepia"

    def test_blur_pipeline(self, tmp_path):
        """Blur pipeline produces correct output."""
        video_path = _create_test_video(tmp_path)
        result = generate_video(
            description="blur effect",
            input_video_path=str(video_path),
        )
        assert result["effect_applied"] == "blur"

    def test_zoom_pipeline(self, tmp_path):
        """Zoom pipeline produces correct output."""
        video_path = _create_test_video(tmp_path, width=640, height=480)
        result = generate_video(
            description="zoom 2",
            input_video_path=str(video_path),
        )
        assert result["width"] == 320
        assert result["height"] == 240

    def test_rotation_pipeline(self, tmp_path):
        """Rotation pipeline produces correct output."""
        video_path = _create_test_video(tmp_path, width=640, height=480)
        result = generate_video(
            description="rotate 90 degrees",
            input_video_path=str(video_path),
        )
        assert result["width"] == 480
        assert result["height"] == 640

    def test_overlay_pipeline(self, tmp_path):
        """Overlay pipeline produces correct output."""
        video_path = _create_test_video(tmp_path)
        result = generate_video(
            description="grayscale",
            input_video_path=str(video_path),
            overlay_text="Test Overlay",
            overlay_position="center",
        )
        assert result["effect_applied"] == "grayscale"
        assert os.path.exists(result["output_path"])

    def test_custom_output_path(self, tmp_path):
        """Custom output path is respected."""
        video_path = _create_test_video(tmp_path)
        custom_output = str(tmp_path / "custom_output.mp4")
        result = generate_video(
            description="grayscale",
            input_video_path=str(video_path),
            output_path=custom_output,
        )
        assert result["output_path"] == custom_output
        assert os.path.exists(custom_output)

    def test_result_structure(self, tmp_path):
        """Result contains all expected keys."""
        video_path = _create_test_video(tmp_path)
        result = generate_video(
            description="grayscale",
            input_video_path=str(video_path),
        )
        expected_keys = [
            "output_path",
            "frames_processed",
            "duration_seconds",
            "width",
            "height",
            "fps",
            "effect_applied",
            "instructions",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_complex_description(self, tmp_path):
        """Complex description with multiple features works."""
        video_path = _create_test_video(tmp_path)
        result = generate_video(
            description="grayscale with blur and brightness 30, 5 seconds duration",
            input_video_path=str(video_path),
        )
        assert result["effect_applied"] == "grayscale"
        assert result["instructions"].grayscale is True
        assert result["instructions"].blur_amount == 5
        assert result["instructions"].brightness == 30
        assert result["instructions"].duration == 5.0
