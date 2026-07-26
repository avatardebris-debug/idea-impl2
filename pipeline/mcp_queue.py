"""
mcp_factory_job.v1 — file-based MCP factory job queue.

Layout under PIPELINE_DIR:
  queues/mcp_factory/pending/{job_id}.json
  queues/mcp_factory/done/{job_id}.json

Enqueue is side-effect free for the software factory: jobs wait for the
separate MCP factory CLI (T4) to drain. Never invent MCP servers here.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import get_pipeline_dir

SCHEMA = "mcp_factory_job.v1"

__all__ = [
    "SCHEMA",
    "queue_dir",
    "enqueue_wrap",
    "list_pending",
    "mark_done",
    "load_job",
]


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def queue_dir() -> Path:
    """Return queues/mcp_factory and ensure pending/ + done/ exist."""
    d = get_pipeline_dir() / "queues" / "mcp_factory"
    (d / "pending").mkdir(parents=True, exist_ok=True)
    (d / "done").mkdir(parents=True, exist_ok=True)
    return d


def enqueue_wrap(
    capability_slug: str,
    *,
    goal_id: str | None = None,
    reason: str = "",
) -> Path:
    """Write a pending mcp_factory_job.v1 for wrapping *capability_slug*.

    Returns the path to pending/{job_id}.json.
    """
    slug = (capability_slug or "").strip()
    if not slug:
        raise ValueError("capability_slug is required")

    job_id = f"mcpjob_{uuid.uuid4().hex[:12]}"
    job: dict[str, Any] = {
        "schema": SCHEMA,
        "job_id": job_id,
        "capability_slug": slug,
        "reason": reason or "",
        "goal_id": goal_id,
        "status": "pending",
        "created_at": _iso(),
    }
    path = queue_dir() / "pending" / f"{job_id}.json"
    path.write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def list_pending() -> list[Path]:
    """Sorted list of pending/*.json job files."""
    pending = queue_dir() / "pending"
    if not pending.is_dir():
        return []
    return sorted(pending.glob("*.json"))


def load_job(path: Path) -> dict[str, Any]:
    """Load a job JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def mark_done(job_path: Path, result: dict | None = None) -> Path:
    """Move job from pending/ to done/, set status done|failed from *result*.

    *result* may include:
      - ok: bool (False => failed)
      - status: "done"|"failed"
      - any other fields stored under job["result"]

    Returns the path under done/.
    """
    job_path = Path(job_path)
    if not job_path.is_file():
        raise FileNotFoundError(f"job not found: {job_path}")

    job = load_job(job_path)
    result = dict(result or {})

    explicit = str(result.get("status") or "").strip().lower()
    if explicit in ("done", "failed"):
        status = explicit
    elif result.get("ok") is False:
        status = "failed"
    else:
        status = "done"

    job["status"] = status
    job["finished_at"] = _iso()
    if result:
        job["result"] = result

    done_path = queue_dir() / "done" / job_path.name
    done_path.write_text(
        json.dumps(job, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    try:
        if job_path.resolve() != done_path.resolve():
            job_path.unlink(missing_ok=True)
    except OSError:
        pass
    return done_path
