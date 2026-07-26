"""Tests for goal graph store paths and graph.v1 compile/critique/persist."""

from __future__ import annotations

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
