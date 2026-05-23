"""Tests for metrics module."""

import numpy as np
import pytest

from sim_real_comparator.metrics import compute_ssim, compute_phash_distance


def _make_frame(height: int = 64, width: int = 64, channels: int = 3) -> np.ndarray:
    return np.random.randint(0, 256, size=(height, width, channels), dtype=np.uint8)


def test_ssim_identical_frames():
    frame = _make_frame()
    score = compute_ssim(frame, frame)
    assert score == pytest.approx(1.0, abs=1e-6)


def test_ssim_different_frames():
    frame_a = _make_frame()
    frame_b = _make_frame()
    score = compute_ssim(frame_a, frame_b)
    assert score < 1.0


def test_ssim_completely_different():
    frame_a = np.zeros((64, 64, 3), dtype=np.uint8)
    frame_b = np.full((64, 64, 3), 255, dtype=np.uint8)
    score = compute_ssim(frame_a, frame_b)
    assert score < 1.0
    assert score >= 0.0


def test_phash_distance_identical_frames():
    frame = _make_frame()
    distance = compute_phash_distance(frame, frame)
    assert distance == pytest.approx(0.0, abs=1e-6)


def test_phash_distance_different_frames():
    frame_a = _make_frame()
    frame_b = _make_frame()
    distance = compute_phash_distance(frame_a, frame_b)
    assert distance > 0.0


def test_phash_distance_completely_different():
    frame_a = np.zeros((64, 64, 3), dtype=np.uint8)
    frame_b = np.full((64, 64, 3), 255, dtype=np.uint8)
    distance = compute_phash_distance(frame_a, frame_b)
    assert distance >= 0.0
    assert distance <= 1.0


def test_ssim_returns_float():
    frame = _make_frame()
    score = compute_ssim(frame, frame)
    assert isinstance(score, float)


def test_phash_distance_returns_float():
    frame = _make_frame()
    distance = compute_phash_distance(frame, frame)
    assert isinstance(distance, float)
