"""Tests for frame_extractor module."""

import numpy as np
import pytest

from sim_real_comparator.frame_extractor import extract_frames, extract_aligned_frames


def _make_dummy_video(path: str, num_frames: int = 10, height: int = 64, width: int = 64):
    """Create a dummy MP4 video file for testing."""
    frames = np.random.randint(0, 256, size=(num_frames, height, width, 3), dtype=np.uint8)
    import imageio.v3 as iio
    iio.imwrite(path, frames, fps=30)


def test_extract_frames_returns_numpy_array(tmp_path):
    video_path = str(tmp_path / "test.mp4")
    _make_dummy_video(video_path, num_frames=5)
    result = extract_frames(video_path)
    assert isinstance(result, np.ndarray)
    assert result.shape == (5, 64, 64, 3)


def test_extract_frames_all_frames(tmp_path):
    video_path = str(tmp_path / "test.mp4")
    _make_dummy_video(video_path, num_frames=12)
    result = extract_frames(video_path)
    assert len(result) == 12


def test_extract_frames_num_frames_limit(tmp_path):
    video_path = str(tmp_path / "test.mp4")
    _make_dummy_video(video_path, num_frames=20)
    result = extract_frames(video_path, num_frames=8)
    assert len(result) == 8


def test_extract_aligned_frames_aligned_counts(tmp_path):
    real_path = str(tmp_path / "real.mp4")
    sim_path = str(tmp_path / "sim.mp4")
    _make_dummy_video(real_path, num_frames=10)
    _make_dummy_video(sim_path, num_frames=10)
    real_frames, sim_frames = extract_aligned_frames(real_path, sim_path)
    assert len(real_frames) == len(sim_frames) == 10


def test_extract_aligned_frames_truncates_to_min(tmp_path):
    real_path = str(tmp_path / "real.mp4")
    sim_path = str(tmp_path / "sim.mp4")
    _make_dummy_video(real_path, num_frames=15)
    _make_dummy_video(sim_path, num_frames=8)
    real_frames, sim_frames = extract_aligned_frames(real_path, sim_path)
    assert len(real_frames) == len(sim_frames) == 8


def test_extract_aligned_frames_output_shapes(tmp_path):
    real_path = str(tmp_path / "real.mp4")
    sim_path = str(tmp_path / "sim.mp4")
    _make_dummy_video(real_path, num_frames=5, height=32, width=48)
    _make_dummy_video(sim_path, num_frames=5, height=32, width=48)
    real_frames, sim_frames = extract_aligned_frames(real_path, sim_path)
    assert real_frames.shape == (5, 32, 48, 3)
    assert sim_frames.shape == (5, 32, 48, 3)
