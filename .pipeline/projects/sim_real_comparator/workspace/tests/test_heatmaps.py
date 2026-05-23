"""Tests for heatmap generation module."""

import os
import tempfile
import numpy as np
import pytest

from sim_real_comparator.heatmaps import generate_heatmap, generate_heatmap_batch


def _make_frame(color: tuple, size: int = 64) -> np.ndarray:
    """Create a solid-color numpy frame."""
    return np.full((size, size, 3), color, dtype=np.uint8)


def test_generate_heatmap_creates_png():
    """generate_heatmap should produce a valid PNG file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_heatmap.png")
        frame_a = _make_frame((100, 100, 100))
        frame_b = _make_frame((150, 150, 150))
        result = generate_heatmap(frame_a, frame_b, output_path)
        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0


def test_generate_heatmap_batch():
    """generate_heatmap_batch should produce multiple PNG files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        frames_a = [_make_frame((i * 50, i * 50, i * 50)) for i in range(3)]
        frames_b = [_make_frame((i * 50 + 30, i * 50 + 30, i * 50 + 30)) for i in range(3)]
        paths = generate_heatmap_batch(frames_a, frames_b, tmpdir)
        assert len(paths) == 3
        for p in paths:
            assert os.path.exists(p)
            assert os.path.getsize(p) > 0


def test_identical_frames_heatmap():
    """Heatmap for identical frames should be all green (no difference)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "identical.png")
        frame = _make_frame((128, 64, 200))
        generate_heatmap(frame, frame, output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
