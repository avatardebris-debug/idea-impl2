"""
pipeline/run_loop.py
Main pipeline monitoring loop (extracted from runner.py).
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pipeline.run_context import RunContext

_TPS_PRINT_INTERVAL = 900.0  # print throughput breakdown every 15 minutes


@dataclass
class LoopControl:
    stop_requested: bool = False


@dataclass
class MainLoopState:
    ideation_in_progress: bool = False
    ideation_requested_at: float = 0.0
    last_health_check: float = 0.0
    last_dropbox_check: float = 0.0
    last_orphan_requeue: float = 0.0
    status_count: int = 0
    last_tps_print: float = 0.0
    zero_progress_since: dict[str, float] = field(default_factory=dict)
    zero_task_warned: set[str] = field(default_factory=set)
    parallel_seeds: int = 1


@dataclass
class MainLoopConfig:
    bus: Any
    supervisor: Any
    run_ctx: RunContext | None
    ideas_path: Path
    run_metrics: Any
    control: LoopControl
    state: MainLoopState
    polish: bool
    from_list: bool
    fresh_list_only: bool
    provider: str
    model: str
    time_limit_minutes: float
    base_budget: int
    phase_budget: int
    start_time: float
    health_check_interval: float = 60.0
    dropbox_interval_s: float = 600.0
    ideation_timeout_s: float = 35 * 60
    orphan_requeue_cooldown_s: float = 660.0
    zero_task_phase_kill_s: float = 15 * 60
    zero_task_warn_s: float = 10 * 60
    tuner: Any = None
    tuner_log_path: Path | None = None
    count_active_projects: Callable[[], int] | None = None
    warm_upcoming_projects: Callable[..., None] | None = None


def run_main_loop(cfg: MainLoopConfig) -> None:
    import pipeline.runner as r

    while not cfg.control.stop_requested:
        # Dropbox user steering (~every 10 min)
        if time.time() - cfg.state.last_dropbox_check >= cfg.dropbox_interval_s:
            try:
                from pipeline.dropbox import check_dropbox, ensure_dropbox

                ensure_dropbox()
                _dn = check_dropbox(cfg.bus, cfg.ideas_path)
                if _dn:
                    print(f"  [dropbox] Queued {_dn} user message(s) for manager")
            except Exception as _db_err:
                print(f"  [dropbox] check failed: {_db_err}")
            cfg.state.last_dropbox_check = time.time()

        # Check for priority eviction
        try:
            r._check_priority_eviction(cfg.bus, cfg.state.parallel_seeds, ideas_path=cfg.ideas_path)
        except Exception as _ee:
            print(f"  [eviction] Controller error: {_ee}")

        # Time limit check
        if cfg.time_limit_minutes > 0:
            elapsed = (time.time() - cfg.start_time) / 60
            if elapsed >= cfg.time_limit_minutes:
                print(f"\n  ⏰ Time limit reached ({cfg.time_limit_minutes:.0f} min)")
                break

        # Periodic health check
        if time.time() - cfg.state.last_health_check >= cfg.health_check_interval:
            if cfg.polish and cfg.run_ctx and cfg.run_ctx.polish_path and cfg.state.status_count % 3 == 0:
                from pipeline.polish_mode import queue_pending
                _pa = cfg.count_active_projects()
                _pp = queue_pending(cfg.bus)
                from pipeline.polish_status import save_polish_status
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

            # Compact queues periodically (every ~30 health checks ≈ 30 min)
            if cfg.state.status_count > 0 and cfg.state.status_count % 10 == 0:
                compacted = cfg.bus.compact_all()
                if compacted > 0:
                    print(f"  🧹 Compacted {compacted} stale messages from queues")
                try:
                    from pipeline.agent_metrics import trim_old_records
                    trim_old_records()
                except Exception:
                    pass

            # --- Deterministic self-healing checks (every 5th cycle ≈ 5 min) ---
            # Pure Python, no LLM calls. Catches and auto-fixes:
            #   - stray files (src/, tests/ at root)
            #   - missing __init__.py
            #   - state inconsistencies
            #   - import issues
            if cfg.state.status_count > 0 and cfg.state.status_count % 5 == 0:
                try:
                    from pipeline.health_checks import run_all_checks, write_health_report
                    _active_for_health = r._get_active_idea_state(r.PIPELINE_DIR)
                    _health_slug = _active_for_health.get("_slug", "")
                    hc_results = run_all_checks(
                        r.PROJECT_ROOT, r.PIPELINE_DIR, _health_slug,
                    )
                    if hc_results:
                        fixes = sum(1 for r in hc_results if r.auto_fixed)
                        issues = len(hc_results) - fixes
                        if fixes:
                            print(f"  🩺 Health check: {fixes} auto-fixed, {issues} reported")
                        write_health_report(hc_results, r.PIPELINE_DIR)
                except Exception as _hc_err:
                    print(f"  [health] Check failed: {_hc_err}")

            # --- Constitutional patcher: auto-patch prompts from recurring failures ---
            # Runs every 30 health-check cycles (~30 min) — non-critical, never blocks.
            # Finds patterns in bug_resolutions.jsonl that recur across 3+ projects
            # and permanently injects guardrails into the relevant prompts/*.md file.
            if cfg.state.status_count > 0 and cfg.state.status_count % 30 == 0:
                try:
                    from pipeline.constitutional_patcher import run_patcher as _const_patch
                    _patches = _const_patch(min_projects=3, dry_run=False, verbose=False)
                    if _patches:
                        _patch_roles = ", ".join(set(p.role for p in _patches))
                        print(f"  [constitutional] {len(_patches)} new guardrail(s) "
                              f"patched into prompts: {_patch_roles}")
                except Exception as _cp_err:
                    pass  # Never crash the runner over a patcher error

            # Check if all queues are empty AND all ideas done
            all_empty = cfg.bus.all_queues_empty()
            # Find the most recently updated project's current_idea.json
            idea_state = r._get_active_idea_state(r.PIPELINE_DIR)

            # --- Per-session budget enforcement ---
            # If the active project has been running longer than
            # PROJECT_TIME_BUDGET, force-complete it so we move on.
            # NOTE: Only use session_started_at — never fall back to started_at.
            # started_at records project creation (can be days/weeks old).
            # session_started_at tracks only the current pipeline session.
            # If session_started_at is missing (manual reset), stamp now so the
            # project gets a fresh budget window instead of immediately triggering.
            _active_slug = idea_state.get("_slug", "")
            _active_status_for_budget = idea_state.get("status", "")
            _active_started = idea_state.get("session_started_at", "")
            if (_active_slug
                    and _active_status_for_budget not in ("", "complete", "budget_exceeded")
                    and not _active_started):
                # Missing session_started_at — stamp now for a clean budget window
                _active_started = datetime.now(timezone.utc).isoformat()
                idea_state["session_started_at"] = _active_started
                _stamp_file = r.PIPELINE_DIR / "projects" / _active_slug / "state" / "current_idea.json"
                try:
                    _stamp_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
                except Exception:
                    pass
            if _active_slug and _active_started and _active_status_for_budget not in ("", "complete", "budget_exceeded"):
                _is_locked = idea_state.get("budget_lock", False)
                try:
                    _start = datetime.fromisoformat(_active_started)
                    _elapsed = (datetime.now(timezone.utc) - _start).total_seconds() / 60

                    # Budget scales with complexity: cfg.phase_budget min per phase, min cfg.base_budget
                    _total_phases = idea_state.get("total_phases", 3)
                    _cfg.phase_budget = max(cfg.base_budget, int(_total_phases) * cfg.phase_budget)

                    # Grace: don't kill a project on its FINAL phase — let it finish
                    _current_phase = idea_state.get("phase", 1)
                    _on_final_phase = (isinstance(_current_phase, int) and
                                       isinstance(_total_phases, int) and
                                       _current_phase >= _total_phases)
                    # Allow 50% extra time if on final phase
                    if _on_final_phase:
                        _cfg.phase_budget = int(_cfg.phase_budget * 1.5)

                    if _elapsed > _cfg.phase_budget and not _is_locked:
                        _proj_file = r.PIPELINE_DIR / "projects" / _active_slug / "state" / "current_idea.json"
                        idea_state["pre_budget_status"] = idea_state.get("status", "phase_1_executing")
                        idea_state["status"] = "budget_exceeded"
                        idea_state["budget_note"] = f"Force-completed after {_elapsed:.0f} min (budget: {_cfg.phase_budget} min for {_total_phases}-phase project)"
                        _proj_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
                        print(f"  Budget exceeded for '{idea_state.get('title', _active_slug)}' ({_elapsed:.0f}m > {_cfg.phase_budget}m [{_total_phases} phases]) -- skipping")
                        cleared = 0
                        for _role in r.AGENT_ROLES:
                            cleared += cfg.bus.clear_queue(_role)
                        if cleared:
                            print(f"  Cleared {cleared} queued message(s) for budget-exceeded project")
                    elif _elapsed > _cfg.phase_budget and _is_locked:
                        if int(_elapsed) % 30 < 2:  # warn once every 30 min
                            print(f"  🔒 [LOCKED] '{idea_state.get('title', _active_slug)}' over budget ({_elapsed:.0f}m) but lock prevents skip")
                except Exception:
                    pass

            # --- Immediate _reviewed advancement ---
            # If the active project is at phase_X_reviewed and queues are
            # empty, advance it NOW. Don't wait for _rebuild_queues_from_state
            # (which has an 11-min cooldown and multiple preconditions).
            _active_status = idea_state.get("status", "")
            if _active_status.endswith("_reviewed") and all_empty and _active_slug:
                _rv_match = re.match(r"phase_(\d+)_reviewed", _active_status)
                if _rv_match:
                    _rv_phase = int(_rv_match.group(1))
                    _rv_proj = r.PIPELINE_DIR / "projects" / _active_slug
                    _rv_state_file = _rv_proj / "state" / "current_idea.json"
                    if _rv_state_file.exists():
                        try:
                            _rv_state = json.loads(_rv_state_file.read_text(encoding="utf-8"))
                            routed = r._tick_project(bus, _rv_proj, _rv_state, _rv_phase, _active_slug)
                            if routed:
                                # Re-read idea_state since _tick_project may have changed it
                                idea_state = r._get_active_idea_state(r.PIPELINE_DIR)
                        except Exception as _rv_err:
                            print(f"  [reviewed] Failed to advance {_active_slug}: {_rv_err}")

            # If active project is budget_exceeded or complete, advance to next project.
            if idea_state.get("status") in ("budget_exceeded", "complete"):
                slug = idea_state.get("_slug", "")
                orphaned = r._rebuild_queues_from_state(cfg.bus)
                if orphaned:
                    print(f"  ▶️  Advancing past '{slug}' → {orphaned} project(s) queued")
                if cfg.polish and cfg.run_ctx and cfg.run_ctx.polish_path and not cfg.bus.has_active_work():
                    from pipeline.polish_mode import queue_pending, run_polish_mode
                    _pq = run_polish_mode(cfg.bus, cfg.run_ctx.polish_path, r._seeded_this_session)
                    if _pq:
                        print(f"  [polish] Re-queued {_pq} project(s) from polish_queue.md")
                elif cfg.from_list and not cfg.polish and not cfg.bus.has_active_work():
                    # --- Strategy 6: Parallel seeding ---
                    # Try to fill all open slots up to cfg.state.parallel_seeds.
                    active_now = cfg.count_active_projects()
                    slots_free = max(1, cfg.state.parallel_seeds - active_now)
                    for _seed_i in range(slots_free):
                        seeded = r.seed_from_master_list(cfg.bus, silent=cfg.state.ideation_in_progress,
                                                        ideas_path=cfg.ideas_path, resume_inprogress=cfg.fresh_list_only)
                        if seeded == r._SEED_SEEDED:
                            cfg.state.ideation_in_progress = False
                            cfg.state.ideation_requested_at = 0.0
                            # After seeding, pre-warm next batch (Strategy 7)
                            if cfg.state.parallel_seeds > 1:
                                threading.Thread(
                                    target=cfg.warm_upcoming_projects,
                                    args=(cfg.state.parallel_seeds,),
                                    daemon=True,
                                    name="env-pool-refill",
                                ).start()
                        elif seeded == r._SEED_EMPTY:
                            cfg.state.ideation_in_progress, cfg.state.ideation_requested_at, _stop = r._apply_seed_empty(
                                seeded,
                                cfg.bus,
                                ideation_in_progress=cfg.state.ideation_in_progress,
                                ideation_requested_at=cfg.state.ideation_requested_at,
                                ideation_timeout_s=cfg.ideation_timeout_s,
                            )
                            if _stop:
                                cfg.control.stop_requested = True
                            break
                        else:
                            break  # _SEED_BLOCKED or no more ideas
                elif cfg.from_list and not cfg.polish and not orphaned:
                    r.seed_from_master_list(cfg.bus, silent=True, ideas_path=cfg.ideas_path,
                                          resume_inprogress=cfg.fresh_list_only)

            running_agents = sum(1 for s in health.values() if s == "running")

            # Print status line
            pending_total = sum(cfg.bus.queue_depth(r) for r in r.AGENT_ROLES)
            elapsed_m = (time.time() - cfg.start_time) / 60
            phase = idea_state.get("status", "?")
            title = idea_state.get("title", "")
            # Multi-project title: show all active projects when cfg.state.parallel_seeds > 1
            if cfg.state.parallel_seeds > 1:
                _all_active = r._get_all_active_idea_states(r.PIPELINE_DIR)
                if len(_all_active) > 1:
                    title_str = " | " + " / ".join(
                        f"[{s.get('title', '?')[:15]}]"
                        for s in _all_active[:4]
                    )
                elif title:
                    title_str = f" | [{title[:28]}]"
                else:
                    title_str = ""
            else:
                title_str = f" | [{title[:28]}]" if title else ""

            # --- Live task progress from tasks.md (not stale JSON) ---
            # The executor only writes tasks_done/tasks_total once at start.
            # We re-read the actual file every tick for live progress.
            tasks_done, tasks_total = 0, 0
            try:
                slug = idea_state.get("_slug", "")
                phase_num = idea_state.get("phase", 1)
                if slug:
                    tasks_file = r.PIPELINE_DIR / "projects" / slug / f"phases/phase_{phase_num}/tasks.md"
                    if tasks_file.exists():
                        from pipeline.agent_process import AgentProcess
                        AgentProcess.normalize_tasks_file(tasks_file)  # fix heading format
                        raw = tasks_file.read_text(encoding="utf-8")
                        scoped = AgentProcess._extract_phase_tasks(raw, phase_num)
                        tasks_total = len(re.findall(r'^\s*- \[[ xX]\]', scoped, re.MULTILINE))
                        tasks_done  = len(re.findall(r'^\s*- \[[xX]\]', scoped, re.MULTILINE))
                        # Fallback: count numbered task lines if no checkbox format found
                        if tasks_total == 0:
                            numbered = re.findall(r'^\d+\.\s+\S', scoped, re.MULTILINE)
                            tasks_total = len(numbered)
            except Exception:
                pass
            task_str = f" {tasks_done}/{tasks_total}✓" if tasks_total else ""

            # --- Workspace activity signal (used by stall-kill guard below) ---
            # Measures file-write activity independently of checkbox state.
            # The executor often writes files for 10-15 min before marking any [x].
            _ws_file_count = 0
            _ws_last_mtime = 0.0
            try:
                if _active_slug:
                    _ws_dir = r.PIPELINE_DIR / "projects" / _active_slug / "workspace"
                    if _ws_dir.exists():
                        for _wf in _ws_dir.rglob("*"):
                            if _wf.is_file() and not _wf.name.startswith("."):
                                _ws_file_count += 1
                                _mt = _wf.stat().st_mtime
                                if _mt > _ws_last_mtime:
                                    _ws_last_mtime = _mt
            except Exception:
                pass

            # Improve display: when 0 checkboxes but files exist, show file count
            if tasks_total and tasks_done == 0 and _ws_file_count > 0:
                task_str = f" 0/{tasks_total}✓ ({_ws_file_count} files)"

            # Ollama GPU heartbeat (checks every 5 min, cached otherwise)
            gpu_str = ""
            _gpu_idle = False
            if cfg.provider == "ollama":
                gpu_status = r._check_ollama_heartbeat(cfg.model)
                if gpu_status:
                    if "IDLE" in gpu_status or "ERR" in gpu_status:
                        gpu_str = f" ⚠️ {gpu_status} — cfg.model evicted from VRAM!"
                        _gpu_idle = True
                    else:
                        gpu_str = f" {gpu_status}"

            # --- Live tok/s from throughput.json ---
            _tps_str = ""
            _live_gpu_pct = 0.0   # will be populated below and passed to tuner
            try:
                _tp_live_path = r.PIPELINE_DIR / "state" / "throughput.json"
                if _tp_live_path.exists():
                    _tp_live = json.loads(_tp_live_path.read_text(encoding="utf-8"))
                    _live_cum_tok   = _tp_live.get("cumulative_tokens", 0)
                    _live_cum_inf_s = _tp_live.get("cumulative_inference_s", 0.0)
                    _live_cum_wall  = _tp_live.get("cumulative_wall_s", 0.0)
                    _live_last_tps  = _tp_live.get("tps", 0.0)   # last LLM call
                    _live_age_s     = time.time() - _tp_live.get("updated_at", 0)
                    if _live_cum_tok > 0 and _live_age_s < 600:  # skip if >10m stale
                        _live_avg_tps = (_live_cum_tok / _live_cum_inf_s
                                         if _live_cum_inf_s > 0 else 0)
                        # Show: "42t/s last / 54t/s avg"
                        _tps_str = (f" {_live_last_tps:.0f}t/s"
                                    f"/{_live_avg_tps:.0f}avg")
                        # GPU util % = fraction of wall time spent in inference
                        if _live_cum_wall > 0:
                            _live_gpu_pct = min(100.0, _live_cum_inf_s / _live_cum_wall * 100)
            except Exception:
                pass

            # --- Dynamic Parallelizer: observe & adjust ---
            _tuner_str = ""
            if cfg.tuner is not None:
                try:
                    _tp_path = r.PIPELINE_DIR / "state" / "throughput.json"
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
                                _tlf.write(json.dumps({
                                    "ts": time.time(),
                                    "old_seeds": _decision.old_seeds,
                                    "new_seeds": _decision.new_seeds,
                                    "reason": _decision.reason,
                                    "confidence": round(_decision.confidence, 3),
                                }) + "\n")
                        except Exception:
                            pass
                    if cfg.state.status_count % 4 == 0:
                        _tuner_str = f"  {cfg.tuner.status_line(cfg.state.parallel_seeds)}"
                except Exception:
                    pass  # Never crash the loop on tuner errors

            status_line = r._clean(
                f"  [{elapsed_m:.0f}m] agents={running_agents}/{len(r.AGENT_ROLES)} "
                f"pending={pending_total} phase={phase}{task_str}"
                f"{gpu_str}{_tps_str}{title_str}"
            )
            # Always print on a new line — ’\r’ tricks break on cloud/Windows terminals.
            # Throttle to every 4 checks (~4 min) to keep output readable.
            if cfg.state.status_count % 4 == 0:
                print(status_line, flush=True)
                if _tuner_str:
                    print(_tuner_str, flush=True)
            cfg.state.status_count += 1

            # Print full throughput breakdown every 15 minutes
            _now = time.time()
            if cfg.provider == "ollama" and (_now - cfg.state.last_tps_print) >= _TPS_PRINT_INTERVAL:
                _tp_path = r.PIPELINE_DIR / "state" / "throughput.json"
                if _tp_path.exists():
                    try:
                        _tp = json.loads(_tp_path.read_text(encoding="utf-8"))
                        _age_s      = _now - _tp.get("updated_at", _now)
                        _cum_tok    = _tp.get("cumulative_tokens", 0)
                        _cum_inf_s  = _tp.get("cumulative_inference_s", 0.0)
                        _cum_wall_s = _tp.get("cumulative_wall_s", 0.0) or 1
                        _cum_tool_s = _tp.get("cumulative_tool_s", 0.0)
                        _calls      = _tp.get("call_count", 0)
                        _tool_calls = _tp.get("tool_call_count", 0)
                        _tps_inf    = _tp.get("tps", 0)  # last-call GPU tok/s
                        # Pipeline tok/s = total tokens / total elapsed time
                        _tps_pipe   = _cum_tok / _cum_wall_s if _cum_tok else 0
                        # Average inference tok/s over the whole session
                        _tps_inf_avg = _cum_tok / _cum_inf_s if _cum_inf_s > 0 else 0
                        # Time allocation percentages
                        _gpu_pct    = (_cum_inf_s  / _cum_wall_s) * 100
                        _tool_pct   = (_cum_tool_s / _cum_wall_s) * 100
                        _overhead_pct = max(0, 100 - _gpu_pct - _tool_pct)
                        # Human-readable wall time
                        _wall_h     = int(_cum_wall_s // 3600)
                        _wall_m     = int((_cum_wall_s % 3600) // 60)
                        _wall_str   = (f"{_wall_h}h{_wall_m:02d}m" if _wall_h
                                       else f"{_wall_m}m")
                        _age_str    = (f"{int(_age_s // 60)}m ago"
                                       if _age_s > 90 else "recent")
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
                                f"/ {_cum_tok//_calls if _calls else 0} avg/call  "
                                f"(last: {_age_str})",
                                flush=True,
                            )

                        # --- Stall detector ---
                        # If agents are running but no LLM call in >10 min,
                        # something is looping silently. Print a visible warning
                        # showing which roles have messages stuck in 'processing'.
                        _STALL_THRESHOLD_S = 600  # 10 minutes
                        _run_elapsed_s = _now - cfg.start_time
                        if _run_elapsed_s > _STALL_THRESHOLD_S and _age_s > _STALL_THRESHOLD_S and running_agents > 0:
                            print(
                                f"  ⚠️  STALL DETECTED: no LLM call in {int(_age_s//60)}m "
                                f"({running_agents} agents running)",
                                flush=True,
                            )
                            # Show which roles have processing-state messages
                            try:
                                _stuck = cfg.bus.get_processing_messages()
                                if _stuck:
                                    _by_role: dict[str, int] = {}
                                    for _sm in _stuck:
                                        _by_role[_sm.to_agent] = _by_role.get(_sm.to_agent, 0) + 1
                                    _stuck_str = ", ".join(
                                        f"{r}×{n}" for r, n in sorted(_by_role.items())
                                    )
                                    print(f"     Stuck in processing: {_stuck_str}", flush=True)
                                else:
                                    print(
                                        f"     No messages in 'processing' — queue empty, "
                                        f"agents idle (phase transition stall?)",
                                        flush=True,
                                    )
                            except Exception:
                                pass

                    except Exception:
                        pass
                cfg.state.last_tps_print = _now

            # --- Zero-task-progress phase kill ---
            # If the executor has been in *_executing phase for cfg.zero_task_phase_kill_s
            # with 0/N tasks done, the project is genuinely stuck (e.g. external API
            # unavailable, impossible task). Mark budget_exceeded and move on.
            _zpk = f"{_active_slug}:{idea_state.get('phase', 1)}"
            _is_locked = idea_state.get("budget_lock", False)
            if (tasks_total > 0 and tasks_done == 0
                    and "executing" in idea_state.get("status", "")
                    and _active_slug
                    and not _is_locked
                    and idea_state.get("status", "") not in ("complete", "budget_exceeded")):
                # Guard: if workspace files were written recently the executor IS
                # making progress — it just hasn't ticked checkboxes yet (0→N pattern).
                # Reset the stall timer so we don't kill a productive executor.
                _ACTIVITY_WINDOW = 8 * 60  # 8 min — executor marks boxes at end
                _ws_active = (
                    _ws_last_mtime > 0
                    and (time.time() - _ws_last_mtime) < _ACTIVITY_WINDOW
                )
                if _ws_active:
                    # Files modified recently → reset stall clock silently
                    cfg.state.zero_progress_since.pop(_zpk, None)
                    cfg.state.zero_task_warned.discard(_zpk)
                elif _zpk not in cfg.state.zero_progress_since:
                    cfg.state.zero_progress_since[_zpk] = time.time()
                else:
                    _stall_secs = time.time() - cfg.state.zero_progress_since[_zpk]
                    # 10-min warning
                    if _stall_secs > cfg.zero_task_warn_s and _zpk not in cfg.state.zero_task_warned:
                        cfg.state.zero_task_warned.add(_zpk)
                        print(
                            f"  ⚠️  Zero-task stall: '{idea_state.get('title', _active_slug)}' "
                            f"phase {idea_state.get('phase',1)} — "
                            f"0/{tasks_total} tasks for {int(_stall_secs//60)}m, "
                            f"{_ws_file_count} workspace file(s), "
                            f"last write {int((time.time()-_ws_last_mtime)//60) if _ws_last_mtime else '?'}m ago "
                            f"(kill in {(cfg.zero_task_phase_kill_s - _stall_secs)//60:.0f}m)"
                        )
                    # 15-min kill — only fires if no recent file activity either
                    if _stall_secs > cfg.zero_task_phase_kill_s:
                        _proj_file = (r.PIPELINE_DIR / "projects" / _active_slug
                                      / "state" / "current_idea.json")
                        try:
                            _st = json.loads(_proj_file.read_text(encoding="utf-8"))
                            if _st.get("status", "") not in ("complete", "budget_exceeded"):
                                _st["status"] = "budget_exceeded"
                                _st["budget_note"] = (
                                    f"Phase {idea_state.get('phase',1)} stuck: "
                                    f"0/{tasks_total} tasks after {cfg.zero_task_phase_kill_s//60}m"
                                )
                                _proj_file.write_text(json.dumps(_st, indent=2), encoding="utf-8")
                                print(
                                    f"  ⏰ Zero-task timeout: '{idea_state.get('title', _active_slug)}' "
                                    f"phase {idea_state.get('phase',1)} — "
                                    f"0/{tasks_total} tasks in {cfg.zero_task_phase_kill_s//60}m → budget_exceeded"
                                )
                                for _role in r.AGENT_ROLES:
                                    cfg.bus.clear_queue(_role)
                        except Exception:
                            pass
                        cfg.state.zero_progress_since.pop(_zpk, None)
                        cfg.state.zero_task_warned.discard(_zpk)
            else:
                cfg.state.zero_progress_since.pop(_zpk, None)  # reset when tasks progress or phase changes
                cfg.state.zero_task_warned.discard(_zpk)

            if all_empty and not cfg.from_list:
                # Single idea mode — might be done
                # Wait a bit longer to make sure nothing new arrives
                time.sleep(10)
                if cfg.bus.all_queues_empty():
                    print(f"\n  ✓ All queues empty — pipeline complete.")
                    break
            elif all_empty and cfg.from_list:
                # --- Guard: don't seed a new project if any project is
                # actively being worked on.  The queue looks empty because
                # the agent acked the message, but the agent is still
                # processing it.  Check if ANY project has a working-state
                # status that was recently modified (< 15 min ago). ---
                _any_working = False
                _working_states = ("_executing", "_validating", "_reviewing", "_planning")
                _recency_cutoff = time.time() - 900  # 15 min
                _projects_dir = r.PIPELINE_DIR / "projects"
                if _projects_dir.exists():
                    for _pd in _projects_dir.iterdir():
                        _sf = _pd / "state" / "current_idea.json"
                        if not _sf.exists():
                            continue
                        try:
                            if os.path.getmtime(str(_sf)) < _recency_cutoff:
                                continue
                            _st = json.loads(_sf.read_text(encoding="utf-8"))
                            _ss = _st.get("status", "")
                            if any(_ss.endswith(ws) for ws in _working_states):
                                _any_working = True
                                break
                        except Exception:
                            pass

                if _any_working:
                    pass  # agent is mid-task — wait for it to finish
                elif not cfg.bus.has_active_work():
                    now = time.time()
                    if now - cfg.state.last_orphan_requeue >= cfg.orphan_requeue_cooldown_s:
                        orphaned = 0 if cfg.fresh_list_only else r._rebuild_queues_from_state(cfg.bus)
                        if orphaned:
                            cfg.state.last_orphan_requeue = now
                            print(f"  🔁 Re-queued {orphaned} orphaned project(s) — not seeding new ideas yet")
                        elif cfg.polish and cfg.run_ctx and cfg.run_ctx.polish_path:
                            from pipeline.polish_mode import run_polish_mode as _run_polish_mode
                            _pq = _run_polish_mode(
                                cfg.bus, cfg.run_ctx.polish_path, r._seeded_this_session
                            )
                            if _pq:
                                print(f"  [polish] Re-queued {_pq} project(s) from polish_queue.md")
                        elif not cfg.polish:
                            seeded = r.seed_from_master_list(cfg.bus, silent=cfg.state.ideation_in_progress,
                                                            ideas_path=cfg.ideas_path, resume_inprogress=cfg.fresh_list_only)
                            if seeded == r._SEED_SEEDED:
                                cfg.state.ideation_in_progress = False
                                cfg.state.ideation_requested_at = 0.0
                            elif seeded == r._SEED_EMPTY:
                                cfg.state.ideation_in_progress, cfg.state.ideation_requested_at, _stop = r._apply_seed_empty(
                                    seeded,
                                    cfg.bus,
                                    ideation_in_progress=cfg.state.ideation_in_progress,
                                    ideation_requested_at=cfg.state.ideation_requested_at,
                                    ideation_timeout_s=cfg.ideation_timeout_s,
                                )
                                if _stop:
                                    cfg.control.stop_requested = True
                            # _SEED_BLOCKED — deps pending, just wait

            # --- Collect per-project metrics from state files ---
            try:
                projects_dir = r.PIPELINE_DIR / "projects"
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

                            # Read retry counts from phase_retries.json
                            retries = 0
                            pr_path = proj_dir / "state" / "phase_retries.json"
                            if pr_path.exists():
                                try:
                                    pr_data = json.loads(pr_path.read_text(encoding="utf-8"))
                                    retries = sum(v for v in pr_data.values() if isinstance(v, int))
                                except Exception:
                                    pass

                            # --- Global lifetime retry cap ---
                            # If a project has accumulated too many retries across all
                            # phases, force budget_exceeded to break infinite loops.
                            if (retries >= r.MAX_PROJECT_LIFETIME_RETRIES
                                    and st not in ("complete", "budget_exceeded", "", "dep_waiting")):
                                ci["status"] = "budget_exceeded"
                                ci["budget_note"] = (
                                    f"Force-completed: exceeded {r.MAX_PROJECT_LIFETIME_RETRIES} "
                                    f"total retries across all phases (actual: {retries})"
                                )
                                ci_path.write_text(json.dumps(ci, indent=2), encoding="utf-8")
                                print(
                                    f"  \U0001f6d1 Lifetime retry cap hit: '{ci.get('title', slug)}' "
                                    f"({retries} retries \u2265 {r.MAX_PROJECT_LIFETIME_RETRIES}) \u2192 budget_exceeded"
                                )
                                for _role in r.AGENT_ROLES:
                                    cfg.bus.clear_queue(_role)
                                st = "budget_exceeded"  # update local var for metrics

                            if st == "complete":
                                cfg.run_metrics.record_project_complete(
                                    slug,
                                    phases=ci.get("phase", 0),
                                    retries=retries,
                                )
            except Exception:
                pass  # metrics are best-effort, never crash the runner

            # --- Wire token counts from throughput.json into metrics ---
            # throughput.json is written by the LLM interface on every call.
            # We snapshot cumulative_tokens here so per-run totals are accurate.
            try:
                _tp_metrics_path = r.PIPELINE_DIR / "state" / "throughput.json"
                if _tp_metrics_path.exists():
                    _tp_data = json.loads(_tp_metrics_path.read_text(encoding="utf-8"))
                    _total_tok = _tp_data.get("cumulative_tokens", 0)
                    # Attribute all tokens to the active project for this tick
                    if _active_slug and _total_tok > 0:
                        # Only record the delta since last tick to avoid double-counting
                        _prev_tok = getattr(r.run_pipeline, "_last_tok_snapshot", 0)
                        _delta_tok = max(0, _total_tok - _prev_tok)
                        if _delta_tok > 0:
                            cfg.run_metrics.record_tokens(_active_slug, _delta_tok)
                        r.run_pipeline._last_tok_snapshot = _total_tok
                    # Record task completions from live tasks.md
                    if _active_slug and tasks_done > 0:
                        _prev_tasks = getattr(r.run_pipeline, "_last_tasks_snapshot", {}).get(_active_slug, 0)
                        _delta_tasks = max(0, tasks_done - _prev_tasks)
                        if _delta_tasks > 0:
                            cfg.run_metrics.record_task_complete(_active_slug, _delta_tasks)
                        if not hasattr(r.run_pipeline, "_last_tasks_snapshot"):
                            r.run_pipeline._last_tasks_snapshot = {}
                        r.run_pipeline._last_tasks_snapshot[_active_slug] = tasks_done
            except Exception:
                pass  # Never crash the runner over metrics

            cfg.state.last_health_check = time.time()

        time.sleep(2)
