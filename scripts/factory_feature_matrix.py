#!/usr/bin/env python3
"""
Factory feature matrix — automated PASS/FAIL for goal compose + MCP factory + related.

Default: isolated temp PIPELINE_DIR (safe; does not touch thepipeline).
Optional: --pipeline-dir for a real root, --live for extra live-only checks.

Usage:
  python scripts/factory_feature_matrix.py
  python scripts/factory_feature_matrix.py --json
  python scripts/factory_feature_matrix.py --pipeline-dir C:\\Users\\avata\\aicompete\\thepipeline --live
  python scripts/factory_feature_matrix.py --keep-temp   # leave temp dir for inspection

Exit 0 = all HARD checks pass; 1 = any HARD fail.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@dataclass
class CheckResult:
    id: str
    hard: bool
    ok: bool
    detail: str
    section: str = "isolated"


@dataclass
class MatrixReport:
    pipeline_dir: str
    mode: str  # isolated | provided | live
    ok: bool
    checks: list[CheckResult] = field(default_factory=list)


def _reload(pipeline_dir: Path) -> None:
    os.environ["PIPELINE_DIR"] = str(pipeline_dir)
    from pipeline.paths import reload_pipeline_dir

    reload_pipeline_dir()


def _run(cid: str, hard: bool, section: str, fn: Callable[[], str]) -> CheckResult:
    try:
        detail = fn() or "ok"
        return CheckResult(id=cid, hard=hard, ok=True, detail=detail[:300], section=section)
    except Exception as exc:
        tb = traceback.format_exc(limit=2)
        return CheckResult(
            id=cid,
            hard=hard,
            ok=False,
            detail=f"{exc} | {tb[-200:]}",
            section=section,
        )


def check_paths() -> str:
    from pipeline.paths import get_pipeline_dir, graphs_dir, mcps_dir, metrics_dir

    p = get_pipeline_dir()
    assert p.is_dir(), f"pipeline_dir missing: {p}"
    g, m, met = graphs_dir(), mcps_dir(), metrics_dir()
    for d in (g, m, met):
        d.mkdir(parents=True, exist_ok=True)
    return f"root={p} graphs={g.name} mcps={m.name}"


def check_goal_compile() -> str:
    from pipeline.goal_graph import GRAPH_SCHEMA, load_graph
    from pipeline.paths import graphs_dir

    # Prefer library API (stable) over CLI subprocess
    from pipeline.goal_graph import compile_goal_graph, save_graph

    g = compile_goal_graph(
        "wrap helper as mcp and connect tools",
        goal_id="matrix_itest",
        route_hits=[
            {
                "slug": "helper_tool",
                "requires_ok": True,
                "kind": "project",
                "status": "verified",
            }
        ],
    )
    assert g.get("schema") == GRAPH_SCHEMA, g.get("schema")
    save_graph(g)
    path = graphs_dir() / "matrix_itest.json"
    assert path.is_file(), f"missing {path}"
    loaded = load_graph("matrix_itest")
    assert loaded and loaded.get("goal_id") == "matrix_itest"
    return f"nodes={len(g.get('nodes') or [])} path={path.name}"


def check_plan_factories_missing_mcp() -> str:
    from pipeline.goal_graph import plan_factory_actions, save_graph
    from pipeline.mcp_queue import list_pending

    graph = {
        "schema": "graph.v1",
        "goal_id": "matrix_mcp_plan",
        "goal_text": "need mcp",
        "status": "draft",
        "nodes": [
            {
                "id": "n1",
                "kind": "mcp",
                "slug": "mcp_matrix_cap",
                "label": "missing mcp",
                "status": "missing",
                "oracle": {"name": "capability_invoke_help", "pass": None},
                "requires": [],
            }
        ],
        "edges": [],
        "critique": {"ok": False, "issues": []},
    }
    save_graph(graph)
    before = len(list_pending())
    out = plan_factory_actions(graph)
    after = list_pending()
    assert out.get("enqueued"), f"expected enqueued, got {out}"
    assert len(after) > before, "pending queue did not grow"
    return f"enqueued={len(out['enqueued'])} pending={len(after)}"


def check_mcp_wrap_smoke_list() -> str:
    from pipeline.mcp_factory import list_mcps, mcp_slug_for, smoke_mcp, wrap_capability_as_mcp
    from pipeline.paths import mcps_dir

    slug = "matrix_demo_tool"
    man = wrap_capability_as_mcp(slug, force=True)
    mslug = man.get("mcp_slug") or mcp_slug_for(slug)
    server = mcps_dir() / mslug / "server.py"
    assert server.is_file(), f"missing server {server}"
    # Soft smoke: matrix has no live capability project for invoke oracle
    rep = smoke_mcp(mslug, require_invoke=False)
    assert rep.get("ok") is True, rep
    listed = list_mcps()
    assert any(m.get("mcp_slug") == mslug for m in listed), listed
    return f"mcp={mslug} smoke_ok tools={man.get('tools')}"


def check_mcp_resmoke_revoke() -> str:
    """HARD: re-smoke updates last_smoke_at; revoke clears is_mcp_smoked."""
    from pipeline.mcp_factory import (
        is_mcp_smoked,
        resmoke_mcp,
        revoke_mcp,
        smoke_mcp,
        wrap_capability_as_mcp,
    )
    from pipeline.paths import mcps_dir

    slug = "matrix_resmoke_cap"
    wrap_capability_as_mcp(slug, force=True)
    mslug = f"mcp_{slug}"
    assert smoke_mcp(mslug, require_invoke=False).get("ok") is True
    r2 = resmoke_mcp(mslug, require_invoke=False)
    assert r2.get("ok") is True, r2
    man = json.loads(
        (mcps_dir() / mslug / "manifest.json").read_text(encoding="utf-8")
    )
    assert man.get("last_smoke_at"), man
    assert is_mcp_smoked(mslug)
    rev = revoke_mcp(mslug, reason="matrix")
    assert rev.get("ok") is True, rev
    assert not is_mcp_smoked(mslug)
    return f"mcp={mslug} resmoke_ok revoked"


def check_drain_queue() -> str:
    from pipeline.mcp_factory import drain_queue
    from pipeline.mcp_queue import enqueue_wrap, list_pending

    enqueue_wrap("matrix_drain_cap", reason="matrix test")
    n_before = len(list_pending())
    assert n_before >= 1
    results = drain_queue(limit=3)
    # drain returns list of result dicts
    assert isinstance(results, list), type(results)
    # at least one processed or queue emptied
    n_after = len(list_pending())
    return f"drained_items={len(results)} pending_before={n_before} after={n_after}"


def check_policy_mcp_enqueue() -> str:
    from pipeline.goal_policy import (
        POLICY_MCP,
        classify_goal_branch,
        execute_policy,
    )
    from pipeline.mcp_queue import list_pending
    from pipeline.paths import get_pipeline_dir

    d = classify_goal_branch(
        branch_type="software",
        text="expose foo as mcp",
        route_hits=[{"slug": "foo_cap", "requires_ok": True, "kind": "project"}],
    )
    assert d.policy == POLICY_MCP, d
    before = {p.name for p in list_pending()}
    out = execute_policy(d, goal_text="expose foo as mcp", branch_id="matrix_b1")
    assert out.get("status") == "mcp_enqueued", out
    after = list_pending()
    assert any(p.name not in before for p in after) or out.get("job_path"), out
    # goal_trace may exist
    traces = get_pipeline_dir() / "goal_traces"
    n_traces = len(list(traces.glob("*.json"))) if traces.is_dir() else 0
    return f"status={out.get('status')} job={out.get('job_path')} traces={n_traces}"


def check_goal_traces_dir() -> str:
    from pipeline.paths import get_pipeline_dir

    d = get_pipeline_dir() / "goal_traces"
    if not d.is_dir():
        raise AssertionError("goal_traces dir missing after policy/mcp runs")
    files = list(d.glob("*.json"))
    if not files:
        raise AssertionError("no goal_trace json files written")
    return f"count={len(files)} sample={files[0].name}"


def check_connector_process_oracle() -> str:
    """Runs hard-coded process oracle (no product connectors required)."""
    from pipeline.connector_smoke import run_connector_smoke

    report = run_connector_smoke(oracle_only=True)
    hard = [c for c in report.cases if c.hard]
    assert hard, "no hard cases"
    assert all(c.ok for c in hard), [c.detail for c in hard if not c.ok]
    return f"hard_pass={len(hard)} process_oracle ok"


def check_smoke_graph_fixture() -> str:
    """HARD: tiny verified fixture graph → smoke_graph smoke_pass (no LLM, no field)."""
    from pipeline.goal_graph import (
        DEFAULT_ORACLE,
        GRAPH_SCHEMA,
        MCP_ORACLE,
        critique_graph,
        save_graph,
        smoke_graph,
    )
    from pipeline.mcp_factory import smoke_mcp, wrap_capability_as_mcp
    from pipeline.paths import connectors_dir, projects_dir

    wrap_capability_as_mcp("matrix_smoke_util", force=True)
    assert smoke_mcp("mcp_matrix_smoke_util", require_invoke=False).get("ok") is True

    soft = projects_dir() / "matrix_tool_alpha"
    (soft / "state").mkdir(parents=True, exist_ok=True)
    (soft / "state" / "current_idea.json").write_text(
        json.dumps(
            {
                "title": "matrix_tool_alpha",
                "status": "field_proven",
                "phase": 1,
                "total_phases": 1,
            }
        ),
        encoding="utf-8",
    )

    cdir = connectors_dir()
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "matrix_bridge.yaml").write_text(
        "slug: matrix_bridge\nkind: connector\nsteps:\n  - id: s1\n    type: noop\n",
        encoding="utf-8",
    )

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "matrix_smoke_g",
        "goal_text": "compose smoked matrix tools",
        "status": "executable",
        "nodes": [
            {
                "id": "n1",
                "kind": "software",
                "slug": "matrix_tool_alpha",
                "label": "matrix_tool_alpha",
                "status": "verified",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            },
            {
                "id": "n2",
                "kind": "mcp",
                "slug": "mcp_matrix_smoke_util",
                "label": "mcp_matrix_smoke_util",
                "status": "verified",
                "oracle": MCP_ORACLE,
                "requires": [],
            },
            {
                "id": "n3",
                "kind": "connector",
                "slug": "matrix_bridge",
                "label": "matrix_bridge",
                "status": "verified",
                "oracle": DEFAULT_ORACLE,
                "requires": [],
            },
        ],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    assert critique_graph(graph).get("ok") is True, graph.get("critique")
    report = smoke_graph(graph, mutate=True)
    assert report.get("blocked") is False, report
    assert report.get("smoke_pass") is True, report
    assert report.get("ok") is True, report
    assert all(r.get("ok") for r in (report.get("node_results") or [])), report
    save_graph(graph)
    return (
        f"nodes={len(report.get('node_results') or [])} "
        f"smoke_pass={report.get('smoke_pass')} goal_id=matrix_smoke_g"
    )


def check_dual_gate_field_status() -> str:
    """HARD: runner-green weak plan → field_test_passed, not field_proven without ADEQUATE+bars."""
    from pipeline.field_prove_gate import (
        VERDICT_ADEQUATE,
        assess_plan_bars,
        decide_field_status,
    )

    weak_plan = """# Field Tests

## Product tests
- [ ] Task P1: help
  - Kind: product
  - Command: `python cli.py --help`
  - Expect: exit 0

- [ ] Task P2: syntax
  - Kind: product
  - Command: `python -m py_compile cli.py`
  - Expect: exit 0

## Integration tests
- [ ] Task I1: import
  - Kind: integration
  - Command: `python -c "import cli; print('IMPORT_OK')"`
  - Expect: IMPORT_OK
"""
    strong_plan = """# Field Tests

## Product tests
- [ ] Task P1: core greet path
  - Kind: product
  - Command: `python cli.py --greet world`
  - Expect: GREET:world

## Integration tests
- [ ] Task I1: write out.json
  - Kind: integration
  - Command: `python cli.py --out out.json`
  - Expect: exit 0
"""
    weak_bars = assess_plan_bars(weak_plan)
    d_weak = decide_field_status(
        runner_all_passed=True,
        bars=weak_bars,
        dual_gate=True,
    )
    assert d_weak.runner_all_passed is True, d_weak
    assert d_weak.mechanical_status == "field_test_passed", d_weak
    assert d_weak.status == "field_test_passed", d_weak
    assert d_weak.field_proven is False, d_weak
    assert d_weak.ok is False, d_weak

    # Even LLM ADEQUATE cannot override weak bars
    d_llm = decide_field_status(
        runner_all_passed=True,
        bars=weak_bars,
        evaluator_verdict=VERDICT_ADEQUATE,
        dual_gate=True,
    )
    assert d_llm.field_proven is False, d_llm
    assert d_llm.status == "field_test_passed", d_llm

    strong_bars = assess_plan_bars(strong_plan)
    d_strong = decide_field_status(
        runner_all_passed=True,
        bars=strong_bars,
        dual_gate=True,
    )
    assert d_strong.field_proven is True, d_strong
    assert d_strong.status == "field_proven", d_strong
    assert d_strong.ok is True, d_strong

    d_fail = decide_field_status(
        runner_all_passed=False,
        bars=strong_bars,
        evaluator_verdict=VERDICT_ADEQUATE,
        dual_gate=True,
    )
    assert d_fail.field_proven is False, d_fail
    assert d_fail.status != "field_proven", d_fail
    assert d_fail.mechanical_status == "field_test_failed", d_fail

    return (
        f"weak→{d_weak.status} llm_override→{d_llm.status} "
        f"strong→{d_strong.status} runner_fail→{d_fail.status}"
    )


def check_external_promote_smoke() -> str:
    """HARD: pin→scan→approve→promote fixture then resolve_promoted + smoke external node."""
    from pipeline.external_ingest import (
        approve_asset,
        pin_asset,
        promote_asset,
        resolve_promoted,
        scan_asset,
    )
    from pipeline.goal_graph import (
        EXTERNAL_ORACLE,
        GRAPH_SCHEMA,
        smoke_graph,
        smoke_node,
    )
    from pipeline.paths import get_pipeline_dir

    asset_id = "skill_matrix_ext"
    fx_root = get_pipeline_dir() / "_matrix_fixtures" / asset_id
    fx_root.mkdir(parents=True, exist_ok=True)
    (fx_root / "SKILL.md").write_text(
        f"---\nname: {asset_id}\n---\n\n# {asset_id}\n\nMatrix external skill fixture.\n",
        encoding="utf-8",
    )
    (fx_root / "LICENSE").write_text("MIT License\n", encoding="utf-8")

    pin_asset(fx_root, kind="skill", asset_id=asset_id)
    scanned = scan_asset(asset_id)
    assert scanned.get("status") == "scanned", scanned
    approved = approve_asset(asset_id, notes="matrix hard check")
    assert approved.get("status") == "approved", approved
    # promote_asset returns the asset record (status=promoted), not the draft
    asset_after = promote_asset(asset_id, notes="matrix promote")
    assert asset_after.get("status") == "promoted", asset_after

    # resolve_promoted returns external_promoted.v1 draft (id may be external_skill_*)
    prom = resolve_promoted(asset_id)
    assert prom and prom.get("trust") == "external", prom
    assert str(prom.get("external_asset_id") or "") == asset_id, prom

    node = {
        "id": "n_ext",
        "kind": "skill",
        "slug": asset_id,
        "label": asset_id,
        "status": "verified",
        "oracle": EXTERNAL_ORACLE,
        "requires": [],
        "trust": "external",
        "external_asset_id": asset_id,
    }
    r = smoke_node(node)
    assert r.get("ok") is True, r
    assert r.get("field_proven") is False, r
    assert r.get("presence_only") is True or r.get("check") == "external_promoted", r

    graph = {
        "schema": GRAPH_SCHEMA,
        "goal_id": "matrix_ext_g",
        "goal_text": f"use {asset_id}",
        "status": "executable",
        "nodes": [node],
        "edges": [],
        "critique": {"ok": True, "issues": []},
    }
    report = smoke_graph(graph, mutate=True, re_critique=True)
    assert report.get("smoke_pass") is True, report
    assert report.get("ok") is True, report
    return (
        f"asset={asset_id} promote_ok smoke_pass={report.get('smoke_pass')} "
        f"node_check={r.get('check')} presence_only not field_proven"
    )


def check_live_pipeline_root() -> str:
    from pipeline.paths import get_pipeline_dir, projects_dir

    p = get_pipeline_dir()
    assert (p / "projects").is_dir() or projects_dir().is_dir()
    n = len([x for x in projects_dir().iterdir() if x.is_dir()]) if projects_dir().is_dir() else 0
    return f"root={p} projects≈{n}"


def check_live_connector_smoke() -> str:
    from pipeline.connector_smoke import run_connector_smoke

    report = run_connector_smoke()
    hard = [c for c in report.cases if c.hard]
    bad = [c for c in hard if not c.ok]
    if bad:
        raise AssertionError("; ".join(f"{c.id}:{c.detail[:80]}" for c in bad))
    return f"hard={len(hard)} overall_ok={report.ok}"


def run_matrix(
    *,
    pipeline_dir: Path,
    live: bool,
    section_isolated: bool = True,
) -> MatrixReport:
    _reload(pipeline_dir)
    mode = "live" if live else ("provided" if os.environ.get("_MATRIX_PROVIDED") else "isolated")
    report = MatrixReport(pipeline_dir=str(pipeline_dir), mode=mode, ok=False)

    checks: list[tuple[str, bool, str, Callable[[], str]]] = []
    if section_isolated:
        checks.extend(
            [
                ("paths", True, "isolated", check_paths),
                ("goal_compile", True, "isolated", check_goal_compile),
                ("plan_factories_mcp", True, "isolated", check_plan_factories_missing_mcp),
                ("mcp_wrap_smoke_list", True, "isolated", check_mcp_wrap_smoke_list),
                ("mcp_resmoke_revoke", True, "isolated", check_mcp_resmoke_revoke),
                ("drain_queue", True, "isolated", check_drain_queue),
                ("policy_mcp_enqueue", True, "isolated", check_policy_mcp_enqueue),
                ("goal_traces", True, "isolated", check_goal_traces_dir),
                ("connector_process_oracle", True, "isolated", check_connector_process_oracle),
                # Phase 7 ladder surfaces
                ("smoke_graph_fixture", True, "isolated", check_smoke_graph_fixture),
                ("dual_gate_field_status", True, "isolated", check_dual_gate_field_status),
                ("external_promote_smoke", True, "isolated", check_external_promote_smoke),
            ]
        )
    if live:
        checks.extend(
            [
                ("live_pipeline_root", True, "live", check_live_pipeline_root),
                ("live_connector_smoke", True, "live", check_live_connector_smoke),
            ]
        )

    for cid, hard, section, fn in checks:
        report.checks.append(_run(cid, hard, section, fn))

    report.ok = all(c.ok for c in report.checks if c.hard)
    return report


def format_table(report: MatrixReport) -> str:
    lines = [
        "Factory feature matrix",
        f"  pipeline_dir: {report.pipeline_dir}",
        f"  mode:         {report.mode}",
        f"  overall HARD: {'PASS' if report.ok else 'FAIL'}",
        "",
        f"{'ID':<28} {'SEC':<10} {'HARD':<6} {'OK':<6} DETAIL",
        "-" * 100,
    ]
    for c in report.checks:
        lines.append(
            f"{c.id:<28} {c.section:<10} "
            f"{('yes' if c.hard else 'no'):<6} "
            f"{('PASS' if c.ok else 'FAIL'):<6} "
            f"{(c.detail or '').replace(chr(10), ' ')[:70]}"
        )
    lines.append("-" * 100)
    hard = [c for c in report.checks if c.hard]
    n_ok = sum(1 for c in hard if c.ok)
    lines.append(f"HARD: {n_ok}/{len(hard)} passed")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Factory feature matrix (goal compose + MCP factory + related)")
    ap.add_argument(
        "--pipeline-dir",
        default="",
        help="Use this PIPELINE_DIR (default: create temp dir for isolated §2)",
    )
    ap.add_argument(
        "--live",
        action="store_true",
        help="Also run live checks (requires --pipeline-dir or existing env with projects)",
    )
    ap.add_argument(
        "--keep-temp",
        action="store_true",
        help="Do not delete temp pipeline dir after isolated run",
    )
    ap.add_argument("--json", action="store_true", help="Print JSON report")
    ap.add_argument(
        "--out",
        default="",
        help="Write markdown table to this path",
    )
    args = ap.parse_args()

    temp_dir: str | None = None
    provided = (args.pipeline_dir or "").strip() or (os.environ.get("PIPELINE_DIR") or "").strip()

    if provided and not args.live:
        # User pointed at a dir: run isolated checks *inside* that dir (writes graphs/mcps there)
        pipeline = Path(provided).expanduser().resolve()
        pipeline.mkdir(parents=True, exist_ok=True)
        os.environ["_MATRIX_PROVIDED"] = "1"
        report = run_matrix(pipeline_dir=pipeline, live=False)
    elif args.live:
        if not provided:
            home = Path.home() / "aicompete" / "thepipeline"
            if home.is_dir():
                provided = str(home)
            else:
                print("ERROR: --live requires --pipeline-dir or ~/aicompete/thepipeline", file=sys.stderr)
                return 2
        pipeline = Path(provided).expanduser().resolve()
        # Isolated checks in a temp dir first, then live checks against real root
        temp_dir = tempfile.mkdtemp(prefix="factory_matrix_")
        report_iso = run_matrix(pipeline_dir=Path(temp_dir), live=False)
        report_live = run_matrix(pipeline_dir=pipeline, live=True, section_isolated=False)
        report = MatrixReport(
            pipeline_dir=f"isolated={temp_dir}; live={pipeline}",
            mode="isolated+live",
            ok=report_iso.ok and report_live.ok,
            checks=report_iso.checks + report_live.checks,
        )
    else:
        temp_dir = tempfile.mkdtemp(prefix="factory_matrix_")
        report = run_matrix(pipeline_dir=Path(temp_dir), live=False)

    text = format_table(report)
    if args.json:
        payload = {
            "ok": report.ok,
            "mode": report.mode,
            "pipeline_dir": report.pipeline_dir,
            "checks": [asdict(c) for c in report.checks],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(text)

    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(text + "\n", encoding="utf-8")
        print(f"\nWrote: {outp}")

    if temp_dir and not args.keep_temp:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
    elif temp_dir and args.keep_temp:
        print(f"\nKept temp PIPELINE_DIR: {temp_dir}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
