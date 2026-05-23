"""Integration tests with synthetic video pairs."""

import json
import os
import subprocess
import sys
import tempfile
import numpy as np

import pytest


def _create_synthetic_video(frames: list[np.ndarray], output_path: str):
    """Write synthetic frames as a simple numpy-based video file using imageio."""
    import imageio.v3 as iio
    frames_array = np.stack(frames, axis=0)
    iio.imwrite(output_path, frames_array, fps=30)


def _run_cli(real_video: str, sim_video: str, output_dir: str, num_frames: int = 10):
    """Run the sim-compare CLI."""
    cmd = [
        sys.executable,
        "-m", "sim_real_comparator.cli",
        "--real-video", real_video,
        "--sim-video", sim_video,
        "--output-dir", output_dir,
        "--num-frames", str(num_frames),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"CLI failed: {result.stderr}")
    return result


def test_identical_videos():
    """Identical videos should yield global_score > 0.9."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create identical synthetic videos
        frames = [np.full((64, 64, 3), min(i * 25, 255), dtype=np.uint8) for i in range(20)]
        real_video = os.path.join(tmpdir, "real.mp4")
        sim_video = os.path.join(tmpdir, "sim.mp4")
        _create_synthetic_video(frames, real_video)
        _create_synthetic_video(frames, sim_video)

        output_dir = os.path.join(tmpdir, "output")
        result = _run_cli(real_video, sim_video, output_dir, num_frames=10)

        # Check report
        report_path = os.path.join(output_dir, "report.json")
        assert os.path.exists(report_path)
        with open(report_path) as f:
            report = json.load(f)

        assert report["global"]["global_score"] > 0.9
        assert report["global"]["avg_ssim"] > 0.9
        assert report["global"]["avg_phash_similarity"] > 0.9
        assert report["global"]["avg_clip_similarity"] > 0.9

        # Check heatmaps
        heatmap_dir = os.path.join(output_dir, "heatmaps")
        assert os.path.exists(heatmap_dir)
        assert len(os.listdir(heatmap_dir)) == 10


def test_different_videos():
    """Different videos should yield global_score < 0.5."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create two very different synthetic videos with distinct spatial patterns
        frames_real = []
        frames_sim = []
        for i in range(20):
            # Real: top half white, bottom half black
            real_frame = np.zeros((64, 64, 3), dtype=np.uint8)
            real_frame[:32, :] = 255
            # Sim: top half black, bottom half white (inverted)
            sim_frame = np.zeros((64, 64, 3), dtype=np.uint8)
            sim_frame[32:, :] = 255
            frames_real.append(real_frame)
            frames_sim.append(sim_frame)
        real_video = os.path.join(tmpdir, "real.mp4")
        sim_video = os.path.join(tmpdir, "sim.mp4")
        _create_synthetic_video(frames_real, real_video)
        _create_synthetic_video(frames_sim, sim_video)

        output_dir = os.path.join(tmpdir, "output")
        result = _run_cli(real_video, sim_video, output_dir, num_frames=10)

        # Check report
        report_path = os.path.join(output_dir, "report.json")
        assert os.path.exists(report_path)
        with open(report_path) as f:
            report = json.load(f)

        assert report["global"]["global_score"] < 0.5
        assert report["global"]["avg_ssim"] < 0.5
        assert report["global"]["avg_phash_similarity"] < 0.5
        assert report["global"]["avg_clip_similarity"] < 0.5

        # Check heatmaps
        heatmap_dir = os.path.join(output_dir, "heatmaps")
        assert os.path.exists(heatmap_dir)
        assert len(os.listdir(heatmap_dir)) == 10


def test_fps_normalization():
    """FPS normalization should subsample frames correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create videos with different FPS
        frames_real = [np.full((64, 64, 3), min(i * 25, 255), dtype=np.uint8) for i in range(30)]
        frames_sim = [np.full((64, 64, 3), min(i * 25, 255), dtype=np.uint8) for i in range(10)]
        real_video = os.path.join(tmpdir, "real.mp4")
        sim_video = os.path.join(tmpdir, "sim.mp4")
        _create_synthetic_video(frames_real, real_video)
        _create_synthetic_video(frames_sim, sim_video)

        output_dir = os.path.join(tmpdir, "output")
        # Run with different FPS flags
        cmd = [
            sys.executable,
            "-m", "sim_real_comparator.cli",
            "--real-video", real_video,
            "--sim-video", sim_video,
            "--output-dir", output_dir,
            "--num-frames", "10",
            "--fps-real", "30.0",
            "--fps-sim", "10.0",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0

        report_path = os.path.join(output_dir, "report.json")
        assert os.path.exists(report_path)
        with open(report_path) as f:
            report = json.load(f)

        # Should have 10 frames after normalization
        assert len(report["frames"]) == 10
