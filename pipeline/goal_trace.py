"""
goal_trace.v1 — structured goal reasoning traces for FT / always-on later.

Store: {PIPELINE_DIR}/goal_traces/{goal_id}.json and append-only jsonl.

KEEP_GOAL_TRACES (env):
  Default **true** when unset (1/true/yes/on or missing).
  Set to 0/false/no/off to skip writing new goal traces and history appends.
  In-memory trace dicts still update so callers can use goal_id/status.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool
from pipeline.paths import get_pipeline_dir


SCHEMA = "goal_trace.v1"


def keep_goal_traces() -> bool:
    """Honor KEEP_GOAL_TRACES; default on when unset."""
    return env_bool("KEEP_GOAL_TRACES", default=True)


def goal_traces_dir(*, ensure: bool | None = None) -> Path:
    """Return goal_traces directory. Mkdir only when writing (KEEP_GOAL_TRACES on).

    *ensure*: if True, always mkdir; if False, never mkdir; if None (default),
    mkdir only when keep_goal_traces() is True.
    """
    d = get_pipeline_dir() / "goal_traces"
    do_mkdir = keep_goal_traces() if ensure is None else ensure
    if do_mkdir:
        d.mkdir(parents=True, exist_ok=True)
    return d


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_trace(
    goal_text: str,
    *,
    goal_id: str | None = None,
    mode: str = "sandbox",
    budget: dict[str, Any] | None = None,
    plan: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    gid = goal_id or f"g_{uuid.uuid4().hex[:12]}"
    trace: dict[str, Any] = {
        "schema": SCHEMA,
        "goal_id": gid,
        "goal_text": goal_text,
        "mode": mode,
        "started_at": _iso(),
        "ended_at": None,
        "budget": budget or {"max_tokens": 500000, "max_minutes": 30},
        "plan": plan or [],
        "events": [],
        "oracle": None,
        "status": "in_progress",
        "train_weight": 0.0,
    }
    save_trace(trace)
    return trace


def append_event(
    trace: dict[str, Any],
    *,
    type: str,
    content: str = "",
    tool: str | None = None,
    args: dict[str, Any] | None = None,
    result_snip: str = "",
    ok: bool | None = None,
) -> dict[str, Any]:
    ev: dict[str, Any] = {
        "t": _iso(),
        "type": type,
        "content": content[:4000],
    }
    if tool is not None:
        ev["tool"] = tool
    if args is not None:
        ev["args"] = args
    if result_snip:
        ev["result_snip"] = result_snip[:2000]
    if ok is not None:
        ev["ok"] = ok
    trace.setdefault("events", []).append(ev)
    save_trace(trace)
    return trace


def finalize_trace(
    trace: dict[str, Any],
    *,
    status: str,
    oracle: dict[str, Any] | None = None,
    train_weight: float | None = None,
) -> dict[str, Any]:
    """status: goal_proven | goal_failed | deeper_work_needed"""
    trace["ended_at"] = _iso()
    trace["status"] = status
    if oracle is not None:
        trace["oracle"] = oracle
    if train_weight is not None:
        trace["train_weight"] = float(train_weight)
    elif status == "goal_proven":
        trace["train_weight"] = 4.0
    elif status == "goal_failed":
        trace["train_weight"] = 0.1
    else:
        trace["train_weight"] = 0.0
    save_trace(trace)
    append_jsonl(trace)
    return trace


def trace_path(goal_id: str) -> Path:
    """Path for a goal id; does not create the directory (read-friendly)."""
    return goal_traces_dir(ensure=False) / f"{goal_id}.json"


def save_trace(trace: dict[str, Any]) -> Path | None:
    """Persist per-goal JSON. No-op (returns None) when KEEP_GOAL_TRACES is off."""
    if not keep_goal_traces():
        return None
    gid = str(trace.get("goal_id") or "unknown")
    # ensure=True: we already know flag is on
    path = goal_traces_dir(ensure=True) / f"{gid}.json"
    path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return path


def load_trace(goal_id: str) -> dict[str, Any] | None:
    path = goal_traces_dir(ensure=False) / f"{goal_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(trace: dict[str, Any]) -> Path | None:
    """Append to traces.jsonl. No-op when KEEP_GOAL_TRACES is off."""
    if not keep_goal_traces():
        return None
    path = goal_traces_dir(ensure=True) / "traces.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(trace, ensure_ascii=False) + "\n")
    return path


def sandbox_file_exists_goal(
    target_file: Path,
    *,
    goal_text: str | None = None,
) -> dict[str, Any]:
    """One-shot sandbox: prove a file exists (oracle)."""
    text = goal_text or f"Ensure file exists: {target_file}"
    tr = start_trace(text, mode="sandbox", plan=[{"step": 1, "intent": "check_file", "tool": "path.exists"}])
    append_event(tr, type="think", content=f"Check path {target_file}")
    exists = target_file.is_file()
    append_event(
        tr,
        type="tool",
        tool="path.exists",
        args={"path": str(target_file)},
        result_snip=str(exists),
        ok=exists,
    )
    if exists:
        return finalize_trace(
            tr,
            status="goal_proven",
            oracle={"name": "file_exists", "pass": True, "evidence": str(target_file)},
        )
    return finalize_trace(
        tr,
        status="goal_failed",
        oracle={"name": "file_exists", "pass": False, "evidence": str(target_file)},
    )
