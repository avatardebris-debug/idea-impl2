"""Tests for complete pytest gate → complete / complete_with_bugs."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.complete_gate import assess_complete_quality
from pipeline.dep_policy import is_full_complete
from pipeline.project_phase import _mark_complete


def _proj(tmp: Path, *, force: bool = False) -> Path:
    p = tmp / "proj"
    (p / "workspace" / "tests").mkdir(parents=True)
    (p / "state").mkdir(parents=True)
    (p / "workspace" / "mod.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (p / "workspace" / "tests" / "test_mod.py").write_text(
        "from mod import f\n\ndef test_f():\n    assert f() == 1\n",
        encoding="utf-8",
    )
    state = {
        "title": "proj",
        "status": "phase_1_reviewed",
        "phase": 1,
        "total_phases": 1,
        "_slug": "proj",
    }
    if force:
        state["force_advanced"] = True
        state["quality_risk"] = True
    (p / "state" / "current_idea.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    return p


def test_assess_clean_pytest(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_COMPLETE_PYTEST", "1")
    monkeypatch.setenv("PIPELINE_REQUIRE_TESTS", "0")
    p = _proj(tmp_path)
    state = json.loads((p / "state/current_idea.json").read_text(encoding="utf-8"))
    a = assess_complete_quality(p, state)
    assert a["status"] == "complete"
    assert a["reasons"] == []


def test_assess_force_advanced_is_with_bugs(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_COMPLETE_PYTEST", "1")
    p = _proj(tmp_path, force=True)
    state = json.loads((p / "state/current_idea.json").read_text(encoding="utf-8"))
    a = assess_complete_quality(p, state)
    assert a["status"] == "complete_with_bugs"
    assert any("force" in r or "quality" in r for r in a["reasons"])


def test_assess_pytest_fail(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_COMPLETE_PYTEST", "1")
    p = _proj(tmp_path)
    (p / "workspace" / "tests" / "test_mod.py").write_text(
        "def test_bad():\n    assert False\n",
        encoding="utf-8",
    )
    state = json.loads((p / "state/current_idea.json").read_text(encoding="utf-8"))
    a = assess_complete_quality(p, state)
    assert a["status"] == "complete_with_bugs"
    assert any("pytest" in r for r in a["reasons"])


def test_mark_complete_with_bugs(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_COMPLETE_PYTEST", "1")
    # project_dir is under PIPELINE_DIR/projects
    projects = tmp_path / "projects"
    projects.mkdir()
    p = projects / "proj"
    (p / "workspace" / "tests").mkdir(parents=True)
    (p / "state").mkdir(parents=True)
    (p / "phases" / "phase_1").mkdir(parents=True)
    (p / "phases" / "phase_1" / "tasks.md").write_text(
        "- [x] Task 1: done\n", encoding="utf-8"
    )
    (p / "workspace" / "mod.py").write_text("x=1\n", encoding="utf-8")
    (p / "workspace" / "tests" / "test_mod.py").write_text(
        "def test_bad():\n    assert 0\n", encoding="utf-8"
    )
    state = {
        "title": "proj",
        "status": "phase_1_reviewed",
        "phase": 1,
        "total_phases": 1,
        "_slug": "proj",
    }
    (p / "state" / "current_idea.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    _mark_complete(p, state, "proj")
    st = json.loads((p / "state/current_idea.json").read_text(encoding="utf-8"))
    assert st["status"] == "complete_with_bugs"
    assert st.get("quality_risk") is True
    assert is_full_complete(st) is True


def test_full_complete_includes_with_bugs():
    assert is_full_complete(
        {"status": "complete_with_bugs", "phase": 2, "total_phases": 2}
    )
