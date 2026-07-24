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


def test_mark_complete_ignores_older_phase_open_checkboxes(tmp_path: Path, monkeypatch):
    """Current phase all [x] → complete even if phase 1 still has open boxes."""
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_COMPLETE_PYTEST", "0")
    monkeypatch.setenv("PIPELINE_REQUIRE_TESTS", "0")

    projects = tmp_path / "projects"
    p = projects / "multi"
    (p / "workspace").mkdir(parents=True)
    (p / "state").mkdir(parents=True)
    (p / "phases" / "phase_1").mkdir(parents=True)
    (p / "phases" / "phase_2").mkdir(parents=True)
    # Stale opens on phase 1 (historical) — must NOT block complete
    phase1_tasks = (
        "- [x] Task 1: done early\n"
        "- [ ] Task 2: abandoned leftover\n"
        "- [ ] Task 3: never closed\n"
    )
    phase1_path = p / "phases" / "phase_1" / "tasks.md"
    phase1_path.write_text(phase1_tasks, encoding="utf-8")
    # Current / last phase fully closed
    (p / "phases" / "phase_2" / "tasks.md").write_text(
        "- [x] Task 1: final work\n"
        "- [x] Task 2: review fixes\n",
        encoding="utf-8",
    )
    (p / "workspace" / "mod.py").write_text("x = 1\n", encoding="utf-8")

    state = {
        "title": "multi",
        "status": "phase_2_reviewed",
        "phase": 2,
        "total_phases": 2,
        "_slug": "multi",
    }
    (p / "state" / "current_idea.json").write_text(json.dumps(state), encoding="utf-8")
    _mark_complete(p, state, "multi")
    st = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert st["status"] in ("complete", "complete_with_bugs")
    assert "complete_blocked_reason" not in st
    # Historical phase-1 tasks must not be rewritten/closed silently
    assert phase1_path.read_text(encoding="utf-8") == phase1_tasks
    assert "- [ ] Task 2:" in phase1_path.read_text(encoding="utf-8")


def test_mark_complete_blocks_on_current_phase_open(tmp_path: Path, monkeypatch):
    """Open boxes on the current phase still block complete."""
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_COMPLETE_PYTEST", "0")

    projects = tmp_path / "projects"
    p = projects / "blocked"
    (p / "workspace").mkdir(parents=True)
    (p / "state").mkdir(parents=True)
    (p / "phases" / "phase_1").mkdir(parents=True)
    (p / "phases" / "phase_2").mkdir(parents=True)
    (p / "phases" / "phase_1" / "tasks.md").write_text(
        "- [x] Task 1: old done\n",
        encoding="utf-8",
    )
    (p / "phases" / "phase_2" / "tasks.md").write_text(
        "- [x] Task 1: ok\n"
        "- [ ] Task 2: still open on current phase\n",
        encoding="utf-8",
    )
    state = {
        "title": "blocked",
        "status": "phase_2_reviewed",
        "phase": 2,
        "total_phases": 2,
        "_slug": "blocked",
    }
    (p / "state" / "current_idea.json").write_text(json.dumps(state), encoding="utf-8")
    _mark_complete(p, state, "blocked")
    st = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert st["status"] == "phase_2_executing"
    assert "complete_blocked_reason" in st
    assert "phase 2" in st["complete_blocked_reason"]


def test_mark_complete_waived_allows_open_current_phase(tmp_path: Path, monkeypatch):
    """complete_blocked_waived → terminal complete; current-phase open boxes left as-is."""
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_COMPLETE_PYTEST", "0")
    monkeypatch.setenv("PIPELINE_REQUIRE_TESTS", "0")

    projects = tmp_path / "projects"
    p = projects / "waived"
    (p / "workspace").mkdir(parents=True)
    (p / "state").mkdir(parents=True)
    (p / "phases" / "phase_1").mkdir(parents=True)
    (p / "phases" / "phase_2").mkdir(parents=True)
    (p / "phases" / "phase_1" / "tasks.md").write_text(
        "- [x] Task 1: old done\n",
        encoding="utf-8",
    )
    phase2_tasks = (
        "- [x] Task 1: ok\n"
        "- [ ] Task 2: still open on current phase\n"
    )
    phase2_path = p / "phases" / "phase_2" / "tasks.md"
    phase2_path.write_text(phase2_tasks, encoding="utf-8")
    (p / "workspace" / "mod.py").write_text("x = 1\n", encoding="utf-8")

    state = {
        "title": "waived",
        "status": "phase_2_reviewed",
        "phase": 2,
        "total_phases": 2,
        "_slug": "waived",
        "complete_blocked_waived": True,
        "complete_blocked_waived_reason": "FIX_GATE_ONLY consumer",
    }
    (p / "state" / "current_idea.json").write_text(json.dumps(state), encoding="utf-8")
    _mark_complete(p, state, "waived")
    st = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert st["status"] in ("complete", "complete_with_bugs")
    assert "complete_blocked_reason" not in st
    # Must not rewrite open checkboxes when waived
    assert phase2_path.read_text(encoding="utf-8") == phase2_tasks
    assert "- [ ] Task 2:" in phase2_path.read_text(encoding="utf-8")
