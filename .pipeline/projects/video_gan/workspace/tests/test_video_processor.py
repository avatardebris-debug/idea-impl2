"""
Tests for the VideoProcessor module.

Covers:
  - Construction and default parameters
  - load_video_frames (with mocked OpenCV)
  - save_video_frames (with mocked OpenCV)
  - normalize / denormalize
  - create_random_video / create_constant_video
  - Input validation (type, shape, path)
  - Edge cases (empty path, non-existent file, etc.)
"""

import sys
import pathlib
import pytest
import numpy as np
import cv2
import tempfile
import os
from unittest.mock import patch, MagicMock

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.video_processor import VideoProcessor, _validate_video_path, _validate_frames_array


# ── defaults ──────────────────────────────────────────────────
DEFAULT_FRAME_SIZE = (64, 64)
DEFAULT_NUM_FRAMES = 16
DEFAULT_CHANNELS = 3


class TestVideoProcessorConstruction:
    """Test VideoProcessor __init__ parameter handling."""

    def test_default_construction(self):
        vp = VideoProcessor()
        assert vp.frame_size == (64, 64)
        assert vp.num_frames == 16
        assert vp.channels == 3
        assert vp._normalize_flag is True

    def test_custom_construction(self):
        vp = VideoProcessor(
            frame_size=(32, 32),
            num_frames=8,
            channels=1,
            normalize=False,
        )
        assert vp.frame_size == (32, 32)
        assert vp.num_frames == 8
        assert vp.channels == 1
        assert vp._normalize_flag is False


class TestVideoProcessorLoadVideoFrames:
    """Test VideoProcessor.load_video_frames method."""

    def _make_mock_video(self, num_frames=20, height=64, width=64, channels=3):
        """Create a mock video file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            path = f.name
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(path, fourcc, 10, (width, height))
        for _ in range(num_frames):
            frame = np.random.randint(0, 256, (height, width, channels), dtype=np.uint8)
            out.write(frame)
        out.release()
        return path

    def test_load_video_frames_returns_array(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        path = self._make_mock_video(num_frames=20)
        try:
            frames = vp.load_video_frames(path)
            assert isinstance(frames, np.ndarray)
        finally:
            os.unlink(path)

    def test_load_video_frames_shape(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        path = self._make_mock_video(num_frames=20)
        try:
            frames = vp.load_video_frames(path)
            assert frames.shape == (16, 64, 64, 3)
        finally:
            os.unlink(path)

    def test_load_video_frames_override_num_frames(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        path = self._make_mock_video(num_frames=20)
        try:
            frames = vp.load_video_frames(path, num_frames=10)
            assert frames.shape[0] == 10
        finally:
            os.unlink(path)

    def test_load_video_frames_less_frames_than_available(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        path = self._make_mock_video(num_frames=10)
        try:
            frames = vp.load_video_frames(path)
            assert frames.shape[0] == 10  # all available frames
        finally:
            os.unlink(path)

    def test_load_video_frames_pixel_range(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        path = self._make_mock_video(num_frames=20)
        try:
            frames = vp.load_video_frames(path)
            assert frames.min() >= 0
            assert frames.max() <= 255
        finally:
            os.unlink(path)

    def test_load_video_frames_non_string_path(self):
        vp = VideoProcessor()
        with pytest.raises(TypeError):
            vp.load_video_frames(123)

    def test_load_video_frames_empty_path(self):
        vp = VideoProcessor()
        with pytest.raises(ValueError):
            vp.load_video_frames("")

    def test_load_video_frames_whitespace_path(self):
        vp = VideoProcessor()
        with pytest.raises(ValueError):
            vp.load_video_frames("   ")

    def test_load_video_frames_unopenable_file(self):
        vp = VideoProcessor()
        with pytest.raises(ValueError):
            vp.load_video_frames("/nonexistent/path/video.mp4")

    def test_load_video_alias(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        path = self._make_mock_video(num_frames=20)
        try:
            frames = vp.load_video(path)
            assert isinstance(frames, np.ndarray)
        finally:
            os.unlink(path)


class TestVideoProcessorSaveVideoFrames:
    """Test VideoProcessor.save_video_frames method."""

    def test_save_video_frames_creates_file(self):
        vp = VideoProcessor(frame_size=(64, 64))
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            path = f.name
        try:
            vp.save_video_frames(frames, path)
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_save_video_frames_readability(self):
        vp = VideoProcessor(frame_size=(64, 64))
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            path = f.name
        try:
            vp.save_video_frames(frames, path)
            cap = cv2.VideoCapture(path)
            assert cap.isOpened()
            cap.release()
        finally:
            os.unlink(path)

    def test_save_video_frames_non_string_path(self):
        vp = VideoProcessor()
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        with pytest.raises(TypeError):
            vp.save_video_frames(frames, 123)

    def test_save_video_frames_empty_path(self):
        vp = VideoProcessor()
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        with pytest.raises(ValueError):
            vp.save_video_frames(frames, "")

    def test_save_video_frames_whitespace_path(self):
        vp = VideoProcessor()
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        with pytest.raises(ValueError):
            vp.save_video_frames(frames, "   ")

    def test_save_video_alias(self):
        vp = VideoProcessor(frame_size=(64, 64))
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            path = f.name
        try:
            vp.save(frames, path)
            assert os.path.exists(path)
        finally:
            os.unlink(path)


class TestVideoProcessorNormalizeDenormalize:
    """Test VideoProcessor.normalize and denormalize methods."""

    def test_normalize_output_range(self):
        vp = VideoProcessor(frame_size=(64, 64))
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        normalized = vp.normalize(frames)
        assert normalized.min() >= -1.0 - 1e-5
        assert normalized.max() <= 1.0 + 1e-5

    def test_normalize_output_shape(self):
        vp = VideoProcessor(frame_size=(64, 64))
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        normalized = vp.normalize(frames)
        assert normalized.shape == frames.shape

    def test_denormalize_output_range(self):
        vp = VideoProcessor(frame_size=(64, 64))
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        normalized = vp.normalize(frames)
        denormalized = vp.denormalize(normalized)
        assert denormalized.min() >= 0.0 - 1e-5
        assert denormalized.max() <= 255.0 + 1e-5

    def test_denormalize_output_shape(self):
        vp = VideoProcessor(frame_size=(64, 64))
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        normalized = vp.normalize(frames)
        denormalized = vp.denormalize(normalized)
        assert denormalized.shape == frames.shape

    def test_normalize_denormalize_roundtrip(self):
        vp = VideoProcessor(frame_size=(64, 64))
        frames = np.random.randint(0, 256, (1, 16, 64, 64, 3)).astype(np.float32)
        normalized = vp.normalize(frames)
        denormalized = vp.denormalize(normalized)
        assert np.allclose(frames, denormalized, atol=1e-5)

    def test_normalize_non_array_raises(self):
        vp = VideoProcessor()
        with pytest.raises(TypeError):
            vp.normalize("not an array")

    def test_normalize_wrong_ndim_raises(self):
        vp = VideoProcessor()
        arr = np.random.rand(1, 16, 64, 64)  # 4D instead of 5D
        with pytest.raises(ValueError):
            vp.normalize(arr)

    def test_normalize_wrong_shape_raises(self):
        vp = VideoProcessor(frame_size=(64, 64))
        arr = np.random.rand(1, 16, 32, 32, 3)  # wrong frame size
        with pytest.raises(ValueError):
            vp.normalize(arr)

    def test_normalize_negative_values(self):
        vp = VideoProcessor(frame_size=(64, 64))
        arr = np.random.rand(1, 16, 64, 64, 3) * 255
        arr[0, 0, 0, 0, 0] = -10  # negative value
        with pytest.raises(ValueError):
            vp.normalize(arr)

    def test_normalize_values_above_255(self):
        vp = VideoProcessor(frame_size=(64, 64))
        arr = np.random.rand(1, 16, 64, 64, 3) * 255
        arr[0, 0, 0, 0, 0] = 300  # value above 255
        with pytest.raises(ValueError):
            vp.normalize(arr)

    def test_denormalize_non_array_raises(self):
        vp = VideoProcessor()
        with pytest.raises(TypeError):
            vp.denormalize("not an array")

    def test_denormalize_wrong_ndim_raises(self):
        vp = VideoProcessor()
        arr = np.random.rand(1, 16, 64, 64)  # 4D instead of 5D
        with pytest.raises(ValueError):
            vp.denormalize(arr)

    def test_denormalize_wrong_shape_raises(self):
        vp = VideoProcessor(frame_size=(64, 64))
        arr = np.random.rand(1, 16, 32, 32, 3)  # wrong frame size
        with pytest.raises(ValueError):
            vp.denormalize(arr)

    def test_denormalize_values_below_minus_1(self):
        vp = VideoProcessor(frame_size=(64, 64))
        arr = np.random.rand(1, 16, 64, 64, 3) * 2
        arr[0, 0, 0, 0, 0] = -1.5  # below -1
        with pytest.raises(ValueError):
            vp.denormalize(arr)

    def test_denormalize_values_above_1(self):
        vp = VideoProcessor(frame_size=(64, 64))
        arr = np.random.rand(1, 16, 64, 64, 3) * 2
        arr[0, 0, 0, 0, 0] = 1.5  # above 1
        with pytest.raises(ValueError):
            vp.denormalize(arr)


class TestVideoProcessorCreateRandomVideo:
    """Test VideoProcessor.create_random_video method."""

    def test_create_random_video_shape(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        video = vp.create_random_video()
        assert video.shape == (1, 16, 64, 64, 3)

    def test_create_random_video_range(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        video = vp.create_random_video()
        assert video.min() >= -1.0 - 1e-5
        assert video.max() <= 1.0 + 1e-5

    def test_create_random_video_override_params(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        video = vp.create_random_video(num_frames=10, frame_size=(32, 32))
        assert video.shape == (1, 10, 32, 32, 3)

    def test_create_random_video_with_normalize_false(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16, normalize=False)
        video = vp.create_random_video()
        assert video.min() >= 0.0 - 1e-5
        assert video.max() <= 255.0 + 1e-5

    def test_create_random_video_zero_frames(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        video = vp.create_random_video(num_frames=0)
        assert video.shape == (1, 0, 64, 64, 3)

    def test_create_random_video_negative_frames_raises(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        with pytest.raises(ValueError):
            vp.create_random_video(num_frames=-1)

    def test_create_random_video_zero_size_raises(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        with pytest.raises(ValueError):
            vp.create_random_video(frame_size=(0, 64))


class TestVideoProcessorCreateConstantVideo:
    """Test VideoProcessor.create_constant_video method."""

    def test_create_constant_video_shape(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        video = vp.create_constant_video(value=0.5)
        assert video.shape == (1, 16, 64, 64, 3)

    def test_create_constant_video_value(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        video = vp.create_constant_video(value=0.5)
        assert np.allclose(video, 0.5)

    def test_create_constant_video_override_params(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        video = vp.create_constant_video(value=0.5, num_frames=10, frame_size=(32, 32))
        assert video.shape == (1, 10, 32, 32, 3)

    def test_create_constant_video_with_normalize_false(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16, normalize=False)
        video = vp.create_constant_video(value=127.5)
        assert np.allclose(video, 127.5)

    def test_create_constant_video_zero_frames(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        video = vp.create_constant_video(value=0.5, num_frames=0)
        assert video.shape == (1, 0, 64, 64, 3)

    def test_create_constant_video_negative_frames_raises(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        with pytest.raises(ValueError):
            vp.create_constant_video(value=0.5, num_frames=-1)

    def test_create_constant_video_zero_size_raises(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        with pytest.raises(ValueError):
            vp.create_constant_video(value=0.5, frame_size=(0, 64))

    def test_create_constant_video_value_below_minus_1(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        with pytest.raises(ValueError):
            vp.create_constant_video(value=-1.5)

    def test_create_constant_video_value_above_1(self):
        vp = VideoProcessor(frame_size=(64, 64), num_frames=16)
        with pytest.raises(ValueError):
            vp.create_constant_video(value=1.5)


class TestValidateVideoPath:
    """Test the _validate_video_path helper function."""

    def test_valid_path(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            path = f.name
        try:
            _validate_video_path(path)  # should not raise
        finally:
            os.unlink(path)

    def test_non_string_raises_type_error(self):
        with pytest.raises(TypeError):
            _validate_video_path(123)

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            _validate_video_path("")

    def test_whitespace_string_raises_value_error(self):
        with pytest.raises(ValueError):
            _validate_video_path("   ")

    def test_nonexistent_file_raises_value_error(self):
        with pytest.raises(ValueError):
            _validate_video_path("/nonexistent/file.mp4")


class TestValidateFramesArray:
    """Test the _validate_frames_array helper function."""

    def test_valid_array(self):
        arr = np.random.rand(1, 16, 64, 64, 3)
        _validate_frames_array(arr, (64, 64), 3)  # should not raise

    def test_non_array_raises_type_error(self):
        with pytest.raises(TypeError):
            _validate_frames_array("not an array", (64, 64), 3)

    def test_wrong_ndim_raises_value_error(self):
        arr = np.random.rand(1, 16, 64, 64)
        with pytest.raises(ValueError):
            _validate_frames_array(arr, (64, 64), 3)

    def test_wrong_shape_raises_value_error(self):
        arr = np.random.rand(1, 16, 32, 32, 3)
        with pytest.raises(ValueError):
            _validate_frames_array(arr, (64, 64), 3)
