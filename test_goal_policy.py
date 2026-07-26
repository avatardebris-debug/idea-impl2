"""Tests for thin goal compose policy + durable goal_trace."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.goal_policy import (
    POLICY_BUILD,
    POLICY_COMPOSE,
    POLICY_MCP,
    POLICY_RESEARCH,
    POLICY_REUSE,
    POLICY_YIELD,
    classify_goal_branch,
    execute_policy,
)


def _reload(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass


def test_classify_research_hermes():
    d = classify_goal_branch(
        branch_type="hermes_task",
        text="research papers",
        hermes_prompt="go research",
    )
    assert d.policy == POLICY_RESEARCH


def test_classify_reuse_from_router_hit():
    d = classify_goal_branch(
        branch_type="software",
        text="use the tool",
        route_hits=[{"slug": "foo_cli", "requires_ok": True, "kind": "project"}],
    )
    assert d.policy == POLICY_REUSE
    assert d.capability_slug == "foo_cli"


def test_classify_compose_from_connector_router():
    d = classify_goal_branch(
        branch_type="software",
        text="bridge",
        route_hits=[
            {"slug": "movie_chain_n8n", "requires_ok": True, "kind": "connector"}
        ],
    )
    assert d.policy == POLICY_COMPOSE
    assert d.connector_slug == "movie_chain_n8n"


def test_classify_build_when_no_hits():
    d = classify_goal_branch(
        branch_type="software",
        text="brand new idea with no tools",
        route_hits=[],
    )
    assert d.policy == POLICY_BUILD


def test_classify_compose_from_connector_yaml(tmp_path, monkeypatch):
    _reload(tmp_path, monkeypatch)
    conn = tmp_path / "workflows" / "connectors"
    conn.mkdir(parents=True)
    (conn / "bridge_ab.yaml").write_text(
        "\n".join(
            [
                "slug: bridge_ab",
                "title: bridge",
                "kind: connector",
                "status: draft",
                "backend: native",
                "requires:",
                "  - proj_a",
                "  - proj_b",
                "steps:",
                "  - id: a",
                "    type: capability",
                "    capability: proj_a",
                "    save_as: a",
            ]
        ),
        encoding="utf-8",
    )
    d = classify_goal_branch(
        branch_type="software",
        text="connect proj_a and proj_b to serve process",
        requires=["proj_a", "proj_b"],
        route_hits=[],
    )
    assert d.policy == POLICY_COMPOSE
    assert d.connector_slug == "bridge_ab"


def test_execute_build_writes_goal_trace(tmp_path, monkeypatch):
    _reload(tmp_path, monkeypatch)
    monkeypatch.delenv("KEEP_GOAL_TRACES", raising=False)
    d = classify_goal_branch(
        branch_type="software",
        text="need a new brick",
        route_hits=[],
    )
    assert d.policy == POLICY_BUILD
    out = execute_policy(d, goal_text="need a new brick", branch_id="b1")
    assert out["status"] == "build_needed"
    assert out.get("goal_id")
    tr_path = tmp_path / "goal_traces" / f"{out['goal_id']}.json"
    assert tr_path.is_file()
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    assert tr["schema"] == "goal_trace.v1"
    assert tr["status"] == "deeper_work_needed"


def test_keep_goal_traces_off_skips_write(tmp_path, monkeypatch):
    """KEEP_GOAL_TRACES=0: execute still returns status but does not write trace files."""
    _reload(tmp_path, monkeypatch)
    monkeypatch.setenv("KEEP_GOAL_TRACES", "0")
    d = classify_goal_branch(
        branch_type="software",
        text="need a new brick",
        route_hits=[],
    )
    out = execute_policy(d, goal_text="need a new brick", branch_id="b1")
    assert out["status"] == "build_needed"
    assert out.get("goal_id")
    traces = tmp_path / "goal_traces"
    if traces.is_dir():
        assert list(traces.glob("*.json")) == []
        assert not (traces / "traces.jsonl").is_file()
    else:
        assert not traces.exists()


def test_classify_mcp_from_router_kind():
    d = classify_goal_branch(
        branch_type="software",
        text="expose as tools",
        route_hits=[
            {"slug": "foo_cli", "requires_ok": True, "kind": "mcp"},
        ],
    )
    assert d.policy == POLICY_MCP
    assert d.capability_slug == "foo_cli"


def test_execute_mcp_enqueues_job(tmp_path, monkeypatch):
    _reload(tmp_path, monkeypatch)
    monkeypatch.delenv("KEEP_GOAL_TRACES", raising=False)
    d = classify_goal_branch(
        branch_type="software",
        text="wrap foo_cli as mcp",
        route_hits=[
            {"slug": "foo_cli", "requires_ok": True, "kind": "project"},
        ],
    )
    assert d.policy == POLICY_MCP
    assert d.capability_slug == "foo_cli"
    out = execute_policy(d, goal_text="wrap foo_cli as mcp", branch_id="b_mcp1")
    assert out["status"] == "mcp_enqueued"
    job_path = Path(out["job_path"])
    assert job_path.is_file()
    job = json.loads(job_path.read_text(encoding="utf-8"))
    assert job["schema"] == "mcp_factory_job.v1"
    assert job["capability_slug"] == "foo_cli"
    assert job["status"] == "pending"
    assert job.get("goal_id") == "b_mcp1"
    tr_path = tmp_path / "goal_traces" / f"{out['goal_id']}.json"
    assert tr_path.is_file()
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    assert tr["status"] == "deeper_work_needed"
    assert tr.get("oracle", {}).get("name") == "mcp_factory_enqueued"
