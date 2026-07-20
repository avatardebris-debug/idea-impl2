"""Unit tests for Grok Build CLI adapter (mocked subprocess)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pipeline.engines.base import EngineResult
from pipeline.engines.classic import ClassicEngine
from pipeline.engines.grok_build import (
    build_command,
    main as grok_main,
    phase_log_path,
    run_phase_step,
)
from pipeline.engines.selection import (
    ENGINE_CLASSIC,
    ENGINE_GROK_BUILD,
    get_project_engine,
    resolve_seed_engine,
)


def test_build_command_placeholders(tmp_path: Path):
    ws = tmp_path / "ws"
    ws.mkdir()
    pf = tmp_path / "prompt.md"
    pf.write_text("hi", encoding="utf-8")
    log = tmp_path / "out.log"
    cmd, err = build_command(
        workspace=ws,
        prompt_file=pf,
        skill="implement",
        log_file=log,
        cmd_template="tool --ws {workspace} --p {prompt_file} --s {skill} --l {log_file}",
    )
    assert not err
    assert str(ws.resolve()) in cmd
    assert str(pf.resolve()) in cmd
    assert "implement" in cmd
    assert str(log.resolve()) in cmd


def test_build_command_bad_placeholder(tmp_path: Path):
    ws = tmp_path / "ws"
    ws.mkdir()
    log = tmp_path / "out.log"
    cmd, err = build_command(
        workspace=ws,
        prompt_file=None,
        skill="implement",
        log_file=log,
        cmd_template="tool --bad {unknown_ph}",
    )
    assert err
    assert "unknown_ph" in err or "format error" in err
    assert cmd == ""


def test_dry_run_writes_log_no_subprocess(tmp_path: Path, monkeypatch):
    proj = tmp_path / "proj"
    (proj / "workspace").mkdir(parents=True)
    spy = MagicMock()
    monkeypatch.setenv("GROK_BUILD_CMD", "echo hi")
    result = run_phase_step(
        "proj",
        1,
        "implement",
        project_dir=proj,
        dry_run=True,
        subprocess_run=spy,
    )
    assert result.success
    assert result.dry_run
    spy.assert_not_called()
    log = phase_log_path(proj, 1, "implement")
    assert log.is_file()
    text = log.read_text(encoding="utf-8")
    assert "dry-run" in text.lower() or "dry_run" in text
    assert "command:" in text.lower() or "echo hi" in text or "GROK" in text


def test_missing_cmd_is_hard_failure(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("GROK_BUILD_CMD", raising=False)
    monkeypatch.delenv("GROK_BUILD_DRY_RUN", raising=False)
    proj = tmp_path / "proj"
    (proj / "workspace").mkdir(parents=True)
    monkeypatch.setenv("GROK_BUILD_BACKEND", "cli")
    monkeypatch.delenv("GROK_BUILD_CMD", raising=False)
    result = run_phase_step(
        "proj",
        2,
        "review",
        project_dir=proj,
        dry_run=False,
        cmd_template=None,
    )
    # When backend=cli and CMD unset, hard fail (no pipeline_llm fallback)
    assert result.success is False
    assert result.exit_code == 127
    assert "GROK_BUILD_CMD" in (result.error or "")


def test_subprocess_success(tmp_path: Path, monkeypatch):
    proj = tmp_path / "proj"
    (proj / "workspace").mkdir(parents=True)
    monkeypatch.setenv("GROK_BUILD_CMD", "true")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "ok\n"
    mock_proc.stderr = ""
    spy = MagicMock(return_value=mock_proc)

    result = run_phase_step(
        "proj",
        1,
        "implement",
        project_dir=proj,
        dry_run=False,
        cmd_template="mycli {skill} {workspace}",
        subprocess_run=spy,
        timeout_s=30,
    )
    assert result.success
    assert result.exit_code == 0
    spy.assert_called_once()
    assert Path(result.log_path).is_file()


def test_subprocess_timeout(tmp_path: Path):
    import subprocess as sp

    proj = tmp_path / "proj"
    (proj / "workspace").mkdir(parents=True)

    def boom(*a, **k):
        raise sp.TimeoutExpired(cmd="x", timeout=1)

    result = run_phase_step(
        "proj",
        1,
        "debug",
        project_dir=proj,
        dry_run=False,
        cmd_template="sleep 999",
        subprocess_run=boom,
        timeout_s=1,
    )
    assert not result.success
    assert result.exit_code == 124
    assert "timeout" in (result.error or "").lower()


def test_classic_engine_passthrough():
    eng = ClassicEngine()
    r = eng.run_phase_step("s", 1, "implement")
    assert r.success
    assert eng.name == "classic"
    assert "runner" in r.summary.lower() or "classic" in r.summary.lower()


def test_get_project_engine_default():
    assert get_project_engine({}) == ENGINE_CLASSIC
    assert get_project_engine({"engine": "grok_build"}) == ENGINE_GROK_BUILD
    assert get_project_engine({"engine": "CLASSIC"}) == ENGINE_CLASSIC


def test_resolve_seed_engine_env(monkeypatch):
    monkeypatch.setenv("PIPELINE_ENGINE", "grok_build")
    monkeypatch.delenv("PIPELINE_ENGINE_GROK_FRACTION", raising=False)
    assert resolve_seed_engine() == ENGINE_GROK_BUILD
    monkeypatch.setenv("PIPELINE_ENGINE", "classic")
    assert resolve_seed_engine() == ENGINE_CLASSIC


def test_resolve_seed_engine_fraction(monkeypatch):
    monkeypatch.delenv("PIPELINE_ENGINE", raising=False)
    monkeypatch.setenv("PIPELINE_ENGINE_GROK_FRACTION", "1.0")
    assert resolve_seed_engine() == ENGINE_GROK_BUILD
    monkeypatch.setenv("PIPELINE_ENGINE_GROK_FRACTION", "0")
    assert resolve_seed_engine() == ENGINE_CLASSIC


def test_cli_help():
    with pytest.raises(SystemExit) as ei:
        grok_main(["--help"])
    assert ei.value.code == 0


def test_cli_dry_run(tmp_path: Path, monkeypatch):
    proj = tmp_path / "my_slug"
    (proj / "workspace").mkdir(parents=True)
    monkeypatch.setenv("GROK_BUILD_CMD", "echo test")
    rc = grok_main(
        [
            "--slug",
            "my_slug",
            "--phase",
            "1",
            "--step",
            "implement",
            "--project-dir",
            str(proj),
            "--dry-run",
        ]
    )
    assert rc == 0
    log = proj / "phases" / "phase_1" / "grok_implement.log"
    assert log.is_file()


def test_engine_result_to_dict():
    r = EngineResult(success=True, step="implement", summary="ok")
    d = r.to_dict()
    assert d["success"] is True
    assert d["step"] == "implement"
