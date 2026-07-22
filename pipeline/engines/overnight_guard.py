"""
Overnight Grok Build from-list guards (P0).

- Assert CLI env when PIPELINE_ENGINE=grok_build + backend cli
- Refuse parallel seeds/executors unless explicitly allowed
- Clear stale grok_driver_running flags after crash/sleep
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool


def grok_overnight_mode() -> bool:
    eng = (os.environ.get("PIPELINE_ENGINE") or "").strip().lower()
    return eng == "grok_build"


def _exit2(message: str) -> None:
    """Print *message* to stderr and raise SystemExit(2) (int code, not string)."""
    print(message, file=sys.stderr)
    raise SystemExit(2)


def assert_grok_cli_ready() -> None:
    """Exit-style check: raise SystemExit(2) if CLI backend cannot run.

    Call from runner main when PIPELINE_ENGINE=grok_build and backend=cli
    (or auto with no pipeline_llm fallback intent).
    """
    if not grok_overnight_mode():
        return
    backend = (os.environ.get("GROK_BUILD_BACKEND") or "auto").strip().lower()
    cmd = (os.environ.get("GROK_BUILD_CMD") or "").strip()
    allow_llm = env_bool("GROK_BUILD_ALLOW_PIPELINE_LLM", default=True)

    needs_cli = backend == "cli" or (backend == "auto" and cmd)
    if backend == "auto" and not cmd and allow_llm:
        # pipeline_llm fallback — not a hard CLI night
        return
    if backend == "pipeline_llm":
        return

    if not cmd:
        _exit2(
            "GROK_BUILD_CMD is not set but PIPELINE_ENGINE=grok_build requires CLI "
            "(set GROK_BUILD_CMD or GROK_BUILD_BACKEND=pipeline_llm). Exit 2."
        )

    # Optional: first token is executable path
    first = cmd.split()[0].strip('"')
    # Templates may be shell-like; only check absolute windows/unix paths
    if first.endswith((".exe",)) or ("/" in first or "\\" in first):
        if not Path(first).is_file():
            _exit2(f"GROK_BUILD_CMD executable not found: {first} (Exit 2).")


def assert_serial_for_grok(
    *,
    parallel_seeds: int | None,
    num_executors: int | None,
) -> None:
    """When grok overnight, refuse parallel >1 unless GROK_BUILD_ALLOW_PARALLEL=1."""
    if not grok_overnight_mode():
        return
    if env_bool("GROK_BUILD_ALLOW_PARALLEL", default=False):
        return
    seeds = int(parallel_seeds or 1)
    execs = int(num_executors or 1)
    if seeds > 1 or execs > 1:
        _exit2(
            "PIPELINE_ENGINE=grok_build is serial in v1: use --parallel-seeds 1 "
            "--executors 1 (or set GROK_BUILD_ALLOW_PARALLEL=1 to override). Exit 2."
        )


def _stale_seconds() -> float:
    raw = (os.environ.get("GROK_BUILD_STALE_S") or "3600").strip()
    try:
        return max(60.0, float(raw))
    except ValueError:
        return 3600.0


def clear_stale_grok_driver_flags(
    project_dir: Path,
    state: dict[str, Any],
    *,
    now: float | None = None,
) -> dict[str, Any]:
    """Clear stuck grok_driver_running after crash/sleep so hook can re-enter.

    Cases:
    - grok_driver_running but status is not *_grok_running → always clear
    - status is *_grok_running but state file older than GROK_BUILD_STALE_S → clear
      (process is gone; in-process lock would be free in a new runner)
    """
    if not state.get("grok_driver_running"):
        return state

    status = (state.get("status") or "").strip()
    ts = now if now is not None else time.time()
    sf = project_dir / "state" / "current_idea.json"

    if "grok_running" not in status:
        state = dict(state)
        state.pop("grok_driver_running", None)
        _persist_state(sf, state)
        return state

    # Heartbeat: prefer explicit timestamp, else state file mtime
    started = state.get("grok_driver_started_at") or state.get("checkpoint_at")
    age = None
    if isinstance(started, (int, float)):
        age = ts - float(started)
    elif isinstance(started, str) and started:
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            age = ts - dt.timestamp()
        except Exception:
            age = None
    if age is None and sf.is_file():
        try:
            age = ts - sf.stat().st_mtime
        except OSError:
            age = None

    if age is not None and age > _stale_seconds():
        state = dict(state)
        state.pop("grok_driver_running", None)
        # Re-open as executing so driver can resume
        import re

        m = re.match(r"phase_(\d+)_grok_running$", status)
        if m:
            state["status"] = f"phase_{m.group(1)}_executing"
        _persist_state(sf, state)
    return state


def _persist_state(sf: Path, state: dict[str, Any]) -> None:
    if not sf.is_file():
        return
    try:
        sf.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def preflight_disk_and_paths(pipeline_dir: Path | None = None) -> list[str]:
    """Return list of warning strings (empty if ok)."""
    warnings: list[str] = []
    from pipeline.paths import projects_dir

    root = pipeline_dir or projects_dir().parent
    proj = root / "projects" if (root / "projects").is_dir() else projects_dir()
    if not proj.is_dir():
        warnings.append(f"projects dir missing: {proj}")
    try:
        import shutil

        usage = shutil.disk_usage(str(proj if proj.is_dir() else root))
        free_gb = usage.free / (1024**3)
        if free_gb < 2.0:
            warnings.append(f"low disk free: {free_gb:.1f} GiB")
    except Exception:
        pass
    return warnings
