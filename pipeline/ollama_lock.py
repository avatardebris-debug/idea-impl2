"""Cross-process lock so only one Ollama HTTP request runs at a time."""

from __future__ import annotations

import contextlib
import logging
import sys

from pipeline.paths import state_dir

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def ollama_singleflight():
    """Serialize Ollama /api/chat and /api/generate across all agent subprocesses."""
    lock_path = state_dir() / "ollama.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
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
