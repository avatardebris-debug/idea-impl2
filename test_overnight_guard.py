"""P0 overnight guards: CLI assert, serial, stale grok_driver flags, thin-ship statuses."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from pipeline.engines.overnight_guard import (
    assert_grok_cli_ready,
    assert_serial_for_grok,
    clear_stale_grok_driver_flags,
    grok_overnight_mode,
)


def test_assert_cli_ready_exits_when_cmd_missing(monkeypatch, capsys):
    monkeypatch.setenv("PIPELINE_ENGINE", "grok_build")
    monkeypatch.setenv("GROK_BUILD_BACKEND", "cli")
    monkeypatch.delenv("GROK_BUILD_CMD", raising=False)
    with pytest.raises(SystemExit) as ei:
        assert_grok_cli_ready()
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert "GROK_BUILD_CMD" in err


def test_assert_cli_ready_ok_with_cmd(monkeypatch, tmp_path: Path):
    exe = tmp_path / "grok.exe"
    exe.write_text("", encoding="utf-8")
    monkeypatch.setenv("PIPELINE_ENGINE", "grok_build")
    monkeypatch.setenv("GROK_BUILD_BACKEND", "cli")
    monkeypatch.setenv("GROK_BUILD_CMD", f'{exe} --cwd "{{workspace}}"')
    assert_grok_cli_ready()  # no raise


def test_assert_serial_refuses_parallel(monkeypatch, capsys):
    monkeypatch.setenv("PIPELINE_ENGINE", "grok_build")
    monkeypatch.delenv("GROK_BUILD_ALLOW_PARALLEL", raising=False)
    with pytest.raises(SystemExit) as ei:
        assert_serial_for_grok(parallel_seeds=2, num_executors=1)
    assert ei.value.code == 2
    err = capsys.readouterr().err.lower()
    assert "serial" in err or "parallel" in err


def test_assert_serial_allows_override(monkeypatch):
    monkeypatch.setenv("PIPELINE_ENGINE", "grok_build")
    monkeypatch.setenv("GROK_BUILD_ALLOW_PARALLEL", "1")
    assert_serial_for_grok(parallel_seeds=2, num_executors=2)


def test_clear_stale_running_flag_without_grok_status(tmp_path: Path):
    proj = tmp_path / "p"
    (proj / "state").mkdir(parents=True)
    sf = proj / "state" / "current_idea.json"
    state = {
        "status": "phase_1_executing",
        "grok_driver_running": True,
        "engine": "grok_build",
    }
    sf.write_text(json.dumps(state), encoding="utf-8")
    out = clear_stale_grok_driver_flags(proj, state)
    assert "grok_driver_running" not in out or not out.get("grok_driver_running")
    saved = json.loads(sf.read_text(encoding="utf-8"))
    assert not saved.get("grok_driver_running")


def test_clear_stale_grok_running_by_age(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GROK_BUILD_STALE_S", "100")
    proj = tmp_path / "p2"
    (proj / "state").mkdir(parents=True)
    sf = proj / "state" / "current_idea.json"
    old = time.time() - 500
    state = {
        "status": "phase_2_grok_running",
        "grok_driver_running": True,
        "grok_driver_started_at": old,
        "engine": "grok_build",
    }
    sf.write_text(json.dumps(state), encoding="utf-8")
    out = clear_stale_grok_driver_flags(proj, state, now=time.time())
    assert not out.get("grok_driver_running")
    assert out.get("status") == "phase_2_executing"


def test_grok_overnight_mode(monkeypatch):
    monkeypatch.setenv("PIPELINE_ENGINE", "grok_build")
    assert grok_overnight_mode() is True
    monkeypatch.setenv("PIPELINE_ENGINE", "classic")
    assert grok_overnight_mode() is False
