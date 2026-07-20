"""
Lightweight LLM call / queue-wait metrics (instrumentation only — not vLLM).

Records per-call:
  wait_ms, duration_ms, provider, model, agent role

Storage: PIPELINE_DIR/metrics/llm_calls.jsonl
Activity: event llm_call with duration_ms

CLI:
  python -m pipeline.llm_metrics
  python -m pipeline.llm_metrics --last 50
"""

from __future__ import annotations

import json
import os
import pathlib
import statistics
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any

from pipeline.paths import metrics_dir

_LOCK = threading.Lock()
_MAX_FILE_LINES = 5000


def _calls_path() -> pathlib.Path:
    return metrics_dir() / "llm_calls.jsonl"


def _file_lock_path(path: pathlib.Path) -> pathlib.Path:
    return path.with_suffix(path.suffix + ".lock")


def _acquire_file_lock(path: pathlib.Path, *, blocking: bool = True):
    """
    Cross-process exclusive lock for metrics append+trim.
    Returns open handle or None if non-blocking and busy / error.
    """
    lock_path = _file_lock_path(path)
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(lock_path, "a+", encoding="utf-8")
    except OSError:
        return None
    try:
        if sys.platform == "win32":
            import msvcrt

            handle.seek(0)
            # Windows msvcrt has no true blocking timeout — busy-wait briefly
            deadline = time.time() + (5.0 if blocking else 0.0)
            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    return handle
                except OSError:
                    if not blocking or time.time() >= deadline:
                        handle.close()
                        return None
                    time.sleep(0.01)
        else:
            import fcntl

            flags = fcntl.LOCK_EX if blocking else (fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                fcntl.flock(handle.fileno(), flags)
            except OSError:
                handle.close()
                return None
            return handle
    except Exception:
        try:
            handle.close()
        except Exception:
            pass
        return None


def _release_file_lock(handle) -> None:
    if handle is None:
        return
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
    try:
        handle.close()
    except Exception:
        pass


def record_llm_call(
    *,
    duration_ms: float,
    wait_ms: float = 0.0,
    provider: str = "",
    model: str = "",
    role: str = "",
    slug: str = "",
    kind: str = "chat",
    ok: bool = True,
    extra: dict[str, Any] | None = None,
) -> None:
    """Append one LLM call record. Never raises."""
    try:
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "ts_unix": time.time(),
            "duration_ms": round(float(duration_ms), 1),
            "wait_ms": round(float(wait_ms), 1),
            "provider": provider or "",
            "model": model or "",
            "role": role or "",
            "slug": slug or "",
            "kind": kind,
            "ok": bool(ok),
        }
        if extra:
            entry.update(extra)
        path = _calls_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        # In-process + cross-process lock for append and optional trim together
        with _LOCK:
            fh = _acquire_file_lock(path, blocking=True)
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(line)
                _trim_unlocked(path)
            finally:
                _release_file_lock(fh)

        try:
            from pipeline.pipeline_activity import log_activity

            log_activity(
                "llm_call",
                duration_ms=entry["duration_ms"],
                wait_ms=entry["wait_ms"],
                provider=provider,
                model=model,
                role=role,
                slug=slug,
                kind=kind,
                ok=ok,
            )
        except Exception:
            pass
    except Exception:
        pass


def _trim_unlocked(path: pathlib.Path) -> None:
    """Trim metrics file; caller must hold cross-process lock."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) <= _MAX_FILE_LINES:
            return
        kept = lines[-(_MAX_FILE_LINES // 2) :]
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text("\n".join(kept) + "\n", encoding="utf-8")
        os.replace(str(tmp), str(path))
    except Exception:
        pass


def load_calls(last_n: int = 200) -> list[dict[str, Any]]:
    path = _calls_path()
    if not path.is_file():
        return []
    try:
        with _LOCK:
            lines = path.read_text(encoding="utf-8").splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-max(1, last_n) :]:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
    except Exception:
        return []


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def summarize(last_n: int = 200) -> dict[str, Any]:
    calls = load_calls(last_n=last_n)
    if not calls:
        return {
            "count": 0,
            "duration_ms": {},
            "wait_ms": {},
            "by_role": {},
            "by_provider": {},
        }

    durations = sorted(float(c.get("duration_ms") or 0) for c in calls)
    waits = sorted(float(c.get("wait_ms") or 0) for c in calls)

    def stats(vals: list[float]) -> dict[str, float]:
        if not vals:
            return {"p50": 0.0, "p95": 0.0, "mean": 0.0, "max": 0.0}
        return {
            "p50": round(_percentile(vals, 50), 1),
            "p95": round(_percentile(vals, 95), 1),
            "mean": round(statistics.fmean(vals), 1),
            "max": round(max(vals), 1),
        }

    by_role: dict[str, list[float]] = {}
    by_provider: dict[str, list[float]] = {}
    for c in calls:
        role = c.get("role") or "unknown"
        prov = c.get("provider") or "unknown"
        by_role.setdefault(role, []).append(float(c.get("duration_ms") or 0))
        by_provider.setdefault(prov, []).append(float(c.get("duration_ms") or 0))

    return {
        "count": len(calls),
        "duration_ms": stats(durations),
        "wait_ms": stats(waits),
        "by_role": {
            r: {"count": len(v), **stats(sorted(v))} for r, v in sorted(by_role.items())
        },
        "by_provider": {
            p: {"count": len(v), **stats(sorted(v))} for p, v in sorted(by_provider.items())
        },
        "path": str(_calls_path()),
    }


def print_summary(last_n: int = 200) -> None:
    s = summarize(last_n=last_n)
    print(f"LLM metrics (last {last_n} calls) — count={s['count']}")
    if s["count"] == 0:
        print("  (no records yet — path will be under PIPELINE_DIR/metrics/llm_calls.jsonl)")
        return
    d = s["duration_ms"]
    w = s["wait_ms"]
    print(
        f"  duration_ms: p50={d['p50']}  p95={d['p95']}  mean={d['mean']}  max={d['max']}"
    )
    print(
        f"  wait_ms:     p50={w['p50']}  p95={w['p95']}  mean={w['mean']}  max={w['max']}"
    )
    print("  by role:")
    for role, rs in (s.get("by_role") or {}).items():
        print(
            f"    {role:16} n={rs['count']:4}  p50={rs['p50']}  p95={rs['p95']}"
        )
    print("  by provider:")
    for prov, ps in (s.get("by_provider") or {}).items():
        print(
            f"    {prov:16} n={ps['count']:4}  p50={ps['p50']}  p95={ps['p95']}"
        )
    print(f"  file: {s.get('path')}")
    print(
        "\nIf wait_ms p95 is high relative to duration, consider more GPU/vLLM later."
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Summarize pipeline LLM call metrics")
    parser.add_argument("--last", type=int, default=200, help="Last N calls (default 200)")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = parser.parse_args(argv)
    if args.json:
        print(json.dumps(summarize(last_n=args.last), indent=2))
    else:
        print_summary(last_n=args.last)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
