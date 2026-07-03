"""
pipeline/run_loop_health.py
Health-check preamble, status display, reviewed advance, and metrics collection.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from pipeline.ollama_health import _check_ollama_heartbeat
from pipeline.pipeline_config import (
    AGENT_ROLES,
    MAX_PROJECT_LIFETIME_RETRIES,
    PROJECT_ROOT,
    SHIP_AGENT_ROLES,
)
from pipeline.pipeline_status import _get_active_idea_state, _get_all_active_idea_states
from pipeline.project_ops import _tick_project
from pipeline.text_util import clean_ansi as _clean

from pipeline.project_rebuild import dispatch_phase_requeue
from pipeline.run_loop_types import MainLoopConfig

_TPS_PRINT_INTERVAL = 900.0
_STALL_THRESHOLD_S = 600.0
_STALL_WARN_INTERVAL_S = 900.0


def tick_reviewed_advance(
    cfg: MainLoopConfig,
    idea_state: dict[str, Any],
    all_empty: bool,
) -> dict[str, Any]:
    """Advance phase_X_reviewed immediately when queues are empty."""
    _active_slug = idea_state.get("_slug", "")
    _active_status = idea_state.get("status", "")
    if not (_active_status.endswith("_reviewed") and all_empty and _active_slug):
        return idea_state
    _rv_match = re.match(r"phase_(\d+)_reviewed", _active_status)
    if not _rv_match:
        return idea_state
    _rv_phase = int(_rv_match.group(1))
    _rv_proj = cfg.pipeline_dir / "projects" / _active_slug
    _rv_state_file = _rv_proj / "state" / "current_idea.json"
    if not _rv_state_file.exists():
        return idea_state
    try:
        _rv_state = json.loads(_rv_state_file.read_text(encoding="utf-8"))
        routed = _tick_project(cfg.bus, _rv_proj, _rv_state, _rv_phase, _active_slug)
        if routed:
            idea_state = _get_active_idea_state(cfg.pipeline_dir)
    except Exception as _rv_err:
        print(f"  [reviewed] Failed to advance {_active_slug}: {_rv_err}")
    return idea_state


def read_task_progress(cfg: MainLoopConfig, idea_state: dict[str, Any]) -> tuple[int, int]:
    """Live task done/total from tasks.md for the active project phase."""
    tasks_done, tasks_total = 0, 0
    try:
        slug = idea_state.get("_slug", "")
        phase_num = idea_state.get("phase", 1)
        if slug:
            tasks_file = cfg.pipeline_dir / "projects" / slug / f"phases/phase_{phase_num}/tasks.md"
            if tasks_file.exists():
                from pipeline.agent_process import AgentProcess

                AgentProcess.normalize_tasks_file(tasks_file)
                raw = tasks_file.read_text(encoding="utf-8")
                scoped = AgentProcess._extract_phase_tasks(raw, phase_num)
                tasks_total = len(re.findall(r"^\s*- \[[ xX]\]", scoped, re.MULTILINE))
                tasks_done = len(re.findall(r"^\s*- \[[xX]\]", scoped, re.MULTILINE))
                if tasks_total == 0:
                    numbered = re.findall(r"^\d+\.\s+\S", scoped, re.MULTILINE)
                    tasks_total = len(numbered)
    except Exception:
        pass
    return tasks_done, tasks_total


def read_workspace_activity(cfg: MainLoopConfig, active_slug: str) -> tuple[int, float]:
    """Return (file_count, latest_mtime) for project workspace."""
    _ws_file_count = 0
    _ws_last_mtime = 0.0
    try:
        if active_slug:
            _ws_dir = cfg.pipeline_dir / "projects" / active_slug / "workspace"
            if _ws_dir.exists():
                for _wf in _ws_dir.rglob("*"):
                    if _wf.is_file() and not _wf.name.startswith("."):
                        _ws_file_count += 1
                        _mt = _wf.stat().st_mtime
                        if _mt > _ws_last_mtime:
                            _ws_last_mtime = _mt
    except Exception:
        pass
    return _ws_file_count, _ws_last_mtime


def tick_health_preamble(cfg: MainLoopConfig) -> dict[str, Any]:
    """Supervisor health, compaction, self-healing checks; returns supervisor health map."""
    if cfg.polish and cfg.run_ctx and cfg.run_ctx.polish_path and cfg.state.status_count % 3 == 0:
        from pipeline.polish_mode import queue_pending
        from pipeline.polish_status import save_polish_status

        _pa = cfg.count_active_projects()
        _pp = queue_pending(cfg.bus)
        save_polish_status(
            run_state="running",
            active_projects=_pa,
            pending_messages=_pp,
            queue_path=str(cfg.run_ctx.polish_path),
        )
        print(
            f"  [cfg.polish] RUNNING — {_pa} active project(s), "
            f"{_pp} pending queue message(s)"
        )

    health = cfg.supervisor.check_health()
    restarted = cfg.supervisor.restart_dead()
    if restarted:
        cfg.supervisor.save_registry()

    if cfg.state.status_count > 0 and cfg.state.status_count % 10 == 0:
        compacted = cfg.bus.compact_all()
        if compacted > 0:
            print(f"  🧹 Compacted {compacted} stale messages from queues")
        try:
            from pipeline.agent_metrics import trim_old_records

            trim_old_records()
        except Exception:
            pass

    if cfg.state.status_count > 0 and cfg.state.status_count % 5 == 0:
        try:
            from pipeline.health_checks import run_all_checks, write_health_report

            _active_for_health = _get_active_idea_state(cfg.pipeline_dir)
            _health_slug = _active_for_health.get("_slug", "")
            hc_results = run_all_checks(PROJECT_ROOT, cfg.pipeline_dir, _health_slug)
            if hc_results:
                fixes = sum(1 for r in hc_results if r.auto_fixed)
                issues = len(hc_results) - fixes
                if fixes:
                    print(f"  🩺 Health check: {fixes} auto-fixed, {issues} reported")
                write_health_report(hc_results, cfg.pipeline_dir)
        except Exception as _hc_err:
            print(f"  [health] Check failed: {_hc_err}")

    if cfg.state.status_count > 0 and cfg.state.status_count % 30 == 0:
        try:
            from pipeline.constitutional_patcher import run_patcher as _const_patch

            _patches = _const_patch(min_projects=3, dry_run=False, verbose=False)
            if _patches:
                _patch_roles = ", ".join(set(p.role for p in _patches))
                print(
                    f"  [constitutional] {len(_patches)} new guardrail(s) "
                    f"patched into prompts: {_patch_roles}"
                )
        except Exception:
            pass

    return health


def _ship_artifact_hint(cfg: MainLoopConfig, slug: str) -> str:
    """Latest phases/ship artifact for status line."""
    if not slug:
        return ""
    ship_dir = cfg.pipeline_dir / "projects" / slug / "phases" / "ship"
    if not ship_dir.is_dir():
        return ""
    names = (
        "field_tests.md",
        "field_test_results.md",
        "debug_report.md",
        "thermo_review.md",
        "ship_evaluation.md",
    )
    latest_name = ""
    latest_mtime = 0.0
    for name in names:
        path = ship_dir / name
        if path.is_file():
            mtime = path.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_name = name
    return f" ship:{latest_name}" if latest_name else ""


def tick_status_display(
    cfg: MainLoopConfig,
    health: dict[str, Any],
    idea_state: dict[str, Any],
    *,
    tasks_done: int,
    tasks_total: int,
    ws_file_count: int,
) -> None:
    """Print status line, throughput breakdown, and tuner updates."""
    role_list = SHIP_AGENT_ROLES if cfg.ship_prove else AGENT_ROLES
    running_agents = sum(1 for s in health.values() if s == "running")
    pending_total = sum(cfg.bus.queue_depth(r) for r in role_list)
    elapsed_m = (time.time() - cfg.start_time) / 60
    phase = idea_state.get("status", "?")
    title = idea_state.get("title", "")
    _active_slug = idea_state.get("_slug", "")
    ship_hint = _ship_artifact_hint(cfg, _active_slug) if cfg.ship_prove else ""
    if cfg.ship_prove:
        title_str = f" | [{title[:28]}]" if title else ""
    elif cfg.state.parallel_seeds > 1:
        _all_active = _get_all_active_idea_states(cfg.pipeline_dir)
        if len(_all_active) > 1:
            title_str = " | " + " / ".join(
                f"[{s.get('title', '?')[:15]}]" for s in _all_active[:4]
            )
        elif title:
            title_str = f" | [{title[:28]}]"
        else:
            title_str = ""
    else:
        title_str = f" | [{title[:28]}]" if title else ""

    task_str = f" {tasks_done}/{tasks_total}✓" if tasks_total and not cfg.ship_prove else ""
    if not cfg.ship_prove and tasks_total and tasks_done == 0 and ws_file_count > 0:
        task_str = f" 0/{tasks_total}✓ ({ws_file_count} files)"

    gpu_str = ""
    _gpu_idle = False
    if cfg.provider == "ollama":
        gpu_status = _check_ollama_heartbeat(cfg.model)
        if gpu_status:
            if "IDLE" in gpu_status or "ERR" in gpu_status:
                gpu_str = f" ⚠️ {gpu_status} — cfg.model evicted from VRAM!"
                _gpu_idle = True
            else:
                gpu_str = f" {gpu_status}"

    _tps_str = ""
    _live_gpu_pct = 0.0
    try:
        _tp_live_path = cfg.pipeline_dir / "state" / "throughput.json"
        if _tp_live_path.exists():
            _tp_live = json.loads(_tp_live_path.read_text(encoding="utf-8"))
            _live_cum_tok = _tp_live.get("cumulative_tokens", 0)
            _live_cum_inf_s = _tp_live.get("cumulative_inference_s", 0.0)
            _live_cum_wall = _tp_live.get("cumulative_wall_s", 0.0)
            _live_last_tps = _tp_live.get("tps", 0.0)
            _live_age_s = time.time() - _tp_live.get("updated_at", 0)
            if _live_cum_tok > 0 and _live_age_s < 600:
                _live_avg_tps = _live_cum_tok / _live_cum_inf_s if _live_cum_inf_s > 0 else 0
                _tps_str = f" {_live_last_tps:.0f}t/s/{_live_avg_tps:.0f}avg"
                if _live_cum_wall > 0:
                    _live_gpu_pct = min(100.0, _live_cum_inf_s / _live_cum_wall * 100)
    except Exception:
        pass

    _tuner_str = ""
    if cfg.tuner is not None:
        try:
            _tp_path = cfg.pipeline_dir / "state" / "throughput.json"
            _decision = cfg.tuner.observe(
                throughput_path=_tp_path,
                current_seeds=cfg.state.parallel_seeds,
                gpu_idle=_gpu_idle,
                gpu_util_pct=_live_gpu_pct,
            )
            if _decision.changed:
                cfg.state.parallel_seeds = _decision.new_seeds
                print(f"  {_decision.reason} [conf={_decision.confidence:.0%}]")
                try:
                    with open(cfg.tuner_log_path, "a", encoding="utf-8") as _tlf:
                        _tlf.write(
                            json.dumps(
                                {
                                    "ts": time.time(),
                                    "old_seeds": _decision.old_seeds,
                                    "new_seeds": _decision.new_seeds,
                                    "reason": _decision.reason,
                                    "confidence": round(_decision.confidence, 3),
                                }
                            )
                            + "\n"
                        )
                except Exception:
                    pass
            if cfg.state.status_count % 4 == 0:
                _tuner_str = f"  {cfg.tuner.status_line(cfg.state.parallel_seeds)}"
        except Exception:
            pass

    mode_prefix = "[ship] " if cfg.ship_prove else ""
    status_line = _clean(
        f"  {mode_prefix}[{elapsed_m:.0f}m] agents={running_agents}/{len(role_list)} "
        f"pending={pending_total} status={phase}{ship_hint}{task_str}"
        f"{gpu_str}{_tps_str}{title_str}"
    )
    print_every = 1 if cfg.ship_prove else 4
    if cfg.state.status_count % print_every == 0:
        print(status_line, flush=True)
        if _tuner_str:
            print(_tuner_str, flush=True)
    cfg.state.status_count += 1

    _print_throughput_breakdown(cfg, running_agents)


def _throughput_age_s(cfg: MainLoopConfig) -> float | None:
    """Seconds since last completed LLM call, or None if unknown."""
    path = cfg.pipeline_dir / "state" / "throughput.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        updated_at = data.get("updated_at")
        if updated_at is None:
            return None
        return time.time() - float(updated_at)
    except Exception:
        return None


def _warn_stall(cfg: MainLoopConfig, *, age_s: float, running_agents: int, stuck: list[Any]) -> None:
    now = time.time()
    if now - cfg.state.last_stall_warning < _STALL_WARN_INTERVAL_S:
        return
    cfg.state.last_stall_warning = now
    age_m = int(age_s // 60) if age_s != float("inf") else int((now - cfg.start_time) // 60)
    print(
        f"  ⚠️  STALL DETECTED: no LLM call in {age_m}m "
        f"({running_agents} agents running)",
        flush=True,
    )
    if stuck:
        by_role: dict[str, int] = {}
        for msg in stuck:
            by_role[msg.to_agent] = by_role.get(msg.to_agent, 0) + 1
        stuck_str = ", ".join(f"{role}×{count}" for role, count in sorted(by_role.items()))
        print(f"     Stuck in processing: {stuck_str}", flush=True)
    else:
        print(
            "     No messages in 'processing' — queue empty, "
            "agents idle (phase transition stall?)",
            flush=True,
        )


def _recover_reviewing_deadlock(cfg: MainLoopConfig) -> bool:
    """Re-queue projects stuck in phase_X_reviewing with all tasks complete."""
    projects_root = cfg.pipeline_dir / "projects"
    if not projects_root.exists():
        return False
    for project_dir in sorted(projects_root.iterdir()):
        if not project_dir.is_dir():
            continue
        state_file = project_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = state.get("status", "")
        if not status.endswith("_reviewing"):
            continue
        slug = project_dir.name
        phase_num = state.get("phase", 1)
        tasks_done, tasks_total = read_task_progress(
            cfg,
            {"_slug": slug, "phase": phase_num, **state},
        )
        if tasks_total <= 0 or tasks_done < tasks_total:
            continue
        title = state.get("title", slug)
        if dispatch_phase_requeue(
            cfg.bus,
            slug,
            title,
            state,
            project_dir,
            status,
            log_requeue=True,
        ):
            print(
                f"  🔧 Reviewing deadlock recovery: re-queued '{title}' -> reviewer",
                flush=True,
            )
            return True
    return False


def tick_stall_recovery(cfg: MainLoopConfig, *, running_agents: int) -> None:
    """Detect idle/processing stalls and attempt queue recovery."""
    now = time.time()
    if running_agents <= 0 or (now - cfg.start_time) < _STALL_THRESHOLD_S:
        return

    age_s = _throughput_age_s(cfg)
    no_llm_recently = age_s is None or age_s > _STALL_THRESHOLD_S
    if not no_llm_recently:
        return

    stuck = cfg.bus.get_processing_messages()
    _warn_stall(cfg, age_s=age_s if age_s is not None else float("inf"), running_agents=running_agents, stuck=stuck)

    if stuck:
        _try_recover_stalled_processing(cfg, stuck)

    if cfg.ship_prove:
        from pipeline.ship_mode import ship_bus_has_work

        if ship_bus_has_work(cfg.bus):
            return
    elif cfg.bus.has_active_work():
        return

    if now - cfg.state.last_stall_recovery < cfg.stall_recovery_cooldown_s:
        return
    if _recover_reviewing_deadlock(cfg):
        cfg.state.last_stall_recovery = now


def _print_throughput_breakdown(cfg: MainLoopConfig, running_agents: int) -> None:
    _now = time.time()
    if cfg.provider != "ollama" or (_now - cfg.state.last_tps_print) < _TPS_PRINT_INTERVAL:
        return
    _tp_path = cfg.pipeline_dir / "state" / "throughput.json"
    if not _tp_path.exists():
        cfg.state.last_tps_print = _now
        return
    try:
        _tp = json.loads(_tp_path.read_text(encoding="utf-8"))
        _age_s = _now - _tp.get("updated_at", _now)
        _cum_tok = _tp.get("cumulative_tokens", 0)
        _cum_inf_s = _tp.get("cumulative_inference_s", 0.0)
        _cum_wall_s = _tp.get("cumulative_wall_s", 0.0) or 1
        _cum_tool_s = _tp.get("cumulative_tool_s", 0.0)
        _calls = _tp.get("call_count", 0)
        _tool_calls = _tp.get("tool_call_count", 0)
        _tps_inf = _tp.get("tps", 0)
        _tps_pipe = _cum_tok / _cum_wall_s if _cum_tok else 0
        _tps_inf_avg = _cum_tok / _cum_inf_s if _cum_inf_s > 0 else 0
        _gpu_pct = (_cum_inf_s / _cum_wall_s) * 100
        _tool_pct = (_cum_tool_s / _cum_wall_s) * 100
        _overhead_pct = max(0, 100 - _gpu_pct - _tool_pct)
        _wall_h = int(_cum_wall_s // 3600)
        _wall_m = int((_cum_wall_s % 3600) // 60)
        _wall_str = f"{_wall_h}h{_wall_m:02d}m" if _wall_h else f"{_wall_m}m"
        _age_str = f"{int(_age_s // 60)}m ago" if _age_s > 90 else "recent"
        if _cum_tok > 0 and _age_s < 3600:
            print(
                f"  \U0001f4ca Throughput [{_wall_str} wall-clock, "
                f"{_calls} LLM calls, {_tool_calls} tool calls]\n"
                f"     Inference:  {_tps_inf:.1f} tok/s (last call)  "
                f"/ {_tps_inf_avg:.1f} tok/s avg\n"
                f"     Pipeline:   {_tps_pipe:.1f} tok/s  "
                f"(tokens / total wall-clock)\n"
                f"     Time split: GPU {_gpu_pct:.0f}%  "
                f"| Tools {_tool_pct:.0f}%  "
                f"| Overhead {_overhead_pct:.0f}%  "
                f"(queue/switch/init)\n"
                f"     Tokens:     {_cum_tok:,} generated  "
                f"/ {_cum_tok // _calls if _calls else 0} avg/call  "
                f"(last: {_age_str})",
                flush=True,
            )
    except Exception:
        pass
    cfg.state.last_tps_print = _now


def _try_recover_stalled_processing(cfg: MainLoopConfig, stuck: list[Any]) -> None:
    """Reset processing messages back to pending when throughput has gone stale."""
    if not stuck:
        return
    now = time.time()
    if now - cfg.state.last_stall_recovery < cfg.stall_recovery_cooldown_s:
        return
    try:
        stuck_roles = sorted({m.to_agent for m in stuck})
        reset = cfg.bus.reset_stale_processing()
        if reset:
            cfg.state.last_stall_recovery = now
            print(
                f"  🔧 Stall recovery: reset {reset} processing message(s) → pending",
                flush=True,
            )
            for key in stuck_roles:
                if key in cfg.supervisor.processes:
                    cfg.supervisor.restart_role(key)
                    print(f"  🔧 Stall recovery: restarted {key}", flush=True)
            cfg.supervisor.save_registry()
    except Exception as exc:
        print(f"  [stall recovery] failed: {exc}", flush=True)


def tick_project_metrics(
    cfg: MainLoopConfig,
    idea_state: dict[str, Any],
    *,
    tasks_done: int,
) -> None:
    """Collect per-project metrics and wire throughput deltas."""
    _active_slug = idea_state.get("_slug", "")
    try:
        projects_dir = cfg.pipeline_dir / "projects"
        if projects_dir.exists():
            for proj_dir in projects_dir.iterdir():
                if not proj_dir.is_dir():
                    continue
                slug = proj_dir.name
                ci_path = proj_dir / "state" / "current_idea.json"
                if ci_path.exists():
                    ci = json.loads(ci_path.read_text(encoding="utf-8"))
                    cfg.run_metrics.record_project_start(slug)
                    st = ci.get("status", "")

                    retries = 0
                    pr_path = proj_dir / "state" / "phase_retries.json"
                    if pr_path.exists():
                        try:
                            pr_data = json.loads(pr_path.read_text(encoding="utf-8"))
                            retries = sum(v for v in pr_data.values() if isinstance(v, int))
                        except Exception:
                            pass

                    if (
                        retries >= MAX_PROJECT_LIFETIME_RETRIES
                        and st not in ("complete", "budget_exceeded", "", "dep_waiting")
                    ):
                        ci["status"] = "budget_exceeded"
                        ci["budget_note"] = (
                            f"Force-completed: exceeded {MAX_PROJECT_LIFETIME_RETRIES} "
                            f"total retries across all phases (actual: {retries})"
                        )
                        ci_path.write_text(json.dumps(ci, indent=2), encoding="utf-8")
                        print(
                            f"  \U0001f6d1 Lifetime retry cap hit: '{ci.get('title', slug)}' "
                            f"({retries} retries \u2265 {MAX_PROJECT_LIFETIME_RETRIES}) "
                            f"\u2192 budget_exceeded"
                        )
                        for _role in AGENT_ROLES:
                            cfg.bus.clear_queue(_role)

                    if st == "complete":
                        cfg.run_metrics.record_project_complete(
                            slug,
                            phases=ci.get("phase", 0),
                            retries=retries,
                        )
    except Exception:
        pass

    try:
        _tp_metrics_path = cfg.pipeline_dir / "state" / "throughput.json"
        if _tp_metrics_path.exists():
            _tp_data = json.loads(_tp_metrics_path.read_text(encoding="utf-8"))
            _total_tok = _tp_data.get("cumulative_tokens", 0)
            if _active_slug and _total_tok > 0:
                _prev_tok = cfg.state.last_tok_snapshot
                _delta_tok = max(0, _total_tok - _prev_tok)
                if _delta_tok > 0:
                    cfg.run_metrics.record_tokens(_active_slug, _delta_tok)
                cfg.state.last_tok_snapshot = _total_tok
            if _active_slug and tasks_done > 0:
                _prev_tasks = cfg.state.last_tasks_snapshot.get(_active_slug, 0)
                _delta_tasks = max(0, tasks_done - _prev_tasks)
                if _delta_tasks > 0:
                    cfg.run_metrics.record_task_complete(_active_slug, _delta_tasks)
                cfg.state.last_tasks_snapshot[_active_slug] = tasks_done
    except Exception:
        pass


def check_single_idea_complete(cfg: MainLoopConfig, all_empty: bool) -> bool:
    """Return True if single-idea mode should exit the main loop."""
    if cfg.from_list:
        return False

    # pending=0 while an agent holds a message in 'processing' is not complete.
    if cfg.bus.has_active_work():
        return False
    if not all_empty:
        return False

    slug, status = _single_idea_focus_status(cfg)
    if slug and status not in _TERMINAL_PROJECT_STATUSES:
        if _try_requeue_focus_project(cfg, slug):
            return False
        return False

    time.sleep(10)
    if cfg.bus.has_active_work() or not cfg.bus.all_queues_empty():
        return False

    slug, status = _single_idea_focus_status(cfg)
    if slug and status not in _TERMINAL_PROJECT_STATUSES:
        if _try_requeue_focus_project(cfg, slug):
            return False
        return False

    print("\n  ✓ All queues empty — pipeline complete.")
    return True


_TERMINAL_PROJECT_STATUSES = frozenset({"complete", "budget_exceeded", "evicted"})


def _single_idea_focus_status(cfg: MainLoopConfig) -> tuple[str, str]:
    slug = (cfg.focus_slug or "").strip()
    if not slug:
        idea_state = _get_active_idea_state(cfg.pipeline_dir, preferred_slug=cfg.focus_slug)
        slug = (idea_state.get("_slug") or "").strip()
    if not slug:
        return "", ""
    state_file = cfg.pipeline_dir / "projects" / slug / "state" / "current_idea.json"
    if not state_file.exists():
        return slug, ""
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return slug, ""
    return slug, state.get("status", "")


def _try_requeue_focus_project(cfg: MainLoopConfig, slug: str) -> bool:
    if cfg.fresh_list_only:
        return False
    from pipeline.project_rebuild import _rebuild_single_project

    project_dir = cfg.pipeline_dir / "projects" / slug
    state_file = project_dir / "state" / "current_idea.json"
    if not state_file.exists():
        return False
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return False
    if _rebuild_single_project(cfg.bus, slug, state, project_dir):
        print(f"  🔁 Re-queued orphaned project '{slug}' — continuing")
        return True
    return False
