"""
Lightweight per-project lock file so parallel executors do not work the
same slug simultaneously.

The SQLite message bus serializes *message* claim only (BEGIN IMMEDIATE).
Two executors can still hold different pending tasks for the same project.
This module adds an optional file lock under projects/<slug>/state/project.lock.

Enable with PIPELINE_PROJECT_LOCK=1 (default on when PIPELINE_CLOUD=1).

Lock file format (text):
  line1: holder (e.g. "executor:12345" or "12345")
  line2: unix timestamp
  line3: pid (integer)

Stale recovery:
  - If holder PID is dead → reclaim immediately
  - Else if mtime older than PIPELINE_PROJECT_LOCK_STALE_S (default 1800s) → reclaim
  - Live PID is never treated as stale solely by age

Same-PID re-entry: **rejected** (strict single unit of work). After a phase
timeout with a still-running handle thread, call register_zombie_lock() so a
background reaper releases when the thread finishes — do not leave locks held
forever on long-lived agent processes.
"""

from __future__ import annotations

import logging
import os
import pathlib
import threading
import time
from contextlib import contextmanager
from typing import Iterator

from pipeline.env_flags import env_bool, env_float
from pipeline.output_bootstrap import is_cloud_environment
from pipeline.paths import project_dir, projects_dir

logger = logging.getLogger(__name__)

DEFAULT_STALE_S = 1800.0  # 30 min mtime fallback when PID unknown/alive-check fails

# Process-local zombie tracking: slug -> (handle_thread, reaper_thread, holder)
_zombie_guard = threading.Lock()
_zombie_slugs: dict[str, tuple[threading.Thread, threading.Thread, str]] = {}


def project_lock_enabled() -> bool:
    raw = os.environ.get("PIPELINE_PROJECT_LOCK")
    if raw is not None and str(raw).strip() != "":
        return env_bool("PIPELINE_PROJECT_LOCK", default=False)
    return is_cloud_environment()


def lock_stale_s() -> float:
    return max(60.0, env_float("PIPELINE_PROJECT_LOCK_STALE_S", default=DEFAULT_STALE_S))


def lock_path_for(slug: str) -> pathlib.Path:
    return project_dir(slug) / "state" / "project.lock"


def _pid_alive(pid: int) -> bool:
    """True if process appears to be running. Unknown → True (conservative)."""
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(  # type: ignore[attr-defined]
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                # Access denied often means process exists
                err = ctypes.GetLastError()  # type: ignore[attr-defined]
                if err in (5,):  # ERROR_ACCESS_DENIED
                    return True
                return False
            try:
                exit_code = ctypes.c_ulong()
                ok = ctypes.windll.kernel32.GetExitCodeProcess(  # type: ignore[attr-defined]
                    handle, ctypes.byref(exit_code)
                )
                if not ok:
                    return True
                return int(exit_code.value) == STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
        else:
            os.kill(pid, 0)
            return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    except Exception:
        return True


def _parse_lock(path: pathlib.Path) -> tuple[str, float, int | None]:
    """Return (holder, ts, pid_or_None)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ("", 0.0, None)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    holder = lines[0] if lines else ""
    ts = 0.0
    if len(lines) >= 2:
        try:
            ts = float(lines[1])
        except ValueError:
            ts = 0.0
    pid: int | None = None
    if len(lines) >= 3:
        try:
            pid = int(lines[2])
        except ValueError:
            pid = None
    if pid is None and holder:
        # holder forms: "executor:12345" or "12345"
        tail = holder.rsplit(":", 1)[-1]
        try:
            pid = int(tail)
        except ValueError:
            pid = None
    return holder, ts, pid


def _unlink_quiet(path: pathlib.Path) -> None:
    try:
        path.unlink(missing_ok=True)  # type: ignore[call-arg]
    except TypeError:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    except OSError:
        pass


def is_lock_stale(path: pathlib.Path, *, stale_s: float | None = None) -> bool:
    """True if lock may be safely reclaimed (dead PID or aged without live holder)."""
    if not path.is_file():
        return True
    limit = lock_stale_s() if stale_s is None else max(1.0, float(stale_s))
    holder, ts, pid = _parse_lock(path)
    if pid is not None:
        if not _pid_alive(pid):
            return True
        # Live holder — never reclaim by age alone
        return False
    # No PID: fall back to mtime / recorded ts
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return True
    age = time.time() - max(mtime, ts)
    return age > limit


def slug_has_zombie_lock(slug: str) -> bool:
    """True if this process is holding a zombie lock (timed-out handle still running)."""
    if not slug:
        return False
    with _zombie_guard:
        return slug in _zombie_slugs


def register_zombie_lock(
    slug: str,
    handle_thread: threading.Thread,
    *,
    holder: str = "",
    hard_timeout_s: float | None = None,
) -> None:
    """
    Keep the project lock file until *handle_thread* finishes, then release.

    Call after a phase timeout when the handle thread is still alive and the
    caller has set _release_lock=False. Starts a daemon reaper thread.

    *hard_timeout_s*: optional max wait before force-releasing anyway
    (default: PIPELINE_ZOMBIE_LOCK_HARD_S or 3600).
    """
    if not slug or not project_lock_enabled():
        return
    hold = holder or f"zombie:{os.getpid()}"
    if hard_timeout_s is None:
        try:
            hard_timeout_s = float(os.environ.get("PIPELINE_ZOMBIE_LOCK_HARD_S", "3600") or 3600)
        except ValueError:
            hard_timeout_s = 3600.0
    hard_timeout_s = max(30.0, float(hard_timeout_s))

    def _reaper() -> None:
        try:
            handle_thread.join(timeout=hard_timeout_s)
            if handle_thread.is_alive():
                logger.warning(
                    "[project_lock] zombie hard-timeout (%.0fs) for slug=%s — force release",
                    hard_timeout_s,
                    slug,
                )
            else:
                logger.info(
                    "[project_lock] zombie handle finished for slug=%s — releasing lock",
                    slug,
                )
        except Exception as exc:
            logger.debug("[project_lock] zombie join error for %s: %s", slug, exc)
        finally:
            try:
                release_project_lock(slug, holder=hold)
            except Exception:
                # Force unlink if holder check fails
                try:
                    _unlink_quiet(lock_path_for(slug))
                except Exception:
                    pass
            with _zombie_guard:
                _zombie_slugs.pop(slug, None)

    with _zombie_guard:
        if slug in _zombie_slugs:
            # Already tracking — do not stack reapers
            return
        reaper = threading.Thread(
            target=_reaper,
            daemon=True,
            name=f"lock-reaper-{slug[:24]}",
        )
        _zombie_slugs[slug] = (handle_thread, reaper, hold)
        reaper.start()


def try_acquire_project_lock(
    slug: str,
    *,
    holder: str = "",
    timeout_s: float = 0.0,
    stale_s: float | None = None,
) -> bool:
    """
    Try to create projects/<slug>/state/project.lock.

    Returns True if acquired. timeout_s=0 → single attempt.
    Dead-PID locks reclaimed immediately; mtime stale as fallback.

    Same-PID re-entry is **not** allowed: a live lock (including our own
    zombie hold) returns False so only one unit of work mutates the slug.
    """
    if not slug or not project_lock_enabled():
        return True  # lock disabled → always "acquired"

    # Local zombie still running for this slug — refuse new work
    if slug_has_zombie_lock(slug):
        return False

    path = lock_path_for(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + max(0.0, float(timeout_s))
    pid = os.getpid()
    hold = holder or str(pid)
    content = f"{hold}\n{time.time()}\n{pid}\n"
    limit = lock_stale_s() if stale_s is None else max(1.0, float(stale_s))

    while True:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, content.encode("utf-8"))
            finally:
                os.close(fd)
            return True
        except FileExistsError:
            # Strict: no same-PID re-entry. Only reclaim if truly stale.
            if is_lock_stale(path, stale_s=limit):
                _unlink_quiet(path)
                continue
            if time.time() >= deadline:
                return False
            time.sleep(0.05)


def release_project_lock(slug: str, *, holder: str = "") -> None:
    if not slug or not project_lock_enabled():
        return
    path = lock_path_for(slug)
    try:
        if not path.is_file():
            return
        if holder:
            try:
                cur_holder, _, cur_pid = _parse_lock(path)
                # Allow release if holder matches, or same PID (our process)
                same_holder = cur_holder == holder or cur_holder == str(os.getpid())
                same_pid = cur_pid is None or cur_pid == os.getpid()
                holder_pid_suffix = holder.endswith(f":{os.getpid()}")
                if not same_holder and not (holder_pid_suffix and same_pid):
                    if cur_pid is not None and cur_pid != os.getpid():
                        return
                    if cur_holder and cur_holder != holder:
                        # Still allow release if we own the PID (zombie reaper)
                        if cur_pid != os.getpid():
                            return
            except OSError:
                pass
        _unlink_quiet(path)
    except OSError:
        pass


def sweep_dead_project_locks() -> int:
    """Unlink locks whose holder PID is dead. Returns count removed."""
    if not project_lock_enabled():
        return 0
    root = projects_dir()
    if not root.is_dir():
        return 0
    removed = 0
    try:
        for child in root.iterdir():
            if not child.is_dir():
                continue
            lock = child / "state" / "project.lock"
            if not lock.is_file():
                continue
            if is_lock_stale(lock):
                _unlink_quiet(lock)
                removed += 1
    except OSError:
        pass
    return removed


@contextmanager
def project_lock(
    slug: str,
    *,
    holder: str = "",
    timeout_s: float = 30.0,
) -> Iterator[bool]:
    """Context manager; yields True if lock held (or disabled)."""
    ok = try_acquire_project_lock(slug, holder=holder, timeout_s=timeout_s)
    try:
        yield ok
    finally:
        if ok:
            release_project_lock(slug, holder=holder)
