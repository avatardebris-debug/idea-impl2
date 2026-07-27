"""
Thin graph engineer — author/revise **draft** graph.v1 via existing gates only.

Pipeline only:
  load/save graph · critique_graph · compile_goal_graph · compile_graph_from_deconstruct
  · smoke_graph (finalize only)

Rules:
  - Engineer author/revise never set smoke_pass or field_proven.
  - Status after author/revise stays draft | critiqued | blocked.
  - Finalize that would claim smoke_pass/executable **must** call smoke_graph
    (or refuse). Fail-closed on smoke fail → smoke_failed / blocked.

No heavy LLM agent. Optional LLM path is inject/fixture only (not used here).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.goal_graph import (
    DEFAULT_ORACLE,
    GRAPH_SCHEMA,
    compile_goal_graph,
    compile_graph_from_deconstruct,
    critique_graph,
    load_graph,
    save_graph,
    smoke_graph,
)

# Author/revise may only leave the graph in these statuses.
ENGINEER_DRAFT_STATUSES = frozenset({"draft", "critiqued", "blocked"})

# Statuses that imply executability / smoke claim — finalize only via smoke_graph.
SMOKE_CLAIM_STATUSES = frozenset(
    {"smoke_pass", "executable", "smoke_failed"}
)

# Default repo-relative fixture for success-model inventory import.
DEFAULT_SUCCESS_MODEL_FIXTURE = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "fixtures"
    / "success_model_inventory.json"
)

__all__ = [
    "ENGINEER_DRAFT_STATUSES",
    "SMOKE_CLAIM_STATUSES",
    "DEFAULT_SUCCESS_MODEL_FIXTURE",
    "strip_smoke_claims",
    "apply_engineer_status",
    "engineer_author",
    "engineer_revise",
    "engineer_finalize",
    "import_success_model",
    "prepare_workflow_stubs",
    "success_model_fixture_path",
]


def strip_smoke_claims(graph: dict[str, Any]) -> dict[str, Any]:
    """Force engineer honesty: no smoke_pass / field_proven / production claim."""
    if not isinstance(graph, dict):
        raise TypeError("graph must be a dict")
    graph["smoke_pass"] = False
    graph["field_proven"] = False
    graph["production_graph"] = False
    # Drop durable smoke report so revise does not look smoked
    if "smoke_report" in graph:
        # Keep key only if present; clear contents so status is honest
        graph["smoke_report"] = None
    graph.pop("smoked_at", None)
    return graph


def apply_engineer_status(graph: dict[str, Any]) -> str:
    """Set status to draft|critiqued|blocked from critique + nodes. Never smoke_*."""
    crit = graph.get("critique")
    if not isinstance(crit, dict):
        crit = critique_graph(graph)
        graph["critique"] = crit
    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    if not crit.get("ok"):
        status = "blocked"
    elif nodes:
        status = "critiqued"
    else:
        status = "draft"
    graph["status"] = status
    strip_smoke_claims(graph)
    return status


def engineer_author(
    *,
    goal_id: str,
    goal_text: str = "",
    route_hits: list[dict[str, Any]] | None = None,
    deconstruct_doc: dict[str, Any] | None = None,
    deconstruct_id: str | None = None,
    max_nodes: int | None = None,
    include_promoted_ids: list[str] | None = None,
    save: bool = True,
) -> dict[str, Any]:
    """Author a **draft** graph via compile_goal_graph or compile_graph_from_deconstruct.

    Never sets smoke_pass / field_proven. Status is draft|critiqued|blocked.
    Prefer deconstruct_doc / deconstruct_id when both paths could apply.
    """
    gid = str(goal_id or "").strip()
    if not gid:
        raise ValueError("goal_id is required")

    graph: dict[str, Any]
    if deconstruct_doc is not None or deconstruct_id:
        if deconstruct_doc is None:
            from pipeline.deconstructor import load_deconstruct

            doc = load_deconstruct(str(deconstruct_id).strip())
            if doc is None:
                raise FileNotFoundError(
                    f"deconstruct id not found: {deconstruct_id}"
                )
        else:
            doc = deconstruct_doc
        kwargs: dict[str, Any] = {
            "goal_id": gid,
            "goal_text": goal_text or None,
        }
        if max_nodes is not None:
            kwargs["max_nodes"] = max_nodes
        graph = compile_graph_from_deconstruct(doc, **kwargs)
        # compile_graph_from_deconstruct already draft/critiqued/blocked + no smoke
        graph["source"] = graph.get("source") or "deconstruct"
        graph["engineered_by"] = "graph_engineer.author"
    else:
        text = (goal_text or "").strip() or gid
        compile_kwargs: dict[str, Any] = {
            "goal_id": gid,
            "route_hits": route_hits,
        }
        if max_nodes is not None:
            compile_kwargs["max_nodes"] = max_nodes
        if include_promoted_ids:
            compile_kwargs["include_promoted_ids"] = include_promoted_ids
        graph = compile_goal_graph(text, **compile_kwargs)
        # compile_goal_graph may set executable — demote to engineer draft statuses
        graph["source"] = "graph_engineer"
        graph["engineered_by"] = "graph_engineer.author"
        # Re-critique + force non-smoke statuses
        graph["critique"] = critique_graph(graph)
        apply_engineer_status(graph)

    strip_smoke_claims(graph)
    # Ensure status is never smoke_pass/executable from author alone
    cur = str(graph.get("status") or "")
    if cur not in ENGINEER_DRAFT_STATUSES:
        apply_engineer_status(graph)

    path = None
    if save:
        path = save_graph(graph)
    return {
        "ok": True,
        "graph": graph,
        "path": str(path) if path else None,
        "goal_id": graph.get("goal_id"),
        "status": graph.get("status"),
        "smoke_pass": bool(graph.get("smoke_pass")),
        "critique": graph.get("critique"),
        "hint": (
            "Draft only. Resolve nodes then: "
            f"python scripts/graph_engineer.py finalize --goal-id {graph.get('goal_id')} "
            f"OR python scripts/goal_compose.py smoke --goal-id {graph.get('goal_id')}"
        ),
    }


def _apply_node_patches(
    graph: dict[str, Any],
    patches: list[dict[str, Any]],
) -> list[str]:
    """Apply thin patches by node id or slug. Returns issue strings."""
    issues: list[str] = []
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        return ["graph has no nodes list"]
    by_key: dict[str, dict[str, Any]] = {}
    for n in nodes:
        if not isinstance(n, dict):
            continue
        if n.get("id"):
            by_key[str(n["id"])] = n
        if n.get("slug"):
            by_key[str(n["slug"])] = n

    allowed = frozenset(
        {"status", "oracle", "label", "kind", "requires", "layer", "notes"}
    )
    for p in patches:
        if not isinstance(p, dict):
            issues.append("invalid patch entry")
            continue
        key = str(p.get("id") or p.get("slug") or "").strip()
        if not key:
            issues.append("patch missing id/slug")
            continue
        node = by_key.get(key)
        if node is None:
            issues.append(f"node not found: {key}")
            continue
        for field in allowed:
            if field in p:
                node[field] = p[field]
        # Explicit forbid: patches cannot set smoke_pass on a node
        if "smoke_pass" in p or "field_proven" in p:
            issues.append(
                f"patch on {key} refused smoke_pass/field_proven "
                "(engineer revise cannot claim smoke)"
            )
    return issues


def engineer_revise(
    goal_id: str | None = None,
    *,
    graph: dict[str, Any] | None = None,
    node_patches: list[dict[str, Any]] | None = None,
    goal_text: str | None = None,
    re_critique: bool = True,
    save: bool = True,
) -> dict[str, Any]:
    """Revise an existing graph; re-critique; never promote to smoke_pass.

    Strips any prior smoke claims. Status becomes draft|critiqued|blocked.
    """
    g: dict[str, Any] | None = graph
    if g is None:
        gid = str(goal_id or "").strip()
        if not gid:
            raise ValueError("goal_id or graph is required")
        g = load_graph(gid)
        if g is None:
            raise FileNotFoundError(f"no graph for goal_id={gid}")
    if not isinstance(g, dict):
        raise TypeError("graph must be a dict")

    g = dict(g)  # shallow copy top-level
    if isinstance(g.get("nodes"), list):
        g["nodes"] = [dict(n) if isinstance(n, dict) else n for n in g["nodes"]]

    patch_issues: list[str] = []
    if node_patches:
        patch_issues = _apply_node_patches(g, node_patches)
    if goal_text is not None:
        g["goal_text"] = goal_text

    g["engineered_by"] = "graph_engineer.revise"
    g["source"] = g.get("source") or "graph_engineer"

    if re_critique:
        g["critique"] = critique_graph(g)
    apply_engineer_status(g)

    path = None
    if save:
        path = save_graph(g)

    ok = bool((g.get("critique") or {}).get("ok")) and not patch_issues
    return {
        "ok": ok,
        "graph": g,
        "path": str(path) if path else None,
        "goal_id": g.get("goal_id"),
        "status": g.get("status"),
        "smoke_pass": bool(g.get("smoke_pass")),
        "field_proven": bool(g.get("field_proven")),
        "critique": g.get("critique"),
        "patch_issues": patch_issues,
        "hint": (
            "Revised draft only. Finalize via smoke_graph: "
            f"python scripts/graph_engineer.py finalize --goal-id {g.get('goal_id')}"
        ),
    }


def engineer_finalize(
    goal_id: str | None = None,
    *,
    graph: dict[str, Any] | None = None,
    save: bool = True,
    write_trace: bool = False,
    claim_status: str | None = None,
) -> dict[str, Any]:
    """Claim smoke_pass/executable **only** by calling smoke_graph.

    Fail-closed:
      - smoke fail → status smoke_failed (or blocked if critique fails), smoke_pass=False
      - refuses to set smoke_pass without going through smoke_graph
      - never sets field_proven

    *claim_status*: if set to smoke_pass/executable, requires smoke_graph path
    (always taken). Other claim values are ignored with a note.
    """
    g: dict[str, Any] | None = graph
    if g is None:
        gid = str(goal_id or "").strip()
        if not gid:
            raise ValueError("goal_id or graph is required")
        g = load_graph(gid)
        if g is None:
            raise FileNotFoundError(f"no graph for goal_id={gid}")
    if not isinstance(g, dict):
        raise TypeError("graph must be a dict")

    want = str(claim_status or "smoke_pass").strip().lower()
    if want in ("field_proven",):
        return {
            "ok": False,
            "refused": True,
            "reason": (
                "engineer_finalize refuses field_proven — dual-gate field path only; "
                "smoke_pass is presence, not field_proven"
            ),
            "graph": g,
            "smoke_pass": bool(g.get("smoke_pass")),
            "field_proven": False,
        }

    # Always go through smoke_graph — never stamp smoke_pass alone.
    report = smoke_graph(g, mutate=True, re_critique=True)
    g["field_proven"] = False  # honesty: smoke ≠ field

    path = None
    if save:
        path = save_graph(g)

    smoke_ok = bool(report.get("smoke_pass"))
    status = str(g.get("status") or "")

    # Fail-closed: on smoke miss ensure status is smoke_failed or blocked
    if not smoke_ok:
        if report.get("blocked") and status not in ("blocked", "draft"):
            # critique/missing already set by smoke_graph; ensure not smoke_pass
            g["smoke_pass"] = False
            if status not in ("smoke_failed", "blocked", "draft", "critiqued"):
                g["status"] = "smoke_failed"
        elif not report.get("blocked"):
            g["status"] = "smoke_failed"
            g["smoke_pass"] = False
        if save:
            path = save_graph(g)

    trace_path_out = None
    if write_trace:
        try:
            from pipeline.goal_trace import (
                FAILURE_SMOKE,
                append_event,
                finalize_trace,
                start_trace,
            )

            tr = start_trace(
                str(g.get("goal_text") or g.get("goal_id") or "engineer finalize"),
                goal_id=str(g.get("goal_id") or goal_id or "engineer"),
                mode="sandbox",
                plan=[
                    {
                        "step": "engineer_finalize",
                        "via": "smoke_graph",
                    }
                ],
            )
            append_event(
                tr,
                type="smoke",
                content="engineer_finalize → smoke_graph",
                tool="smoke_graph",
                ok=smoke_ok,
                result_snip=json.dumps(
                    {
                        "smoke_pass": smoke_ok,
                        "issues": (report.get("issues") or [])[:5],
                        "status": g.get("status"),
                    }
                )[:400],
            )
            if smoke_ok:
                finalize_trace(
                    tr,
                    outcome="deeper",  # presence smoke ≠ goal proven
                    claim="mcp_smoke",
                    train_weight=1.0,
                    oracle={
                        "kind": "graph_smoke",
                        "smoke_pass": True,
                        "field_proven": False,
                    },
                )
            else:
                finalize_trace(
                    tr,
                    outcome="failed",
                    failure_class=FAILURE_SMOKE,
                    claim="mcp_smoke",
                    oracle={
                        "kind": "graph_smoke",
                        "smoke_pass": False,
                        "issues": report.get("issues") or [],
                    },
                )
            from pipeline.goal_trace import trace_path as _tp

            trace_path_out = str(_tp(str(tr.get("goal_id"))))
        except Exception as exc:
            trace_path_out = f"trace_error={exc}"

    return {
        "ok": smoke_ok,
        "refused": False,
        "graph": g,
        "path": str(path) if path else None,
        "goal_id": g.get("goal_id"),
        "status": g.get("status"),
        "smoke_pass": bool(g.get("smoke_pass")),
        "field_proven": False,
        "smoke": {
            "smoke_pass": report.get("smoke_pass"),
            "ok": report.get("ok"),
            "blocked": report.get("blocked"),
            "issues": report.get("issues") or [],
            "node_results": report.get("node_results") or [],
            "ts": report.get("ts"),
        },
        "trace_path": trace_path_out,
        "hint": (
            "smoke_pass is presence only — never field_proven. "
            "Failed smoke leaves status smoke_failed/blocked (fail-closed)."
            if not smoke_ok
            else "smoke_pass set via smoke_graph only; field_proven still false."
        ),
    }


def success_model_fixture_path() -> Path:
    """Resolve default success-model inventory fixture path."""
    return DEFAULT_SUCCESS_MODEL_FIXTURE


def prepare_workflow_stubs(graph: dict[str, Any]) -> list[str]:
    """Create temp verified stubs under PIPELINE_DIR for workflow executable nodes.

    Knowledge layers (research/human) are skipped. Software → projects/{slug}/state;
    connector → workflows/connectors/{slug}.yaml. Returns list of created paths.
    """
    from pipeline.paths import connectors_dir, projects_dir

    created: list[str] = []
    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        kind = str(node.get("kind") or "").strip().lower()
        layer = str(node.get("layer") or "").strip().lower()
        # Knowledge inventory: no stubs
        if kind in ("research", "human") or layer == "knowledge":
            continue
        slug = str(node.get("slug") or "").strip()
        if not slug or ".." in slug or "/" in slug or "\\" in slug:
            continue
        if kind == "software":
            soft = projects_dir() / slug
            state = soft / "state"
            state.mkdir(parents=True, exist_ok=True)
            idea = state / "current_idea.json"
            if not idea.is_file():
                idea.write_text(
                    json.dumps(
                        {
                            "title": slug,
                            "status": "complete",
                            "phase": 1,
                            "total_phases": 1,
                            "source": "success_model_stub",
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                created.append(str(idea))
        elif kind == "connector":
            cdir = connectors_dir()
            cdir.mkdir(parents=True, exist_ok=True)
            ypath = cdir / f"{slug}.yaml"
            if not ypath.is_file():
                ypath.write_text(
                    f"slug: {slug}\nkind: connector\n"
                    f"source: success_model_stub\n"
                    f"steps:\n  - id: s1\n    type: noop\n",
                    encoding="utf-8",
                )
                created.append(str(ypath))
        # mcp/skill: leave to factories — not auto-stubbed here
    return created


def import_success_model(
    fixture_path: str | Path | None = None,
    *,
    goal_id: str | None = None,
    prepare_stubs: bool = True,
    smoke: bool = True,
    write_trace: bool = False,
    save: bool = True,
) -> dict[str, Any]:
    """Import a success-model inventory fixture graph → critique → optional smoke.

    Knowledge (research/human) vs workflow (software/connector/mcp/skill) stay
    separate via node.layer. Import never sets field_proven. Smoke is optional
    and uses prepare_workflow_stubs for local presence checks under temp PIPELINE_DIR.
    """
    path = Path(fixture_path) if fixture_path else success_model_fixture_path()
    if not path.is_file():
        raise FileNotFoundError(f"success-model fixture not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"fixture must be a graph.v1 object: {path}")

    graph = dict(raw)
    if goal_id:
        graph["goal_id"] = str(goal_id).strip()
    if not graph.get("goal_id"):
        graph["goal_id"] = "success_model_inventory"
    if not graph.get("schema"):
        graph["schema"] = GRAPH_SCHEMA

    graph["source"] = graph.get("source") or "success_model_fixture"
    graph["fixture_path"] = str(path)
    graph["engineered_by"] = "graph_engineer.import_success_model"
    # Import is not production and not field-proven
    strip_smoke_claims(graph)

    # Separate knowledge vs workflow for operators
    knowledge_nodes = []
    workflow_nodes = []
    for n in graph.get("nodes") or []:
        if not isinstance(n, dict):
            continue
        kind = str(n.get("kind") or "").lower()
        layer = str(n.get("layer") or "").lower()
        if layer == "knowledge" or kind in ("research", "human"):
            knowledge_nodes.append(n.get("slug") or n.get("id"))
        else:
            workflow_nodes.append(n.get("slug") or n.get("id"))
    graph["knowledge_nodes"] = knowledge_nodes
    graph["workflow_nodes"] = workflow_nodes

    crit = critique_graph(graph)
    graph["critique"] = crit
    if not crit.get("ok"):
        graph["status"] = "blocked"
    else:
        graph["status"] = "critiqued" if (graph.get("nodes") or []) else "draft"
    strip_smoke_claims(graph)

    stubs: list[str] = []
    if prepare_stubs:
        stubs = prepare_workflow_stubs(graph)

    smoke_result = None
    if smoke:
        # Promote workflow executable nodes to verified if stubs prepared
        # (fixture already marks them verified; knowledge stays draft)
        smoke_result = smoke_graph(graph, mutate=True, re_critique=True)
        graph["field_proven"] = False
    else:
        # Leave draft/critiqued without smoke claim
        apply_engineer_status(graph)

    path_out = None
    if save:
        path_out = save_graph(graph)

    trace_path_out = None
    if write_trace:
        try:
            from pipeline.goal_trace import (
                FAILURE_SMOKE,
                append_event,
                finalize_trace,
                start_trace,
            )

            tr = start_trace(
                str(graph.get("goal_text") or "success model import"),
                goal_id=str(graph.get("goal_id")),
                mode="sandbox",
                plan=[
                    {"step": "import_fixture", "path": str(path)},
                    {"step": "critique"},
                    {"step": "smoke" if smoke else "skip_smoke"},
                ],
            )
            append_event(
                tr,
                type="import",
                content="success_model fixture import",
                tool="import_success_model",
                ok=True,
                result_snip=(
                    f"knowledge={knowledge_nodes}; workflow={workflow_nodes}; "
                    f"stubs={len(stubs)}"
                )[:400],
            )
            smoke_ok = bool(smoke_result and smoke_result.get("smoke_pass"))
            if smoke and smoke_ok:
                finalize_trace(
                    tr,
                    outcome="deeper",
                    claim="mcp_smoke",
                    train_weight=1.0,
                    oracle={
                        "kind": "success_model_import",
                        "smoke_pass": True,
                        "field_proven": False,
                    },
                )
            elif smoke and not smoke_ok:
                finalize_trace(
                    tr,
                    outcome="failed",
                    failure_class=FAILURE_SMOKE,
                    claim="mcp_smoke",
                    oracle={
                        "kind": "success_model_import",
                        "smoke_pass": False,
                        "issues": (smoke_result or {}).get("issues") or [],
                    },
                )
            else:
                finalize_trace(
                    tr,
                    outcome="deeper",
                    claim="structural",
                    train_weight=0.0,
                )
            from pipeline.goal_trace import trace_path as _tp

            trace_path_out = str(_tp(str(tr.get("goal_id"))))
        except Exception as exc:
            trace_path_out = f"trace_error={exc}"

    smoke_ok = bool(smoke_result and smoke_result.get("smoke_pass")) if smoke else None
    return {
        "ok": bool(crit.get("ok")) and (smoke_ok is not False),
        "graph": graph,
        "path": str(path_out) if path_out else None,
        "fixture_path": str(path),
        "goal_id": graph.get("goal_id"),
        "status": graph.get("status"),
        "smoke_pass": bool(graph.get("smoke_pass")),
        "field_proven": False,
        "critique": crit,
        "stubs_created": stubs,
        "knowledge_nodes": knowledge_nodes,
        "workflow_nodes": workflow_nodes,
        "smoke": (
            {
                "smoke_pass": smoke_result.get("smoke_pass"),
                "ok": smoke_result.get("ok"),
                "blocked": smoke_result.get("blocked"),
                "issues": smoke_result.get("issues") or [],
            }
            if smoke_result
            else None
        ),
        "trace_path": trace_path_out,
        "hint": (
            "Knowledge nodes are inventory only; workflow nodes smoke via presence stubs. "
            "smoke_pass ≠ field_proven. No unattended external pull."
        ),
    }
