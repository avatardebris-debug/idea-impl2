"""
Integration hook: run Grok Build driver for projects with engine=grok_build.

Called from the main health cycle (run_loop). When status is phase_N_executing
(or phase_N_grok_running left mid-flight) and engine is grok_build, runs the
skill chain instead of waiting on classic executor messages.

Classic projects are untouched.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from pipeline.engines.selection import ENGINE_GROK_BUILD, get_project_engine
from pipeline.paths import projects_dir

# Avoid thrashing the same slug every 2s health tick
_last_attempt: dict[str, float] = {}
_MIN_RETRY_S = 30.0


def _parse_executing_phase(status: str) -> int | None:
    m = re.match(r"phase_(\d+)_(?:executing|grok_running)$", status or "")
    if not m:
        return None
    return int(m.group(1))


def _should_attempt(slug: str) -> bool:
    now = time.time()
    last = _last_attempt.get(slug, 0.0)
    if now - last < _MIN_RETRY_S:
        return False
    _last_attempt[slug] = now
    return True


def find_grok_build_candidates(
    root: Path | None = None,
) -> list[tuple[Path, dict, int, str]]:
    """Return (project_dir, state, phase, slug) for grok_build projects ready to run."""
    base = root if root is not None else projects_dir()
    if not base.is_dir():
        return []
    out: list[tuple[Path, dict, int, str]] = []
    for proj in sorted(base.iterdir()):
        if not proj.is_dir():
            continue
        sf = proj / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            state = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if get_project_engine(state) != ENGINE_GROK_BUILD:
            continue
        if state.get("grok_driver_running"):
            # Another tick already owns it (or crashed mid-flight)
            # Allow re-entry only if status is still grok_running and lock free
            status = state.get("status") or ""
            if "grok_running" not in status:
                continue
        phase = _parse_executing_phase(state.get("status") or "")
        if phase is None:
            continue
        # Need tasks.md before driving
        tasks = proj / "phases" / f"phase_{phase}" / "tasks.md"
        if not tasks.is_file():
            continue
        slug = state.get("slug") or proj.name
        out.append((proj, state, phase, slug))
    return out


def tick_grok_build_engines(bus: Any, *, pipeline_dir: Path | None = None) -> int:
    """Run at most one grok_build driver per tick (serial v1). Returns count started."""
    root = None
    if pipeline_dir is not None:
        root = Path(pipeline_dir) / "projects"
    candidates = find_grok_build_candidates(root)
    if not candidates:
        return 0

    from pipeline.engines.driver import run_grok_phase

    started = 0
    for project_dir, state, phase, slug in candidates:
        if not _should_attempt(slug):
            continue
        try:
            from pipeline.pipeline_activity import log_activity

            log_activity(
                "grok_driver_tick",
                engine=ENGINE_GROK_BUILD,
                slug=slug,
                phase=phase,
            )
        except Exception:
            pass
        try:
            outcome = run_grok_phase(bus, project_dir, state, phase, slug)
            started += 1
            # Always one project per health tick (fairness + serial v1)
            _ = outcome  # outcome inspected by callers/logs; break regardless
            break
        except Exception as exc:
            print(f"  [grok_build] driver error for {slug}: {exc}")
            try:
                from pipeline.engines.driver import fallback_to_classic

                fallback_to_classic(
                    bus, project_dir, state, phase, slug,
                    reason=f"driver exception: {exc}",
                )
            except Exception:
                pass
            started += 1
            break
    return started
