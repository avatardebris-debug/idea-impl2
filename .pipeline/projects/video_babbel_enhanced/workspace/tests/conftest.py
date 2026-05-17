"""
conftest.py — shared test fixtures for video_babbel_enhanced tests.

Key fixture: synthetic_video — a 3-second silent black video created
with ffmpeg subprocess, suitable for testing clip_extractor without
needing a real video file.
"""
from __future__ import annotations
import pathlib
import subprocess
import sys
import pytest


@pytest.fixture(scope="session")
def synthetic_video(tmp_path_factory) -> pathlib.Path:
    """Generate a 3-second silent 320x240 black test video using ffmpeg."""
    out_dir = tmp_path_factory.mktemp("videos")
    out_path = out_dir / "test_video.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:size=320x240:duration=3:rate=25",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "3",
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f"ffmpeg not available or failed: {result.stderr[-200:]}")
    return out_path


@pytest.fixture
def sample_segments() -> list[dict]:
    """A small set of pre-built segments for unit testing (no transcription needed)."""
    return [
        {"text": "The cat sat on the mat", "start": 0.0, "end": 1.5},
        {"text": "I want to go to the store and buy some food", "start": 1.5, "end": 3.0},
        {"text": "X", "start": 3.0, "end": 3.5},  # too short — should be penalized
        {"text": "supercalifragilistic expialidocious pneumonoultramicroscopic silicovolcanoconiosis antidisestablishmentarianism",
         "start": 3.5, "end": 5.0},  # rare words — should score low
        {"text": "We can do it now and make it work for all of us here today",
         "start": 5.0, "end": 7.0},  # lots of common words — should score high
    ]


@pytest.fixture
def scored_segments(sample_segments) -> list[dict]:
    """sample_segments with l2_text and freq_score populated (no LLM/model needed)."""
    for i, seg in enumerate(sample_segments):
        seg["l2_text"] = f"[translated] {seg['text']}"
    # Import scorer and score them using bundled data
    try:
        from video_babbel_enhanced.frequency_scorer import score_segments
        return score_segments(sample_segments)
    except FileNotFoundError:
        # If subtlex data is missing, add dummy scores for extractor tests
        for i, seg in enumerate(sample_segments):
            seg.setdefault("freq_score", 1.0 / (i + 1))
            seg.setdefault("word_count", len(seg["text"].split()))
        sample_segments.sort(key=lambda s: s.get("freq_score", 0), reverse=True)
        return sample_segments
