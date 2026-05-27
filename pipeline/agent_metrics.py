"""
pipeline/agent_metrics.py
Lightweight per-agent timing metrics.

Records each agent handle() call's timing to a JSONL file.
The runner reads this to print per-agent breakdowns in the throughput summary.
"""
from __future__ import annotations

import json
import pathlib
import time
import threading
from typing import Any

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
from pipeline.paths import state_dir


def _metrics_path() -> pathlib.Path:
    return state_dir() / "agent_timing.jsonl"
_METRICS_LOCK = threading.Lock()


def record(
    role: str,
    slug: str,
    queue_wait_s: float,
    handle_s: float,
    tokens: int,
    files_written: int = 0,
) -> None:
    """Append one timing record. Non-blocking — errors are silently swallowed."""
    try:
        entry = {
            "ts": time.time(),
            "role": role,
            "slug": slug,
            "queue_wait_s": round(queue_wait_s, 2),
            "handle_s": round(handle_s, 2),
            "tokens": tokens,
            "files_written": files_written,
        }
        _metrics_path().parent.mkdir(parents=True, exist_ok=True)
        with _METRICS_LOCK:
            with open(_metrics_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Never crash the pipeline over metrics


def summarize(window_minutes: float = 15.0) -> dict[str, dict[str, Any]]:
    """
    Return per-role averages for the last `window_minutes` minutes.

    Returns dict: {role: {calls, avg_wait_s, avg_handle_s, total_tokens, files_written}}
    """
    cutoff = time.time() - (window_minutes * 60)
    if not _metrics_path().exists():
        return {}

    by_role: dict[str, list[dict]] = {}
    try:
        with _METRICS_LOCK:
            lines = _metrics_path().read_text(encoding="utf-8").splitlines()
        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("ts", 0) < cutoff:
                    continue
                role = entry.get("role", "unknown")
                by_role.setdefault(role, []).append(entry)
            except Exception:
                continue
    except Exception:
        return {}

    result: dict[str, dict[str, Any]] = {}
    for role, entries in by_role.items():
        n = len(entries)
        result[role] = {
            "calls": n,
            "avg_wait_s": round(sum(e.get("queue_wait_s", 0) for e in entries) / n, 2),
            "avg_handle_s": round(sum(e.get("handle_s", 0) for e in entries) / n, 2),
            "total_tokens": sum(e.get("tokens", 0) for e in entries),
            "files_written": sum(e.get("files_written", 0) for e in entries),
        }
    return result


def trim_old_records(keep_hours: float = 6.0) -> None:
    """Trim records older than keep_hours from the metrics file. Call periodically."""
    cutoff = time.time() - (keep_hours * 3600)
    if not _metrics_path().exists():
        return
    try:
        with _METRICS_LOCK:
            lines = _metrics_path().read_text(encoding="utf-8").splitlines()
            kept = []
            for line in lines:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("ts", 0) >= cutoff:
                        kept.append(line)
                except Exception:
                    pass
            _metrics_path().write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    except Exception:
        pass
