"""
pipeline/pipeline_activity.py
Append-only activity log in the pipeline output repo (PIPELINE_DIR).

All factory-side events that should appear in the output GitHub repo
(projects, finetune corpus, registry, etc.) can call log_activity().
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.pipeline_config import PIPELINE_DIR


def activity_log_path() -> Path:
    return PIPELINE_DIR / "state" / "activity.jsonl"


def log_activity(event: str, **fields: Any) -> None:
    """Append one JSON line to state/activity.jsonl (never raises)."""
    try:
        path = activity_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "pipeline_dir": str(PIPELINE_DIR),
            **fields,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def maybe_sync_output_repo(reason: str = "") -> None:
    """If PIPELINE_AUTO_SYNC=1, run scripts/sync_output_repo.py (non-blocking best-effort)."""
    if os.environ.get("PIPELINE_AUTO_SYNC", "").strip().lower() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return
    try:
        import subprocess
        import sys

        script = Path(__file__).resolve().parent.parent / "scripts" / "sync_output_repo.py"
        if not script.is_file():
            return
        subprocess.run(
            [sys.executable, str(script), "--message", reason or "pipeline auto-sync"],
            cwd=str(script.parent.parent),
            timeout=120,
            check=False,
        )
    except Exception:
        pass
