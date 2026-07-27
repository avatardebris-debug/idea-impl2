"""Tests for goal graph store paths and graph.v1 compile/critique/persist."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_graphs_and_mcps_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.paths import get_pipeline_dir, graphs_dir, mcps_dir

    reload_pipeline_dir()
    root = get_pipeline_dir()
    assert root == pipeline.resolve()
    assert graphs_dir() == root / "graphs"
    assert mcps_dir() == root / "mcps"
    assert graphs_dir().name == "graphs"
    assert mcps_dir().name == "mcps"


def test_compile_and_critique_minimal() -> None:
    from pipeline.goal_graph import (
        DEFAULT_ORACLE,
        GRAPH_SCHEMA,
        compile_goal_graph,
        critique_graph,
    )

    g = compile_goal_graph(
        "use foo_cli to export",
        goal_id="g_min",
        route_hits=[
            {
                "slug": "foo_cli",
                "kind": "project",
                "title": "Foo CLI",
                "requires_ok": True,
            }
        ],
    )
    assert g["schema"] == GRAPH_SCHEMA
    assert g["goal_id"] == "g_min"
    assert g["goal_text"] == "use foo_cli to export"
    assert len(g["nodes"]) == 1
    node = g["nodes"][0]
    assert node["slug"] == "foo_cli"
    assert node["kind"] == "software"  # project → software
    assert node["status"] == "verified"
    assert node["oracle"] == DEFAULT_ORACLE
    assert node["id"] == "n1"
    assert g["edges"] == []
    assert g["critique"]["ok"] is True
    assert g["status"] == "executable"

    c = critique_graph(g)
    assert c["ok"] is True
    assert c["issues"] == []

    # multi-node linear control edges
    g2 = compile_goal_graph(
        "chain a then b",
        goal_id="g_chain",
        route_hits=[
            {"slug": "cap_a", "kind": "software", "requires_ok": True},
            {"slug": "cap_b", "kind": "connector", "requires_ok": True},
        ],
    )
    assert len(g2["nodes"]) == 2
    assert len(g2["edges"]) == 1
    assert g2["edges"][0] == {"from": "n1", "to": "n2", "kind": "control"}

    # missing status fails critique
    g3 = compile_goal_graph(
        "need missing thing",
        goal_id="g_miss",
        route_hits=[
            {"slug": "gone_tool", "kind": "software", "status": "missing"},
        ],
    )
    c3 = critique_graph(g3)
    assert c3["ok"] is False
    assert any("missing" in i.lower() for i in c3["issues"])
    assert g3["status"] == "blocked"

    # executable kind without oracle fails critique
    bare = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_no_oracle",
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": "x",
                "label": "x",
                "status": "draft",
                "oracle": "",
                "requires": [],
            }
        ],
        "edges": [],
    }
    c4 = critique_graph(bare)
    assert c4["ok"] is False
    assert any("oracle" in i.lower() for i in c4["issues"])

    # max_nodes cap
    many = [
        {"slug": f"s{i}", "kind": "software", "requires_ok": True} for i in range(15)
    ]
    g5 = compile_goal_graph("many", goal_id="g_cap", route_hits=many, max_nodes=10)
    assert len(g5["nodes"]) == 10
    assert len(g5["edges"]) == 9


def test_save_load_roundtrip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.goal_graph import compile_goal_graph, load_graph, save_graph
    from pipeline.paths import graphs_dir

    reload_pipeline_dir()

    g = compile_goal_graph(
        "persist me",
        goal_id="g_round",
        route_hits=[
            {"slug": "tool_x", "kind": "software", "requires_ok": True},
        ],
    )
    path = save_graph(g)
    assert path == graphs_dir() / "g_round.json"
    assert path.is_file()

    loaded = load_graph("g_round")
    assert loaded is not None
    assert loaded["schema"] == g["schema"]
    assert loaded["goal_id"] == "g_round"
    assert loaded["goal_text"] == "persist me"
    assert len(loaded["nodes"]) == 1
    assert loaded["nodes"][0]["slug"] == "tool_x"
    assert loaded["critique"]["ok"] is True

    assert load_graph("does_not_exist") is None


def test_plan_factory_actions_enqueues_missing_mcp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.goal_graph import GRAPH_SCHEMA, plan_factory_actions
    from pipeline.mcp_queue import list_pending, load_job, queue_dir

    reload_pipeline_dir()

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_mcp_miss",
        "goal_text": "need mcp wrap for foo_cli",
        "nodes": [
            {
                "id": "n1",
                "kind": "mcp",
                "slug": "mcp_foo_cli",
                "label": "mcp_foo_cli",
                "status": "missing",
                "oracle": "capability_invoke_help",
                "requires": [],
            },
            {
                "id": "n2",
                "kind": "software",
                "slug": "gone_tool",
                "label": "gone_tool",
                "status": "missing",
                "oracle": "capability_invoke_help",
                "requires": [],
            },
            {
                "id": "n3",
                "kind": "mcp",
                "slug": "bar_tool",
                "label": "bar_tool",
                "status": "verified",
                "oracle": "capability_invoke_help",
                "requires": [],
            },
        ],
        "edges": [],
        "critique": {"ok": False, "issues": ["node n1 status=missing"]},
    }

    out = plan_factory_actions(graph)
    assert len(out["enqueued"]) == 1
    assert out["issues"] == []
    assert len(out["software_handoffs"]) == 1
    assert out["software_handoffs"][0]["slug"] == "gone_tool"

    pending = list_pending()
    assert len(pending) == 1
    job = load_job(pending[0])
    assert job["schema"] == "mcp_factory_job.v1"
    assert job["capability_slug"] == "foo_cli"  # mcp_ prefix stripped
    assert job["status"] == "pending"
    assert job.get("goal_id") == "g_mcp_miss"
    assert pending[0].is_file()
    assert pending[0].parent == queue_dir() / "pending"

    handoff_path = pipeline / "metrics" / "goal_build_handoffs.jsonl"
    assert handoff_path.is_file()
    lines = [
        ln for ln in handoff_path.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    assert len(lines) == 1
    row = __import__("json").loads(lines[0])
    assert row["slug"] == "gone_tool"
    assert row["policy"] == "build"


def test_compile_graph_from_smoked_mcps(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    monkeypatch.setenv("KEEP_GOAL_TRACES", "1")

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import (
        MCP_ORACLE,
        compile_graph_from_smoked_mcps,
        critique_graph,
        save_graph,
    )
    from pipeline.mcp_factory import smoke_mcp, wrap_capability_as_mcp

    wrap_capability_as_mcp("util_a", force=True)
    wrap_capability_as_mcp("util_b", force=True)
    assert smoke_mcp("mcp_util_a", require_invoke=False)["ok"]
    assert smoke_mcp("mcp_util_b", require_invoke=False)["ok"]

    g = compile_graph_from_smoked_mcps(
        goal_id="mcp_fixture",
        goal_text="use smoked utility MCPs",
        mcp_slugs=["mcp_util_a", "mcp_util_b"],
    )
    assert g["schema"] == "graph.v1"
    assert g.get("source") == "smoked_mcps"
    slugs = {n["slug"] for n in g["nodes"]}
    assert "mcp_util_a" in slugs
    assert "mcp_util_b" in slugs
    for n in g["nodes"]:
        if n["kind"] == "mcp":
            assert n["status"] == "verified"
            o = n.get("oracle")
            name = o.get("name") if isinstance(o, dict) else o
            assert name == MCP_ORACLE
    crit = critique_graph(g)
    assert crit["ok"] is True, crit
    save_graph(g)


def test_smoke_graph_all_verified_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """P3: all resolved executable nodes with local assets → smoke_pass."""
    import json

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    monkeypatch.setenv("KEEP_GOAL_TRACES", "1")

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import (
        DEFAULT_ORACLE,
        GRAPH_SCHEMA,
        MCP_ORACLE,
        critique_graph,
        load_graph,
        save_graph,
        smoke_graph,
    )
    from pipeline.mcp_factory import smoke_mcp, wrap_capability_as_mcp
    from pipeline.paths import connectors_dir, projects_dir

    # MCP asset
    wrap_capability_as_mcp("smoke_util", force=True)
    assert smoke_mcp("mcp_smoke_util", require_invoke=False)["ok"]

    # Software project asset
    soft = projects_dir() / "tool_alpha"
    (soft / "state").mkdir(parents=True)
    (soft / "state" / "current_idea.json").write_text(
        json.dumps(
            {
                "title": "tool_alpha",
                "status": "field_proven",
                "phase": 2,
                "total_phases": 2,
            }
        ),
        encoding="utf-8",
    )

    # Connector YAML asset
    cdir = connectors_dir()
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "bridge_alpha.yaml").write_text(
        "slug: bridge_alpha\nkind: connector\nsteps:\n  - id: s1\n    type: noop\n",
        encoding="utf-8",
    )

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_smoke_ok",
        "goal_text": "compose smoked tools",
        "status": "executable",
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": "tool_alpha",
                "label": "tool_alpha",
                "status": "verified",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            },
            {
                "id": "n2",
                "kind": "mcp",
                "slug": "mcp_smoke_util",
                "label": "mcp_smoke_util",
                "status": "verified",
                "oracle": MCP_ORACLE,
                "requires": [],
            },
            {
                "id": "n3",
                "kind": "connector",
                "slug": "bridge_alpha",
                "label": "bridge_alpha",
                "status": "verified",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            },
        ],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    assert critique_graph(graph)["ok"] is True

    report = smoke_graph(graph, mutate=True)
    assert report["blocked"] is False
    assert report["smoke_pass"] is True
    assert report["ok"] is True
    assert report["issues"] == []
    assert len(report["node_results"]) == 3
    assert all(r["ok"] for r in report["node_results"])
    assert graph["smoke_pass"] is True
    assert graph["status"] == "smoke_pass"
    assert graph.get("smoked_at")

    path = save_graph(graph)
    assert path.is_file()
    loaded = load_graph("g_smoke_ok")
    assert loaded is not None
    assert loaded["smoke_pass"] is True
    assert loaded["status"] == "smoke_pass"


def test_smoke_graph_missing_node_blocked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """P3: status=missing nodes → not smoke_pass (blocked)."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, smoke_graph

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_smoke_miss",
        "goal_text": "need missing",
        "status": "blocked",
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": "gone_tool",
                "label": "gone",
                "status": "missing",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            }
        ],
        "edges": [],
        "critique": {"ok": False, "issues": ["node n1 (gone_tool) status=missing"]},
    }
    report = smoke_graph(graph, mutate=True)
    assert report["smoke_pass"] is False
    assert report["ok"] is False
    assert report["blocked"] is True
    assert graph["smoke_pass"] is False
    # critique fails first path (re_critique default)
    assert any("missing" in i.lower() or "critique" in i.lower() for i in report["issues"])
    assert report.get("block_reason") == "critique"
    # status stays blocked (already non-executable)
    assert graph.get("status") == "blocked"


def test_smoke_graph_missing_nodes_branch_without_recritique(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """re_critique=False + stale critique ok forces dedicated missing_nodes block."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, smoke_graph

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_smoke_miss_branch",
        "goal_text": "stale critique",
        "status": "executable",
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": "gone_tool",
                "label": "gone",
                "status": "missing",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            }
        ],
        "edges": [],
        # Stale: claims ok despite missing node
        "critique": {"ok": True, "issues": []},
    }
    report = smoke_graph(graph, mutate=True, re_critique=False)
    assert report["smoke_pass"] is False
    assert report["blocked"] is True
    assert report.get("block_reason") == "missing_nodes"
    assert any("missing" in i.lower() for i in report["issues"])
    assert graph["status"] == "smoke_failed"
    assert graph["smoke_pass"] is False


def test_smoke_graph_software_empty_dir_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Empty projects/{slug}/ without state is not a software smoke pass."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, smoke_graph
    from pipeline.paths import projects_dir

    (projects_dir() / "empty_proj").mkdir(parents=True)
    # no state/current_idea.json

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_empty_dir",
        "goal_text": "empty dir only",
        "status": "executable",
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": "empty_proj",
                "label": "empty",
                "status": "verified",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            }
        ],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    report = smoke_graph(graph, mutate=True)
    assert report["smoke_pass"] is False
    assert report["blocked"] is False
    assert graph["status"] == "smoke_failed"
    detail = " ".join(r.get("detail") or "" for r in report["node_results"])
    assert "project_dir_no_state" in detail or "verified_but_no_project" in detail


def test_smoke_graph_unsafe_slug_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Path-like slugs are rejected (no join escape)."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, smoke_graph

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_unsafe_slug",
        "goal_text": "bad slug",
        "status": "executable",
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": "../etc",
                "label": "bad",
                "status": "verified",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            }
        ],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    report = smoke_graph(graph, mutate=True)
    assert report["smoke_pass"] is False
    assert any(
        r.get("check") == "slug_safety" or "unsafe" in (r.get("detail") or "")
        for r in report["node_results"]
    )


def test_smoke_graph_dot_slug_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Slug '.' must not resolve to projects_dir itself and false-pass."""
    import json

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, smoke_node
    from pipeline.paths import projects_dir

    # Trap: projects/state/current_idea.json would make '.' look like project_state
    trap = projects_dir() / "state"
    trap.mkdir(parents=True)
    (trap / "current_idea.json").write_text(
        json.dumps({"status": "complete"}), encoding="utf-8"
    )

    r = smoke_node(
        {
            "id": "n1",
            "kind": "software",
            "slug": ".",
            "label": "dot",
            "status": "verified",
            "oracle": DEFAULT_ORACLE,
            "requires": [],
        }
    )
    assert r.get("ok") is False
    assert r.get("check") == "slug_safety" or "unsafe" in (r.get("detail") or "")


def test_smoke_graph_software_without_asset_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Verified software node with no project/registry → smoke_failed."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, smoke_graph

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_smoke_soft_miss",
        "goal_text": "ghost software",
        "status": "executable",
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": "ghost_cli",
                "label": "ghost",
                "status": "verified",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            }
        ],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    report = smoke_graph(graph, mutate=True)
    assert report["smoke_pass"] is False
    assert report["blocked"] is False
    assert graph["status"] == "smoke_failed"
    assert any("ghost_cli" in i for i in report["issues"])


def test_smoke_graph_mcp_not_smoked_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """MCP node without smoke → fail (is_mcp_smoked false)."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import MCP_ORACLE, GRAPH_SCHEMA, smoke_graph
    from pipeline.mcp_factory import wrap_capability_as_mcp

    # wrap only — no smoke_mcp
    wrap_capability_as_mcp("raw_cap", force=True)

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_mcp_raw",
        "goal_text": "unsmoked mcp",
        "status": "executable",
        "nodes": [
            {
                "id": "n1",
                "kind": "mcp",
                "slug": "mcp_raw_cap",
                "label": "mcp_raw_cap",
                "status": "verified",
                "oracle": MCP_ORACLE,
                "requires": [],
            }
        ],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    report = smoke_graph(graph, mutate=True)
    assert report["smoke_pass"] is False
    assert report["blocked"] is False
    assert any(
        r.get("slug") == "mcp_raw_cap" and not r.get("ok") for r in report["node_results"]
    )
    # Mutation mirrors software-fail path
    assert graph["smoke_pass"] is False
    assert graph["status"] == "smoke_failed"
    failed = (graph.get("smoke_report") or {}).get("failed") or []
    assert "mcp_raw_cap" in failed


def test_smoke_graph_mcp_invoke_oracle_and_revoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """MCP honesty: presence pass; failed invoke_report fails; revoke fails."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import MCP_ORACLE, GRAPH_SCHEMA, smoke_graph, smoke_node
    from pipeline.mcp_factory import (
        revoke_mcp,
        smoke_mcp,
        wrap_capability_as_mcp,
    )
    from pipeline.paths import mcps_dir

    wrap_capability_as_mcp("honest_cap", force=True)
    # Soft smoke → presence only (no durable failed invoke_report)
    assert smoke_mcp("mcp_honest_cap", require_invoke=False)["ok"] is True

    node = {
        "id": "n1",
        "kind": "mcp",
        "slug": "mcp_honest_cap",
        "label": "mcp_honest_cap",
        "status": "verified",
        "oracle": MCP_ORACLE,
        "requires": [],
    }
    r_presence = smoke_node(node)
    assert r_presence["ok"] is True
    assert r_presence.get("check") == "is_mcp_smoked"
    assert r_presence.get("presence_only") is True

    graph_ok = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_mcp_honest_ok",
        "goal_text": "smoked presence mcp",
        "status": "executable",
        "nodes": [dict(node)],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    rep_ok = smoke_graph(graph_ok, mutate=True)
    assert rep_ok["smoke_pass"] is True, rep_ok

    # Failed invoke oracle on disk → graph smoke fails
    inv_path = mcps_dir() / "mcp_honest_cap" / "invoke_report.json"
    inv_path.write_text(
        json.dumps(
            {
                "schema": "mcp_invoke_report.v1",
                "ok": False,
                "mcp_slug": "mcp_honest_cap",
                "args": "--help",
                "require_invoke": True,
                "ts": "2026-01-01T00:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    r_inv = smoke_node(node)
    assert r_inv["ok"] is False
    assert r_inv.get("check") == "invoke_oracle"

    graph_fail = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_mcp_honest_inv",
        "goal_text": "failed invoke mcp",
        "status": "executable",
        "nodes": [dict(node)],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    rep_fail = smoke_graph(graph_fail, mutate=True)
    assert rep_fail["smoke_pass"] is False
    assert graph_fail["status"] == "smoke_failed"

    # Successful invoke_report → pass via invoke-oracle check
    inv_path.write_text(
        json.dumps(
            {
                "schema": "mcp_invoke_report.v1",
                "ok": True,
                "mcp_slug": "mcp_honest_cap",
                "args": "--help",
                "require_invoke": True,
                "ts": "2026-01-01T00:00:01+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    r_ok_inv = smoke_node(node)
    assert r_ok_inv["ok"] is True
    assert r_ok_inv.get("check") == "invoke_oracle"

    # Revoke → fail even if invoke_report was ok
    revoke_mcp("mcp_honest_cap", reason="graph honesty")
    r_rev = smoke_node(node)
    assert r_rev["ok"] is False
    assert r_rev.get("check") == "revoked"

    graph_rev = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_mcp_honest_rev",
        "goal_text": "revoked mcp",
        "status": "executable",
        "nodes": [dict(node)],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    rep_rev = smoke_graph(graph_rev, mutate=True)
    assert rep_rev["smoke_pass"] is False


def test_smoke_graph_mcp_failed_smoke_and_stale_invoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Ladder: smoke_report.ok=false fails; newer failed smoke beats stale ok invoke."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import MCP_ORACLE, smoke_node
    from pipeline.mcp_factory import smoke_mcp, wrap_capability_as_mcp
    from pipeline.paths import mcps_dir

    wrap_capability_as_mcp("ladder_cap", force=True)
    assert smoke_mcp("mcp_ladder_cap", require_invoke=False)["ok"] is True
    d = mcps_dir() / "mcp_ladder_cap"
    node = {
        "id": "n1",
        "kind": "mcp",
        "slug": "mcp_ladder_cap",
        "label": "mcp_ladder_cap",
        "status": "verified",
        "oracle": MCP_ORACLE,
        "requires": [],
    }

    # (1) only failed smoke_report, no invoke_report → fail check=smoke_report
    if (d / "invoke_report.json").is_file():
        (d / "invoke_report.json").unlink()
    (d / "smoke_report.json").write_text(
        json.dumps(
            {
                "ok": False,
                "mcp_slug": "mcp_ladder_cap",
                "ts": "2026-06-01T00:00:00+00:00",
                "error": "ping failed",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    r1 = smoke_node(node)
    assert r1["ok"] is False
    assert r1.get("check") == "smoke_report"

    # (2) stale ok invoke + newer failed smoke → still fail (Issue 1 regression)
    (d / "invoke_report.json").write_text(
        json.dumps(
            {
                "schema": "mcp_invoke_report.v1",
                "ok": True,
                "mcp_slug": "mcp_ladder_cap",
                "ts": "2026-01-01T00:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (d / "smoke_report.json").write_text(
        json.dumps(
            {
                "ok": False,
                "mcp_slug": "mcp_ladder_cap",
                "ts": "2026-06-01T00:00:00+00:00",
                "error": "later fail",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    r2 = smoke_node(node)
    assert r2["ok"] is False
    assert r2.get("check") == "smoke_report"
    assert r2.get("stale_invoke_superseded") is True


def test_goal_compose_smoke_cli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """CLI smoke --goal-id loads, smokes, saves, exit code matches smoke_pass."""
    import json
    import sys

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, save_graph
    from pipeline.paths import projects_dir

    soft = projects_dir() / "cli_tool"
    (soft / "state").mkdir(parents=True)
    (soft / "state" / "current_idea.json").write_text(
        json.dumps({"status": "complete", "phase": 1, "total_phases": 1}),
        encoding="utf-8",
    )
    save_graph(
        {
            "schema": GRAPH_SCHEMA,
            "goal_id": "cli_smoke_g",
            "goal_text": "cli smoke",
            "status": "executable",
            "nodes": [
                {
                    "id": "n1",
                    "kind": "software",
                    "slug": "cli_tool",
                    "label": "cli_tool",
                    "status": "verified",
                    "oracle": DEFAULT_ORACLE,
                    "requires": [],
                }
            ],
            "edges": [],
            "critique": {"ok": True, "issues": []},
        }
    )

    # Ensure scripts/ is importable via main
    root = pathlib.Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.goal_compose import main as gc_main

    rc = gc_main(["--pipeline-dir", str(pipeline), "smoke", "--goal-id", "cli_smoke_g"])
    assert rc == 0
    loaded = json.loads(
        (pipeline / "graphs" / "cli_smoke_g.json").read_text(encoding="utf-8")
    )
    assert loaded.get("smoke_pass") is True
    assert loaded.get("status") == "smoke_pass"

    # missing node → exit 1
    save_graph(
        {
            "schema": GRAPH_SCHEMA,
            "goal_id": "cli_smoke_bad",
            "goal_text": "bad",
            "status": "blocked",
            "nodes": [
                {
                    "id": "n1",
                    "kind": "software",
                    "slug": "nope",
                    "label": "nope",
                    "status": "missing",
                    "oracle": DEFAULT_ORACLE,
                    "requires": [],
                }
            ],
            "edges": [],
            "critique": {"ok": False, "issues": ["missing"]},
        }
    )
    rc2 = gc_main(
        ["--pipeline-dir", str(pipeline), "smoke", "--goal-id", "cli_smoke_bad"]
    )
    assert rc2 == 1


def _attempt_graph_fixture(
    pipeline: pathlib.Path,
    *,
    goal_id: str,
    status: str,
    slug: str = "att_tool",
    node_status: str = "verified",
    smoke_pass: bool | None = None,
    with_project: bool = False,
) -> None:
    import json

    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, save_graph
    from pipeline.paths import projects_dir

    if with_project:
        soft = projects_dir() / slug
        (soft / "state").mkdir(parents=True, exist_ok=True)
        (soft / "state" / "current_idea.json").write_text(
            json.dumps({"status": "complete", "phase": 1, "total_phases": 1}),
            encoding="utf-8",
        )
    g: dict = {
        "schema": GRAPH_SCHEMA,
        "goal_id": goal_id,
        "goal_text": f"attempt fixture {goal_id}",
        "status": status,
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": slug,
                "label": slug,
                "status": node_status,
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            }
        ],
        "edges": [],
        "critique": {
            "ok": node_status != "missing",
            "issues": [] if node_status != "missing" else [f"node n1 status=missing"],
        },
    }
    if smoke_pass is not None:
        g["smoke_pass"] = smoke_pass
    save_graph(g)


def test_attempt_auto_smoke_fail_closed_no_execute(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """executable + no assets → exit 1; execute_policy not called."""
    import sys

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    _attempt_graph_fixture(
        pipeline,
        goal_id="att_fail",
        status="executable",
        slug="ghost_att",
        with_project=False,
    )

    called: list[str] = []

    def fake_execute(*a, **k):
        called.append("execute")
        return {"status": "ok"}

    monkeypatch.setattr("pipeline.goal_policy.execute_policy", fake_execute)
    monkeypatch.setattr(
        "pipeline.goal_policy.classify_goal_branch",
        lambda **kw: type(
            "D",
            (),
            {
                "policy": "reuse",
                "reason": "test",
                "capability_slug": None,
                "connector_slug": None,
            },
        )(),
    )

    root = pathlib.Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.goal_compose import main as gc_main

    rc = gc_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "attempt",
            "--goal-id",
            "att_fail",
            "--text",
            "try me",
        ]
    )
    assert rc == 1
    assert called == []


def test_attempt_skips_auto_smoke_when_draft(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """draft/blocked/critiqued do not auto-smoke (not over-eager)."""
    import sys

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    _attempt_graph_fixture(
        pipeline, goal_id="att_draft", status="draft", with_project=False
    )

    smoke_calls: list[str] = []
    exec_calls: list[str] = []

    def fake_smoke(graph, **kw):
        smoke_calls.append("smoke")
        return {"smoke_pass": True, "ok": True, "issues": [], "node_results": []}

    def fake_execute(*a, **k):
        exec_calls.append("execute")
        return {"status": "ok"}

    monkeypatch.setattr("pipeline.goal_graph.smoke_graph", fake_smoke)
    # cmd_attempt imports smoke_graph into its local namespace at call time
    monkeypatch.setattr("scripts.goal_compose.smoke_graph", fake_smoke, raising=False)
    monkeypatch.setattr("pipeline.goal_policy.execute_policy", fake_execute)
    monkeypatch.setattr(
        "pipeline.goal_policy.classify_goal_branch",
        lambda **kw: type(
            "D",
            (),
            {
                "policy": "research",
                "reason": "test",
                "capability_slug": None,
                "connector_slug": None,
            },
        )(),
    )

    root = pathlib.Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts import goal_compose as gc_mod

    # Patch where cmd_attempt will look up via from-import inside function
    # cmd_attempt does: from pipeline.goal_graph import ... smoke_graph
    # so patch pipeline.goal_graph.smoke_graph
    monkeypatch.setattr("pipeline.goal_graph.smoke_graph", fake_smoke)

    rc = gc_mod.main(
        [
            "--pipeline-dir",
            str(pipeline),
            "attempt",
            "--goal-id",
            "att_draft",
            "--text",
            "draft goal",
        ]
    )
    assert rc == 0
    assert smoke_calls == []  # not auto-smoked
    assert exec_calls == ["execute"]


def test_attempt_skips_resmoke_when_smoke_pass_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """smoke_pass=True skips re-smoke and proceeds to policy."""
    import sys

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    _attempt_graph_fixture(
        pipeline,
        goal_id="att_done",
        status="smoke_pass",
        smoke_pass=True,
        with_project=True,
    )

    smoke_calls: list[str] = []
    exec_calls: list[str] = []

    def fake_smoke(graph, **kw):
        smoke_calls.append("smoke")
        return {"smoke_pass": True, "ok": True, "issues": [], "node_results": []}

    def fake_execute(*a, **k):
        exec_calls.append("execute")
        return {"status": "ok"}

    monkeypatch.setattr("pipeline.goal_graph.smoke_graph", fake_smoke)
    monkeypatch.setattr("pipeline.goal_policy.execute_policy", fake_execute)
    monkeypatch.setattr(
        "pipeline.goal_policy.classify_goal_branch",
        lambda **kw: type(
            "D",
            (),
            {
                "policy": "reuse",
                "reason": "test",
                "capability_slug": "att_tool",
                "connector_slug": None,
            },
        )(),
    )

    root = pathlib.Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.goal_compose import main as gc_main

    rc = gc_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "attempt",
            "--goal-id",
            "att_done",
            "--text",
            "already smoked",
        ]
    )
    assert rc == 0
    assert smoke_calls == []
    assert exec_calls == ["execute"]


def test_attempt_resmokes_when_smoke_failed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """status=smoke_failed re-runs smoke; pass then execute."""
    import sys

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    _attempt_graph_fixture(
        pipeline,
        goal_id="att_retry",
        status="smoke_failed",
        smoke_pass=False,
        with_project=True,
        slug="retry_tool",
    )

    smoke_calls: list[str] = []
    exec_calls: list[str] = []

    def fake_smoke(graph, **kw):
        smoke_calls.append("smoke")
        graph["smoke_pass"] = True
        graph["status"] = "smoke_pass"
        return {
            "smoke_pass": True,
            "ok": True,
            "issues": [],
            "node_results": [],
            "blocked": False,
        }

    def fake_execute(*a, **k):
        exec_calls.append("execute")
        return {"status": "ok"}

    monkeypatch.setattr("pipeline.goal_graph.smoke_graph", fake_smoke)
    monkeypatch.setattr("pipeline.goal_policy.execute_policy", fake_execute)
    monkeypatch.setattr(
        "pipeline.goal_policy.classify_goal_branch",
        lambda **kw: type(
            "D",
            (),
            {
                "policy": "reuse",
                "reason": "test",
                "capability_slug": "retry_tool",
                "connector_slug": None,
            },
        )(),
    )

    root = pathlib.Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.goal_compose import main as gc_main

    rc = gc_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "attempt",
            "--goal-id",
            "att_retry",
            "--text",
            "retry smoke",
        ]
    )
    assert rc == 0
    assert smoke_calls == ["smoke"]
    assert exec_calls == ["execute"]


def test_attempt_save_graph_failure_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """save_graph failure after smoke → exit 1, no execute_policy."""
    import sys

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    _attempt_graph_fixture(
        pipeline,
        goal_id="att_save_fail",
        status="executable",
        slug="save_tool",
        with_project=True,
    )

    exec_calls: list[str] = []
    n_save = {"n": 0}

    def fake_save(graph):
        n_save["n"] += 1
        # First save is fixture; attempt's post-smoke save should fail.
        # cmd_attempt only calls save after smoke; fixture already on disk.
        raise OSError("simulated disk full")

    def fake_execute(*a, **k):
        exec_calls.append("execute")
        return {"status": "ok"}

    def fake_smoke(graph, **kw):
        graph["smoke_pass"] = True
        graph["status"] = "smoke_pass"
        return {
            "smoke_pass": True,
            "ok": True,
            "issues": [],
            "node_results": [],
            "blocked": False,
        }

    monkeypatch.setattr("pipeline.goal_graph.smoke_graph", fake_smoke)
    monkeypatch.setattr("pipeline.goal_graph.save_graph", fake_save)
    monkeypatch.setattr("pipeline.goal_policy.execute_policy", fake_execute)
    monkeypatch.setattr(
        "pipeline.goal_policy.classify_goal_branch",
        lambda **kw: type(
            "D",
            (),
            {
                "policy": "reuse",
                "reason": "test",
                "capability_slug": None,
                "connector_slug": None,
            },
        )(),
    )

    root = pathlib.Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.goal_compose import main as gc_main

    rc = gc_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "attempt",
            "--goal-id",
            "att_save_fail",
            "--text",
            "save fail",
        ]
    )
    assert rc == 1
    assert exec_calls == []
    assert n_save["n"] >= 1


def _promote_skill_fixture(
    monkeypatch: pytest.MonkeyPatch, pipeline: pathlib.Path, tmp_path: pathlib.Path, asset_id: str
) -> dict:
    """pin→scan→approve→promote a skill fixture; return promoted record."""
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    monkeypatch.setenv("KEEP_GOAL_TRACES", "1")
    monkeypatch.setenv("EXTERNAL_INGEST_ACTOR", "test-operator")
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    sk = tmp_path / "fx" / asset_id
    sk.mkdir(parents=True, exist_ok=True)
    (sk / "SKILL.md").write_text(
        f"---\nname: {asset_id}\n---\n\n# {asset_id}\n", encoding="utf-8"
    )
    (sk / "LICENSE").write_text("MIT\n", encoding="utf-8")
    from pipeline.external_ingest import (
        approve_asset,
        load_promoted,
        pin_asset,
        promote_asset,
        scan_asset,
    )

    pin_asset(sk, kind="skill", asset_id=asset_id)
    scan_asset(asset_id)
    approve_asset(asset_id)
    promote_asset(asset_id)
    return load_promoted(asset_id)


def test_smoke_external_promoted_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Promoted external skill node presence-smokes; not field_proven."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    prom = _promote_skill_fixture(monkeypatch, pipeline, tmp_path, "skill_smokepass")
    from pipeline.goal_graph import EXTERNAL_ORACLE, GRAPH_SCHEMA, smoke_graph, smoke_node

    node = {
        "id": "n1",
        "kind": "skill",
        "slug": "skill_smokepass",
        "label": prom.get("id"),
        "status": "verified",
        "oracle": EXTERNAL_ORACLE,
        "requires": [],
        "trust": "external",
        "external_asset_id": "skill_smokepass",
    }
    r = smoke_node(node)
    assert r["ok"] is True
    assert r.get("check") == "external_promoted"
    assert r.get("field_proven") is False
    assert r.get("presence_only") is True
    assert r.get("trust") == "external"

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "g_ext_smoke_ok",
        "goal_text": "use skill_smokepass",
        "status": "executable",
        "nodes": [node],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    report = smoke_graph(graph, mutate=True, re_critique=True)
    assert report["smoke_pass"] is True
    assert report["ok"] is True


def test_smoke_external_not_promoted_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Draft / missing promoted external node → smoke fail with clear issue."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.goal_graph import EXTERNAL_ORACLE, smoke_node

    r = smoke_node(
        {
            "id": "n1",
            "kind": "external_mcp",
            "slug": "ghost_external",
            "status": "verified",
            "oracle": EXTERNAL_ORACLE,
            "trust": "external",
        }
    )
    assert r["ok"] is False
    assert "external" in (r.get("detail") or "").lower()
    assert r.get("check") in ("external_promoted", "slug_safety")


def test_smoke_external_revoked_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Revoked external asset → smoke fail."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _promote_skill_fixture(monkeypatch, pipeline, tmp_path, "skill_revsmoke")
    from pipeline.external_ingest import revoke_asset
    from pipeline.goal_graph import EXTERNAL_ORACLE, smoke_node

    revoke_asset("skill_revsmoke", reason="dep drift")
    r = smoke_node(
        {
            "id": "n1",
            "kind": "skill",
            "slug": "skill_revsmoke",
            "status": "verified",
            "oracle": EXTERNAL_ORACLE,
            "trust": "external",
            "external_asset_id": "skill_revsmoke",
        }
    )
    assert r["ok"] is False
    assert "revok" in (r.get("detail") or "").lower() or "not_usable" in (
        r.get("detail") or ""
    )


def test_smoke_external_unpinned_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Promoted JSON without pin hash → smoke fail."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.external_ingest import promoted_dir
    from pipeline.goal_graph import EXTERNAL_ORACLE, smoke_node

    # Orphan promoted file: no pin, no live asset → unpinned fail closed
    p = promoted_dir() / "skill_nopin.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            {
                "schema": "external_promoted.v1",
                "id": "external_skill_skill_nopin",
                "external_asset_id": "skill_nopin",
                "kind": "skill",
                "status": "draft",
                "trust": "external",
                "pin": {},
            }
        ),
        encoding="utf-8",
    )
    r = smoke_node(
        {
            "id": "n1",
            "kind": "skill",
            "slug": "skill_nopin",
            "status": "verified",
            "oracle": EXTERNAL_ORACLE,
            "trust": "external",
            "external_asset_id": "skill_nopin",
        }
    )
    assert r["ok"] is False
    detail = (r.get("detail") or "").lower()
    assert "pin" in detail or "not_usable" in detail or "missing" in detail


def test_compile_with_promoted_external_fixture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Compile graph including a promoted external node without live pin/scan."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    prom = _promote_skill_fixture(monkeypatch, pipeline, tmp_path, "skill_compile")
    from pipeline.goal_graph import compile_goal_graph, smoke_graph
    from pipeline.external_ingest import route_hit_from_promoted

    hit = route_hit_from_promoted("skill_compile")
    g = compile_goal_graph(
        "use skill_compile external fixture",
        goal_id="g_ext_compile",
        route_hits=[hit],
        max_nodes=10,
    )
    assert g["schema"] == "graph.v1"
    nodes = g.get("nodes") or []
    assert any(n.get("slug") == "skill_compile" for n in nodes)
    ext_nodes = [n for n in nodes if n.get("trust") == "external"]
    assert ext_nodes
    assert ext_nodes[0].get("external_asset_id") == "skill_compile"
    assert ext_nodes[0].get("status") == "verified"
    # include_promoted_ids path
    g2 = compile_goal_graph(
        "include promoted",
        goal_id="g_ext_include",
        route_hits=[],
        include_promoted_ids=["skill_compile"],
    )
    assert any(
        n.get("slug") == "skill_compile" and n.get("trust") == "external"
        for n in (g2.get("nodes") or [])
    )
    report = smoke_graph(g2, mutate=True)
    assert report["smoke_pass"] is True
    assert prom["pin"]["content_sha256"]
