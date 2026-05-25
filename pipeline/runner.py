"""
pipeline/runner.py
Main entry point — subprocess orchestrator for the multi-agent pipeline.

Starts each agent as a subprocess, monitors health, handles shutdown.

Usage:
    python pipeline/runner.py "Build a web scraper for Hacker News"
    python pipeline/runner.py --from-list
    python pipeline/runner.py --resume
    python pipeline/runner.py --from-list --provider ollama --model qwen3.5:35b --time-limit 480
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import textwrap
import threading
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Auto-load .env file (stdlib only — no python-dotenv needed)
# Supports: KEY=value, KEY="value", export KEY=value
# ---------------------------------------------------------------------------
_ENV_FILE = pathlib.Path(__file__).parent.parent / ".env"
if _ENV_FILE.exists():
    _ENV_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[\"']?(.*?)[\"']?\s*$")
    for _line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        if _line.strip().startswith("#") or not _line.strip():
            continue
        _m = _ENV_RE.match(_line)
        if _m:
            _key, _val = _m.group(1), _m.group(2)
            if _key not in os.environ:  # don't override explicit env vars
                os.environ[_key] = _val

# Suppress Jupyter/cloud terminal escape sequences (^[]11;rgb:... etc.)
# These are OSC color query responses that pollute output in web terminals.
if not sys.stdout.isatty():
    os.environ.setdefault("TERM", "dumb")

# Repo root on sys.path (required when invoked as `python pipeline/runner.py`)
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from pipeline.pipeline_config import (
    AGENT_ROLES,
    AGENTS_DIR,
    DEFAULT_BASE_BUDGET,
    DEFAULT_PHASE_BUDGET,
    MAX_PHASE_RETRIES,
    MAX_PROJECT_LIFETIME_RETRIES,
    PIPELINE_DIR,
    PROJECT_ROOT,
)
from pipeline.slug_util import slugify_title as _slugify
from pipeline.agent_supervisor import AgentSupervisor
from pipeline.ollama_health import _check_ollama_heartbeat, _check_ollama_model
from pipeline.pipeline_status import (
    _get_active_idea_state,
    _get_all_active_idea_states,
    init_pipeline_dirs,
    load_pipeline_status,
    save_pipeline_status,
    set_runner_ideas_path,
)
from pipeline.seeding import (
    SEED_BLOCKED,
    SEED_EMPTY,
    SEED_GOAL_QUEUED,
    SEED_SEEDED,
    _SEED_BLOCKED,
    _SEED_EMPTY,
    _SEED_GOAL_QUEUED,
    _SEED_SEEDED,
    _purge_dep_blocked_messages,
    _seeded_this_session,
    check_resume,
    seed_from_master_list,
    seed_idea,
)
from pipeline.project_ops import (
    _check_priority_eviction,
    _rebuild_queues_from_state,
    _tick_project,
)
from pipeline.startup import resolve_initial_work

__all__ = [
    "AGENT_ROLES",
    "MAX_PROJECT_LIFETIME_RETRIES",
    "PIPELINE_DIR",
    "PROJECT_ROOT",
    "AgentSupervisor",
    "_SEED_BLOCKED",
    "_SEED_EMPTY",
    "_SEED_GOAL_QUEUED",
    "_SEED_SEEDED",
    "_check_ollama_heartbeat",
    "_check_priority_eviction",
    "_get_active_idea_state",
    "_get_all_active_idea_states",
    "_seeded_this_session",
    "_tick_project",
    "_rebuild_queues_from_state",
    "main",
    "run_pipeline",
    "seed_from_master_list",
]


_run_ctx: "RunContext | None" = None

def run_pipeline(
    idea: str | None = None,
    from_list: bool = False,
    resume: bool = False,
    provider: str = "ollama",
    model: str = os.environ.get("PIPELINE_MODEL", "qwen3.5:35b"),
    time_limit_minutes: float = 0,
    base_budget: int = DEFAULT_BASE_BUDGET,
    phase_budget: int = DEFAULT_PHASE_BUDGET,
    ideas_file: str | None = None,
    fresh_list_only: bool = False,
    polish: bool = False,
    polish_queue_file: str | None = None,
    parallel_seeds: int = 1,
    auto_tune: bool = False,
    max_seeds: int = 4,
    num_executors: int = 1,
    legacy: bool = False,
) -> None:
    """Main pipeline orchestrator."""
    from pipeline.context_aggregator import (
        refresh_all_projects,
        start_background_refresh,
        stop_background_refresh,
    )
    from pipeline.message_bus import MessageBus
    from pipeline.metrics import RunMetrics
    from pipeline.pipeline_mode import set_legacy_mode
    from pipeline.run_context import RunContext

    set_legacy_mode(legacy)
    global PROJECT_ROOT, _run_ctx
    _ideas_path = pathlib.Path(ideas_file).resolve() if ideas_file else PROJECT_ROOT.resolve() / "master_ideas.md"
    _polish_path: pathlib.Path | None = None
    if polish:
        from pipeline.polish_mode import resolve_polish_path
        _polish_path = resolve_polish_path(
            polish_queue_file=polish_queue_file,
            ideas_file=ideas_file,
        )
        _ideas_path = _polish_path
    _run_ctx = RunContext(
        mode="polish" if polish else ("resume" if resume else ("from_list" if from_list else "single")),
        ideas_path=_ideas_path,
        legacy=legacy,
        polish_path=_polish_path,
    )
    set_runner_ideas_path(_ideas_path)
    if ideas_file and not polish:
        print(f"  Ideas:    {_ideas_path}")
    init_pipeline_dirs()
    bus = MessageBus()

    # One-shot migration: import any legacy JSONL queue files into SQLite.
    # Safe to call every startup — INSERT OR IGNORE skips already-imported msgs.
    try:
        _migrated = bus.migrate_from_jsonl()
        if _migrated:
            print(f"  🗄️  Migrated {_migrated} legacy queue message(s) to SQLite bus")
    except Exception:
        pass

    print("=" * 60)
    print("  🏭 Idea Development Pipeline")
    print("=" * 60)
    print(f"  Provider: {provider}")
    print(f"  Model:    {model}")
    if time_limit_minutes > 0:
        print(f"  Time:     {time_limit_minutes:.0f} minutes")
    else:
        print(f"  Time:     unlimited")
    print(f"  Agents:   {len(AGENT_ROLES)}")
    print(f"  Budget:   {base_budget}min base, {phase_budget}min/phase")
    if fresh_list_only:
        print(f"  Mode:     FRESH LIST ONLY — skipping all stray/in-progress projects")
    if polish:
        print(f"  Mode:     POLISH - resuming complete projects with missing phases")
    if legacy:
        print(f"  Mode:     LEGACY - capability registry disabled (reusable_tools.md only)")
    else:
        print(f"  Mode:     CAPABILITIES - registry via context_cache (not rebuilt each run)")
        try:
            from pipeline.capability_registry import REGISTRY_DB
            if REGISTRY_DB.exists():
                print(f"  Registry: {REGISTRY_DB.relative_to(PROJECT_ROOT)}")
            else:
                print("  Registry: missing — run python scripts/build_capability_registry.py")
        except Exception as _reg_err:
            print(f"  Registry: status unknown ({_reg_err})")
    if auto_tune:
        print(f"  Seeds:    auto-tune ON (start={parallel_seeds}, max={max_seeds})")
    elif parallel_seeds > 1:
        print(f"  Seeds:    {parallel_seeds} parallel project slots (Strategy 6)")
    if num_executors > 1:
        print(f"  Executors:{num_executors} parallel executor instances")
    _light_model_env = os.environ.get("PIPELINE_LIGHT_MODEL", "").strip()
    if _light_model_env:
        print(f"  Light:    {_light_model_env} (light-tier agents: planner/manager/validator)")

    startup = resolve_initial_work(
        bus,
        run_ctx=_run_ctx,
        ideas_path=_ideas_path,
        idea=idea,
        from_list=from_list,
        resume=resume,
        polish=polish,
        fresh_list_only=fresh_list_only,
        parallel_seeds=parallel_seeds,
        save_pipeline_status=save_pipeline_status,
    )
    if startup.stop_early:
        return
    from_list = startup.from_list
    has_work = startup.has_work
    if polish:
        from_list = True  # polish replays queue only; never master_ideas seeding

    if not has_work:
        print("\n  ✗ Nothing to do. Provide an idea, use --from-list, or --resume.")
        print("    python pipeline/runner.py \"Your idea here\"")
        print("    python pipeline/runner.py --from-list")
        return

    # Save initial status
    save_pipeline_status({
        "status": "running",
        "run_mode": _run_ctx.mode if _run_ctx else "single",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "current_idea": idea or ("polish_queue" if polish else "(from list)"),
        "polish_queue": str(_run_ctx.polish_path) if _run_ctx and _run_ctx.polish_path else "",
    })
    if polish and _run_ctx and _run_ctx.polish_path:
        from pipeline.polish_status import save_polish_status
        save_polish_status(
            run_state="running",
            reason="agents_starting",
            queue_path=str(_run_ctx.polish_path),
        )

    # Start metrics collection
    run_metrics = RunMetrics.start(provider=provider, model=model)
    print(f"  Prompts:  {run_metrics.prompt_version}")

    # --- Ollama pre-flight check ---
    if provider == "ollama":
        model = _check_ollama_model(model)  # Returns canonical API name (may differ in case)

    # Start all agents
    print(f"\n  Starting agents...")
    supervisor = AgentSupervisor(provider, model, num_executors=num_executors, legacy=legacy)

    # Handle Ctrl+C
    from pipeline.run_loop import LoopControl, MainLoopConfig, MainLoopState, run_main_loop

    loop_control = LoopControl()
    original_sigint = signal.getsignal(signal.SIGINT)

    def _handle_interrupt(signum, frame):
        if loop_control.stop_requested:
            print("\n  Force stopping...")
            supervisor.stop_all()
            sys.exit(1)
        loop_control.stop_requested = True
        print("\n\n  [Pipeline] Graceful stop — checkpointing all active projects...")
        # Stamp checkpoint_at on all in-flight projects so resume display is clear
        try:
            for _ckpt_state in _get_all_active_idea_states(PIPELINE_DIR):
                _ckpt_slug = _ckpt_state.get("_slug", "")
                if not _ckpt_slug:
                    continue
                _ckpt_file = (
                    PIPELINE_DIR / "projects" / _ckpt_slug / "state" / "current_idea.json"
                )
                try:
                    _ckpt_data = json.loads(_ckpt_file.read_text(encoding="utf-8"))
                    _ckpt_data["checkpoint_at"] = datetime.now(timezone.utc).isoformat()
                    _ckpt_file.write_text(json.dumps(_ckpt_data, indent=2), encoding="utf-8")
                except Exception:
                    pass
        except Exception:
            pass
        print("  Checkpointed. Press Ctrl+C again to force stop.")

    signal.signal(signal.SIGINT, _handle_interrupt)

    try:
        supervisor.start_all()
        supervisor.save_registry()

        # --- Warm context caches for all existing projects ---
        _ctx_refreshed = refresh_all_projects(PIPELINE_DIR)
        if _ctx_refreshed:
            print(f"  📦 Context cache: warmed {_ctx_refreshed} project(s)")
        start_background_refresh(PIPELINE_DIR, interval_seconds=120)

        if polish:
            print(f"\n  🚀 Polish pipeline RUNNING. Press Ctrl+C to stop.")
            print(f"     Status file: .pipeline/state/polish_status.json\n")
        else:
            print(f"\n  🚀 Pipeline running. Press Ctrl+C to stop.\n")

        start_time = time.time()
        loop_state = MainLoopState(
            parallel_seeds=parallel_seeds,
            last_health_check=start_time,
        )

        # --- Dynamic Parallelizer (auto-tune) ---
        _tuner = None
        _tuner_log_path = PIPELINE_DIR / "state" / "tuner_log.jsonl"
        if auto_tune:
            try:
                from pipeline.dynamic_parallelizer import DynamicParallelizer
                _tuner = DynamicParallelizer(
                    min_seeds=1,
                    max_seeds=max_seeds,
                )
            except Exception as _te:
                print(f"  [tuner] Failed to init DynamicParallelizer: {_te}")

        # --- Strategy 6: Parallel seed slot tracking ---
        # Count how many distinct non-terminal projects are currently active.
        # When active_count < parallel_seeds, we can seed another project.
        def _count_active_projects() -> int:
            """Count projects that are in-flight (not complete/budget_exceeded)."""
            pd = PIPELINE_DIR / "projects"
            if not pd.exists():
                return 0
            active = 0
            for p in pd.iterdir():
                if not p.is_dir():
                    continue
                sf = p / "state" / "current_idea.json"
                if not sf.exists():
                    continue
                try:
                    s = json.loads(sf.read_text(encoding="utf-8"))
                    if s.get("status", "") not in ("complete", "budget_exceeded", "evicted", ""):
                        active += 1
                except Exception:
                    pass
            return active

        # --- Strategy 7: Environment pooling — pre-warm context caches ---
        # Mirrors PufferLib's environment pool: spin up N environments before
        # any training starts.  Here we pre-build context_cache.json for the
        # next N unstarted ideas so agents start with a warm cache instead of
        # doing 5-10 file reads on their first turn.
        def _warm_upcoming_projects(n: int = 3) -> None:
            """Background thread: pre-build context caches for next N ideas."""
            try:
                from pipeline.context_aggregator import get_aggregator
                agg = get_aggregator()
                ideas_path = _ideas_path  # closure over outer scope
                if not ideas_path.exists():
                    return
                text = ideas_path.read_text(encoding="utf-8")
                # Extract unchecked items (same logic as seed_from_master_list)
                import re as _re
                unchecked = _re.findall(
                    r'^-\s*\[\s*\]\s+(.+?)\s*$', text, _re.MULTILINE
                )
                warmed = 0
                for raw_title in unchecked[:n]:
                    slug = _slugify(raw_title.split(".")[0][:50])
                    agg.build(slug=slug, force=False)  # no-op if cache exists
                    warmed += 1
                if warmed:
                    pass  # silent — background activity
            except Exception:
                pass

        # Kick off initial context pre-warming for next batch of ideas
        if from_list and parallel_seeds > 1:
            threading.Thread(
                target=_warm_upcoming_projects,
                args=(parallel_seeds + 2,),
                daemon=True,
                name="env-pool-warmup",
            ).start()

        run_main_loop(MainLoopConfig(
            bus=bus,
            supervisor=supervisor,
            run_ctx=_run_ctx,
            ideas_path=_ideas_path,
            run_metrics=run_metrics,
            control=loop_control,
            state=loop_state,
            polish=polish,
            from_list=from_list,
            fresh_list_only=fresh_list_only,
            provider=provider,
            model=model,
            time_limit_minutes=time_limit_minutes,
            base_budget=base_budget,
            phase_budget=phase_budget,
            start_time=start_time,
            tuner=_tuner,
            tuner_log_path=_tuner_log_path,
            count_active_projects=_count_active_projects,
            warm_upcoming_projects=_warm_upcoming_projects,
        ))

    finally:
        stop_background_refresh()
        print("\n  Stopping agents...")
        supervisor.stop_all()
        supervisor.save_registry()

        save_pipeline_status({
            "status": "stopped",
            "run_mode": _run_ctx.mode if _run_ctx else "pipeline",
            "stopped_at": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "model": model,
        })
        if polish and _run_ctx and _run_ctx.polish_path:
            from pipeline.polish_mode import queue_pending
            from pipeline.polish_status import print_polish_lifecycle
            reason = "graceful_stop" if loop_control.stop_requested else "pipeline_stopped"
            print_polish_lifecycle(
                "terminated",
                reason=reason,
                queue_path=str(_run_ctx.polish_path),
                pending_messages=queue_pending(bus),
            )

        # Finalize and save metrics report
        try:
            metrics_path = run_metrics.finish()
            metrics_report = metrics_path.parent / "report.md"
        except Exception as e:
            metrics_report = None
            print(f"  ⚠ Metrics save failed: {e}")

        signal.signal(signal.SIGINT, original_sigint)

        print("\n" + "=" * 60)
        print("  Pipeline stopped.")
        print(f"  Logs: .pipeline/logs/")
        print(f"  Output: .pipeline/workspace/")
        print(f"  Decisions: .pipeline/state/manager_decisions.md")
        try:
            from pipeline.dropbox import ensure_dropbox
            ensure_dropbox()
            print(f"  Dropbox:   dropbox.md (checked every 10 min)")
        except Exception:
            pass
        if metrics_report and metrics_report.exists():
            print(f"  Run Report: {metrics_report.relative_to(PROJECT_ROOT)}")
            print(f"  Prompt Ver: {run_metrics.prompt_version}")
        print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Multi-agent idea development pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python pipeline/runner.py "Build a CLI tool that converts CSV to JSON"
              python pipeline/runner.py --from-list
              python pipeline/runner.py --from-list --provider ollama --model qwen3.5:35b --time-limit 480
              python pipeline/runner.py --resume
              python pipeline/runner.py --from-list --legacy
        """),
    )
    parser.add_argument("idea", nargs="?", default=None,
                        help="Idea description to implement")
    parser.add_argument("--from-list", action="store_true",
                        help="Read ideas from master_ideas.md")
    parser.add_argument("--resume", action="store_true",
                        help="Resume a previously stopped pipeline")
    parser.add_argument("--provider", default="ollama",
                        choices=["openai", "claude", "gemini", "ollama", "grok"],
                        help="LLM provider (default: ollama)")
    parser.add_argument("--model", default=os.environ.get("PIPELINE_MODEL", "qwen3.5:35b"),
                        help="LLM model (default: qwen3.5:35b, or $PIPELINE_MODEL env var)")
    parser.add_argument("--time-limit", type=float, default=0,
                        help="Time limit in minutes (0 = unlimited)")
    parser.add_argument("--base-budget", type=int, default=DEFAULT_BASE_BUDGET,
                        help=f"Minimum minutes per project (default: {DEFAULT_BASE_BUDGET}). "
                             f"Lower for smaller GPUs, higher for bigger ones.")
    parser.add_argument("--phase-budget", type=int, default=DEFAULT_PHASE_BUDGET,
                        help=f"Minutes per phase (default: {DEFAULT_PHASE_BUDGET}). "
                             f"Total budget = max(base-budget, phases * phase-budget).")
    parser.add_argument("--ideas-file", default=None,
                        help="Path to a specific master ideas file (default: master_ideas.md). "
                             "Use this to run separate instances on different idea lists.")
    parser.add_argument("--fresh-list-only", action="store_true",
                        help="Skip all stray/in-progress projects. Only work from --ideas-file "
                             "(or master_ideas.md). Use for a clean second instance.")
    parser.add_argument("--polish", action="store_true",
                        help="Resume complete/budget_exceeded projects with missing phases "
                             "from polish_queue.md. Writes .pipeline/state/polish_status.json "
                             "(RUNNING vs TERMINATED). Does not read master_ideas.md.")
    parser.add_argument("--polish-queue", default=None, metavar="PATH",
                        help="Alternate polish queue file (default: polish_queue.md). "
                             "Not the same as --ideas-file (which is for master_ideas only).")
    parser.add_argument("--parallel-seeds", type=int, default=1, metavar="N",
                        help="Seed up to N independent projects simultaneously. "
                             "With --auto-tune this becomes the starting value (default: 1). "
                             "Example: --parallel-seeds 2")
    parser.add_argument("--auto-tune", action="store_true",
                        help="Enable the DynamicParallelizer: automatically detects diminishing "
                             "returns and adjusts parallel seeds to maximise throughput. "
                             "Starts at --parallel-seeds N and self-adjusts up to --max-seeds M. "
                             "Example: --auto-tune --parallel-seeds 1 --max-seeds 4")
    parser.add_argument("--max-seeds", type=int, default=4, metavar="M",
                        help="Upper ceiling for --auto-tune (default: 4). Ignored when "
                             "--auto-tune is not set.")
    parser.add_argument("--executors", type=int, default=1, metavar="N",
                        help="Number of parallel executor agent instances (default: 1). "
                             "Each executor independently processes tasks from the shared "
                             "SQLite queue — no extra config needed. "
                             "Recommended: 2 when using --parallel-seeds 3+. "
                             "Example: --parallel-seeds 3 --executors 2")
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use pre-capability-registry behavior: no SQLite registry, no "
             "capabilities_summary in context_cache or executor prompts. "
             "Same as before the capability-registry fork.",
    )

    args = parser.parse_args()

    if not args.idea and not args.from_list and not args.resume and not args.polish:
        parser.print_help()
        print("\nProvide an idea, use --from-list, --resume, or --polish.")
        sys.exit(1)

    run_pipeline(
        idea=args.idea,
        from_list=args.from_list,
        resume=args.resume,
        provider=args.provider,
        model=args.model,
        time_limit_minutes=args.time_limit,
        base_budget=args.base_budget,
        phase_budget=args.phase_budget,
        ideas_file=args.ideas_file,
        fresh_list_only=args.fresh_list_only,
        polish=args.polish,
        polish_queue_file=args.polish_queue,
        parallel_seeds=args.parallel_seeds,
        auto_tune=args.auto_tune,
        max_seeds=args.max_seeds,
        num_executors=args.executors,
        legacy=args.legacy,
    )


if __name__ == "__main__":
    main()
