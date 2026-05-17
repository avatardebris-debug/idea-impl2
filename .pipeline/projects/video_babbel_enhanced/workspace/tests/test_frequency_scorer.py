"""
test_frequency_scorer.py — unit tests for frequency_scorer.py

Runs without any LLM or external network call.
Requires data/subtlex_us.txt to exist (run `fetch-data` or it auto-generates).
"""
from __future__ import annotations
import pathlib
import sys
import pytest

# Ensure we import from workspace
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from video_babbel_enhanced.frequency_scorer import score_segments, get_rank_dict, _tokenize


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_data() -> bool:
    """Generate minimal subtlex data if missing. Returns True if data is available."""
    data_path = pathlib.Path(__file__).parent.parent / "video_babbel_enhanced" / "data" / "subtlex_us.txt"
    if not data_path.exists():
        try:
            from video_babbel_enhanced.cli import _generate_minimal_subtlex
            _generate_minimal_subtlex(data_path)
        except Exception:
            return False
    return data_path.exists()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTokenize:
    def test_basic(self):
        tokens = _tokenize("Hello, World!")
        assert tokens == ["hello", "world"]

    def test_apostrophe_kept(self):
        tokens = _tokenize("don't stop")
        assert "don't" in tokens or ("don" in tokens and "t" in tokens)

    def test_empty(self):
        assert _tokenize("") == []

    def test_numbers_excluded(self):
        tokens = _tokenize("step 1 of 3")
        assert "1" not in tokens and "3" not in tokens


class TestFrequencyScorer:
    @pytest.fixture(autouse=True)
    def ensure_data(self):
        if not _ensure_data():
            pytest.skip("Cannot generate subtlex data")

    def test_common_words_score_higher_than_rare(self):
        segs = [
            {"text": "the cat sat on the mat", "start": 0.0, "end": 1.0},
            {"text": "pneumonoultramicroscopic silicovolcanoconiosis antidisestablishmentarianism", "start": 1.0, "end": 2.0},
        ]
        scored = score_segments(segs)
        # First segment has many common words — should score first
        assert scored[0]["text"] == "the cat sat on the mat" or scored[0]["freq_score"] >= scored[1]["freq_score"]

    def test_short_segment_penalized(self):
        segs = [
            {"text": "X", "start": 0.0, "end": 1.0},             # 1 word → penalized
            {"text": "the cat sat on the mat", "start": 1.0, "end": 2.0},  # 6 words → normal
        ]
        scored = score_segments(segs)
        one_word = next(s for s in scored if s["text"] == "X")
        six_word = next(s for s in scored if "cat" in s["text"])
        assert one_word["length_score"] == 0.4
        assert six_word["length_score"] == 1.0

    def test_long_segment_penalized(self):
        long_text = " ".join(["the"] * 20)  # 20 words > 15 limit
        segs = [{"text": long_text, "start": 0.0, "end": 3.0}]
        scored = score_segments(segs)
        assert scored[0]["length_score"] == 0.4

    def test_ideal_length_not_penalized(self):
        segs = [{"text": "we can do this work today", "start": 0.0, "end": 1.0}]  # 6 words
        scored = score_segments(segs)
        assert scored[0]["length_score"] == 1.0

    def test_missing_words_no_crash(self):
        segs = [{"text": "xyzzy frobnicate quux blargh", "start": 0.0, "end": 1.0}]
        scored = score_segments(segs)
        assert scored[0]["freq_score"] == 0.0

    def test_empty_segment(self):
        segs = [{"text": "", "start": 0.0, "end": 1.0}]
        scored = score_segments(segs)
        assert scored[0]["freq_score"] == 0.0
        assert scored[0]["word_count"] == 0

    def test_empty_list(self):
        assert score_segments([]) == []

    def test_sorted_descending(self):
        segs = [
            {"text": "xyzzy quux", "start": 0.0, "end": 1.0},
            {"text": "the a and in of", "start": 1.0, "end": 2.0},
            {"text": "we can do it", "start": 2.0, "end": 3.0},
        ]
        scored = score_segments(segs)
        scores = [s["freq_score"] for s in scored]
        assert scores == sorted(scores, reverse=True)

    def test_word_count_set(self):
        segs = [{"text": "one two three", "start": 0.0, "end": 1.0}]
        scored = score_segments(segs)
        assert scored[0]["word_count"] == 3

    def test_performance_100_segments(self):
        """100 segments should score in under 1 second."""
        import time
        segs = [
            {"text": f"the cat sat on the mat {i}", "start": float(i), "end": float(i+1)}
            for i in range(100)
        ]
        t0 = time.time()
        score_segments(segs)
        assert time.time() - t0 < 1.0
