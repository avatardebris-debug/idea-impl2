"""Factory truth-density report: field_proven per hour (and per token when known)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def parse_iso_to_utc(s: str) -> datetime:
    """Parse ISO-8601 (including fractional seconds and offsets) to aware UTC."""
    text = (s or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    # Python <3.11 may struggle with >6 fractional digits; trim if needed
    if "." in text:
        head, rest = text.split(".", 1)
        # rest may be "4870944-05:00"
        sign_i = max(rest.rfind("+"), rest.rfind("-"))
        if sign_i > 0:
            frac, off = rest[:sign_i], rest[sign_i:]
            frac = (frac + "000000")[:6]
            text = f"{head}.{frac}{off}"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def wall_clock_hours(start: datetime, end: datetime) -> float:
    if end < start:
        return 0.0
    return (end - start).total_seconds() / 3600.0


@dataclass
class RunWindow:
    start: datetime
    end: datetime
    source: str = ""
    time_limit_min: float | None = None
    partial: bool = False  # True if end is "now" mid-run

    @property
    def hours(self) -> float:
        return wall_clock_hours(self.start, self.end)

    def overrun(self, margin: float = 0.10) -> bool:
        if self.time_limit_min is None or self.time_limit_min <= 0:
            return False
        limit_h = self.time_limit_min / 60.0
        if limit_h <= 0:
            return False
        return self.hours > limit_h * (1.0 + margin)


def resolve_run_window(
    *,
    pipeline_dir: Path,
    since: str | None = None,
    until: str | None = None,
    now: datetime | None = None,
) -> RunWindow:
    """Resolve start/end. Prefer overnight log dir / preflight when since is a path."""
    now = now or datetime.now(timezone.utc)
    end: datetime | None = None
    start: datetime | None = None
    source = ""
    time_limit_min: float | None = None
    partial = False

    if until:
        end = parse_iso_to_utc(until)

    if since:
        p = Path(since)
        if p.is_dir():
            pre_path = p / "preflight.json"
            if pre_path.is_file():
                try:
                    pre = json.loads(pre_path.read_text(encoding="utf-8-sig"))
                    if pre.get("ts"):
                        start = parse_iso_to_utc(str(pre["ts"]))
                        source = f"preflight:{p.name}"
                    if pre.get("time_limit_min") is not None:
                        time_limit_min = float(pre["time_limit_min"])
                except Exception:
                    pass
            log_path = p / "runner.log"
            if end is None and log_path.is_file():
                end = datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc)
                if not source:
                    source = f"log_mtime:{p.name}"
            if start is None:
                # fallback: dir mtime as weak start
                start = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                source = source or f"dir:{p.name}"
        else:
            start = parse_iso_to_utc(since)
            source = "cli_since"

    if start is None:
        # activity.jsonl last runner_start
        act = pipeline_dir / "state" / "activity.jsonl"
        if act.is_file():
            last_start = None
            try:
                for line in act.read_text(encoding="utf-8", errors="replace").splitlines():
                    if not line.strip():
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if ev.get("event") == "runner_start" and ev.get("ts"):
                        last_start = parse_iso_to_utc(str(ev["ts"]))
                if last_start is not None:
                    start = last_start
                    source = "activity_runner_start"
            except Exception:
                pass

    if start is None:
        start = now - timedelta(hours=24)
        source = "fallback_24h"

    if end is None:
        end = now
        partial = True
        if not source.endswith("+now"):
            source = f"{source}+now"

    return RunWindow(
        start=start,
        end=end,
        source=source,
        time_limit_min=time_limit_min,
        partial=partial,
    )


@dataclass
class FieldProvenScan:
    count: int
    slugs: list[str] = field(default_factory=list)
    low_confidence_slugs: list[str] = field(default_factory=list)


def count_field_proven_in_window(
    pipeline_dir: Path,
    window: RunWindow,
) -> FieldProvenScan:
    projects = pipeline_dir / "projects"
    slugs: list[str] = []
    low: list[str] = []
    if not projects.is_dir():
        return FieldProvenScan(count=0)

    for d in sorted(projects.iterdir()):
        if not d.is_dir():
            continue
        sf = d / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if (st.get("status") or "") != "field_proven":
            continue
        proven_raw = st.get("field_proven_at") or st.get("last_active_work_at")
        low_conf = False
        if proven_raw:
            try:
                proven = parse_iso_to_utc(str(proven_raw))
            except Exception:
                proven = datetime.fromtimestamp(sf.stat().st_mtime, tz=timezone.utc)
                low_conf = True
        else:
            proven = datetime.fromtimestamp(sf.stat().st_mtime, tz=timezone.utc)
            low_conf = True
        if window.start <= proven <= window.end:
            slugs.append(d.name)
            if low_conf:
                low.append(d.name)

    return FieldProvenScan(count=len(slugs), slugs=slugs, low_confidence_slugs=low)
