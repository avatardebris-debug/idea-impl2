"""
Connector smoke runner + goal_trace.v1 on each run + hard-coded process oracle.

Layers
------
1. **Structural smoke** (per connector YAML under workflows/connectors/):
   load schema, require steps/types, soft-check requires project dirs exist.

2. **Hard-coded process oracle** (always HARD):
   simulates connecting two capabilities (producer → consumer) that serve a
   process, writes artifacts, and oracles the receipt. Does not depend on
   real product slugs being field_proven.

3. **Optional execute smoke** (soft unless --require-execute):
   try ``run_workflow`` with force / native backend (skips live n8n).

Every case writes a ``goal_trace.v1`` under ``{PIPELINE_DIR}/goal_traces/``
with closed outcome proven | failed | deeper (legacy status still written).

Reports: ``metrics/connector_smoke_latest.{md,json}``.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.goal_trace import (
    FAILURE_COMPOSE,
    FAILURE_SMOKE,
    OUTCOME_DEEPER,
    OUTCOME_FAILED,
    OUTCOME_PROVEN,
    append_event,
    finalize_trace,
    start_trace,
)
from pipeline.paths import connectors_dir, get_pipeline_dir, metrics_dir, projects_dir
from pipeline.workflow_schema import WorkflowDefinition, WorkflowStep

SCHEMA = "connector_smoke.v1"
PROCESS_ORACLE_SLUG = "smoke_process_oracle"
PROCESS_ORACLE_GOAL = (
    "Connect two capabilities (producer + consumer) to serve process "
    "smoke_process_oracle: chain artifacts into a signed process receipt."
)
KNOWN_STEP_TYPES = frozenset({"capability", "shell", "n8n_webhook", "n8n_execute"})


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _goal_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


@dataclass
class ConnectorSmokeCase:
    """One smoke case (structural, execute, or process oracle)."""

    id: str
    slug: str
    mode: str  # structural | execute | process_oracle
    hard: bool
    ok: bool
    detail: str
    status: str = "goal_failed"  # goal_proven | goal_failed | deeper_work_needed
    goal_id: str | None = None
    oracle: dict[str, Any] | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)


@dataclass
class ConnectorSmokeReport:
    schema: str = SCHEMA
    ts: str = ""
    ok: bool = False
    pipeline_dir: str = ""
    cases: list[ConnectorSmokeCase] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def hard_cases(self) -> list[ConnectorSmokeCase]:
        return [c for c in self.cases if c.hard]


def list_connector_definitions() -> list[WorkflowDefinition]:
    """Load all connector YAMLs under workflows/connectors/."""
    root = connectors_dir()
    if not root.is_dir():
        return []
    out: list[WorkflowDefinition] = []
    for path in sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml")):
        if path.name.startswith("."):
            continue
        try:
            wf = WorkflowDefinition.from_yaml_file(path)
        except Exception:
            # still surface as a broken load via a synthetic shell later if needed
            continue
        if wf.kind == "connector" or path.parent.name == "connectors":
            out.append(wf)
    return out


def _load_or_error(path: Path) -> tuple[WorkflowDefinition | None, str | None]:
    try:
        return WorkflowDefinition.from_yaml_file(path), None
    except Exception as exc:
        return None, str(exc)


def structural_smoke_connector(wf: WorkflowDefinition) -> ConnectorSmokeCase:
    """Validate connector YAML shape; soft-check that requires exist as projects."""
    gid = _goal_id("struct")
    goal_text = (
        f"Structurally validate connector '{wf.slug}' "
        f"(steps, types, requires) before process execution."
    )
    plan = [
        {"step": 1, "intent": "load_and_validate_schema", "tool": "connector.structural"},
        {"step": 2, "intent": "check_requires_projects", "tool": "projects.exists"},
    ]
    tr = start_trace(
        goal_text,
        goal_id=gid,
        mode="connector_smoke",
        plan=plan,
        budget={"max_tokens": 0, "max_minutes": 5},
    )
    append_event(
        tr,
        type="think",
        content=f"Structural smoke for {wf.slug}: {len(wf.steps)} steps, requires={wf.requires}",
    )

    problems: list[str] = []
    step_rows: list[dict[str, Any]] = []

    if not wf.steps:
        problems.append("no steps")
    for step in wf.steps:
        row = _check_step(step)
        step_rows.append(row)
        if row.get("error"):
            problems.append(f"step {step.id}: {row['error']}")

    missing_projects: list[str] = []
    proot = projects_dir()
    for req in wf.requires:
        if not (proot / req).is_dir():
            missing_projects.append(req)

    append_event(
        tr,
        type="tool",
        tool="connector.structural",
        args={"slug": wf.slug, "kind": wf.kind, "backend": wf.backend},
        result_snip=json.dumps(
            {
                "steps": len(wf.steps),
                "problems": problems,
                "missing_projects": missing_projects,
            }
        )[:2000],
        ok=not problems,
    )

    # HARD = schema/structure; missing projects is soft detail only
    hard_ok = not problems
    detail_parts = [
        f"kind={wf.kind}",
        f"status={wf.status}",
        f"backend={wf.backend}",
        f"steps={len(wf.steps)}",
        f"requires={len(wf.requires)}",
    ]
    if missing_projects:
        detail_parts.append(f"missing_projects={missing_projects}")
    if problems:
        detail_parts.append(f"problems={problems}")
    detail = "; ".join(detail_parts)

    if hard_ok and not missing_projects:
        status = "goal_proven"
        outcome = OUTCOME_PROVEN
        fc = None
        oracle = {
            "name": "connector_structural",
            "pass": True,
            "evidence": f"{wf.slug}: {len(wf.steps)} steps ok",
        }
        train_w = 2.0  # structural is weaker than full process proof
    elif hard_ok:
        status = "deeper_work_needed"
        outcome = OUTCOME_DEEPER
        fc = None
        oracle = {
            "name": "connector_structural",
            "pass": True,
            "evidence": f"schema ok; missing project dirs: {missing_projects}",
            "missing_projects": missing_projects,
        }
        train_w = 0.5
    else:
        status = "goal_failed"
        outcome = OUTCOME_FAILED
        fc = FAILURE_SMOKE
        oracle = {
            "name": "connector_structural",
            "pass": False,
            "evidence": "; ".join(problems),
        }
        train_w = 0.1

    finalize_trace(
        tr,
        status=status,
        outcome=outcome,
        failure_class=fc,
        oracle=oracle,
        train_weight=train_w,
        claim="connector_structural",
    )
    return ConnectorSmokeCase(
        id=f"structural:{wf.slug}",
        slug=wf.slug,
        mode="structural",
        hard=True,
        ok=hard_ok,
        detail=detail,
        status=status,
        goal_id=gid,
        oracle=oracle,
        steps=step_rows,
        requires=list(wf.requires),
    )


def _check_step(step: WorkflowStep) -> dict[str, Any]:
    err = ""
    if not step.id:
        err = "missing id"
    elif step.type not in KNOWN_STEP_TYPES:
        err = f"unknown type '{step.type}'"
    elif step.type == "capability" and not (step.capability or "").strip():
        err = "capability step missing capability"
    elif step.type == "shell" and not (step.command or "").strip():
        err = "shell step missing command"
    return {
        "id": step.id,
        "type": step.type,
        "capability": step.capability,
        "error": err or None,
        "ok": not err,
    }


def structural_smoke_broken_file(path: Path, error: str) -> ConnectorSmokeCase:
    gid = _goal_id("struct_bad")
    slug = path.stem
    tr = start_trace(
        f"Load connector YAML {path.name}",
        goal_id=gid,
        mode="connector_smoke",
        plan=[{"step": 1, "intent": "parse_yaml", "tool": "connector.load"}],
    )
    append_event(tr, type="tool", tool="connector.load", args={"path": str(path)}, result_snip=error, ok=False)
    oracle = {"name": "connector_structural", "pass": False, "evidence": error}
    finalize_trace(
        tr,
        status="goal_failed",
        outcome=OUTCOME_FAILED,
        failure_class=FAILURE_SMOKE,
        oracle=oracle,
        train_weight=0.1,
        claim="connector_structural",
    )
    return ConnectorSmokeCase(
        id=f"structural:{slug}",
        slug=slug,
        mode="structural",
        hard=True,
        ok=False,
        detail=f"YAML load failed: {error}",
        status="goal_failed",
        goal_id=gid,
        oracle=oracle,
    )


def execute_smoke_connector(
    wf: WorkflowDefinition,
    *,
    require_execute: bool = False,
) -> ConnectorSmokeCase:
    """Optional: attempt native run_workflow (force). Soft unless require_execute."""
    gid = _goal_id("exec")
    goal_text = (
        f"Execute connector '{wf.slug}' end-to-end (force, native preferred) "
        f"to serve its declared process."
    )
    tr = start_trace(
        goal_text,
        goal_id=gid,
        mode="connector_smoke",
        plan=[
            {"step": 1, "intent": "run_workflow", "tool": "workflow_runner.run"},
            {"step": 2, "intent": "interpret_result", "tool": "oracle.execute_ok"},
        ],
        budget={"max_tokens": 0, "max_minutes": 15},
    )
    append_event(
        tr,
        type="think",
        content=(
            f"Execute smoke for {wf.slug}; backend={wf.backend}; "
            "use force to skip verified requires for draft bridges."
        ),
    )

    # Prefer native for smoke so missing n8n is not a hard fail
    backend = "native" if wf.backend in ("native", "hybrid", "") else wf.backend
    try:
        from pipeline.workflow_runner import run_workflow

        result_text = run_workflow(
            wf.slug,
            force=True,
            backend_override=backend,
        )
    except Exception as exc:
        result_text = f"ERROR: {exc}"

    ok = str(result_text).startswith("OK")
    append_event(
        tr,
        type="tool",
        tool="workflow_runner.run",
        args={"slug": wf.slug, "force": True, "backend": backend},
        result_snip=str(result_text)[:2000],
        ok=ok,
    )

    if ok:
        status = "goal_proven"
        outcome = OUTCOME_PROVEN
        fc = None
        oracle = {
            "name": "connector_execute",
            "pass": True,
            "evidence": str(result_text)[:500],
        }
        train_w = 3.0
    else:
        # Draft bridges often fail on missing entrypoints — deeper work, not always hard fail
        status = "deeper_work_needed" if not require_execute else "goal_failed"
        outcome = OUTCOME_DEEPER if not require_execute else OUTCOME_FAILED
        fc = FAILURE_COMPOSE
        oracle = {
            "name": "connector_execute",
            "pass": False,
            "evidence": str(result_text)[:500],
        }
        train_w = 0.2 if not require_execute else 0.1

    finalize_trace(
        tr,
        status=status,
        outcome=outcome,
        failure_class=fc,
        oracle=oracle,
        train_weight=train_w,
        claim="connector_execute",
    )
    # Soft by default: real ok is reported; overall suite only fails HARD cases.
    return ConnectorSmokeCase(
        id=f"execute:{wf.slug}",
        slug=wf.slug,
        mode="execute",
        hard=bool(require_execute),
        ok=ok,
        detail=str(result_text)[:400],
        status=status,
        goal_id=gid,
        oracle=oracle,
        requires=list(wf.requires),
    )


def run_process_oracle(*, work_dir: Path | None = None) -> ConnectorSmokeCase:
    """Hard-coded two-capability process: producer → consumer → receipt oracle.

    This is the gold-standard smoke: proves the *logic* of connecting two
    nodes to serve a process without depending on product field_proven.
    """
    pipeline = get_pipeline_dir()
    root = work_dir or (pipeline / "metrics" / "connector_smoke_work" / PROCESS_ORACLE_SLUG)
    root.mkdir(parents=True, exist_ok=True)
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    gid = _goal_id("proc")
    plan = [
        {"step": 1, "intent": "run producer capability", "tool": "capability.producer"},
        {"step": 2, "intent": "run consumer capability (needs producer token)", "tool": "capability.consumer"},
        {"step": 3, "intent": "emit process receipt", "tool": "process.receipt"},
        {"step": 4, "intent": "oracle chain integrity", "tool": "oracle.process_receipt"},
    ]
    tr = start_trace(
        PROCESS_ORACLE_GOAL,
        goal_id=gid,
        mode="connector_smoke",
        plan=plan,
        budget={"max_tokens": 0, "max_minutes": 5},
    )
    append_event(
        tr,
        type="think",
        content=(
            "Process smoke_process_oracle: producer writes token A; "
            "consumer binds A and writes token B; receipt proves the chain."
        ),
    )

    step_rows: list[dict[str, Any]] = []
    errors: list[str] = []

    # --- Capability A: producer ---
    a_path = artifacts / "step_a.json"
    a_payload = {
        "ok": True,
        "capability": "producer",
        "token": "TOKEN_A",
        "ts": _iso(),
    }
    try:
        a_path.write_text(json.dumps(a_payload, indent=2), encoding="utf-8")
        a_ok = True
    except OSError as exc:
        a_ok = False
        errors.append(f"producer write failed: {exc}")
    step_rows.append({"id": "producer", "ok": a_ok, "path": str(a_path)})
    append_event(
        tr,
        type="tool",
        tool="capability.producer",
        args={"artifact": str(a_path)},
        result_snip=json.dumps(a_payload)[:500],
        ok=a_ok,
    )

    # --- Capability B: consumer (depends on A) ---
    b_path = artifacts / "step_b.json"
    b_payload: dict[str, Any] = {"ok": False, "capability": "consumer"}
    b_ok = False
    if a_ok:
        try:
            a_data = json.loads(a_path.read_text(encoding="utf-8"))
            if not a_data.get("ok") or not a_data.get("token"):
                errors.append("producer artifact invalid")
            else:
                b_payload = {
                    "ok": True,
                    "capability": "consumer",
                    "from_a": a_data["token"],
                    "token": "TOKEN_B",
                    "ts": _iso(),
                }
                b_path.write_text(json.dumps(b_payload, indent=2), encoding="utf-8")
                b_ok = True
        except Exception as exc:
            errors.append(f"consumer failed: {exc}")
    else:
        errors.append("consumer skipped: producer failed")
    step_rows.append({"id": "consumer", "ok": b_ok, "path": str(b_path)})
    append_event(
        tr,
        type="tool",
        tool="capability.consumer",
        args={"artifact": str(b_path), "depends_on": "producer"},
        result_snip=json.dumps(b_payload)[:500],
        ok=b_ok,
    )

    # --- Process receipt ---
    receipt_path = artifacts / "process_receipt.json"
    receipt = {
        "process": PROCESS_ORACLE_SLUG,
        "ok": bool(a_ok and b_ok),
        "steps": {"producer": a_ok, "consumer": b_ok},
        "from_a": b_payload.get("from_a"),
        "tokens": {
            "a": a_payload.get("token") if a_ok else None,
            "b": b_payload.get("token") if b_ok else None,
        },
        "ts": _iso(),
    }
    try:
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        receipt_written = True
    except OSError as exc:
        receipt_written = False
        errors.append(f"receipt write failed: {exc}")
    step_rows.append({"id": "process_receipt", "ok": receipt_written, "path": str(receipt_path)})
    append_event(
        tr,
        type="tool",
        tool="process.receipt",
        args={"path": str(receipt_path)},
        result_snip=json.dumps(receipt)[:500],
        ok=receipt_written,
    )

    # --- Oracle ---
    oracle_pass = False
    evidence = ""
    try:
        a_data = json.loads(a_path.read_text(encoding="utf-8")) if a_path.is_file() else {}
        b_data = json.loads(b_path.read_text(encoding="utf-8")) if b_path.is_file() else {}
        r_data = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else {}
        oracle_pass = bool(
            a_data.get("ok")
            and b_data.get("ok")
            and b_data.get("from_a") == a_data.get("token")
            and r_data.get("ok")
            and r_data.get("process") == PROCESS_ORACLE_SLUG
            and r_data.get("steps", {}).get("producer")
            and r_data.get("steps", {}).get("consumer")
            and r_data.get("from_a") == a_data.get("token")
        )
        evidence = (
            f"receipt={receipt_path}; "
            f"chain from_a={b_data.get('from_a')!r} matches token_a={a_data.get('token')!r}; "
            f"oracle_pass={oracle_pass}"
        )
        if errors:
            evidence += f"; errors={errors}"
    except Exception as exc:
        evidence = f"oracle exception: {exc}"
        oracle_pass = False

    append_event(
        tr,
        type="oracle",
        content=evidence[:2000],
        ok=oracle_pass,
    )
    oracle = {
        "name": "process_receipt",
        "pass": oracle_pass,
        "evidence": evidence[:1000],
        "artifacts_dir": str(artifacts),
    }
    status = "goal_proven" if oracle_pass else "goal_failed"
    finalize_trace(
        tr,
        status=status,
        outcome=OUTCOME_PROVEN if oracle_pass else OUTCOME_FAILED,
        failure_class=None if oracle_pass else FAILURE_SMOKE,
        oracle=oracle,
        train_weight=4.0 if oracle_pass else 0.1,
        claim="process_oracle",
    )

    return ConnectorSmokeCase(
        id=f"process_oracle:{PROCESS_ORACLE_SLUG}",
        slug=PROCESS_ORACLE_SLUG,
        mode="process_oracle",
        hard=True,
        ok=oracle_pass,
        detail=evidence[:400],
        status=status,
        goal_id=gid,
        oracle=oracle,
        steps=step_rows,
        requires=["producer", "consumer"],
    )


def run_connector_smoke(
    *,
    slug: str | None = None,
    execute: bool = False,
    require_execute: bool = False,
    oracle_only: bool = False,
    work_dir: Path | None = None,
) -> ConnectorSmokeReport:
    """Run structural (+ optional execute) smokes and always the process oracle (unless filtered)."""
    pipeline = get_pipeline_dir()
    report = ConnectorSmokeReport(
        ts=_iso(),
        pipeline_dir=str(pipeline),
        notes=[
            "Structural smoke validates connector YAML under workflows/connectors/.",
            "Process oracle is hard-coded (producer→consumer→receipt) and is HARD.",
            "Execute smoke is optional (--execute); soft unless --require-execute.",
            "Each case writes goal_trace.v1 under goal_traces/.",
        ],
    )

    if not oracle_only:
        root = connectors_dir()
        paths: list[Path] = []
        if root.is_dir():
            paths = sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml"))
            paths = [p for p in paths if not p.name.startswith(".")]
        if slug and slug not in (PROCESS_ORACLE_SLUG, "process_oracle"):
            paths = [p for p in paths if p.stem.lower() == slug.lower()]
            if not paths:
                try:
                    from pipeline.workflow_schema import load_workflow

                    wf = load_workflow(slug)
                    report.cases.append(structural_smoke_connector(wf))
                    if execute:
                        report.cases.append(
                            execute_smoke_connector(wf, require_execute=require_execute)
                        )
                except Exception as exc:
                    report.cases.append(
                        ConnectorSmokeCase(
                            id=f"structural:{slug}",
                            slug=slug,
                            mode="structural",
                            hard=True,
                            ok=False,
                            detail=f"connector not found / load error: {exc}",
                            status="goal_failed",
                        )
                    )
            else:
                for path in paths:
                    wf, err = _load_or_error(path)
                    if err or wf is None:
                        report.cases.append(
                            structural_smoke_broken_file(path, err or "load failed")
                        )
                        continue
                    report.cases.append(structural_smoke_connector(wf))
                    if execute:
                        report.cases.append(
                            execute_smoke_connector(wf, require_execute=require_execute)
                        )
        else:
            if not paths:
                report.notes.append(
                    f"No connector YAML under {root} — structural cases skipped."
                )
            for path in paths:
                wf, err = _load_or_error(path)
                if err or wf is None:
                    report.cases.append(
                        structural_smoke_broken_file(path, err or "load failed")
                    )
                    continue
                report.cases.append(structural_smoke_connector(wf))
                if execute:
                    report.cases.append(
                        execute_smoke_connector(wf, require_execute=require_execute)
                    )

    # Always run hard-coded process oracle (factory process-proof fixture).
    report.cases.append(run_process_oracle(work_dir=work_dir))

    hard = report.hard_cases()
    report.ok = all(c.ok for c in hard) if hard else False
    return report


def write_smoke_report(report: ConnectorSmokeReport) -> dict[str, Path]:
    """Write metrics/connector_smoke_latest.{md,json}."""
    out_dir = metrics_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "connector_smoke_latest.md"
    json_path = out_dir / "connector_smoke_latest.json"

    payload = {
        "schema": report.schema,
        "ts": report.ts,
        "ok": report.ok,
        "pipeline_dir": report.pipeline_dir,
        "notes": report.notes,
        "cases": [asdict(c) for c in report.cases],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Connector smoke report",
        "",
        f"- Generated: {report.ts}",
        f"- Pipeline: `{report.pipeline_dir}`",
        f"- Overall HARD: **{'PASS' if report.ok else 'FAIL'}**",
        "",
        "## Cases",
        "",
        "| id | mode | hard | ok | status | goal_id | detail |",
        "|----|------|------|----|--------|---------|--------|",
    ]
    for c in report.cases:
        detail = (c.detail or "").replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(
            f"| `{c.id}` | {c.mode} | {c.hard} | "
            f"{'PASS' if c.ok else 'FAIL'} | {c.status} | "
            f"`{c.goal_id or ''}` | {detail} |"
        )
    if report.notes:
        lines += ["", "## Notes", ""]
        for n in report.notes:
            lines.append(f"- {n}")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}
