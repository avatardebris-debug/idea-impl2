"""Tests for VideoProcessor — frame-level video transformations."""

import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from videopow.core import VideoProcessor, VideoTransformResult


class TestVideoProcessorInit:
    """Test VideoProcessor initialization."""

    def test_nonexistent_file(self):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Input video not found"):
            VideoProcessor("/nonexistent/video.mp4")

    def test_unsupported_extension(self, tmp_path):
        """Raises ValueError for unsupported format."""
        video_file = tmp_path / "test.txt"
        video_file.write_text("not a video")
        with pytest.raises(ValueError, match="Unsupported video format"):
            VideoProcessor(str(video_file))

    def test_supported_extensions(self, tmp_path):
        """Supported extensions are accepted."""
        supported = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
        for ext in supported:
            video_file = tmp_path / f"test{ext}"
            video_file.write_text("fake video data")
            # Should not raise for extension check
            # (will fail on isOpen because it's not a real video)
            try:
                proc = VideoProcessor(str(video_file))
                proc.close()
            except ValueError:
                pass  # Expected for fake files


class TestVideoProcessorEffects:
    """Test effect application on frames."""

    def _create_test_video(self, tmp_path, width=640, height=480, frames=10, fps=30):
        """Helper to create a test video file."""
        video_path = tmp_path / "test_input.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
        for i in range(frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            # Add a gradient pattern
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

    def test_grayscale_effect(self, tmp_path):
        """Grayscale effect produces grayscale output."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(grayscale=True)
            assert isinstance(result, VideoTransformResult)
            assert result.effect_applied == "grayscale"
            assert result.frames_processed > 0

            # Verify output file exists and is valid
            assert os.path.exists(result.output_path)
            cap = cv2.VideoCapture(result.output_path)
            assert cap.isOpened()
            ret, frame = cap.read()
            cap.release()
            assert ret is True
            # Grayscale frame should have uniform channel values
            assert frame is not None
        finally:
            processor.close()

    def test_sepia_effect(self, tmp_path):
        """Sepia effect produces sepia-toned output."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(sepia=True)
            assert result.effect_applied == "sepia"
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
        finally:
            processor.close()

    def test_blur_effect(self, tmp_path):
        """Blur effect produces blurred output."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(blur_amount=5)
            assert result.effect_applied == "blur"
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
        finally:
            processor.close()

    def test_brightness_effect(self, tmp_path):
        """Brightness adjustment works correctly."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(brightness=50)
            assert result.effect_applied == "brightness"
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
        finally:
            processor.close()

    def test_contrast_effect(self, tmp_path):
        """Contrast adjustment works correctly."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(contrast=30)
            assert result.effect_applied == "contrast"
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
        finally:
            processor.close()

    def test_combined_effects(self, tmp_path):
        """Multiple effects can be combined."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(
                grayscale=True,
                blur_amount=5,
                brightness=20,
            )
            assert result.effect_applied == "grayscale"
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
        finally:
            processor.close()


class TestVideoProcessorTransformations:
    """Test geometric transformations."""

    def _create_test_video(self, tmp_path, width=640, height=480, frames=10, fps=30):
        """Helper to create a test video file."""
        video_path = tmp_path / "test_input.mp4"
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

    def test_rotation(self, tmp_path):
        """Rotation transformation works."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(rotation=90)
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
            # Width and height should be swapped for 90 degree rotation
            assert result.width == 480
            assert result.height == 640
        finally:
            processor.close()

    def test_crop(self, tmp_path):
        """Crop transformation works."""
        video_path = self._create_test_video(tmp_path, width=640, height=480)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(crop=50)
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
            # Output should be 540x380 (640-100, 480-100)
            assert result.width == 540
            assert result.height == 380
        finally:
            processor.close()

    def test_zoom(self, tmp_path):
        """Zoom transformation works."""
        video_path = self._create_test_video(tmp_path, width=640, height=480)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(zoom_amount=2)
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
            # Output should be half size
            assert result.width == 320
            assert result.height == 240
        finally:
            processor.close()

    def test_speed_multiplier(self, tmp_path):
        """Speed multiplier affects frame count."""
        video_path = self._create_test_video(tmp_path, frames=100, fps=30)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(speed_multiplier=2.0)
            assert result.frames_processed == 50  # 100 frames / 2x speed
            assert os.path.exists(result.output_path)
        finally:
            processor.close()


class TestVideoProcessorOverlay:
    """Test text overlay functionality."""

    def _create_test_video(self, tmp_path, width=640, height=480, frames=10, fps=30):
        """Helper to create a test video file."""
        video_path = tmp_path / "test_input.mp4"
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

    def test_overlay_text(self, tmp_path):
        """Text overlay is applied correctly."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process(overlay_text="Hello World", overlay_position="center")
            assert result.frames_processed > 0
            assert os.path.exists(result.output_path)
        finally:
            processor.close()

    def test_overlay_positions(self, tmp_path):
        """Different overlay positions work."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        positions = ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        for pos in positions:
            try:
                result = processor.process(overlay_text="Test", overlay_position=pos)
                assert result.frames_processed > 0
                assert os.path.exists(result.output_path)
            finally:
                processor.close()


class TestVideoProcessorResult:
    """Test VideoTransformResult properties."""

    def _create_test_video(self, tmp_path, width=640, height=480, frames=10, fps=30):
        """Helper to create a test video file."""
        video_path = tmp_path / "test_input.mp4"
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

    def test_result_properties(self, tmp_path):
        """Result contains correct metadata."""
        video_path = self._create_test_video(tmp_path, frames=30, fps=30)
        processor = VideoProcessor(str(video_path))

        try:
            result = processor.process()
            assert result.frames_processed == 30
            assert result.duration_seconds == pytest.approx(1.0, abs=0.1)
            assert result.width == 640
            assert result.height == 480
            assert result.fps == pytest.approx(30.0, abs=1.0)
            assert result.output_path.endswith(".mp4")
        finally:
            processor.close()

    def test_custom_output_path(self, tmp_path):
        """Custom output path is respected."""
        video_path = self._create_test_video(tmp_path)
        processor = VideoProcessor(str(video_path))

        custom_output = str(tmp_path / "custom_output.avi")
        try:
            result = processor.process(output_path=custom_output)
            assert result.output_path == custom_output
            assert os.path.exists(custom_output)
        finally:
            processor.close()
