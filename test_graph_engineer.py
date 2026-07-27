"""Phase 8: thin graph engineer + success-model import."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "tests" / "fixtures" / "success_model_inventory.json"


def _bind_tmp_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path):
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    monkeypatch.setenv("KEEP_GOAL_TRACES", "1")
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    return pipeline


def test_engineer_author_draft_never_smoke_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Task 1: engineer helper authors draft; smoke_pass never true from engineer alone."""
    _bind_tmp_pipeline(monkeypatch, tmp_path)
    from pipeline.graph_engineer import ENGINEER_DRAFT_STATUSES, engineer_author
    from pipeline.goal_graph import load_graph

    result = engineer_author(
        goal_id="eng_draft_1",
        goal_text="use eng_cli to export",
        route_hits=[
            {
                "slug": "eng_cli",
                "kind": "software",
                "title": "Eng CLI",
                "requires_ok": True,
            }
        ],
        save=True,
    )
    assert result["ok"] is True
    assert result["smoke_pass"] is False
    g = result["graph"]
    assert g["smoke_pass"] is False
    assert g.get("field_proven") is False
    assert g.get("production_graph") is False
    assert g["status"] in ENGINEER_DRAFT_STATUSES
    assert g["critique"] is not None
    # compile_goal_graph would have set executable — engineer demotes
    assert g["status"] != "executable"
    assert g["status"] != "smoke_pass"

    loaded = load_graph("eng_draft_1")
    assert loaded is not None
    assert loaded["smoke_pass"] is False
    assert loaded["status"] in ENGINEER_DRAFT_STATUSES


def test_engineer_revise_strips_smoke_and_recritiques(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Task 1: revise re-critiques and cannot keep smoke_pass from prior claim."""
    _bind_tmp_pipeline(monkeypatch, tmp_path)
    from pipeline.graph_engineer import engineer_author, engineer_revise
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, save_graph

    # Seed a graph that falsely claims smoke_pass (map fiction)
    save_graph(
        {
            "schema": GRAPH_SCHEMA,
            "goal_id": "eng_rev_1",
            "goal_text": "revise me",
            "status": "smoke_pass",
            "smoke_pass": True,
            "field_proven": True,
            "production_graph": True,
            "nodes": [
                {
                    "id": "n1",
                    "kind": "software",
                    "slug": "rev_tool",
                    "label": "rev_tool",
                    "status": "verified",
                    "oracle": DEFAULT_ORACLE,
                    "requires": [],
                }
            ],
            "edges": [],
            "critique": {"ok": True, "issues": []},
        }
    )

    out = engineer_revise(
        "eng_rev_1",
        node_patches=[{"slug": "rev_tool", "label": "Revised Tool"}],
        save=True,
    )
    assert out["smoke_pass"] is False
    assert out["field_proven"] is False
    g = out["graph"]
    assert g["smoke_pass"] is False
    assert g["field_proven"] is False
    assert g["production_graph"] is False
    assert g["status"] in ("draft", "critiqued", "blocked")
    assert g["status"] != "smoke_pass"
    labels = [n.get("label") for n in g["nodes"]]
    assert "Revised Tool" in labels
    assert g["critique"]["ok"] is True


def test_engineer_cannot_mark_smoke_pass_without_smoke_graph(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Task 2: finalize must call smoke_graph; fail-closed when assets missing."""
    _bind_tmp_pipeline(monkeypatch, tmp_path)
    from pipeline.graph_engineer import engineer_author, engineer_finalize
    from pipeline.goal_graph import load_graph

    author = engineer_author(
        goal_id="eng_fin_fail",
        goal_text="missing asset",
        route_hits=[
            {
                "slug": "no_such_project_xyz",
                "kind": "software",
                "requires_ok": True,
            }
        ],
        save=True,
    )
    assert author["smoke_pass"] is False

    fin = engineer_finalize("eng_fin_fail", save=True)
    assert fin["refused"] is False
    assert fin["smoke_pass"] is False
    assert fin["ok"] is False
    assert fin["field_proven"] is False
    status = str(fin["status"] or "")
    assert status in ("smoke_failed", "blocked")
    assert fin["graph"]["smoke_pass"] is False

    loaded = load_graph("eng_fin_fail")
    assert loaded is not None
    assert loaded["smoke_pass"] is False
    assert loaded["status"] in ("smoke_failed", "blocked")


def test_engineer_finalize_smoke_pass_only_via_smoke_graph(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Task 2: with verified stubs, finalize sets smoke_pass via smoke_graph only."""
    _bind_tmp_pipeline(monkeypatch, tmp_path)
    from pipeline.graph_engineer import engineer_finalize
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, save_graph
    from pipeline.paths import projects_dir

    soft = projects_dir() / "fin_ok_tool"
    (soft / "state").mkdir(parents=True)
    (soft / "state" / "current_idea.json").write_text(
        json.dumps({"status": "complete", "phase": 1, "total_phases": 1}),
        encoding="utf-8",
    )
    save_graph(
        {
            "schema": GRAPH_SCHEMA,
            "goal_id": "eng_fin_ok",
            "goal_text": "finalize ok",
            "status": "critiqued",
            "smoke_pass": False,
            "nodes": [
                {
                    "id": "n1",
                    "kind": "software",
                    "slug": "fin_ok_tool",
                    "label": "fin_ok_tool",
                    "status": "verified",
                    "oracle": DEFAULT_ORACLE,
                    "requires": [],
                }
            ],
            "edges": [],
            "critique": {"ok": True, "issues": []},
        }
    )

    calls: list[str] = []
    import pipeline.goal_graph as gg

    real_smoke = gg.smoke_graph

    def tracking_smoke(graph, **kwargs):
        calls.append("smoke_graph")
        return real_smoke(graph, **kwargs)

    monkeypatch.setattr("pipeline.goal_graph.smoke_graph", tracking_smoke)
    # engineer_finalize imports smoke_graph at module level from goal_graph
    monkeypatch.setattr("pipeline.graph_engineer.smoke_graph", tracking_smoke)

    fin = engineer_finalize("eng_fin_ok", save=True, write_trace=True)
    assert "smoke_graph" in calls
    assert fin["smoke_pass"] is True
    assert fin["ok"] is True
    assert fin["field_proven"] is False
    assert fin["status"] == "smoke_pass"
    assert fin["graph"]["smoke_pass"] is True
    assert fin["graph"].get("field_proven") is False


def test_engineer_finalize_refuses_field_proven_claim(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Task 2: finalize refuses claim_status=field_proven."""
    _bind_tmp_pipeline(monkeypatch, tmp_path)
    from pipeline.graph_engineer import engineer_finalize
    from pipeline.goal_graph import DEFAULT_ORACLE, GRAPH_SCHEMA, save_graph

    save_graph(
        {
            "schema": GRAPH_SCHEMA,
            "goal_id": "eng_refuse_fp",
            "goal_text": "no field",
            "status": "draft",
            "nodes": [
                {
                    "id": "n1",
                    "kind": "research",
                    "slug": "know",
                    "label": "know",
                    "status": "draft",
                    "oracle": "",
                    "requires": [],
                }
            ],
            "edges": [],
        }
    )
    out = engineer_finalize("eng_refuse_fp", claim_status="field_proven", save=False)
    assert out["refused"] is True
    assert out["ok"] is False
    assert out["field_proven"] is False


def test_import_success_model_fixture_smoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Task 3: fixture import → critique → smoke with stubs; knowledge vs workflow."""
    _bind_tmp_pipeline(monkeypatch, tmp_path)
    assert FIXTURE.is_file(), f"missing fixture {FIXTURE}"

    from pipeline.graph_engineer import import_success_model
    from pipeline.goal_graph import load_graph
    from pipeline.goal_trace import load_trace

    result = import_success_model(
        FIXTURE,
        goal_id="sm_import_test",
        prepare_stubs=True,
        smoke=True,
        write_trace=True,
        save=True,
    )
    assert result["critique"]["ok"] is True
    assert result["smoke_pass"] is True, result.get("smoke")
    assert result["field_proven"] is False
    assert result["status"] == "smoke_pass"
    assert "sm_knowledge_roles" in (result.get("knowledge_nodes") or [])
    assert "sm_workflow_cli" in (result.get("workflow_nodes") or [])
    assert result["stubs_created"], "expected workflow stubs under PIPELINE_DIR"

    loaded = load_graph("sm_import_test")
    assert loaded is not None
    assert loaded["smoke_pass"] is True
    assert loaded.get("field_proven") is False
    # Knowledge nodes remain non-executable kinds
    kinds = {n["slug"]: n["kind"] for n in loaded["nodes"]}
    assert kinds["sm_knowledge_roles"] == "research"
    assert kinds["sm_human_gate"] == "human"
    assert kinds["sm_workflow_cli"] == "software"

    tr = load_trace("sm_import_test")
    assert tr is not None
    assert tr.get("schema") == "goal_trace.v1"


def test_import_success_model_no_smoke_stays_draft(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Task 3: import without smoke leaves draft/critiqued, smoke_pass false."""
    _bind_tmp_pipeline(monkeypatch, tmp_path)
    from pipeline.graph_engineer import ENGINEER_DRAFT_STATUSES, import_success_model

    result = import_success_model(
        FIXTURE,
        prepare_stubs=False,
        smoke=False,
        write_trace=False,
        save=True,
    )
    assert result["smoke_pass"] is False
    assert result["status"] in ENGINEER_DRAFT_STATUSES
    assert result["smoke"] is None


def test_graph_engineer_cli_author_and_finalize(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """CLI path: author then finalize with stub."""
    pipeline = _bind_tmp_pipeline(monkeypatch, tmp_path)
    from pipeline.paths import projects_dir
    from scripts.graph_engineer import main as eng_main

    soft = projects_dir() / "cli_eng_tool"
    (soft / "state").mkdir(parents=True)
    (soft / "state" / "current_idea.json").write_text(
        json.dumps({"status": "complete", "phase": 1, "total_phases": 1}),
        encoding="utf-8",
    )
    hits = tmp_path / "hits.json"
    hits.write_text(
        json.dumps(
            [
                {
                    "slug": "cli_eng_tool",
                    "kind": "software",
                    "requires_ok": True,
                }
            ]
        ),
        encoding="utf-8",
    )

    rc = eng_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "author",
            "--goal-id",
            "cli_eng",
            "--text",
            "use cli_eng_tool",
            "--hits-json",
            str(hits),
        ]
    )
    assert rc == 0
    gpath = pipeline / "graphs" / "cli_eng.json"
    assert gpath.is_file()
    g = json.loads(gpath.read_text(encoding="utf-8"))
    assert g["smoke_pass"] is False
    assert g["status"] in ("draft", "critiqued", "blocked")

    rc2 = eng_main(
        ["--pipeline-dir", str(pipeline), "finalize", "--goal-id", "cli_eng"]
    )
    assert rc2 == 0
    g2 = json.loads(gpath.read_text(encoding="utf-8"))
    assert g2["smoke_pass"] is True
    assert g2.get("field_proven") is False


def test_graph_engineer_cli_import_success_model(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = _bind_tmp_pipeline(monkeypatch, tmp_path)
    from scripts.graph_engineer import main as eng_main

    rc = eng_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "import-success-model",
            "--fixture",
            str(FIXTURE),
            "--goal-id",
            "cli_sm",
            "--write-trace",
        ]
    )
    assert rc == 0
    gpath = pipeline / "graphs" / "cli_sm.json"
    assert gpath.is_file()
    g = json.loads(gpath.read_text(encoding="utf-8"))
    assert g["smoke_pass"] is True
    assert g.get("field_proven") is False
