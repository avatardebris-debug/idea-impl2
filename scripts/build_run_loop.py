"""One-off script to generate pipeline/run_loop.py from runner.py loop body."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
lines = (ROOT / "pipeline/runner.py").read_text(encoding="utf-8").splitlines()
chunk = lines[2586:3239]
body_lines = [ln[4:] if ln.startswith("        ") else ln for ln in chunk]
body = "\n".join(body_lines)

body = re.sub(r"\bbus\.", "cfg.bus.", body)
body = re.sub(r"\bsupervisor\.", "cfg.supervisor.", body)

for sym in [
    "AGENT_ROLES",
    "PIPELINE_DIR",
    "PROJECT_ROOT",
    "MAX_PROJECT_LIFETIME_RETRIES",
    "_SEED_SEEDED",
    "_SEED_EMPTY",
]:
    body = re.sub(rf"\b{sym}\b", f"r.{sym}", body)

for fn in [
    "_check_priority_eviction",
    "_get_active_idea_state",
    "_get_all_active_idea_states",
    "_tick_project",
    "_rebuild_queues_from_state",
    "seed_from_master_list",
    "_apply_seed_empty",
    "_check_ollama_heartbeat",
    "_clean",
]:
    body = re.sub(rf"\b{fn}\(", f"r.{fn}(", body)

replacements = {
    "while not stop_requested:": "while not cfg.control.stop_requested:",
    "stop_requested = True": "cfg.control.stop_requested = True",
    "_ideas_path": "cfg.ideas_path",
    "parallel_seeds": "cfg.state.parallel_seeds",
    "ideation_in_progress": "cfg.state.ideation_in_progress",
    "ideation_requested_at": "cfg.state.ideation_requested_at",
    "last_health_check": "cfg.state.last_health_check",
    "last_orphan_requeue": "cfg.state.last_orphan_requeue",
    "_status_count": "cfg.state.status_count",
    "_last_tps_print": "cfg.state.last_tps_print",
    "_zero_progress_since": "cfg.state.zero_progress_since",
    "_zero_task_warned": "cfg.state.zero_task_warned",
    "time_limit_minutes": "cfg.time_limit_minutes",
    "start_time": "cfg.start_time",
    "health_check_interval": "cfg.health_check_interval",
    "base_budget": "cfg.base_budget",
    "phase_budget": "cfg.phase_budget",
    "from_list": "cfg.from_list",
    "fresh_list_only": "cfg.fresh_list_only",
    "run_metrics": "cfg.run_metrics",
    "IDEATION_TIMEOUT": "cfg.ideation_timeout_s",
    "ORPHAN_REQUEUE_COOLDOWN": "cfg.orphan_requeue_cooldown_s",
    "ZERO_TASK_PHASE_KILL": "cfg.zero_task_phase_kill_s",
    "ZERO_TASK_WARN": "cfg.zero_task_warn_s",
}
for old, new in sorted(replacements.items(), key=lambda x: -len(x[0])):
    body = body.replace(old, new)

body = re.sub(r"\bpolish\b", "cfg.polish", body)
body = re.sub(r"\b_run_ctx\b", "cfg.run_ctx", body)
body = body.replace("cfg.run_ctx.cfg.run_ctx", "cfg.run_ctx")

body = body.replace("_count_active_projects()", "cfg.count_active_projects()")
body = body.replace("target=_warm_upcoming_projects", "target=cfg.warm_upcoming_projects")
body = body.replace("_warm_upcoming_projects", "cfg.warm_upcoming_projects")

body = re.sub(r"\bprovider\b", "cfg.provider", body)
body = re.sub(r"\bmodel\b", "cfg.model", body)
body = body.replace("cfg.cfg.", "cfg.")

body = body.replace("getattr(run_pipeline,", "getattr(r.run_pipeline,")
body = body.replace("run_pipeline._last", "r.run_pipeline._last")
body = body.replace("hasattr(run_pipeline,", "hasattr(r.run_pipeline,")

body = body.replace(
    "r._check_priority_eviction(bus,",
    "r._check_priority_eviction(cfg.bus,",
)
body = body.replace("queue_pending(bus)", "queue_pending(cfg.bus)")
body = body.replace("seed_from_master_list(bus,", "seed_from_master_list(cfg.bus,")
body = body.replace("_apply_seed_empty(\n", "_apply_seed_empty(\n")
body = body.replace("_rebuild_queues_from_state(bus)", "_rebuild_queues_from_state(cfg.bus)")
body = body.replace("_rebuild_queues_from_state(cfg.bus, ideas_path=", "_rebuild_queues_from_state(cfg.bus, ideas_path=")

header = '''"""
pipeline/run_loop.py
Main pipeline monitoring loop (extracted from runner.py).
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pipeline.run_context import RunContext


@dataclass
class LoopControl:
    stop_requested: bool = False


@dataclass
class MainLoopState:
    ideation_in_progress: bool = False
    ideation_requested_at: float = 0.0
    last_health_check: float = 0.0
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
    ideation_timeout_s: float = 35 * 60
    orphan_requeue_cooldown_s: float = 660.0
    zero_task_phase_kill_s: float = 15 * 60
    zero_task_warn_s: float = 10 * 60
    tuner: Any = None
    tuner_log_path: Path | None = None
    count_active_projects: Callable[[], int] = field(default=lambda: (lambda: 0))
    warm_upcoming_projects: Callable[..., None] = field(default=lambda: (lambda *a, **k: None))


def run_main_loop(cfg: MainLoopConfig) -> None:
    import pipeline.runner as r

'''

out = header + body + "\n"
(ROOT / "pipeline/run_loop.py").write_text(out, encoding="utf-8")
print("Wrote", ROOT / "pipeline/run_loop.py", len(out.splitlines()), "lines")
print("stop_requested left:", "stop_requested" in body)
