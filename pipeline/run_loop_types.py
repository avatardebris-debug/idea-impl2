"""
pipeline/run_loop_types.py
Shared types for the main pipeline monitoring loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    last_dropbox_check: float = 0.0
    last_orphan_requeue: float = 0.0
    status_count: int = 0
    last_tps_print: float = 0.0
    last_stall_recovery: float = 0.0
    zero_progress_since: dict[str, float] = field(default_factory=dict)
    zero_task_warned: set[str] = field(default_factory=set)
    parallel_seeds: int = 1
    last_tok_snapshot: int = 0
    last_tasks_snapshot: dict[str, int] = field(default_factory=dict)


@dataclass
class MainLoopConfig:
    pipeline_dir: Path
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
    stall_recovery_cooldown_s: float = 900.0
    zero_task_phase_kill_s: float = 15 * 60
    zero_task_warn_s: float = 10 * 60
    tuner: Any = None
    tuner_log_path: Path | None = None
    count_active_projects: Callable[[], int] | None = None
    warm_upcoming_projects: Callable[..., None] | None = None
