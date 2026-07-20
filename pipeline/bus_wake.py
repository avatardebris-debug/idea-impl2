"""
Optional short-poll / wake-file for the message bus.

After MessageBus.send, touch state/bus_wake. Agents with PIPELINE_BUS_WAKE=1
wait on mtime changes with a short timeout instead of only fixed long sleeps.

Default: enabled when PIPELINE_CLOUD=1 (see cloud_defaults.cloud_bus_wake_default).
Backward compatible when flag is off.
"""

from __future__ import annotations

import os
import pathlib
import time
from typing import Callable

from pipeline.cloud_defaults import cloud_bus_wake_default
from pipeline.env_flags import env_float
from pipeline.paths import state_dir


def bus_wake_enabled() -> bool:
    return cloud_bus_wake_default()


def wake_path() -> pathlib.Path:
    return state_dir() / "bus_wake"


def touch_bus_wake() -> None:
    """Touch the wake file (best-effort; never raises).

    Writes a monotonic counter + timestamp so waiters can detect wakes even when
    filesystem mtime resolution is coarse (same-second multi-send).
    """
    if not bus_wake_enabled():
        return
    try:
        path = wake_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        prev = 0
        if path.is_file():
            try:
                raw = path.read_text(encoding="utf-8", errors="replace").strip().split()
                if raw:
                    prev = int(float(raw[0]))
            except (ValueError, OSError):
                prev = 0
        # token is integer counter (first field); second field is wall time
        path.write_text(f"{prev + 1} {time.time():.6f}\n", encoding="utf-8")
    except Exception:
        pass


def wake_poll_timeout_s() -> float:
    """Short wait between wake checks (default 0.5s)."""
    return max(0.05, env_float("PIPELINE_BUS_WAKE_TIMEOUT", default=0.5))


def wait_for_bus_wake(
    *,
    last_mtime: float | None = None,
    last_token: int | None = None,
    timeout_s: float | None = None,
    stop_check: Callable[[], bool] | None = None,
) -> float:
    """
    Sleep until bus_wake content/mtime changes or timeout.

    Returns the latest mtime observed (or previous last_mtime).
    When wake is disabled, sleeps timeout_s (or 0.5) once and returns last_mtime.

    *last_token* is optional; when provided, content counter changes wake immediately
    even if mtime is unchanged (coarse FS).
    """
    timeout = wake_poll_timeout_s() if timeout_s is None else max(0.05, float(timeout_s))
    if not bus_wake_enabled():
        time.sleep(timeout)
        return last_mtime if last_mtime is not None else 0.0

    path = wake_path()
    deadline = time.time() + timeout
    base_mt = last_mtime if last_mtime is not None else _mtime(path)
    base_tok = last_token if last_token is not None else _token(path)

    # Small steps so stop_check is responsive
    step = min(0.2, timeout)
    while time.time() < deadline:
        if stop_check and stop_check():
            break
        mt = _mtime(path)
        tok = _token(path)
        if mt > base_mt or tok > base_tok:
            return mt
        time.sleep(step)
    return _mtime(path) if path.exists() else base_mt


def _mtime(path: pathlib.Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _token(path: pathlib.Path) -> int:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace").strip().split()
        if not raw:
            return 0
        return int(float(raw[0]))
    except (OSError, ValueError):
        return 0


def read_wake_token() -> int:
    """Current wake counter (0 if missing)."""
    return _token(wake_path())
