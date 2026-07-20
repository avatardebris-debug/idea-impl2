"""Tests for thin field ship + plan adapters."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.engines.field_ship import (
    ensure_field_plan,
    plan_heuristic,
    run_thin_field_ship,
    thin_ship_enabled,
    write_usefulness_report,
)


def _proj(tmp: Path, *, engine: str = "grok_build") -> Path:
    p = tmp / "proj"
    (p / "workspace").mkdir(parents=True)
    (p / "state").mkdir(parents=True)
    (p / "workspace" / "cli.py").write_text(
        "#!/usr/bin/env python3\n"
        "import argparse\n"
        "p=argparse.ArgumentParser()\n"
        "p.parse_args()\n"
        "print('ok')\n",
        encoding="utf-8",
    )
    (p / "state" / "master_plan.md").write_text(
        "# Master Plan\n\n## Goal\nShip a tiny CLI.\n",
        encoding="utf-8",
    )
    (p / "state" / "current_idea.json").write_text(
        json.dumps(
            {
                "title": "tiny cli",
                "status": "complete",
                "phase": 1,
                "total_phases": 1,
                "engine": engine,
                "slug": "proj",
            }
        ),
        encoding="utf-8",
    )
    return p


def test_thin_ship_enabled(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("GROK_BUILD_THIN_SHIP", raising=False)
    assert thin_ship_enabled({"engine": "grok_build"}) is True
    assert thin_ship_enabled({"engine": "classic"}) is False
    monkeypatch.setenv("GROK_BUILD_THIN_SHIP", "0")
    assert thin_ship_enabled({"engine": "grok_build"}) is False


def test_plan_heuristic_writes_tasks(tmp_path: Path):
    p = _proj(tmp_path)
    body = plan_heuristic(p, p / "workspace")
    assert "# Field Tests" in body
    assert "Task P1" in body
    assert "Command:" in body


def test_ensure_field_plan_heuristic(tmp_path: Path, monkeypatch):
    p = _proj(tmp_path)
    monkeypatch.setenv("FIELD_PLAN_ENGINE", "heuristic")
    ok, eng, detail = ensure_field_plan(p, p / "workspace", slug="proj")
    assert ok
    assert eng == "heuristic"
    assert (p / "phases/ship/field_tests.md").is_file()


def test_run_thin_field_ship_heuristic_pass(tmp_path: Path, monkeypatch):
    p = _proj(tmp_path)
    # Help exits 0 with argparse even without args if no required — use py_compile friendly
    monkeypatch.setenv("FIELD_PLAN_ENGINE", "heuristic")
    monkeypatch.setenv("GROK_BUILD_THIN_SHIP", "1")
    state = json.loads((p / "state/current_idea.json").read_text(encoding="utf-8"))
    # Pre-write a reliable field plan so we don't depend on --help behavior
    ship = p / "phases/ship"
    ship.mkdir(parents=True)
    py = __import__("sys").executable
    (ship / "field_tests.md").write_text(
        f"""# Field Tests

## Product tests
- [ ] Task P1: syntax
  - Kind: product
  - Command: `{py} -m py_compile cli.py`
  - Expect: exit 0

## Integration tests
- [ ] Task I1: import
  - Kind: integration
  - Command: `{py} -c "import cli; print('IMPORT_OK')"`
  - Expect: IMPORT_OK
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("FIELD_PLAN_ENGINE", "none")
    result = run_thin_field_ship(p, state, slug="proj")
    assert result.ok is True
    assert result.status == "field_proven"
    assert (p / "phases/ship/field_test_results.md").is_file()
    assert (p / "phases/ship/usefulness_report.md").is_file()
    st = json.loads((p / "state/current_idea.json").read_text(encoding="utf-8"))
    assert st["status"] == "field_proven"


def test_usefulness_report(tmp_path: Path):
    p = _proj(tmp_path)
    path = write_usefulness_report(
        p, run_passed=True, passed=3, failed=0, plan_engine="heuristic"
    )
    text = path.read_text(encoding="utf-8")
    assert "field_fitness" in text
    assert "goal_fitness: not_evaluated" in text
