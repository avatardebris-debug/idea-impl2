"""Integration tests for grok_build phase driver + FakeEngine."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pipeline.engines.base import EngineResult
from pipeline.engines.driver import (
    DriverOutcome,
    fallback_to_classic,
    run_grok_phase,
)
from pipeline.engines.hook import find_grok_build_candidates, tick_grok_build_engines
from pipeline.engines.selection import ENGINE_CLASSIC, ENGINE_GROK_BUILD
from pipeline.review_artifacts import build_review_result, review_verdict_is_fail


class FakeBus:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def send(self, msg: Any) -> None:
        self.messages.append(msg)


class FakeEngine:
    """Creates files, marks tasks [x], writes PASS review.md."""

    def __init__(self, *, fail_step: str | None = None) -> None:
        self.calls: list[str] = []
        self.fail_step = fail_step

    def __call__(
        self,
        slug: str,
        phase: int,
        step: str,
        *,
        project_dir: Path,
        workspace: Path,
        **kwargs: Any,
    ) -> EngineResult:
        self.calls.append(step)
        if self.fail_step and step == self.fail_step:
            return EngineResult(
                success=False,
                step=step,
                exit_code=127,
                error=f"fake hard failure on {step}",
            )

        phase_dir = project_dir / "phases" / f"phase_{phase}"
        phase_dir.mkdir(parents=True, exist_ok=True)
        workspace.mkdir(parents=True, exist_ok=True)

        if step == "idea_plan":
            state_dir = project_dir / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "master_plan.md").write_text(
                "# Master Plan: Fake\n\n## Goal\nFake MVP\n\n"
                "## Phase 1: Foundation\n"
                "- **Description**: scaffold\n"
                "- **Deliverable**: main.py\n"
                "- **Dependencies**: none\n"
                "- **Success criteria**:\n"
                "  - main.py exists\n\n"
                "## Architecture Notes\n- test\n\n## Risks\n- none\n\n"
                "## Phase count\n- total_phases: 1\n",
                encoding="utf-8",
            )
            idea = state_dir / "current_idea.json"
            if idea.is_file():
                try:
                    data = json.loads(idea.read_text(encoding="utf-8"))
                    data["total_phases"] = 1
                    idea.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                except Exception:
                    pass

        if step == "phase_plan":
            phase_dir.mkdir(parents=True, exist_ok=True)
            (phase_dir / "tasks.md").write_text(
                f"# Phase {phase} Tasks: Fake\n\n"
                "- [ ] Task 1: Create main\n"
                "  - What: write main.py\n"
                "  - Files: main.py\n"
                "  - Done when: file exists\n",
                encoding="utf-8",
            )

        if step == "implement":
            (workspace / "main.py").write_text(
                'def hello():\n    return "ok"\n',
                encoding="utf-8",
            )
            # Close main + overflow task lists if present
            for tasks in (
                phase_dir / "tasks.md",
                project_dir / f"phases/phase_{phase}_overflow" / "tasks.md",
            ):
                if tasks.is_file():
                    text = tasks.read_text(encoding="utf-8")
                    text = re.sub(r"- \[ \]", "- [x]", text)
                    tasks.write_text(text, encoding="utf-8")

        if step in ("review", "fix"):
            review = (
                f"# Code Review — Phase {phase}\n\n"
                f"### What's Good\n"
                f"- FakeEngine implemented workspace/main.py cleanly.\n"
                f"- Tasks marked complete after Done-when met.\n\n"
                f"## Blocking Bugs\n"
                f"- None\n\n"
                f"## Non-Blocking Notes\n"
                f"- None\n\n"
                f"## Reusable Components\n"
                f"- None\n\n"
                f"## Verdict\n"
                f"PASS — synthetic review for dual-engine tests\n"
            )
            # ensure length for review_artifacts_complete
            review += "\n### Extra\nSynthetic padding so artifact checks treat this as a real review body.\n"
            (phase_dir / "review.md").write_text(review, encoding="utf-8")

        if step == "debug":
            (workspace / "fix.py").write_text("# fixed\n", encoding="utf-8")

        if step == "deep_review":
            (phase_dir / "deep_review.md").write_text(
                f"# Deep Review — Phase {phase}\n\nPASS advisory\n",
                encoding="utf-8",
            )

        return EngineResult(success=True, step=step, summary=f"fake {step} ok")


def _make_project(tmp_path: Path, *, engine: str = ENGINE_GROK_BUILD) -> Path:
    proj = tmp_path / "fake_proj"
    (proj / "state").mkdir(parents=True)
    (proj / "workspace").mkdir(parents=True)
    (proj / "phases" / "phase_1").mkdir(parents=True)
    (proj / "phases" / "phase_1" / "tasks.md").write_text(
        "# Phase 1 Tasks\n\n"
        "- [ ] Task 1: create main\n"
        "  - What: hello module\n"
        "  - Files: main.py\n"
        "  - Done when: main.py exists\n",
        encoding="utf-8",
    )
    (proj / "state" / "master_plan.md").write_text(
        "# Master Plan: Fake Proj\n\n"
        "## Goal\nShip a hello module for dual-engine tests.\n\n"
        "## Phase 1: MVP — Foundation\n"
        "- **Description**: Create main.py with hello()\n"
        "- **Deliverable**: workspace/main.py\n"
        "- **Dependencies**: none\n"
        "- **Success criteria**:\n"
        "  - main.py exists and is importable\n\n"
        "## Architecture Notes\n- Minimal Python module\n\n"
        "## Risks\n- None for tests\n\n"
        "## Phase count\n- total_phases: 1\n",
        encoding="utf-8",
    )
    state = {
        "title": "Fake Proj",
        "slug": "fake_proj",
        "status": "phase_1_executing",
        "phase": 1,
        "total_phases": 1,
        "engine": engine,
    }
    (proj / "state" / "current_idea.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    return proj


def test_plan_skills_run_when_artifacts_missing(tmp_path: Path):
    """Driver runs idea_plan + phase_plan before implement when plan files absent."""
    proj = tmp_path / "plan_first"
    (proj / "state").mkdir(parents=True)
    (proj / "workspace").mkdir(parents=True)
    (proj / "phases" / "phase_1").mkdir(parents=True)
    # No master_plan.md, no tasks.md
    (proj / "state" / "current_idea.json").write_text(
        json.dumps(
            {
                "title": "Plan First",
                "description": "A tool that prints hello",
                "slug": "plan_first",
                "status": "phase_1_executing",
                "phase": 1,
                "total_phases": 1,
                "engine": ENGINE_GROK_BUILD,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()
    fake = FakeEngine()
    outcome = run_grok_phase(
        bus,
        proj,
        state,
        1,
        "plan_first",
        invoke=fake,
        skip_validate=True,
    )
    assert "idea_plan" in fake.calls
    assert "phase_plan" in fake.calls
    assert fake.calls.index("idea_plan") < fake.calls.index("phase_plan")
    assert fake.calls.index("phase_plan") < fake.calls.index("implement")
    assert (proj / "state" / "master_plan.md").is_file()
    assert (proj / "phases" / "phase_1" / "tasks.md").is_file()
    assert outcome.completed or outcome.advanced or not outcome.fell_back


def test_plan_skills_skipped_when_present(tmp_path: Path):
    proj = _make_project(tmp_path)
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()
    fake = FakeEngine()
    run_grok_phase(
        bus, proj, state, 1, "fake_proj", invoke=fake, skip_validate=True
    )
    assert "idea_plan" not in fake.calls
    assert "phase_plan" not in fake.calls
    assert "implement" in fake.calls


def test_hook_finds_candidate_without_tasks(tmp_path: Path):
    root = tmp_path / "projects"
    root.mkdir()
    p = root / "needs_plan"
    p.mkdir()
    (p / "state").mkdir()
    (p / "workspace").mkdir()
    (p / "phases" / "phase_1").mkdir(parents=True)
    (p / "state" / "current_idea.json").write_text(
        json.dumps(
            {
                "title": "Needs Plan",
                "slug": "needs_plan",
                "status": "phase_1_executing",
                "phase": 1,
                "engine": ENGINE_GROK_BUILD,
            }
        ),
        encoding="utf-8",
    )
    found = find_grok_build_candidates(root)
    assert any(slug == "needs_plan" for *_, slug in found)


def test_fake_engine_completes_phase(tmp_path: Path):
    proj = _make_project(tmp_path)
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()
    fake = FakeEngine()

    outcome = run_grok_phase(
        bus,
        proj,
        state,
        1,
        "fake_proj",
        invoke=fake,
        skip_validate=True,
    )

    assert isinstance(outcome, DriverOutcome)
    assert not outcome.fell_back
    assert not outcome.blocked
    assert outcome.completed or outcome.advanced
    assert "implement" in fake.calls
    assert "review" in fake.calls
    assert (proj / "workspace" / "main.py").is_file()
    tasks = (proj / "phases" / "phase_1" / "tasks.md").read_text(encoding="utf-8")
    assert "- [ ]" not in tasks
    assert "- [x]" in tasks
    review = (proj / "phases" / "phase_1" / "review.md").read_text(encoding="utf-8")
    assert not review_verdict_is_fail(review)
    rr = build_review_result(
        review_content=review,
        review_path="phases/phase_1/review.md",
        tasks_path="phases/phase_1/tasks.md",
        workspace_path=str(proj / "workspace"),
    )
    assert rr["blocking_bugs"] == 0

    final = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    # complete / mvp_complete, or thin-ship terminal field_proven / ship_insufficient
    assert final.get("status") in (
        "complete",
        "mvp_complete",
        "phase_1_reviewed",
        "field_proven",
        "ship_insufficient",
    )
    if outcome.completed:
        assert final.get("status") in (
            "complete",
            "mvp_complete",
            "field_proven",
            "ship_insufficient",
        )


def test_hard_failure_falls_back_to_classic(tmp_path: Path):
    proj = _make_project(tmp_path)
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()
    fake = FakeEngine(fail_step="implement")

    outcome = run_grok_phase(
        bus,
        proj,
        state,
        1,
        "fake_proj",
        invoke=fake,
        skip_validate=True,
    )

    assert outcome.fell_back
    assert not outcome.completed
    final = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert final.get("engine") == ENGINE_CLASSIC
    assert final.get("engine_fallback") == ENGINE_CLASSIC
    assert any(getattr(m, "to_agent", None) == "executor" for m in bus.messages)


def test_fallback_helper_enqueues_executor(tmp_path: Path):
    proj = _make_project(tmp_path)
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()
    fallback_to_classic(bus, proj, state, 1, "fake_proj", reason="unit test")
    assert state["engine"] == ENGINE_CLASSIC
    assert len(bus.messages) == 1
    assert bus.messages[0].to_agent == "executor"


def test_open_tasks_block_advance(tmp_path: Path):
    """If FakeEngine skips marking tasks, gates block advance."""
    proj = _make_project(tmp_path)
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()

    def noop_invoke(slug, phase, step, **kw):
        # review pass but leave tasks open
        if step == "review":
            p = kw["project_dir"] / "phases" / f"phase_{phase}" / "review.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                "# Code Review — Phase 1\n\n"
                "### What's Good\n- nothing implemented\n\n"
                "## Blocking Bugs\n- None\n\n"
                "## Non-Blocking Notes\n- None\n\n"
                "## Reusable Components\n- None\n\n"
                "## Verdict\n"
                "PASS — but tasks still open intentionally for gate test\n",
                encoding="utf-8",
            )
        return EngineResult(success=True, step=step, dry_run=False)

    outcome = run_grok_phase(
        bus,
        proj,
        state,
        1,
        "fake_proj",
        invoke=noop_invoke,
        skip_validate=True,
    )
    assert outcome.blocked
    assert not outcome.completed
    assert not outcome.advanced


def test_find_candidates(tmp_path: Path, monkeypatch):
    root = tmp_path / "projects"
    root.mkdir()
    proj = _make_project(root)
    # _make_project uses tmp parent name; move into projects/
    # already under root if we pass root — _make_project uses tmp_path / fake_proj
    # so proj is root/fake_proj — good
    cands = find_grok_build_candidates(root)
    assert len(cands) == 1
    assert cands[0][3] == "fake_proj"


def test_tick_hook_runs_fake(tmp_path: Path, monkeypatch):
    root = tmp_path / "projects"
    root.mkdir()
    proj = _make_project(root)
    bus = FakeBus()

    # Patch run_grok_phase via driver used by hook
    calls = []

    def fake_run(bus, project_dir, state, phase, slug, **kw):
        calls.append(slug)
        from pipeline.engines.driver import DriverOutcome

        return DriverOutcome(completed=True, reason="test")

    monkeypatch.setattr(
        "pipeline.engines.driver.run_grok_phase",
        fake_run,
    )
    # Reset retry throttle
    from pipeline.engines import hook as hook_mod

    hook_mod._last_attempt.clear()

    n = tick_grok_build_engines(bus, pipeline_dir=tmp_path)
    assert n >= 1
    assert "fake_proj" in calls


def test_classic_engine_not_in_candidates(tmp_path: Path):
    root = tmp_path / "projects"
    root.mkdir()
    _make_project(root, engine=ENGINE_CLASSIC)
    assert find_grok_build_candidates(root) == []


def test_validation_fail_blocks_advance(tmp_path: Path, monkeypatch):
    """Issue 1: red pytest after debug must not complete/advance."""
    proj = _make_project(tmp_path)
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()
    fake = FakeEngine()

    def fake_validate(workspace):
        return False, {"failed": 1, "returncode": 1, "summary_line": "1 failed"}

    monkeypatch.setattr(
        "pipeline.engines.driver._run_validate",
        fake_validate,
    )

    outcome = run_grok_phase(
        bus,
        proj,
        state,
        1,
        "fake_proj",
        invoke=fake,
        skip_validate=False,
    )
    assert outcome.blocked
    assert not outcome.completed
    assert not outcome.advanced
    assert "validation" in (outcome.reason or "").lower()
    final = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert final.get("status") == "phase_1_executing"
    assert final.get("engine") == ENGINE_GROK_BUILD  # not demoted on first block


def test_soft_review_fail_no_auto_pass(tmp_path: Path):
    """Issue 2: soft review fail without review.md must not complete."""
    proj = _make_project(tmp_path)
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()

    def soft_review_fail(slug, phase, step, **kw):
        project_dir = kw["project_dir"]
        workspace = kw["workspace"]
        if step == "implement":
            (workspace / "main.py").write_text("x=1\n", encoding="utf-8")
            tasks = project_dir / "phases" / f"phase_{phase}" / "tasks.md"
            text = tasks.read_text(encoding="utf-8")
            tasks.write_text(re.sub(r"- \[ \]", "- [x]", text), encoding="utf-8")
            return EngineResult(success=True, step=step)
        if step == "review":
            # Soft fail, no review.md written
            return EngineResult(
                success=False,
                step=step,
                exit_code=1,
                error="review crashed",
            )
        return EngineResult(success=True, step=step)

    outcome = run_grok_phase(
        bus,
        proj,
        state,
        1,
        "fake_proj",
        invoke=soft_review_fail,
        skip_validate=True,
    )
    assert outcome.blocked
    assert not outcome.completed
    assert not outcome.advanced
    review = (proj / "phases" / "phase_1" / "review.md").read_text(encoding="utf-8")
    assert review_verdict_is_fail(review)
    assert "auto" not in review.lower() or "FAIL" in review


def test_overflow_does_not_enqueue_classic_for_grok(tmp_path: Path):
    """Issue 3: overflow on grok_build must not dual-schedule classic executor."""
    proj = _make_project(tmp_path)
    overflow = proj / "phases" / "phase_1_overflow"
    overflow.mkdir(parents=True)
    (overflow / "tasks.md").write_text(
        "# Overflow\n\n- [ ] Task 9: extra work\n",
        encoding="utf-8",
    )
    state = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    bus = FakeBus()
    fake = FakeEngine()

    outcome = run_grok_phase(
        bus,
        proj,
        state,
        1,
        "fake_proj",
        invoke=fake,
        skip_validate=True,
    )
    # Main batch closed → advance hits overflow → re-enter, no classic enqueue
    assert not any(getattr(m, "to_agent", None) == "executor" for m in bus.messages)
    final = json.loads((proj / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert final.get("engine") == ENGINE_GROK_BUILD
    # Either overflow pending re-entry or completed both batches in one run
    # FakeEngine marks overflow tasks on implement when present; if both closed
    # and no next phase → complete. If overflow was queued mid-flight:
    if final.get("grok_overflow_pending"):
        assert "executing" in (final.get("status") or "")
    else:
        # Driver may have finished overflow in same run if implement closed both
        assert outcome.completed or outcome.advanced or final.get("status") in (
            "complete",
            "mvp_complete",
            "phase_1_executing",
        )


def test_hook_one_project_per_tick(tmp_path: Path, monkeypatch):
    """Issue 4: even gate-blocked outcomes stop after one project."""
    root = tmp_path / "projects"
    root.mkdir()
    for name in ("a_proj", "b_proj"):
        p = root / name
        p.mkdir()
        (p / "state").mkdir()
        (p / "workspace").mkdir()
        (p / "phases" / "phase_1").mkdir(parents=True)
        (p / "phases" / "phase_1" / "tasks.md").write_text(
            "- [ ] Task 1: x\n", encoding="utf-8"
        )
        (p / "state" / "current_idea.json").write_text(
            json.dumps(
                {
                    "title": name,
                    "slug": name,
                    "status": "phase_1_executing",
                    "phase": 1,
                    "engine": ENGINE_GROK_BUILD,
                }
            ),
            encoding="utf-8",
        )

    calls: list[str] = []

    def fake_run(bus, project_dir, state, phase, slug, **kw):
        calls.append(slug)
        return DriverOutcome(blocked=True, reason="gates failed: open tasks")

    monkeypatch.setattr("pipeline.engines.driver.run_grok_phase", fake_run)
    from pipeline.engines import hook as hook_mod

    hook_mod._last_attempt.clear()
    n = tick_grok_build_engines(FakeBus(), pipeline_dir=tmp_path)
    assert n == 1
    assert len(calls) == 1
