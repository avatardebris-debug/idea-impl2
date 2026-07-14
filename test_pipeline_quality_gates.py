"""Unit tests for pipeline quality-gate cleanup (status policy, force_advance, reuse)."""

from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Status policy
# ---------------------------------------------------------------------------

def test_is_full_complete_and_mvp():
    from pipeline.dep_policy import (
        is_full_complete,
        phases_fully_built,
        dep_status_satisfied,
        dep_blocking_reason,
        is_polishable,
        is_runner_inactive,
        is_agent_sacred,
    )

    full = {"status": "complete", "phase": 3, "total_phases": 3}
    mvp = {"status": "mvp_complete", "phase": 1, "total_phases": 5}
    early = {"status": "complete", "phase": 1, "total_phases": 5}

    assert phases_fully_built(full)
    assert is_full_complete(full)
    assert not is_full_complete(mvp)
    assert not is_full_complete(early)

    # State-aware: legacy incomplete complete does NOT satisfy
    assert dep_status_satisfied(state=full, context="seeding")
    assert not dep_status_satisfied(state=mvp, context="seeding")
    assert not dep_status_satisfied(state=early, context="seeding")
    # Status-only complete fails closed without state
    assert not dep_status_satisfied("complete", context="seeding")
    assert dep_status_satisfied("field_proven", context="seeding")

    reason = dep_blocking_reason("x", state=early, context="seeding")
    assert reason and "not full" in reason

    assert is_polishable("mvp_complete")
    assert is_runner_inactive("field_proven")
    assert is_agent_sacred("mvp_complete")


def test_is_project_complete_uses_full_complete(tmp_path):
    from pipeline import project_complete as pc

    proj = tmp_path / "projects" / "demo" / "state"
    proj.mkdir(parents=True)
    state_file = proj / "current_idea.json"
    state_file.write_text(
        json.dumps({"status": "mvp_complete", "phase": 1, "total_phases": 3}),
        encoding="utf-8",
    )
    assert pc.is_project_complete("demo", pipeline_dir=tmp_path) is False

    state_file.write_text(
        json.dumps({"status": "complete", "phase": 3, "total_phases": 3}),
        encoding="utf-8",
    )
    assert pc.is_project_complete("demo", pipeline_dir=tmp_path) is True


def test_mark_complete_mvp_vs_full(tmp_path, monkeypatch):
    from pipeline.project_phase import _mark_complete

    monkeypatch.setattr("pipeline.pipeline_config.PROJECT_ROOT", tmp_path)

    project_dir = tmp_path / "projects" / "widget"
    (project_dir / "state").mkdir(parents=True)
    state = {
        "title": "Widget",
        "_slug": "widget",
        "phase": 1,
        "total_phases": 4,
        "description": "test",
    }
    _mark_complete(project_dir, state, "Widget", ideas_path=tmp_path / "master_ideas.md")
    written = json.loads((project_dir / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert written["status"] == "mvp_complete"
    polish = tmp_path / "polish_queue.md"
    assert polish.exists()
    assert "widget" in polish.read_text(encoding="utf-8")

    state2 = {
        "title": "Done",
        "_slug": "done_proj",
        "phase": 2,
        "total_phases": 2,
        "description": "full",
    }
    pd2 = tmp_path / "projects" / "done_proj"
    (pd2 / "state").mkdir(parents=True)
    _mark_complete(pd2, state2, "Done", ideas_path=tmp_path / "master_ideas.md")
    written2 = json.loads((pd2 / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert written2["status"] == "complete"


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def test_build_validation_report_require_tests(tmp_path, monkeypatch):
    from pipeline.agents.validator import build_validation_report

    monkeypatch.setenv("PIPELINE_REQUIRE_TESTS", "1")
    monkeypatch.setenv("PIPELINE_STRUCTURAL_GATE", "0")
    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
    pr = {
        "returncode": 5,
        "stdout": "collected 0 items",
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "no_tests": True,
        "summary_line": "",
    }
    report, is_pass = build_validation_report(1, pr, "", tmp_path, structural_ok=True)
    assert is_pass is False
    assert "Verdict: FAIL" in report


def test_require_tests_default_off(tmp_path, monkeypatch):
    from pipeline.agents.validator import build_validation_report, _require_tests_enabled

    monkeypatch.delenv("PIPELINE_REQUIRE_TESTS", raising=False)
    assert _require_tests_enabled() is False
    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
    pr = {
        "returncode": 5,
        "stdout": "collected 0 items",
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "no_tests": True,
        "summary_line": "",
    }
    _, is_pass = build_validation_report(1, pr, "", tmp_path, structural_ok=True)
    assert is_pass is True


def test_empty_workspace_soft_pass(tmp_path, monkeypatch):
    from pipeline.agents.validator import build_validation_report

    monkeypatch.delenv("PIPELINE_REQUIRE_TESTS", raising=False)
    pr = {
        "returncode": 5,
        "stdout": "collected 0 items",
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "no_tests": True,
        "summary_line": "",
    }
    report, is_pass = build_validation_report(1, pr, "", tmp_path, structural_ok=True)
    assert is_pass is True
    assert "soft pass" in report.lower() or "Verdict: PASS" in report


def test_structural_scan_fail_closed(tmp_path, monkeypatch):
    from pipeline.agents import validator as v

    monkeypatch.setenv("PIPELINE_STRUCTURAL_GATE", "1")

    def boom(_ws):
        raise RuntimeError("scanner exploded")

    monkeypatch.setattr("pipeline.import_graph.scan_workspace", boom)
    ok, section = v._run_structural_scan(tmp_path)
    assert ok is False
    assert "FAIL" in section or "error" in section.lower()


def test_structural_external_import_non_blocking(tmp_path, monkeypatch):
    from pipeline.import_graph import scan_workspace
    from pipeline.agents import validator as v

    monkeypatch.setenv("PIPELINE_STRUCTURAL_GATE", "1")
    (tmp_path / "app.py").write_text(
        "import totally_missing_third_party_xyz\n",
        encoding="utf-8",
    )
    graph = scan_workspace(tmp_path)
    assert graph.has_blocking_issues is False
    assert graph.warnings  # external unresolved

    ok, _ = v._run_structural_scan(tmp_path)
    assert ok is True


def test_structural_local_import_blocking(tmp_path, monkeypatch):
    from pipeline.import_graph import scan_workspace

    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "a.py").write_text("import mypkg.does_not_exist\n", encoding="utf-8")
    graph = scan_workspace(tmp_path)
    assert graph.has_blocking_issues is True


def test_seed_list_skip_derived():
    from pipeline.dep_policy import is_seed_list_skip, is_rebuild_skip

    assert is_seed_list_skip("mvp_complete")
    assert is_seed_list_skip("field_proven")
    assert not is_seed_list_skip("dep_waiting")
    assert not is_seed_list_skip("phase_1_executing")
    assert is_rebuild_skip("field_proven")
    assert is_rebuild_skip("ship_insufficient")
    assert not is_rebuild_skip("phase_2_planning")


def test_count_active_and_seed_cap(tmp_path, monkeypatch):
    from pipeline.project_state import count_active_pipeline_projects
    from pipeline import seeding
    from pipeline.message_bus import MessageBus

    projects = tmp_path / "projects"
    for i, st in enumerate(["phase_1_executing", "phase_2_planning", "complete"]):
        d = projects / f"p{i}" / "state"
        d.mkdir(parents=True)
        (d / "current_idea.json").write_text(
            json.dumps({"status": st, "phase": 1, "total_phases": 3}),
            encoding="utf-8",
        )
    assert count_active_pipeline_projects(projects) == 2

    ideas = tmp_path / "master_ideas.md"
    ideas.write_text("- [ ] **New One** — brand new\n", encoding="utf-8")
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    from pipeline import paths
    monkeypatch.setattr(paths, "get_pipeline_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "projects_dir", lambda: projects)
    monkeypatch.setattr(paths, "project_state_file", lambda s: projects / s / "state" / "current_idea.json")
    monkeypatch.setattr(paths, "project_dir", lambda s: projects / s)
    monkeypatch.setattr(seeding, "project_state_file", lambda s: projects / s / "state" / "current_idea.json")
    monkeypatch.setattr(seeding, "project_dir", lambda s: projects / s)
    monkeypatch.setattr(seeding, "pipeline_projects_dir", lambda: projects)
    monkeypatch.setattr(
        "pipeline.project_state.count_active_pipeline_projects",
        lambda root=None: count_active_pipeline_projects(projects),
    )
    monkeypatch.setattr(
        "pipeline.capability_gaps.seed_next_capability_gap",
        lambda bus: seeding.SEED_EMPTY,
        raising=False,
    )
    seeding._seeded_this_session.clear()
    bus = MessageBus.__new__(MessageBus)
    bus.send = lambda msg: setattr(bus, "_sent", True)
    bus.peek = lambda role: []
    bus.fail = lambda msg: None
    bus.has_active_work = lambda: False

    result = seeding.seed_from_master_list(
        bus, ideas_path=ideas, silent=True, max_active=2,
    )
    assert result == seeding.SEED_BLOCKED
    assert not getattr(bus, "_sent", False)

    result2 = seeding.seed_from_master_list(
        bus, ideas_path=ideas, silent=True, max_active=3,
    )
    assert result2 == seeding.SEED_SEEDED


# ---------------------------------------------------------------------------
# Activity / force advance / reuse
# ---------------------------------------------------------------------------

def test_log_activity_writes(tmp_path, monkeypatch):
    from pipeline import paths

    monkeypatch.setattr(paths, "get_pipeline_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "activity_jsonl", lambda: tmp_path / "state" / "activity.jsonl")

    from pipeline.pipeline_activity import log_activity

    log_activity("test_event", slug="demo", foo=1)
    act = tmp_path / "state" / "activity.jsonl"
    assert act.exists()
    row = json.loads(act.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert row["event"] == "test_event"
    assert row["slug"] == "demo"


def test_force_advance_phase(tmp_path, monkeypatch):
    from pipeline import paths
    from pipeline.force_advance import force_advance_phase

    slug = "stuck_proj"
    proj = tmp_path / "projects" / slug
    (proj / "state").mkdir(parents=True)
    (proj / "state" / "current_idea.json").write_text(
        json.dumps({"status": "phase_1_validating", "phase": 1}),
        encoding="utf-8",
    )
    monkeypatch.setattr(paths, "project_dir", lambda s: tmp_path / "projects" / s)
    monkeypatch.setattr(paths, "get_pipeline_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "activity_jsonl", lambda: tmp_path / "state" / "activity.jsonl")
    monkeypatch.setenv("PIPELINE_FORCE_ADVANCE_QUALITY_RISK", "1")

    assert force_advance_phase(slug, 1, "test stuck", retry_count=3) is True
    st = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert st["status"] == "phase_1_reviewed"
    assert st["review_result"]["force_advanced"] is True
    assert st.get("quality_risk") is True


def test_corpus_weights_force_advanced_is_d():
    from pipeline.corpus_weights import train_tier_from_record, enrich_record_weights

    rec = {
        "test_verdict": "PASS",
        "review_verdict": "PASS",
        "quality_label": "clean",
        "force_advanced": True,
    }
    assert train_tier_from_record(rec) == "D"
    enrich_record_weights(rec)
    assert rec["train_weight"] == 0.0

    rec2 = {
        "test_verdict": "PASS",
        "review_verdict": "PASS",
        "quality_label": "clean",
        "final_status": "mvp_complete",
    }
    assert train_tier_from_record(rec2) == "D"


def test_polish_first_flag(monkeypatch):
    from pipeline.run_loop_seed_idle import polish_first_enabled

    monkeypatch.delenv("PIPELINE_POLISH_FIRST", raising=False)
    assert polish_first_enabled() is False
    monkeypatch.setenv("PIPELINE_POLISH_FIRST", "1")
    assert polish_first_enabled() is True


def test_capability_reuse_soft_and_hard(monkeypatch):
    from pipeline import capability_reuse as cr
    import pipeline.capability_router as router

    def fake_route(task_text, limit=5, min_score=1.0):
        return [{"slug": "csv_analyzer", "score": 9.0, "requires_ok": True}]

    monkeypatch.setattr(router, "route_task", fake_route)
    monkeypatch.setattr(router, "format_suggestions", lambda s: "suggested: csv_analyzer")
    monkeypatch.setenv("CAPABILITY_REUSE_MIN_SCORE", "4.0")

    monkeypatch.delenv("PIPELINE_INVOKE_BEFORE_SEED", raising=False)
    soft = cr.evaluate_seed_reuse("CSV stats", "analyze csv files")
    assert soft.skip_seed is False
    assert soft.suggestions
    assert soft.slug == "csv_analyzer"

    monkeypatch.setenv("PIPELINE_INVOKE_BEFORE_SEED", "1")
    hard = cr.evaluate_seed_reuse("CSV stats", "analyze csv files")
    assert hard.skip_seed is True
    assert hard.score == 9.0


def test_env_flags():
    from pipeline.env_flags import env_bool, env_float

    os.environ.pop("TEST_BOOL_X", None)
    assert env_bool("TEST_BOOL_X", default=True) is True
    os.environ["TEST_BOOL_X"] = "0"
    assert env_bool("TEST_BOOL_X", default=True) is False
    os.environ["TEST_FLOAT_X"] = "3.5"
    assert env_float("TEST_FLOAT_X", default=1.0) == 3.5


def test_invoke_capability_allows_sys_executable():
    from pipeline.capability_tools import _allowed_prefixes
    import sys
    from pathlib import Path

    prefixes = _allowed_prefixes()
    assert any(p.lower().startswith("python") for p in prefixes)
    assert any(p.lower().startswith("py") for p in prefixes)
    exe = str(Path(sys.executable).resolve())
    assert any(exe.lower() in p.lower() or p.lower().rstrip().endswith(Path(exe).name.lower()) for p in prefixes)


def test_agent_role_map_importable():
    from pipeline.agent_role_map import NEXT_ROLE_MAP, next_role

    assert next_role("executor") == "reviewer"
    assert "validator" in NEXT_ROLE_MAP


def test_seed_skips_mvp_without_starving(tmp_path, monkeypatch):
    """mvp_complete / hermes failure must not return SEED_SEEDED and block the list."""
    from pipeline import seeding
    from pipeline.message_bus import MessageBus

    ideas = tmp_path / "master_ideas.md"
    ideas.write_text(
        "- [ ] **MVP Done** — already built\n"
        "- [ ] **Next Tool** — brand new idea\n",
        encoding="utf-8",
    )
    # Fake pipeline dirs
    projects = tmp_path / "projects"
    mvp_dir = projects / "mvp_done" / "state"
    mvp_dir.mkdir(parents=True)
    (mvp_dir / "current_idea.json").write_text(
        json.dumps({
            "title": "MVP Done",
            "status": "mvp_complete",
            "phase": 1,
            "total_phases": 3,
        }),
        encoding="utf-8",
    )
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    from pipeline import paths
    monkeypatch.setattr(paths, "get_pipeline_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "projects_dir", lambda: projects)
    monkeypatch.setattr(paths, "project_state_file", lambda s: projects / s / "state" / "current_idea.json")
    monkeypatch.setattr(paths, "project_dir", lambda s: projects / s)
    monkeypatch.setattr(seeding, "project_state_file", lambda s: projects / s / "state" / "current_idea.json")
    monkeypatch.setattr(seeding, "project_dir", lambda s: projects / s)
    monkeypatch.setattr(seeding, "pipeline_projects_dir", lambda: projects)
    # No capability gaps
    monkeypatch.setattr(
        "pipeline.capability_gaps.seed_next_capability_gap",
        lambda bus: seeding.SEED_EMPTY,
        raising=False,
    )
    seeding._seeded_this_session.clear()
    bus = MessageBus.__new__(MessageBus)
    bus.send = lambda msg: setattr(bus, "_last", msg) or None
    bus.peek = lambda role: []
    bus.fail = lambda msg: None

    result = seeding.seed_from_master_list(bus, ideas_path=ideas, silent=True)
    assert result == seeding.SEED_SEEDED
    assert getattr(bus, "_last", None) is not None
    assert bus._last.payload.get("title") == "Next Tool"


def test_hermes_failure_continues(tmp_path, monkeypatch):
    from pipeline import seeding
    from pipeline.message_bus import MessageBus

    ideas = tmp_path / "master_ideas.md"
    ideas.write_text(
        "- [ ] **Hermes Task** — do research. --hermes\n"
        "- [ ] **After Hermes** — normal software idea\n",
        encoding="utf-8",
    )
    projects = tmp_path / "projects"
    projects.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    from pipeline import paths
    monkeypatch.setattr(paths, "get_pipeline_dir", lambda: tmp_path)
    monkeypatch.setattr(paths, "projects_dir", lambda: projects)
    monkeypatch.setattr(paths, "project_state_file", lambda s: projects / s / "state" / "current_idea.json")
    monkeypatch.setattr(paths, "project_dir", lambda s: projects / s)
    monkeypatch.setattr(seeding, "project_state_file", lambda s: projects / s / "state" / "current_idea.json")
    monkeypatch.setattr(seeding, "project_dir", lambda s: projects / s)
    monkeypatch.setattr(seeding, "pipeline_projects_dir", lambda: projects)

    class Boom:
        def run(self, **kwargs):
            raise RuntimeError("Hermes not found")

    monkeypatch.setattr("pipeline.hermes_runner.HermesGoalRunner", Boom)
    seeding._seeded_this_session.clear()
    bus = MessageBus.__new__(MessageBus)
    bus.send = lambda msg: setattr(bus, "_last", msg) or None
    bus.peek = lambda role: []
    bus.fail = lambda msg: None

    result = seeding.seed_from_master_list(bus, ideas_path=ideas, silent=True)
    assert result == seeding.SEED_SEEDED
    assert bus._last.payload.get("title") == "After Hermes"
