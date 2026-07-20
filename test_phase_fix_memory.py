"""Tests for structured phase fix memory."""

from __future__ import annotations

from pathlib import Path

from pipeline.phase_fix_memory import (
    MAX_RECURRING,
    clear_fix_memory,
    format_for_prompt,
    load_fix_memory,
    record_failed_attempt,
)


def test_record_and_recurring(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / "state").mkdir(parents=True)
    data = record_failed_attempt(
        proj,
        1,
        summary="ImportError: no module named foo",
        source_text="E   ModuleNotFoundError: No module named 'foo'\nFAILED tests/test_x.py",
        ban=True,
    )
    assert len(data["attempts"]) == 1
    assert data["attempts"][0]["summary"]
    assert data["recurring_signatures"] or data["banned_signatures"]
    loaded = load_fix_memory(proj, 1)
    assert len(loaded["attempts"]) == 1


def test_format_wording_is_failure_signatures_not_banned_fixes(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / "state").mkdir(parents=True)
    record_failed_attempt(proj, 2, summary="first fail", signature="sig_a", ban=True)
    record_failed_attempt(proj, 2, summary="second fail", signature="sig_b", ban=True)
    record_failed_attempt(proj, 2, summary="third fail", signature="sig_c", ban=True)
    block = format_for_prompt(proj, 2, last_n=3)
    assert "Recurring failure signatures" in block
    assert "failure signatures" in block.lower()
    assert "banned fixes" not in block.lower()
    assert "sig_a" in block or "sig_b" in block
    assert "third fail" in block
    assert "first fail" in block


def test_recurring_cap(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / "state").mkdir(parents=True)
    for i in range(MAX_RECURRING + 10):
        record_failed_attempt(
            proj, 1, summary=f"fail {i}", signature=f"unique_sig_{i}", ban=True
        )
    data = load_fix_memory(proj, 1)
    assert len(data["recurring_signatures"]) <= MAX_RECURRING
    assert len(data["banned_signatures"]) <= MAX_RECURRING


def test_clear(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / "state").mkdir(parents=True)
    record_failed_attempt(proj, 1, summary="x", signature="y")
    clear_fix_memory(proj, 1)
    data = load_fix_memory(proj, 1)
    assert data["attempts"] == []
    assert data["recurring_signatures"] == []
