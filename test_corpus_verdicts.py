"""Tests for shared corpus verdict parsing."""

from pipeline.corpus_verdicts import parse_phase_verdicts, verdict_from_report


def test_parse_phase_verdicts() -> None:
    test_v, review_v = parse_phase_verdicts("Verdict: PASS\n", "## Verdict\nFAIL\n")
    assert test_v == "PASS"
    assert review_v == "FAIL"
