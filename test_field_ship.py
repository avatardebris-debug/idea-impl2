"""Tests for thin field ship + plan adapters."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.engines.field_repair import classify_field_failure
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
    monkeypatch.delenv("FIELD_SHIP_ALLOW_CLASSIC", raising=False)
    monkeypatch.delenv("FIELD_SHIP_BULK", raising=False)
    assert thin_ship_enabled({"engine": "grok_build"}) is True
    assert thin_ship_enabled({"engine": "classic"}) is False
    monkeypatch.setenv("FIELD_SHIP_ALLOW_CLASSIC", "1")
    assert thin_ship_enabled({"engine": "classic"}) is True
    monkeypatch.setenv("GROK_BUILD_THIN_SHIP", "0")
    monkeypatch.delenv("FIELD_SHIP_ALLOW_CLASSIC", raising=False)
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
    monkeypatch.setenv("FIELD_SHIP_REPAIR", "0")
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
    assert (p / "state/capability_claims.md").is_file()
    assert "Outcome class" in (p / "state/capability_claims.md").read_text(
        encoding="utf-8"
    )


def test_classify_field_failure_bad_plan():
    md = "## P1: x — FAIL\nNo module named foo\n## Verdict: FAIL\n"
    assert classify_field_failure(md) == "bad_plan"


def test_classify_field_failure_pytest():
    md = "## I1: Pytest suite — FAIL\n27 failed, 183 passed\n## Verdict: FAIL\n"
    assert classify_field_failure(md) == "product_bug"


def test_write_field_evaluation_report(tmp_path: Path):
    from pipeline.engines.field_repair import write_field_evaluation_report

    p = _proj(tmp_path)
    path = write_field_evaluation_report(
        p,
        slug="proj",
        classification="product_bug",
        steps_run=["field_fail_repair", "field_systematic_debug", "field_code_review"],
        final_passed=2,
        final_failed=1,
        results_md="## I1: Pytest — FAIL\n",
        invoke_errors=[],
    )
    text = path.read_text(encoding="utf-8")
    assert "repair exhausted" in text.lower() or "Repair steps run" in text
    assert "Recommended next steps" in text
    assert "ship_insufficient" in text


def test_repair_chain_max_and_evaluation(tmp_path: Path, monkeypatch):
    """Mocked repair chain: max steps then evaluation report."""
    from pipeline.engines import field_repair as fr
    from pipeline.engines.base import EngineResult

    p = _proj(tmp_path)
    (p / "phases" / "ship").mkdir(parents=True)
    (p / "phases" / "ship" / "field_tests.md").write_text(
        "# Field Tests\n- [ ] Task P1: x\n  - Kind: product\n"
        "  - Command: `echo hi`\n  - Expect: exit 0\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FIELD_SHIP_REPAIR", "1")
    monkeypatch.setenv("FIELD_SHIP_REPAIR_MAX", "2")

    class FakeRun:
        def __init__(self):
            self.passed = 0
            self.failed = 1
            self.all_passed = False

    calls: list[str] = []

    def fake_invoke(step, **kwargs):
        calls.append(step)
        return EngineResult(success=True, step=step, exit_code=0)

    def fake_rerun(project_dir, workspace):
        return FakeRun(), "## P1 — FAIL\n## Verdict: FAIL\n"

    monkeypatch.setattr(fr, "_invoke_repair_step", fake_invoke)
    monkeypatch.setattr(fr, "_rerun_field", fake_rerun)

    out = fr.run_field_repair_chain(p, p / "workspace", slug="proj", phase=1)
    assert out.passed is False
    assert len(out.steps_run) == 2
    assert (p / "phases/ship/field_evaluation.md").is_file()
    assert "field_fail_repair" in calls


def test_field_systematic_debug_prompt_injects_skill(tmp_path: Path, monkeypatch):
    from pipeline.engines.grok_build import render_prompt_for_phase

    sk = tmp_path / "skills" / "systematic-debugging"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        "---\nname: systematic-debugging\n---\n\nUNIQUE_SKILL_MARKER_XYZ\n"
        "Root Cause Investigation required.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [tmp_path / "skills"],
    )
    p = _proj(tmp_path)
    out, err = render_prompt_for_phase(
        "field_systematic_debug",
        project_dir=p,
        workspace=p / "workspace",
        slug="proj",
        phase=1,
    )
    assert err == "" or err is None or not err
    text = out.read_text(encoding="utf-8")
    assert "UNIQUE_SKILL_MARKER_XYZ" in text
    assert "{systematic_debugging_skill}" not in text
