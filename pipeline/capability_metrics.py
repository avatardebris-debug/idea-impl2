"""
pipeline/capability_metrics.py
Phase 7: append-only usage metrics for registry routing and invoke.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.pipeline_config import PIPELINE_DIR

METRICS_LOG = PIPELINE_DIR / "state" / "capability_metrics.jsonl"


def log_capability_event(
    event: str,
    slug: str = "",
    *,
    ok: bool | None = None,
    detail: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    """Events: route, suggest, invoke, register, promote."""
    if not event:
        return
    METRICS_LOG.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "slug": slug,
        "ok": ok,
        "detail": (detail or "")[:500],
    }
    if extra:
        row.update(extra)
    try:
        with METRICS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def read_metrics(limit: int = 5000) -> list[dict[str, Any]]:
    if not METRICS_LOG.exists():
        return []
    lines = METRICS_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def summarize_metrics() -> dict[str, Any]:
    """Top slugs by invoke/suggest; failure counts."""
    rows = read_metrics()
    by_slug: dict[str, dict[str, int]] = {}
    by_event: dict[str, int] = {}

    for r in rows:
        ev = r.get("event", "?")
        by_event[ev] = by_event.get(ev, 0) + 1
        slug = r.get("slug") or ""
        if not slug:
            continue
        bucket = by_slug.setdefault(slug, {"invoke": 0, "invoke_fail": 0, "suggest": 0, "route": 0})
        if ev == "invoke":
            bucket["invoke"] += 1
            if r.get("ok") is False:
                bucket["invoke_fail"] += 1
        elif ev == "suggest":
            bucket["suggest"] += 1
        elif ev == "route":
            bucket["route"] += 1

    top_invoke = sorted(by_slug.items(), key=lambda x: x[1]["invoke"], reverse=True)[:15]
    top_fail = sorted(
        [(s, d) for s, d in by_slug.items() if d["invoke_fail"] > 0],
        key=lambda x: x[1]["invoke_fail"],
        reverse=True,
    )[:10]

    return {
        "total_events": len(rows),
        "by_event": by_event,
        "top_invoke": top_invoke,
        "top_fail": top_fail,
    }
