"""
frequency_scorer.py — SUBTLEX-US frequency scoring for video segments.

Loads data/subtlex_us.txt (word TAB rank TAB freq_per_million TAB POS).
Scores each segment by the mean inverse rank of known words, penalising
segments that are too short (<3 words) or too long (>15 words).

Formula:
    freq_score = mean(1.0 / rank[w] for w in tokens if w in rank_dict)
    length_score = 1.0 if 3 <= word_count <= 15 else 0.4
    segment.score = freq_score * length_score
"""
from __future__ import annotations
import pathlib
import re
from typing import Any

_DATA_DIR = pathlib.Path(__file__).parent / "data"
_SUBTLEX_PATH = _DATA_DIR / "subtlex_us.txt"

# Module-level cache: loaded once per process
_rank_dict: dict[str, float] | None = None


def _load_rank_dict() -> dict[str, float]:
    """Load SUBTLEX-US frequency list into a {word: rank} dict (lowercase)."""
    global _rank_dict
    if _rank_dict is not None:
        return _rank_dict

    if not _SUBTLEX_PATH.exists():
        raise FileNotFoundError(
            f"SUBTLEX-US data not found at {_SUBTLEX_PATH}. "
            "Run `python -m video_babbel_enhanced fetch-data` to download it, "
            "or place subtlex_us.txt in the data/ directory."
        )

    rank_dict: dict[str, float] = {}
    with _SUBTLEX_PATH.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            word = parts[0].strip().lower()
            try:
                rank = float(parts[1])
                if rank > 0 and word:
                    rank_dict[word] = rank
            except ValueError:
                continue  # skip header or malformed lines

    _rank_dict = rank_dict
    return _rank_dict


def _tokenize(text: str) -> list[str]:
    """Lowercase and strip punctuation, return list of word tokens."""
    return [t for t in re.findall(r"[a-z']+", text.lower()) if t]


def score_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score segments by word frequency and length, return sorted descending.

    Adds 'freq_score', 'length_score', and 'word_count' to each segment dict.
    Segments are sorted in-place and returned (highest score first).
    """
    rank_dict = _load_rank_dict()

    for seg in segments:
        text = seg.get("text", "") or seg.get("l1_text", "")
        tokens = _tokenize(text)
        word_count = len(tokens)

        if word_count == 0:
            seg["freq_score"] = 0.0
            seg["length_score"] = 0.4
            seg["word_count"] = 0
            continue

        # Frequency score: mean inverse rank of known words
        inv_ranks = [1.0 / rank_dict[w] for w in tokens if w in rank_dict]
        freq_score = sum(inv_ranks) / len(tokens) if inv_ranks else 0.0

        # Length penalty for very short or very long segments
        length_score = 1.0 if 3 <= word_count <= 15 else 0.4

        seg["freq_score"] = round(freq_score * length_score, 8)
        seg["length_score"] = length_score
        seg["word_count"] = word_count

    segments.sort(key=lambda s: s.get("freq_score", 0.0), reverse=True)
    return segments


def get_rank_dict() -> dict[str, float]:
    """Return the loaded {word: rank} dict (for testing and inspection)."""
    return _load_rank_dict()
