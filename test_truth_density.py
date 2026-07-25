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
