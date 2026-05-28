"""Tests for corpus collection closeout gate."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.corpus_gate import (
    CollectGateResult,
    run_collect_gate,
    should_skip_collect,
)
from pipeline.corpus_verdicts import verdict_from_report


def test_verdict_parsing() -> None:
    assert verdict_from_report("## Verdict\nPASS\n") == "PASS"
    assert verdict_from_report("Verdict: FAIL\n") == "FAIL"
    assert verdict_from_report("") == "UNKNOWN"


def test_gate_blocks_empty_workspace(tmp_path: Path, monkeypatch) -> None:
    import pipeline.corpus_gate as cg

    monkeypatch.setattr(cg, "gate_policy", lambda: "enforce")

    proj = tmp_path / "empty_proj"
    (proj / "state").mkdir(parents=True)
    (proj / "phases" / "phase_1").mkdir(parents=True)
    (proj / "phases" / "phase_1" / "tasks.md").write_text("- [ ] do thing\n", encoding="utf-8")
    (proj / "phases" / "phase_1" / "validation_report.md").write_text(
        "Verdict: PASS\n", encoding="utf-8"
    )
    (proj / "phases" / "phase_1" / "review.md").write_text("Verdict: PASS\n", encoding="utf-8")
    (proj / "workspace").mkdir()

    state = {"_slug": "empty_proj", "status": "complete", "total_phases": 1, "phase": 1}
    result = run_collect_gate(proj, state, policy="enforce")
    assert not result.allow_collect
    assert any("workspace" in b.lower() or ".py" in b for b in result.blockers)


def test_gate_passes_minimal_project(tmp_path: Path, monkeypatch) -> None:
    import pipeline.corpus_gate as cg

    monkeypatch.setattr(cg, "gate_policy", lambda: "enforce")
    monkeypatch.setattr(cg, "_check_quality_score", lambda slug, policy="enforce": [])

    proj = tmp_path / "ok_proj"
    (proj / "workspace").mkdir(parents=True)
    (proj / "workspace" / "main.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    (proj / "phases" / "phase_1").mkdir(parents=True)
    (proj / "phases" / "phase_1" / "tasks.md").write_text("- [ ] task\n", encoding="utf-8")
    (proj / "phases" / "phase_1" / "validation_report.md").write_text(
        "Verdict: PASS\n", encoding="utf-8"
    )
    (proj / "phases" / "phase_1" / "review.md").write_text("## Verdict\nPASS\n", encoding="utf-8")
    (proj / "state").mkdir()
    state = {"_slug": "ok_proj", "status": "complete", "total_phases": 1, "phase": 1}

    result = run_collect_gate(proj, state, policy="enforce")
    assert result.allow_collect


def test_warn_policy_always_allows_collect(tmp_path: Path, monkeypatch) -> None:
    import pipeline.corpus_gate as cg

    monkeypatch.setattr(cg, "gate_policy", lambda: "warn")
    monkeypatch.setattr(cg, "_check_quality_score", lambda slug, policy="warn": [])

    proj = tmp_path / "bad"
    (proj / "state").mkdir(parents=True)
    state = {"_slug": "bad", "status": "complete", "total_phases": 1, "phase": 1}
    result = run_collect_gate(proj, state, policy="warn")
    assert result.allow_collect
    assert not result.passed


def test_should_skip_collect_off(monkeypatch, tmp_path: Path) -> None:
    import pipeline.corpus_gate as cg

    monkeypatch.setattr(cg, "gate_policy", lambda: "off")
    proj = tmp_path / "x"
    (proj / "state").mkdir(parents=True)
    state = {"status": "complete"}
    blocked, gate = should_skip_collect(proj, state)
    assert not blocked
    assert gate is None
