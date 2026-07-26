"""Factory truth-density report: field_proven per hour (and per token when known)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path


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


def candidate_pipeline_dirs(primary: Path) -> list[Path]:
    """Ordered unique roots that may hold factory logs/projects.

    Worktrees under ``.grok/worktrees/...`` often resolve ``get_pipeline_dir()``
    to a local ``.pipeline`` with few projects, while overnight runs write under
    ``~/aicompete/thepipeline``. Search both (and a few common layouts).
    """
    roots: list[Path] = []

    def add(p: Path | None) -> None:
        if p is None:
            return
        try:
            r = p.expanduser().resolve()
        except OSError:
            r = Path(p)
        key = str(r)
        if any(str(existing) == key for existing in roots):
            return
        roots.append(r)

    add(Path(primary))
    env = (os.environ.get("PIPELINE_DIR") or "").strip()
    if env:
        add(Path(env))
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        add(PROJECT_ROOT / ".pipeline")
        add(PROJECT_ROOT.parent / "thepipeline")
        # Walk up a few parents looking for sibling thepipeline (worktrees)
        cur = PROJECT_ROOT
        for _ in range(5):
            add(cur.parent / "thepipeline")
            if cur.parent == cur:
                break
            cur = cur.parent
    except Exception:
        pass
    home = Path.home()
    add(home / "aicompete" / "thepipeline")
    add(home / "aicompete" / "idea impl" / ".pipeline")
    return roots


def pipeline_dir_from_log_dir(log_dir: Path) -> Path | None:
    """If *log_dir* is ``{pipeline}/logs/{name}``, return the pipeline root."""
    try:
        p = log_dir.resolve()
    except OSError:
        p = Path(log_dir)
    if p.parent.name.lower() == "logs":
        root = p.parent.parent
        if root.is_dir():
            return root
    return None


def resolve_since_path(pipeline_dir: Path, since: str) -> Path | None:
    """Resolve --since to an overnight log directory if it names a folder.

    Accepts absolute paths, relative paths, or bare names like
    ``overnight_20260724_233953`` (looked up under ``{pipeline_dir}/logs/``
    and other candidate factory roots — e.g. ``~/aicompete/thepipeline/logs/``).
    """
    text = (since or "").strip()
    if not text:
        return None
    candidates: list[Path] = [
        Path(text),
        Path(text).expanduser(),
        Path.cwd() / text,
        Path.cwd() / "logs" / text,
    ]
    for root in candidate_pipeline_dirs(pipeline_dir):
        candidates.append(root / text)
        candidates.append(root / "logs" / text)
    # de-dupe while preserving order
    seen: set[str] = set()
    for p in candidates:
        try:
            key = str(p.resolve()) if p.exists() else str(p)
        except OSError:
            key = str(p)
        if key in seen:
            continue
        seen.add(key)
        try:
            if p.is_dir():
                return p.resolve()
        except OSError:
            continue
    return None


def tried_log_locations(pipeline_dir: Path, since: str) -> list[str]:
    """Human-readable log dirs checked for a bare overnight name."""
    text = (since or "").strip()
    locs: list[str] = []
    for root in candidate_pipeline_dirs(pipeline_dir):
        s = str(root / "logs")
        if s not in locs:
            locs.append(s)
    if text:
        locs.append(f"(also absolute/relative: {text})")
    return locs


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
        p = resolve_since_path(pipeline_dir, since)
        if p is not None and p.is_dir():
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
            try:
                start = parse_iso_to_utc(since)
                source = "cli_since"
            except ValueError as exc:
                tried = ", ".join(tried_log_locations(pipeline_dir, since))
                home_ex = Path.home() / "aicompete" / "thepipeline" / "logs" / (
                    since if since.startswith("overnight_") else "overnight_YYYYMMDD_HHMMSS"
                )
                raise ValueError(
                    f"Invalid --since {since!r}: not an existing log directory "
                    f"(tried under {tried}) and not a valid ISO timestamp. "
                    f"Example: --since overnight_20260724_233953 "
                    f"or --since {home_ex}"
                ) from exc

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
    """Collect token totals for the window. Never treat unknown as 0 tokens."""
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
    stall_i: int | None
    if stall is None:
        stall_i = None
    else:
        try:
            stall_i = int(stall)
        except (TypeError, ValueError):
            stall_i = None
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
            mark = (
                " (low-confidence timestamp)"
                if s in report.field_proven.low_confidence_slugs
                else ""
            )
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
