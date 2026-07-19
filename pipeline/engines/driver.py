"""
Grok Build phase driver — deterministic skill chain for one phase.

Sequence (v1: planners stay classic; this owns implement/review/fix only):
  1. implement (CLI or injected engine) — skipped if tasks already closed mid-retry
  2. validate via run_pytest
  3. debug once on validate fail
  4. review skill → review.md (compatible with build_review_result)
  5. fix once on review FAIL
  6. gates: validate ok + checkboxes + non-FAIL review (never auto-PASS stubs)
  7. _advance_phase / _mark_complete when gates pass

Hard invoke failure → fallback to classic (engine field + enqueue executor).

Hard vs soft exits:
  - implement: any non-success (except dry_run) → hard fallback
  - debug/review/fix: exit 127 (missing CLI) / 124 (timeout) → hard fallback
  - other non-zero: soft — continue only if a real review.md with ## Verdict exists;
    otherwise block (no auto-PASS)
"""

from __future__ import annotations

import json
import pathlib
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from pipeline.engines.base import EngineResult
from pipeline.engines.selection import (
    ENGINE_CLASSIC,
    ENGINE_GROK_BUILD,
    get_project_engine,
)
from pipeline.env_flags import env_bool

# v1: at most one concurrent Grok Build phase driver (serial sessions = 1)
_GROK_SERIAL_LOCK = threading.Lock()
_grok_active_slug: str | None = None

# After this many gate-blocked driver cycles, demote to classic (Issue 5)
_MAX_GROK_BLOCK_COUNT = 5

# Exit codes treated as hard invoke failure for non-implement steps
_HARD_EXIT_CODES = frozenset({127, 124})


@dataclass
class DriverOutcome:
    advanced: bool = False
    completed: bool = False
    fell_back: bool = False
    blocked: bool = False
    reason: str = ""
    steps: list[str] = field(default_factory=list)
    review_result: dict[str, Any] = field(default_factory=dict)


def _log_activity(event: str, **fields: Any) -> None:
    try:
        from pipeline.pipeline_activity import log_activity

        log_activity(event, engine=ENGINE_GROK_BUILD, **fields)
    except Exception:
        pass


def _load_state(project_dir: pathlib.Path) -> dict:
    sf = project_dir / "state" / "current_idea.json"
    if not sf.is_file():
        return {}
    try:
        return json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(project_dir: pathlib.Path, state: dict) -> None:
    from pipeline.project_state import _write_state_dict

    _write_state_dict(project_dir, state)


def _last_phase_from_plan(project_dir: pathlib.Path, phase: int, state: dict) -> bool:
    total = int(state.get("total_phases") or 0)
    if total > 0:
        return phase >= total
    master = project_dir / "state" / "master_plan.md"
    if not master.is_file():
        return True
    try:
        text = master.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True
    nums = [int(m) for m in re.findall(r"##\s+Phase\s+(\d+)\b", text, re.IGNORECASE)]
    if not nums:
        return True
    return phase >= max(nums)


def _default_invoke(
    slug: str,
    phase: int,
    step: str,
    *,
    project_dir: pathlib.Path,
    workspace: pathlib.Path,
    **kwargs: Any,
) -> EngineResult:
    from pipeline.engines.grok_build import run_phase_step

    return run_phase_step(
        slug,
        phase,
        step,
        project_dir=project_dir,
        workspace=workspace,
        **kwargs,
    )


def _run_validate(workspace: pathlib.Path) -> tuple[bool, dict]:
    """Return (ok, pytest_result). Missing tests = ok (legacy soft default)."""
    try:
        from pipeline.agents.validator import run_pytest

        result = run_pytest(workspace)
    except Exception as exc:
        return False, {"error": str(exc), "failed": 1}

    if result.get("no_tests"):
        return True, result
    failed = int(result.get("failed") or 0) + int(result.get("errors") or 0)
    rc = int(result.get("returncode") or 0)
    ok = failed == 0 and rc in (0, 5)
    return ok, result


def _write_validation_report(
    phase_dir: pathlib.Path, phase_num: int, val_ok: bool, val_result: dict
) -> None:
    try:
        (phase_dir / "validation_report.md").write_text(
            f"# Validation — Phase {phase_num}\n\n"
            f"ok={val_ok}\n\n```\n{str(val_result)[:4000]}\n```\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def _write_fail_review_stub(
    review_path: pathlib.Path,
    phase: int,
    *,
    reason: str,
) -> str:
    """Write a FAIL review for operator visibility — never used to auto-advance."""
    content = (
        f"# Code Review — Phase {phase}\n\n"
        f"### What's Good\n"
        f"- (none — review skill did not produce a complete artifact)\n\n"
        f"## Blocking Bugs\n"
        f"- Review artifact missing or incomplete: {reason}\n\n"
        f"## Non-Blocking Notes\n"
        f"- Driver will not auto-PASS. Re-run review skill or fall back to classic.\n\n"
        f"## Reusable Components\n"
        f"- None\n\n"
        f"## Verdict\n"
        f"FAIL — {reason}\n"
    )
    if len(content) < 220:
        content += (
            "\n### Context\n"
            "This FAIL stub was written by the grok_build driver because no parseable "
            "review.md with a ## Verdict section was produced by the review skill.\n"
        )
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(content, encoding="utf-8")
    return content


def _read_review_if_complete(review_path: pathlib.Path) -> str | None:
    """Return review body only if it has a ## Verdict section (real or FAIL stub)."""
    if not review_path.is_file():
        return None
    try:
        text = review_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.strip():
        return None
    if not re.search(r"##\s+Verdict", text, re.IGNORECASE):
        return None
    return text


def _is_hard_exit(result: EngineResult) -> bool:
    return (not result.success) and (not result.dry_run) and (
        result.exit_code in _HARD_EXIT_CODES
    )


def _active_tasks_context(
    project_dir: pathlib.Path, phase_num: int
) -> tuple[pathlib.Path, str, bool]:
    """Return (tasks_path, relative, is_overflow).

    When main phase tasks are closed and overflow batch exists unfinished,
    gate and implement against the overflow tasks file.
    """
    from pipeline.task_checkboxes import phase_tasks_closed, stats_for_tasks_file

    main = project_dir / "phases" / f"phase_{phase_num}" / "tasks.md"
    main_rel = f"phases/phase_{phase_num}/tasks.md"
    overflow = project_dir / f"phases/phase_{phase_num}_overflow" / "tasks.md"
    overflow_done = project_dir / f"phases/phase_{phase_num}_overflow" / ".completed"
    overflow_rel = f"phases/phase_{phase_num}_overflow/tasks.md"

    if overflow.is_file() and not overflow_done.is_file():
        main_closed = phase_tasks_closed(project_dir, phase_num)
        # Also treat empty/missing checkboxes on main as closed when overflow pending
        if main_closed:
            return overflow, overflow_rel, True
        # Main still open — work main first
        return main, main_rel, False

    return main, main_rel, False


def _tasks_closed_for(path: pathlib.Path) -> bool:
    from pipeline.task_checkboxes import stats_for_tasks_file

    if not path.is_file():
        return True
    st = stats_for_tasks_file(path)
    if st.total == 0:
        return True
    return st.open_count == 0


def fallback_to_classic(
    bus: Any,
    project_dir: pathlib.Path,
    state: dict,
    phase_num: int,
    slug: str,
    reason: str,
) -> None:
    """Demote project to classic once; enqueue classic executor; log activity."""
    state["engine"] = ENGINE_CLASSIC
    state["engine_fallback"] = ENGINE_CLASSIC
    state["engine_fallback_reason"] = reason[:500]
    state["status"] = f"phase_{phase_num}_executing"
    state.pop("grok_driver_running", None)
    state.pop("grok_overflow_pending", None)
    _write_state(project_dir, state)

    try:
        from pipeline.pipeline_activity import log_activity

        log_activity(
            "engine_fallback",
            engine=ENGINE_CLASSIC,
            previous=ENGINE_GROK_BUILD,
            slug=slug,
            phase=phase_num,
            reason=reason[:300],
        )
    except Exception:
        pass

    if bus is not None:
        try:
            from pipeline.message_bus import Message

            workspace = project_dir / "workspace"
            # Prefer overflow path when pending so classic picks up correct batch
            tasks_path = f"phases/phase_{phase_num}/tasks.md"
            overflow = project_dir / f"phases/phase_{phase_num}_overflow" / "tasks.md"
            overflow_done = project_dir / f"phases/phase_{phase_num}_overflow" / ".completed"
            if overflow.is_file() and not overflow_done.is_file():
                from pipeline.task_checkboxes import phase_tasks_closed

                if phase_tasks_closed(project_dir, phase_num):
                    tasks_path = f"phases/phase_{phase_num}_overflow/tasks.md"
            bus.send(
                Message.create(
                    from_agent="runner",
                    to_agent="executor",
                    type="task",
                    payload={
                        "phase": phase_num,
                        "tasks_path": tasks_path,
                        "workspace_path": str(workspace),
                        "idea_slug": slug,
                        "engine_fallback": True,
                        "fix_instructions": (
                            f"Grok Build engine fell back to classic: {reason[:200]}"
                        ),
                    },
                )
            )
        except Exception:
            pass

    print(f"  ↩️  engine_fallback classic for '{slug}' phase {phase_num}: {reason[:120]}")


def _block_outcome(
    outcome: DriverOutcome,
    project_dir: pathlib.Path,
    state: dict,
    phase_num: int,
    slug: str,
    reason: str,
    *,
    bus: Any = None,
) -> DriverOutcome:
    """Mark gate-blocked; may demote after repeated blocks."""
    count = int(state.get("grok_block_count") or 0) + 1
    state["grok_block_count"] = count
    state["grok_gates_blocked"] = True
    state["status"] = f"phase_{phase_num}_executing"
    state.pop("grok_driver_running", None)

    if count >= _MAX_GROK_BLOCK_COUNT:
        fallback_to_classic(
            bus,
            project_dir,
            state,
            phase_num,
            slug,
            reason=f"grok blocked {count} times: {reason}",
        )
        outcome.fell_back = True
        outcome.blocked = True
        outcome.reason = f"fallback after {count} blocks: {reason}"
        _write_state(project_dir, state)
        return outcome

    _write_state(project_dir, state)
    outcome.blocked = True
    outcome.reason = reason
    _log_activity(
        "grok_driver_blocked",
        slug=slug,
        phase=phase_num,
        reason=reason,
        block_count=count,
    )
    return outcome


def run_grok_phase(
    bus: Any,
    project_dir: pathlib.Path,
    state: dict,
    phase_num: int,
    slug: str,
    *,
    invoke: Callable[..., EngineResult] | None = None,
    skip_validate: bool = False,
) -> DriverOutcome:
    """Run the full grok_build skill chain for one phase.

    *invoke(slug, phase, step, project_dir=..., workspace=...) -> EngineResult*
    defaults to pipeline.engines.grok_build.run_phase_step.
    """
    outcome = DriverOutcome()
    invoke_fn = invoke or _default_invoke
    workspace = project_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    phase_dir = project_dir / "phases" / f"phase_{phase_num}"
    phase_dir.mkdir(parents=True, exist_ok=True)
    review_path = phase_dir / "review.md"

    if get_project_engine(state) != ENGINE_GROK_BUILD:
        outcome.reason = "not grok_build engine"
        return outcome

    # Serial mutex for v1 (concurrent Grok sessions = 1)
    acquired = _GROK_SERIAL_LOCK.acquire(blocking=False)
    if not acquired:
        outcome.blocked = True
        outcome.reason = "another grok_build session is active (serial v1)"
        _log_activity(
            "grok_driver_skipped",
            slug=slug,
            phase=phase_num,
            reason=outcome.reason,
        )
        return outcome

    global _grok_active_slug
    try:
        _grok_active_slug = slug
        state["grok_driver_running"] = True
        state["status"] = f"phase_{phase_num}_grok_running"
        _write_state(project_dir, state)
        _log_activity("grok_driver_start", slug=slug, phase=phase_num)

        tasks_path, tasks_rel, is_overflow = _active_tasks_context(project_dir, phase_num)

        def _step(step: str) -> EngineResult:
            result = invoke_fn(
                slug,
                phase_num,
                step,
                project_dir=project_dir,
                workspace=workspace,
            )
            outcome.steps.append(step)
            return result

        # 1. Implement (skip re-implement when retrying after gates block with closed tasks)
        tasks_already_closed = _tasks_closed_for(tasks_path)
        skip_implement = bool(
            state.get("grok_gates_blocked") and tasks_already_closed
        )
        if not skip_implement:
            impl = _step("implement")
            if not impl.success and not impl.dry_run:
                fallback_to_classic(
                    bus,
                    project_dir,
                    state,
                    phase_num,
                    slug,
                    reason=impl.error or f"implement failed exit={impl.exit_code}",
                )
                outcome.fell_back = True
                outcome.reason = impl.error or "implement hard failure"
                return outcome
            # Re-resolve tasks path after implement (main may have closed → overflow)
            tasks_path, tasks_rel, is_overflow = _active_tasks_context(
                project_dir, phase_num
            )
        else:
            outcome.steps.append("implement_skipped")

        # 2. Validate
        val_ok = True
        val_result: dict = {}
        if not skip_validate:
            val_ok, val_result = _run_validate(workspace)
            _write_validation_report(phase_dir, phase_num, val_ok, val_result)

        # 3. Debug once on fail
        if not val_ok:
            dbg = _step("debug")
            if _is_hard_exit(dbg):
                fallback_to_classic(
                    bus,
                    project_dir,
                    state,
                    phase_num,
                    slug,
                    reason=dbg.error or "debug hard failure",
                )
                outcome.fell_back = True
                outcome.reason = dbg.error or "debug hard failure"
                return outcome
            val_ok, val_result = _run_validate(workspace)
            _write_validation_report(phase_dir, phase_num, val_ok, val_result)

        # Issue 1: failing pytest after debug must not advance
        if not val_ok and not skip_validate:
            return _block_outcome(
                outcome,
                project_dir,
                state,
                phase_num,
                slug,
                reason="validation failed after debug (pytest not green)",
                bus=bus,
            )

        # 4. Review
        rev = _step("review")
        if _is_hard_exit(rev):
            fallback_to_classic(
                bus,
                project_dir,
                state,
                phase_num,
                slug,
                reason=rev.error or "review hard failure",
            )
            outcome.fell_back = True
            outcome.reason = rev.error or "review hard failure"
            return outcome

        from pipeline.review_artifacts import (
            build_review_result,
            review_verdict_is_fail,
        )

        # Issue 2: never auto-PASS — require real review.md with ## Verdict
        review_content = _read_review_if_complete(review_path)
        if review_content is None:
            # Soft fail or empty skill output — FAIL stub for visibility, then block
            reason = "review skill did not produce parseable review.md"
            if not rev.success and not rev.dry_run:
                reason = (
                    f"review soft-fail exit={rev.exit_code}: "
                    f"{rev.error or 'no review.md'}"
                )
            elif rev.dry_run:
                reason = "dry-run review left no review.md (no auto-PASS)"
            _write_fail_review_stub(review_path, phase_num, reason=reason)
            review_content = _read_review_if_complete(review_path) or ""
            return _block_outcome(
                outcome,
                project_dir,
                state,
                phase_num,
                slug,
                reason=reason,
                bus=bus,
            )

        # Soft review failure even with a file: if exit non-zero and not dry_run,
        # still use the file (skill may write FAIL). Only hard codes already fell back.

        # 5. Fix once on FAIL
        if review_verdict_is_fail(review_content):
            fix = _step("fix")
            if _is_hard_exit(fix):
                fallback_to_classic(
                    bus,
                    project_dir,
                    state,
                    phase_num,
                    slug,
                    reason=fix.error or "fix hard failure",
                )
                outcome.fell_back = True
                outcome.reason = fix.error or "fix hard failure"
                return outcome
            # Re-review once after fix
            rev2 = _step("review")
            if _is_hard_exit(rev2):
                fallback_to_classic(
                    bus,
                    project_dir,
                    state,
                    phase_num,
                    slug,
                    reason=rev2.error or "re-review hard failure",
                )
                outcome.fell_back = True
                outcome.reason = rev2.error or "re-review hard failure"
                return outcome
            review_content = _read_review_if_complete(review_path)
            if review_content is None:
                _write_fail_review_stub(
                    review_path,
                    phase_num,
                    reason="re-review after fix produced no parseable review.md",
                )
                return _block_outcome(
                    outcome,
                    project_dir,
                    state,
                    phase_num,
                    slug,
                    reason="re-review missing after fix",
                    bus=bus,
                )

        # Optional deep review
        if deep_review_enabled(project_dir, phase_num, state):
            _step("deep_review")
            deep_path = phase_dir / "deep_review.md"
            if not deep_path.is_file():
                deep_path.write_text(
                    f"# Deep Review — Phase {phase_num}\n\n"
                    f"Optional comprehensive review step completed "
                    f"(or dry-run logged).\n",
                    encoding="utf-8",
                )

        # Re-read for gates
        review_content = _read_review_if_complete(review_path)
        if review_content is None:
            return _block_outcome(
                outcome,
                project_dir,
                state,
                phase_num,
                slug,
                reason="review.md missing at gate time",
                bus=bus,
            )

        try:
            rel_review = str(review_path.relative_to(project_dir))
        except ValueError:
            rel_review = str(review_path)
        review_result = build_review_result(
            review_content=review_content,
            review_path=rel_review,
            tasks_path=tasks_rel,
            workspace_path=str(workspace),
        )
        outcome.review_result = review_result
        state["review_result"] = review_result

        # 6. Checkbox + FAIL gates (+ validation already enforced above)
        from pipeline.task_checkboxes import (
            stats_for_tasks_file,
            sync_task_counts_to_state,
        )

        try:
            sync_task_counts_to_state(state, project_dir, phase_num)
        except Exception:
            pass

        # Refresh active tasks (overflow may apply after implement)
        tasks_path, tasks_rel, is_overflow = _active_tasks_context(project_dir, phase_num)
        tasks_closed = _tasks_closed_for(tasks_path)
        blocking = int(review_result.get("blocking_bugs") or 0)
        if review_result.get("review_fail"):
            blocking = max(blocking, 1)

        if not tasks_closed or blocking > 0:
            stats = stats_for_tasks_file(tasks_path)
            return _block_outcome(
                outcome,
                project_dir,
                state,
                phase_num,
                slug,
                reason=(
                    f"gates failed: tasks_closed={tasks_closed} "
                    f"open={stats.open_count} blocking={blocking} "
                    f"overflow={is_overflow}"
                ),
                bus=bus,
            )

        # Overflow batch finished — mark done so _advance_phase can proceed
        if is_overflow:
            done_marker = (
                project_dir / f"phases/phase_{phase_num}_overflow" / ".completed"
            )
            done_marker.parent.mkdir(parents=True, exist_ok=True)
            try:
                done_marker.write_text("completed", encoding="utf-8")
            except OSError:
                pass
            state.pop("grok_overflow_pending", None)

        # 7. Advance / complete
        state.pop("grok_driver_running", None)
        state.pop("grok_gates_blocked", None)
        state.pop("grok_block_count", None)
        state["status"] = f"phase_{phase_num}_reviewed"
        _write_state(project_dir, state)

        from pipeline.project_phase import _advance_phase, _mark_complete
        from pipeline.project_state import _reset_retries

        _reset_retries(project_dir, phase_num)
        title = state.get("title", slug)
        advanced = _advance_phase(bus, project_dir, state, phase_num, slug)
        if not advanced:
            _mark_complete(project_dir, state, title)
            outcome.completed = True
            outcome.reason = "complete"
            print(f"  ✅ grok_build '{title}' completed all phases!")
        else:
            outcome.advanced = True
            # Overflow re-queue sets phase_N_executing without next phase
            if state.get("grok_overflow_pending") or (
                (state.get("status") or "").endswith("_executing")
                and int(state.get("phase") or phase_num) == phase_num
            ):
                outcome.reason = f"overflow batch queued for phase {phase_num}"
            else:
                outcome.reason = f"advanced to phase {phase_num + 1}"
            print(
                f"  ➡️  grok_build '{title}' phase {phase_num} passed → "
                f"{outcome.reason}"
            )

        _log_activity(
            "grok_driver_done",
            slug=slug,
            phase=phase_num,
            advanced=outcome.advanced,
            completed=outcome.completed,
        )
        return outcome
    finally:
        _grok_active_slug = None
        try:
            state.pop("grok_driver_running", None)
            cur = _load_state(project_dir)
            if cur.get("grok_driver_running"):
                cur.pop("grok_driver_running", None)
                _write_state(project_dir, cur)
        except Exception:
            pass
        _GROK_SERIAL_LOCK.release()


def deep_review_enabled(project_dir: pathlib.Path, phase: int, state: dict) -> bool:
    """Whether to run optional comprehensive review."""
    if env_bool("GROK_BUILD_DEEP_REVIEW", default=False):
        return True
    if env_bool("GROK_BUILD_DEEP_REVIEW_LAST", default=False):
        return _last_phase_from_plan(project_dir, phase, state)
    return False


def run_deep_review_if_needed(
    slug: str,
    phase: int,
    project_dir: pathlib.Path,
    state: dict,
    *,
    invoke: Callable[..., EngineResult] | None = None,
) -> EngineResult | None:
    if not deep_review_enabled(project_dir, phase, state):
        return None
    invoke_fn = invoke or _default_invoke
    workspace = project_dir / "workspace"
    result = invoke_fn(
        slug, phase, "deep_review", project_dir=project_dir, workspace=workspace
    )
    deep_path = project_dir / "phases" / f"phase_{phase}" / "deep_review.md"
    if not deep_path.is_file():
        deep_path.parent.mkdir(parents=True, exist_ok=True)
        deep_path.write_text(
            f"# Deep Review — Phase {phase}\n\n"
            f"Comprehensive review step (success={result.success}).\n"
            f"{result.summary}\n",
            encoding="utf-8",
        )
    return result
