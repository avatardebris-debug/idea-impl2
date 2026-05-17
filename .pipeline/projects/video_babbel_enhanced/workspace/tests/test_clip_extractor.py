"""
test_clip_extractor.py — unit tests for clip_extractor.py

Tests real ffmpeg clip cutting using the synthetic_video fixture from conftest.py.
Skips automatically if ffmpeg is not available.
"""
from __future__ import annotations
import json
import pathlib
import subprocess
import sys
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from video_babbel_enhanced.clip_extractor import extract_clips


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


pytestmark = pytest.mark.skipif(not _ffmpeg_available(), reason="ffmpeg not on PATH")


def _make_segments(n: int, duration: float = 3.0) -> list[dict]:
    """Make n evenly-spaced segments across [0, duration]."""
    step = duration / n
    segs = []
    for i in range(n):
        segs.append({
            "text": f"This is segment {i} with common words the and of",
            "l2_text": f"Este es el segmento {i}",
            "start": round(i * step, 3),
            "end": round((i + 1) * step, 3),
            "freq_score": 1.0 / (i + 1),
            "word_count": 8,
        })
    return segs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExtractClips:
    def test_produces_correct_number_of_files(self, synthetic_video, tmp_path):
        segs = _make_segments(5)
        clips = extract_clips(str(synthetic_video), segs, str(tmp_path / "clips"), top_n=3)
        assert len(clips) == 3

    def test_mp4_files_created(self, synthetic_video, tmp_path):
        segs = _make_segments(3)
        out_dir = tmp_path / "clips"
        extract_clips(str(synthetic_video), segs, str(out_dir), top_n=3)
        mp4_files = list(out_dir.glob("*.mp4"))
        assert len(mp4_files) == 3

    def test_json_files_created(self, synthetic_video, tmp_path):
        segs = _make_segments(3)
        out_dir = tmp_path / "clips"
        extract_clips(str(synthetic_video), segs, str(out_dir), top_n=3)
        json_files = list(out_dir.glob("*.json"))
        assert len(json_files) == 3

    def test_json_has_required_keys(self, synthetic_video, tmp_path):
        segs = _make_segments(2)
        out_dir = tmp_path / "clips"
        extract_clips(str(synthetic_video), segs, str(out_dir), top_n=2)
        for jf in sorted(out_dir.glob("*.json")):
            meta = json.loads(jf.read_text())
            required = {"clip_id", "l1_text", "l2_text", "start", "end", "duration",
                        "freq_score", "word_count", "source_video"}
            assert required.issubset(set(meta.keys())), f"Missing keys in {jf.name}: {required - set(meta.keys())}"

    def test_clips_nonzero_size(self, synthetic_video, tmp_path):
        segs = _make_segments(3)
        out_dir = tmp_path / "clips"
        clips = extract_clips(str(synthetic_video), segs, str(out_dir), top_n=3)
        for clip_path in clips:
            assert clip_path.exists()
            assert clip_path.stat().st_size > 0, f"{clip_path.name} is empty"

    def test_output_dir_created_if_missing(self, synthetic_video, tmp_path):
        segs = _make_segments(1)
        nested = tmp_path / "deep" / "nested" / "clips"
        assert not nested.exists()
        extract_clips(str(synthetic_video), segs, str(nested), top_n=1)
        assert nested.exists()

    def test_top_n_limits_output(self, synthetic_video, tmp_path):
        segs = _make_segments(10)
        out_dir = tmp_path / "clips"
        clips = extract_clips(str(synthetic_video), segs, str(out_dir), top_n=4)
        assert len(clips) == 4

    def test_empty_segments_no_crash(self, synthetic_video, tmp_path):
        out_dir = tmp_path / "clips"
        clips = extract_clips(str(synthetic_video), [], str(out_dir), top_n=10)
        assert clips == []

    def test_clip_naming(self, synthetic_video, tmp_path):
        segs = _make_segments(3)
        out_dir = tmp_path / "clips"
        extract_clips(str(synthetic_video), segs, str(out_dir), top_n=3)
        names = sorted(p.stem for p in out_dir.glob("*.mp4"))
        assert names == ["clip_000", "clip_001", "clip_002"]
