"""
test_integration.py — end-to-end pipeline test (no LLM, no network).

Mocks the translator so the full chain runs offline:
  transcribe (synthetic video) → mock-translate → score → extract 3 clips
"""
from __future__ import annotations
import json
import pathlib
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


def _mock_translate(segments, target_lang, source_lang="en", model="qwen3:6b"):
    """Mock translator: adds [translated] prefix without any LLM call."""
    for seg in segments:
        seg["l2_text"] = f"[{target_lang}] {seg.get('text', '')}"
    return segments


def _mock_transcribe(video_path, language=None):
    """Mock transcriber: returns 5 synthetic segments."""
    return [
        {"text": "The quick brown fox jumps over the lazy dog", "start": 0.0, "end": 1.0, "words": []},
        {"text": "We can do this work together today and make it happen",  "start": 1.0, "end": 2.0, "words": []},
        {"text": "A very good way to learn a new language fast", "start": 2.0, "end": 3.0, "words": []},
        {"text": "xyzzy frobnicate quux", "start": 2.5, "end": 3.0, "words": []},
        {"text": "Hello world", "start": 2.8, "end": 3.0, "words": []},
    ]


def _ensure_subtlex_data() -> None:
    """Ensure subtlex data exists for the scorer to run."""
    data_path = pathlib.Path(__file__).parent.parent / "video_babbel_enhanced" / "data" / "subtlex_us.txt"
    if not data_path.exists():
        from video_babbel_enhanced.cli import _generate_minimal_subtlex
        _generate_minimal_subtlex(data_path)


class TestIntegration:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        _ensure_subtlex_data()

    def test_full_pipeline_produces_clips(self, synthetic_video, tmp_path):
        """Run full pipeline end-to-end with mocked transcriber and translator."""
        import subprocess
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pytest.skip("ffmpeg not available")

        from video_babbel_enhanced.frequency_scorer import score_segments
        from video_babbel_enhanced.clip_extractor import extract_clips

        with patch("video_babbel_enhanced.transcriber.transcribe", side_effect=_mock_transcribe):
            from video_babbel_enhanced.transcriber import transcribe
            segments = transcribe(str(synthetic_video))

        segments = _mock_translate(segments, "es")
        segments = score_segments(segments)
        out_dir = tmp_path / "clips"
        clips = extract_clips(str(synthetic_video), segments, str(out_dir), top_n=3)

        # Assertions
        assert len(clips) == 3, f"Expected 3 clips, got {len(clips)}"

        mp4_files = list(out_dir.glob("*.mp4"))
        json_files = list(out_dir.glob("*.json"))
        assert len(mp4_files) == 3
        assert len(json_files) == 3

        required_keys = {"clip_id", "l1_text", "l2_text", "start", "end",
                         "duration", "freq_score", "word_count", "source_video"}
        for jf in sorted(out_dir.glob("*.json")):
            meta = json.loads(jf.read_text())
            missing = required_keys - set(meta.keys())
            assert not missing, f"Missing keys in {jf.name}: {missing}"
            assert meta["l2_text"].startswith("[es]"), f"l2_text not translated: {meta['l2_text']}"

        for clip_path in clips:
            assert clip_path.stat().st_size > 0

    def test_scorer_ranks_common_words_first(self):
        """Common-word segments should beat rare-word segments after scoring."""
        _ensure_subtlex_data()
        from video_babbel_enhanced.frequency_scorer import score_segments

        segs = [
            {"text": "xyzzy frobnicate quux blorp", "start": 0.0, "end": 1.0},
            {"text": "the cat and the dog go to the park today", "start": 1.0, "end": 2.0},
        ]
        scored = score_segments(segs)
        assert scored[0]["text"] == "the cat and the dog go to the park today"

    def test_empty_video_no_crash(self, tmp_path):
        """Pipeline should exit gracefully with empty transcription."""
        from video_babbel_enhanced.frequency_scorer import score_segments
        from video_babbel_enhanced.clip_extractor import extract_clips

        segments = []
        segments = _mock_translate(segments, "fr")
        segments = score_segments(segments)
        clips = extract_clips("/nonexistent.mp4", segments, str(tmp_path / "clips"), top_n=5)
        assert clips == []
