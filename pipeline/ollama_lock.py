"""Cross-process lock so only one Ollama HTTP request runs at a time."""

from __future__ import annotations

import contextlib
import logging
import sys
import time

from pipeline.paths import state_dir

logger = logging.getLogger(__name__)

# Last lock wait (ms) observed in this process — read by llm metrics
_last_wait_ms: float = 0.0


def last_lock_wait_ms() -> float:
    return _last_wait_ms


@contextlib.contextmanager
def ollama_singleflight():
    """Serialize Ollama /api/chat and /api/generate across all agent subprocesses.

    Yields wait_ms (float): time spent acquiring the lock.
    """
    global _last_wait_ms
    lock_path = state_dir() / "ollama.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+", encoding="utf-8")
    t0 = time.time()
    wait_ms = 0.0
    try:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        wait_ms = (time.time() - t0) * 1000.0
        _last_wait_ms = wait_ms
        yield wait_ms
    finally:
        try:
            if sys.platform == "win32":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        handle.close()
