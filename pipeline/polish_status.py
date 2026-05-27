"""
pipeline/polish_status.py
Persisted status for --polish runs (running vs terminated) for logs and zip import.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.pipeline_config import PIPELINE_DIR

POLISH_STATUS_PATH = PIPELINE_DIR / "state" / "polish_status.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_polish_status(**fields: Any) -> None:
    POLISH_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = load_polish_status()
    data.update(fields)
    data["updated_at"] = _now()
    POLISH_STATUS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_polish_status() -> dict[str, Any]:
    if not POLISH_STATUS_PATH.exists():
        return {}
    try:
        return json.loads(POLISH_STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def print_polish_lifecycle(
    state: str,
    *,
    reason: str = "",
    queued: int = 0,
    queue_path: str = "",
    pending_messages: int = 0,
) -> None:
    """Print a single clear line for operators (also stored in polish_status.json)."""
    path_label = queue_path or "polish_queue.md"
    if state == "running":
        msg = (
            f"  [polish] RUNNING — {queued} project(s) queued from {path_label}"
        )
        if pending_messages:
            msg += f"; {pending_messages} pending queue message(s)"
    elif state == "terminated":
        msg = f"  [polish] TERMINATED — {reason or 'no work remaining'}"
    else:
        msg = f"  [polish] {state.upper()} — {reason}"
    print(msg)
    save_polish_status(
        run_state=state,
        reason=reason,
        queued_at_start=queued,
        queue_path=path_label,
        pending_messages=pending_messages,
    )
