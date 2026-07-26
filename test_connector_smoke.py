"""Tests for connector smoke runner + process oracle + goal_trace."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from pipeline.connector_smoke import (
    PROCESS_ORACLE_SLUG,
    run_connector_smoke,
    run_process_oracle,
    structural_smoke_connector,
    write_smoke_report,
)
from pipeline.workflow_schema import WorkflowDefinition


def _reload(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass


def _write_connector(root: Path, slug: str, **overrides) -> Path:
    conn = root / "workflows" / "connectors"
    conn.mkdir(parents=True, exist_ok=True)
    doc = {
        "slug": slug,
        "title": slug,
        "kind": "connector",
        "status": "draft",
        "backend": "native",
        "purpose": "test bridge",
        "requires": ["proj_a", "proj_b"],
        "steps": [
            {
                "id": "proj_a",
                "type": "capability",
                "capability": "proj_a",
                "args": "--help",
                "save_as": "proj_a",
            },
            {
                "id": "proj_b",
                "type": "capability",
                "capability": "proj_b",
                "args": "--help",
                "save_as": "proj_b",
                "when": "{{ steps.proj_a.ok }}",
            },
        ],
    }
    doc.update(overrides)
    path = conn / f"{slug}.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return path


def test_process_oracle_goal_proven(tmp_path, monkeypatch):
    _reload(tmp_path, monkeypatch)
    work = tmp_path / "oracle_work"
    case = run_process_oracle(work_dir=work)
    assert case.mode == "process_oracle"
    assert case.hard is True
    assert case.ok is True
    assert case.status == "goal_proven"
    assert case.oracle and case.oracle.get("pass") is True
    assert case.goal_id
    # artifacts
    art = work / "artifacts"
    assert (art / "step_a.json").is_file()
    assert (art / "step_b.json").is_file()
    assert (art / "process_receipt.json").is_file()
    receipt = json.loads((art / "process_receipt.json").read_text(encoding="utf-8"))
    assert receipt["process"] == PROCESS_ORACLE_SLUG
    assert receipt["ok"] is True
    # goal_trace written
    assert (tmp_path / "goal_traces" / f"{case.goal_id}.json").is_file()
    tr = json.loads((tmp_path / "goal_traces" / f"{case.goal_id}.json").read_text(encoding="utf-8"))
    assert tr["schema"] == "goal_trace.v1"
    assert tr["status"] == "goal_proven"
    assert tr["train_weight"] == 4.0
    assert any(e.get("type") == "tool" for e in tr["events"])


def test_structural_smoke_ok_and_missing_projects(tmp_path, monkeypatch):
    _reload(tmp_path, monkeypatch)
    _write_connector(tmp_path, "bridge_ab")
    # create only one project dir
    (tmp_path / "projects" / "proj_a").mkdir(parents=True)

    wf = WorkflowDefinition.from_yaml_file(
        tmp_path / "workflows" / "connectors" / "bridge_ab.yaml"
    )
    case = structural_smoke_connector(wf)
    assert case.ok is True  # schema hard-pass
    assert case.status == "deeper_work_needed"  # missing proj_b
    assert case.goal_id
    assert (tmp_path / "goal_traces" / f"{case.goal_id}.json").is_file()


def test_structural_smoke_bad_step(tmp_path, monkeypatch):
    _reload(tmp_path, monkeypatch)
    _write_connector(
        tmp_path,
        "bad_conn",
        steps=[{"id": "x", "type": "capability", "capability": "", "save_as": "x"}],
        requires=[],
    )
    wf = WorkflowDefinition.from_yaml_file(
        tmp_path / "workflows" / "connectors" / "bad_conn.yaml"
    )
    case = structural_smoke_connector(wf)
    assert case.ok is False
    assert case.status == "goal_failed"


def test_run_connector_smoke_suite(tmp_path, monkeypatch):
    _reload(tmp_path, monkeypatch)
    _write_connector(tmp_path, "bridge_ab")
    (tmp_path / "projects" / "proj_a").mkdir(parents=True)
    (tmp_path / "projects" / "proj_b").mkdir(parents=True)

    report = run_connector_smoke()
    assert report.ok is True
    modes = {c.mode for c in report.cases}
    assert "structural" in modes
    assert "process_oracle" in modes
    paths = write_smoke_report(report)
    assert paths["markdown"].is_file()
    assert paths["json"].is_file()
    md = paths["markdown"].read_text(encoding="utf-8")
    assert "PASS" in md
    assert "process_oracle" in md


def test_oracle_only(tmp_path, monkeypatch):
    _reload(tmp_path, monkeypatch)
    report = run_connector_smoke(oracle_only=True)
    assert report.ok is True
    assert len(report.cases) == 1
    assert report.cases[0].mode == "process_oracle"
