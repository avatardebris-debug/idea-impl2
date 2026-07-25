# Factory Truth-Density Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After a factory or overnight run, produce a short read-only report of field-proven projects per wall-clock hour (and per million tokens when known).

**Architecture:** Pure library module resolves a time window, scans project state for field-proven timestamps, optionally reads token totals from metrics/activity, formats Markdown, and appends one JSONL history line. A thin CLI script is the only operator entry point. No status mutation, no dashboard, no database.

**Tech Stack:** Python 3.11+, pytest, existing `pipeline.paths` / `PIPELINE_DIR` conventions (same style as `scripts/overnight_report.py`).

**Spec:** `docs/superpowers/specs/2026-07-24-factory-truth-density-report-design.md`

---

## File map

| File | Responsibility |
|------|----------------|
| `pipeline/truth_density.py` | Window resolution, scans, rates, markdown + jsonl writers |
| `scripts/report_truth_density.py` | CLI (`--pipeline-dir`, `--since`, `--until`, `--out`) |
| `test_truth_density.py` | Unit tests with temp pipeline dirs (repo root, like other `test_*.py`) |
| `COMMANDS.md` | Short usage note under metrics / overnight section |

---

### Task 1: Window resolution helpers (TDD)

**Files:**
- Create: `pipeline/truth_density.py`
- Create: `test_truth_density.py`

- [ ] **Step 1: Write failing tests for ISO parsing and wall-clock hours**

```python
# test_truth_density.py
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import pytest

from pipeline.truth_density import (
    parse_iso_to_utc,
    wall_clock_hours,
    resolve_run_window,
)


def test_parse_iso_to_utc_accepts_offset():
    dt = parse_iso_to_utc("2026-07-24T14:55:11.4870944-05:00")
    assert dt.tzinfo is not None
    assert dt.utcoffset() == timedelta(0) or dt.tzinfo == timezone.utc or dt.utcoffset() is not None
    # Normalize comparison in UTC
    assert abs((dt.astimezone(timezone.utc) - datetime(2026, 7, 24, 19, 55, 11, tzinfo=timezone.utc)).total_seconds()) < 2


def test_wall_clock_hours_positive():
    start = datetime(2026, 7, 24, 15, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 7, 24, 17, 30, 0, tzinfo=timezone.utc)
    assert wall_clock_hours(start, end) == pytest.approx(2.5)


def test_resolve_run_window_from_preflight(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    log_dir = tmp_path / "logs" / "overnight_20260724_145511"
    log_dir.mkdir(parents=True)
    pre = {
        "ts": "2026-07-24T14:55:11-05:00",
        "time_limit_min": 30,
    }
    (log_dir / "preflight.json").write_text(json.dumps(pre), encoding="utf-8")
    (log_dir / "runner.log").write_text("done\n", encoding="utf-8")
    # mtime of runner.log will be "now" ≈ end
    window = resolve_run_window(pipeline_dir=tmp_path, since=str(log_dir))
    assert window.start is not None
    assert window.end is not None
    assert window.time_limit_min == 30
    assert window.source.startswith("preflight") or "overnight" in window.source or "log" in window.source
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
cd C:\Users\avata\.grok\worktrees\aicompete-idea-impl\idea-impl2
python -m pytest test_truth_density.py -q
```

Expected: FAIL (import error / not defined)

- [ ] **Step 3: Implement minimal window helpers**

```python
# pipeline/truth_density.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```powershell
python -m pytest test_truth_density.py -q
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add pipeline/truth_density.py test_truth_density.py
git commit -m "feat(truth_density): add run window resolution helpers"
```

---

### Task 2: Count field_proven in window

**Files:**
- Modify: `pipeline/truth_density.py`
- Modify: `test_truth_density.py`

- [ ] **Step 1: Write failing tests**

```python
def _write_project(root: Path, slug: str, status: str, proven_at: str | None = None):
    d = root / "projects" / slug / "state"
    d.mkdir(parents=True)
    st = {"status": status, "title": slug, "phase": 3, "total_phases": 3}
    if proven_at:
        st["field_proven_at"] = proven_at
    (d / "current_idea.json").write_text(json.dumps(st, indent=2), encoding="utf-8")


def test_count_field_proven_in_window(tmp_path):
    start = datetime(2026, 7, 24, 15, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 7, 24, 18, 0, 0, tzinfo=timezone.utc)
    _write_project(tmp_path, "a", "field_proven", "2026-07-24T16:00:00+00:00")  # in
    _write_project(tmp_path, "b", "field_proven", "2026-07-24T12:00:00+00:00")  # before
    _write_project(tmp_path, "c", "budget_exceeded", None)
    _write_project(tmp_path, "d", "field_proven", "2026-07-24T17:00:00+00:00")  # in

    from pipeline.truth_density import count_field_proven_in_window, RunWindow

    window = RunWindow(start=start, end=end, source="test")
    result = count_field_proven_in_window(tmp_path, window)
    assert result.count == 2
    assert set(result.slugs) == {"a", "d"}
    assert result.low_confidence_slugs == []
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest test_truth_density.py::test_count_field_proven_in_window -v
```

- [ ] **Step 3: Implement counter**

```python
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
```

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest test_truth_density.py -q
```

- [ ] **Step 5: Commit**

```powershell
git add pipeline/truth_density.py test_truth_density.py
git commit -m "feat(truth_density): count field_proven projects in run window"
```

---

### Task 3: Token totals (honest partial / missing)

**Files:**
- Modify: `pipeline/truth_density.py`
- Modify: `test_truth_density.py`

- [ ] **Step 1: Write failing tests**

```python
def test_tokens_missing_mode():
    from pipeline.truth_density import collect_tokens, TokenReport

    report = collect_tokens(Path("/nonexistent"), RunWindow(
        start=datetime(2026, 7, 24, 15, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 24, 16, 0, tzinfo=timezone.utc),
    ))
    assert report.mode == "missing"
    assert report.total_tokens is None


def test_tokens_from_metrics_summary(tmp_path):
    from pipeline.truth_density import collect_tokens, RunWindow

    mdir = tmp_path / "metrics" / "20260724_150000"
    mdir.mkdir(parents=True)
    summary = {"total_tokens": 1_500_000, "stall_tokens": 1000}
    (mdir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    # Prefer newest metrics dir under pipeline_dir/metrics if mtime in window — implementer may also accept --metrics-dir later; for v1 scan latest summary.json under metrics/

    window = RunWindow(
        start=datetime(2026, 7, 24, 14, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 24, 20, 0, tzinfo=timezone.utc),
        source="test",
    )
    report = collect_tokens(tmp_path, window)
    # If scan picks this dir by mtime "now", tokens may still be missing — bind test to explicit path if API supports metrics_dir=
    # Prefer API: collect_tokens(..., metrics_summary_path=optional)
```

Refine API for testability:

```python
def collect_tokens(
    pipeline_dir: Path,
    window: RunWindow,
    *,
    metrics_summary_path: Path | None = None,
) -> TokenReport:
    ...
```

Test with explicit `metrics_summary_path`.

```python
def test_tokens_from_explicit_summary(tmp_path):
    from pipeline.truth_density import collect_tokens, RunWindow, TokenReport

    p = tmp_path / "summary.json"
    p.write_text(json.dumps({"total_tokens": 2_000_000}), encoding="utf-8")
    window = RunWindow(
        start=datetime(2026, 7, 24, 14, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 24, 20, 0, tzinfo=timezone.utc),
    )
    report = collect_tokens(tmp_path, window, metrics_summary_path=p)
    assert report.mode == "full"
    assert report.total_tokens == 2_000_000
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement**

```python
@dataclass
class TokenReport:
    mode: str  # "full" | "partial" | "missing"
    total_tokens: int | None = None
    stall_tokens: int | None = None
    source: str = ""


def collect_tokens(
    pipeline_dir: Path,
    window: RunWindow,
    *,
    metrics_summary_path: Path | None = None,
) -> TokenReport:
    path = metrics_summary_path
    if path is None:
        metrics_root = pipeline_dir / "metrics"
        if metrics_root.is_dir():
            # newest summary.json whose parent dir mtime intersects window (best effort)
            candidates = sorted(
                metrics_root.glob("*/summary.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for cand in candidates[:5]:
                mtime = datetime.fromtimestamp(cand.stat().st_mtime, tz=timezone.utc)
                if window.start <= mtime <= window.end + timedelta(hours=1):
                    path = cand
                    break
            if path is None and candidates:
                # do not silently use out-of-window totals as "full" — leave missing
                path = None

    if path is None or not path.is_file():
        return TokenReport(mode="missing", source="none")

    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return TokenReport(mode="missing", source=str(path))

    total = data.get("total_tokens")
    if total is None:
        return TokenReport(mode="missing", source=str(path))
    try:
        total_i = int(total)
    except (TypeError, ValueError):
        return TokenReport(mode="missing", source=str(path))

    stall = data.get("stall_tokens")
    stall_i = int(stall) if stall is not None else None
    # metrics summary is run-scoped; treat as full when present
    return TokenReport(
        mode="full",
        total_tokens=total_i,
        stall_tokens=stall_i,
        source=str(path),
    )


def field_proven_per_million_tokens(count: int, tokens: int | None) -> float | None:
    if tokens is None or tokens <= 0:
        return None
    return count / (tokens / 1_000_000.0)
```

- [ ] **Step 4: Tests PASS**

- [ ] **Step 5: Commit**

```powershell
git add pipeline/truth_density.py test_truth_density.py
git commit -m "feat(truth_density): honest token collection for per-million rates"
```

---

### Task 4: Build report object and Markdown formatter

**Files:**
- Modify: `pipeline/truth_density.py`
- Modify: `test_truth_density.py`

- [ ] **Step 1: Write failing test for markdown content**

```python
def test_format_report_includes_rates_and_missing_tokens():
    from pipeline.truth_density import (
        RunWindow,
        FieldProvenScan,
        TokenReport,
        TruthDensityReport,
        format_report_markdown,
    )

    window = RunWindow(
        start=datetime(2026, 7, 24, 15, 0, tzinfo=timezone.utc),
        end=datetime(2026, 7, 24, 17, 0, tzinfo=timezone.utc),
        source="test",
        time_limit_min=30,
    )
    # 2 hours wall; limit 0.5h → overrun
    scan = FieldProvenScan(count=2, slugs=["a", "b"])
    tokens = TokenReport(mode="missing")
    report = TruthDensityReport(window=window, field_proven=scan, tokens=tokens)
    md = format_report_markdown(report)
    assert "Field proven" in md or "field proven" in md.lower()
    assert "per wall-clock hour" in md.lower() or "per hour" in md.lower()
    assert "2" in md
    assert "not instrumented" in md.lower() or "missing" in md.lower()
    assert "overran" in md.lower() or "overrun" in md.lower()
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement report + formatter**

```python
@dataclass
class TruthDensityReport:
    window: RunWindow
    field_proven: FieldProvenScan
    tokens: TokenReport
    active_work_hours: float | None = None

    @property
    def per_wall_hour(self) -> float | None:
        h = self.window.hours
        if h <= 0:
            return None
        return self.field_proven.count / h

    @property
    def per_million_tokens(self) -> float | None:
        return field_proven_per_million_tokens(
            self.field_proven.count, self.tokens.total_tokens
        )


def format_report_markdown(report: TruthDensityReport) -> str:
    w = report.window
    lines = [
        "# Factory truth-density report",
        "",
        "## Run window",
        f"- Start (UTC): {w.start.isoformat()}",
        f"- End (UTC): {w.end.isoformat()}",
        f"- Source: {w.source}",
        f"- Wall-clock hours: {w.hours:.2f}",
    ]
    if w.time_limit_min is not None:
        lines.append(f"- Configured time limit (minutes): {w.time_limit_min:.0f}")
        if w.overrun():
            lines.append(
                "- **Note:** Wall-clock time overran the configured limit by more than 10%."
            )
    if w.partial:
        lines.append("- **Note:** End time is approximate (run may still be open).")
    lines += [
        "",
        "## Throughput",
        f"- Field proven in window: **{report.field_proven.count}**",
    ]
    if report.per_wall_hour is not None:
        lines.append(
            f"- Field proven per wall-clock hour: **{report.per_wall_hour:.2f}**"
        )
    if report.active_work_hours is not None and report.active_work_hours > 0:
        rate = report.field_proven.count / report.active_work_hours
        lines.append(f"- Active work hours (if known): {report.active_work_hours:.2f}")
        lines.append(f"- Field proven per active work hour: **{rate:.2f}**")
    lines += ["", "## Model spend (tokens)"]
    if report.tokens.mode == "missing":
        lines.append(
            "- Tokens: **not instrumented for this window** (no complete summary found)."
        )
        lines.append("- Field proven per million tokens: n/a")
    elif report.tokens.mode == "partial":
        lines.append(
            f"- Tokens (partial): {report.tokens.total_tokens:,} (source: {report.tokens.source})"
        )
        lines.append(
            "- Efficiency rates may understate spend; treat as incomplete."
        )
        if report.per_million_tokens is not None:
            lines.append(
                f"- Field proven per million tokens (partial): **{report.per_million_tokens:.2f}**"
            )
    else:
        lines.append(
            f"- Tokens: **{report.tokens.total_tokens:,}** (source: {report.tokens.source})"
        )
        if report.tokens.stall_tokens is not None:
            lines.append(f"- Stall tokens (if recorded): {report.tokens.stall_tokens:,}")
        if report.per_million_tokens is not None:
            lines.append(
                f"- Field proven per million tokens: **{report.per_million_tokens:.2f}**"
            )
    if report.field_proven.slugs:
        lines += ["", "## Projects field-proven in window", ""]
        for s in report.field_proven.slugs:
            mark = " (low-confidence timestamp)" if s in report.field_proven.low_confidence_slugs else ""
            lines.append(f"- `{s}`{mark}")
    lines.append("")
    return "\n".join(lines)


def build_report(
    pipeline_dir: Path,
    *,
    since: str | None = None,
    until: str | None = None,
    metrics_summary_path: Path | None = None,
) -> TruthDensityReport:
    window = resolve_run_window(pipeline_dir=pipeline_dir, since=since, until=until)
    scan = count_field_proven_in_window(pipeline_dir, window)
    tokens = collect_tokens(
        pipeline_dir, window, metrics_summary_path=metrics_summary_path
    )
    return TruthDensityReport(window=window, field_proven=scan, tokens=tokens)
```

- [ ] **Step 4: Tests PASS**

- [ ] **Step 5: Commit**

```powershell
git add pipeline/truth_density.py test_truth_density.py
git commit -m "feat(truth_density): format markdown report with rates"
```

---

### Task 5: History JSONL + write helpers

**Files:**
- Modify: `pipeline/truth_density.py`
- Modify: `test_truth_density.py`

- [ ] **Step 1: Write failing test**

```python
def test_write_report_and_history(tmp_path):
    from pipeline.truth_density import build_report, write_report_outputs

    # minimal projects so count can be 0
    (tmp_path / "projects").mkdir()
    log_dir = tmp_path / "logs" / "overnight_test"
    log_dir.mkdir(parents=True)
    pre = {"ts": "2026-07-24T15:00:00+00:00", "time_limit_min": 60}
    (log_dir / "preflight.json").write_text(json.dumps(pre), encoding="utf-8")
    (log_dir / "runner.log").write_text("ok\n", encoding="utf-8")

    report = build_report(tmp_path, since=str(log_dir))
    paths = write_report_outputs(tmp_path, report, out_path=log_dir / "truth_density.md")
    assert paths["markdown"].is_file()
    assert "Field proven" in paths["markdown"].read_text(encoding="utf-8") or "field proven" in paths["markdown"].read_text(encoding="utf-8").lower()
    hist = tmp_path / "metrics" / "truth_density_history.jsonl"
    assert hist.is_file()
    line = hist.read_text(encoding="utf-8").strip().splitlines()[-1]
    obj = json.loads(line)
    assert "field_proven_count" in obj
    assert "wall_clock_hours" in obj
    assert obj["token_mode"] in ("full", "partial", "missing")
```

- [ ] **Step 2: Implement**

```python
def write_report_outputs(
    pipeline_dir: Path,
    report: TruthDensityReport,
    *,
    out_path: Path | None = None,
) -> dict[str, Path]:
    if out_path is None:
        metrics = pipeline_dir / "metrics"
        metrics.mkdir(parents=True, exist_ok=True)
        out_path = metrics / "truth_density_latest.md"
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    md = format_report_markdown(report)
    out_path.write_text(md, encoding="utf-8")

    hist_dir = pipeline_dir / "metrics"
    hist_dir.mkdir(parents=True, exist_ok=True)
    hist_path = hist_dir / "truth_density_history.jsonl"
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "window_start": report.window.start.isoformat(),
        "window_end": report.window.end.isoformat(),
        "window_source": report.window.source,
        "wall_clock_hours": report.window.hours,
        "time_limit_min": report.window.time_limit_min,
        "overrun": report.window.overrun(),
        "partial_window": report.window.partial,
        "field_proven_count": report.field_proven.count,
        "field_proven_slugs": report.field_proven.slugs,
        "per_wall_hour": report.per_wall_hour,
        "token_mode": report.tokens.mode,
        "total_tokens": report.tokens.total_tokens,
        "per_million_tokens": report.per_million_tokens,
    }
    with hist_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

    return {"markdown": out_path, "history": hist_path}
```

- [ ] **Step 3: Tests PASS + commit**

```powershell
git add pipeline/truth_density.py test_truth_density.py
git commit -m "feat(truth_density): write markdown report and history jsonl"
```

---

### Task 6: CLI script

**Files:**
- Create: `scripts/report_truth_density.py`
- Modify: `test_truth_density.py` (optional smoke via subprocess or import main)

- [ ] **Step 1: Implement CLI** (match `scripts/overnight_report.py` style)

```python
#!/usr/bin/env python3
"""Report field_proven per wall-clock hour (and per token when known)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Factory truth-density: field_proven per hour / per million tokens"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    ap.add_argument(
        "--since",
        default="",
        help="ISO start time or path to overnight log directory (with preflight.json)",
    )
    ap.add_argument("--until", default="", help="Optional ISO end time")
    ap.add_argument("--out", default="", help="Markdown output path")
    ap.add_argument(
        "--metrics-summary",
        default="",
        help="Optional path to metrics summary.json for token totals",
    )
    args = ap.parse_args()

    if args.pipeline_dir:
        os.environ["PIPELINE_DIR"] = args.pipeline_dir

    from pipeline.paths import get_pipeline_dir
    from pipeline.truth_density import build_report, write_report_outputs

    pipeline_dir = get_pipeline_dir()
    if not pipeline_dir.is_dir():
        print(f"ERROR: pipeline dir missing: {pipeline_dir}", file=sys.stderr)
        return 2

    report = build_report(
        pipeline_dir,
        since=args.since or None,
        until=args.until or None,
        metrics_summary_path=Path(args.metrics_summary) if args.metrics_summary else None,
    )

    out = Path(args.out) if args.out else None
    # If --since is overnight log dir, default out there
    if out is None and args.since:
        p = Path(args.since)
        if p.is_dir():
            out = p / "truth_density.md"

    paths = write_report_outputs(pipeline_dir, report, out_path=out)
    print(f"Report: {paths['markdown']}")
    print(f"History: {paths['history']}")
    print(
        f"Field proven: {report.field_proven.count} in {report.window.hours:.2f} wall hours"
        + (
            f" ({report.per_wall_hour:.2f}/hour)"
            if report.per_wall_hour is not None
            else ""
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Manual smoke on real pipeline (optional)**

```powershell
$env:PIPELINE_DIR = "C:\Users\avata\aicompete\thepipeline"
python scripts/report_truth_density.py --since "C:\Users\avata\aicompete\thepipeline\logs\overnight_20260724_145511"
```

Expected: prints report path; creates `truth_density.md` under that log dir if present.

- [ ] **Step 3: Commit**

```powershell
git add scripts/report_truth_density.py
git commit -m "feat(truth_density): add report_truth_density.py CLI"
```

---

### Task 7: Documentation

**Files:**
- Modify: `COMMANDS.md` (find overnight / metrics section; add a short subsection)

- [ ] **Step 1: Add usage**

```markdown
### Truth-density report (field proven per hour)

After overnight or any factory run:

```powershell
set PIPELINE_DIR=C:\Users\avata\aicompete\thepipeline
python scripts/report_truth_density.py --since $env:PIPELINE_DIR\logs\overnight_YYYYMMDD_HHMMSS
```

Writes `truth_density.md` in that log folder (or `metrics/truth_density_latest.md`) and appends `metrics/truth_density_history.jsonl`.

Reports field proven per wall-clock hour; tokens per million only when a metrics summary exists. Does not change project status.
```

- [ ] **Step 2: Commit**

```powershell
git add COMMANDS.md
git commit -m "docs: truth-density report usage"
```

---

### Task 8: Full regression + final check

- [ ] **Step 1: Run focused + related tests**

```powershell
python -m pytest test_truth_density.py -q
python -m pytest test_troubleshoot_gate.py test_classic_to_grok.py -q --tb=no
```

Expected: all pass (truth_density suite green; no regressions required beyond not breaking imports).

- [ ] **Step 2: Confirm report language is readable**

Open generated markdown from smoke run; ensure no fake “0 tokens” when missing; ensure overrun note works with preflight.

- [ ] **Step 3: Final commit if any fixups**

```powershell
git status
# commit only if there are fixups
```

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| Field proven in window | Task 2 |
| Wall-clock hours (default rate) | Tasks 1, 4 |
| Active work hours optional | Task 4 (field on report; v1 may leave None) |
| Tokens full / partial / missing honesty | Task 3, 4 |
| Per million tokens | Task 3, 4 |
| Window: preflight, CLI, activity, 24h fallback | Task 1 |
| Overrun note | Task 4 |
| Markdown output | Task 4, 5 |
| History JSONL | Task 5 |
| CLI | Task 6 |
| Read-only status | No code mutates current_idea status |
| Tests | Tasks 1–5 |
| COMMANDS.md | Task 7 |
| Overnight hook optional | Explicitly deferred (YAGNI) |

## Placeholder scan

No TBD/TODO steps; code is concrete. Active-work hours stay optional without inventing data.

## Type consistency

- `RunWindow`, `FieldProvenScan`, `TokenReport`, `TruthDensityReport` used consistently across tasks.
- CLI calls `build_report` + `write_report_outputs` only.
