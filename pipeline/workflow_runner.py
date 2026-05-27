"""
pipeline/workflow_runner.py
Execute workflow/connector definitions (native, n8n, or hybrid backends).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

from pipeline.capability_registry import PROJECT_ROOT
from pipeline.n8n_bridge import run_n8n_backend, run_n8n_step
from pipeline.workflow_schema import (
    WorkflowDefinition,
    WorkflowStep,
    eval_when,
    load_workflow,
    render_template,
)


def _initial_context(wf: WorkflowDefinition, input_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflow": {
            "slug": wf.slug,
            "title": wf.title,
            "backend": wf.backend,
        },
        "input": input_data,
        "steps": {},
        "n8n": {
            "base_url": wf.n8n.base_url,
            "webhook_path": wf.n8n.webhook_path,
            "workflow_id": wf.n8n.workflow_id,
        },
        "env": dict(os.environ),
    }


def _check_requires(wf: WorkflowDefinition, *, force: bool = False) -> list[str]:
    if force:
        return []
    from pipeline.capability_graph import missing_requires

    return missing_requires(wf.slug)


def _run_capability_step(step: WorkflowStep, context: dict[str, Any], *, force: bool) -> dict[str, Any]:
    slug = render_template(step.capability, context).strip()
    args = render_template(step.args, context).strip()
    cwd = render_template(step.cwd, context).strip()

    from pipeline.capability_tools import invoke_capability

    if force:
        # Direct invoke bypassing verified check — load row and run entrypoint
        from pipeline.capability_registry import _connect
        from pipeline.paths import registry_db

        if not registry_db().exists():
            return {"ok": False, "error": f"registry missing for capability {slug}"}
        conn = _connect()
        row = conn.execute(
            "SELECT entrypoint, cwd_template, status FROM capabilities WHERE slug = ?",
            (slug,),
        ).fetchone()
        conn.close()
        if not row or not row["entrypoint"]:
            return {"ok": False, "error": f"capability '{slug}' has no entrypoint"}
        entry = row["entrypoint"]
        work_dir = PROJECT_ROOT
        if cwd:
            work_dir = (PROJECT_ROOT / cwd).resolve()
        elif row["cwd_template"]:
            work_dir = (PROJECT_ROOT / row["cwd_template"]).resolve()
        cmd = f"{entry} {args}".strip()
        try:
            argv = shlex.split(cmd, posix=False)
            result = subprocess.run(
                argv,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=step.timeout_s,
                shell=False,
            )
            out = (result.stdout or "") + (result.stderr or "")
            return {
                "ok": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": out[:4000],
                "capability": slug,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "capability": slug}

    out = invoke_capability(slug, args=args, cwd=cwd)
    ok = out.startswith("OK")
    return {"ok": ok, "stdout": out, "capability": slug}


def _run_shell_step(step: WorkflowStep, context: dict[str, Any]) -> dict[str, Any]:
    cmd = render_template(step.command, context).strip()
    if not cmd:
        return {"ok": False, "error": "shell step missing command"}
    if re.search(r"[;&|`$<>]", cmd):
        return {"ok": False, "error": "shell command contains disallowed characters"}
    cwd = render_template(step.cwd, context).strip() or "."
    work_dir = (PROJECT_ROOT / cwd).resolve()
    try:
        work_dir.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return {"ok": False, "error": "cwd must stay inside project root"}
    try:
        argv = shlex.split(cmd, posix=False)
        result = subprocess.run(
            argv,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=step.timeout_s,
            shell=False,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return {
            "ok": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": out[:4000],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {step.timeout_s}s"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _run_step(
    step: WorkflowStep,
    wf: WorkflowDefinition,
    context: dict[str, Any],
    *,
    force: bool,
) -> dict[str, Any]:
    stype = step.type
    if stype == "capability":
        return _run_capability_step(step, context, force=force)
    if stype == "shell":
        return _run_shell_step(step, context)
    if stype in ("n8n_webhook", "n8n_execute"):
        return run_n8n_step(step, wf.n8n, context)
    return {"ok": False, "error": f"unknown step type '{stype}'"}


def run_workflow(
    slug: str,
    *,
    args: str = "",
    json_input: dict[str, Any] | None = None,
    step_id: str = "",
    force: bool = False,
    backend_override: str = "",
) -> str:
    """Run a workflow by slug. Returns human-readable result for agents/CLI."""
    try:
        wf = load_workflow(slug)
    except FileNotFoundError as e:
        return f"ERROR: {e}"

    input_data: dict[str, Any] = dict(json_input or {})
    if args and not input_data:
        input_data["args"] = args

    blocked = _check_requires(wf, force=force)
    if blocked:
        return (
            f"ERROR: Workflow '{slug}' blocked — prerequisites not verified: "
            f"{', '.join(blocked)} (use --force to skip)"
        )

    backend = (backend_override or wf.backend or "native").lower()

    if backend == "n8n":
        result = run_n8n_backend(wf, input_data)
        try:
            from pipeline.capability_metrics import log_capability_event

            log_capability_event("workflow", slug, ok=bool(result.get("ok")), detail="backend=n8n")
        except Exception:
            pass
        if result.get("ok"):
            body = json.dumps(result.get("body", result), indent=2)[:3000]
            return f"OK (n8n): {body}"
        return f"FAIL (n8n): {json.dumps(result, indent=2)[:3000]}"

    context = _initial_context(wf, input_data)
    steps_to_run = wf.steps
    if step_id:
        steps_to_run = [s for s in wf.steps if s.id == step_id]
        if not steps_to_run:
            return f"ERROR: unknown step id '{step_id}'"

    failed = False
    lines = [f"Workflow '{wf.slug}' ({backend}) — {len(steps_to_run)} step(s)"]

    for step in steps_to_run:
        if not eval_when(step.when, context):
            lines.append(f"  SKIP {step.id} (when={step.when})")
            context["steps"][step.save_as or step.id] = {"ok": True, "skipped": True}
            continue

        if backend == "hybrid" and step.type in ("n8n_webhook", "n8n_execute"):
            outcome = _run_step(step, wf, context, force=force)
            key = step.save_as or step.id
            context["steps"][key] = outcome
            tag = "OK" if outcome.get("ok") else "FAIL"
            lines.append(f"  {tag} {step.id} ({step.type})")
            if not outcome.get("ok"):
                failed = True
                err = outcome.get("error") or outcome.get("stdout", "")[:200]
                lines.append(f"       {err}")
                break
            continue

        if backend == "native" and step.type in ("n8n_webhook", "n8n_execute"):
            lines.append(f"  SKIP {step.id} (n8n step with native backend; use --backend hybrid or n8n)")
            continue

        outcome = _run_step(step, wf, context, force=force)
        key = step.save_as or step.id
        context["steps"][key] = outcome
        tag = "OK" if outcome.get("ok") else "FAIL"
        lines.append(f"  {tag} {step.id} ({step.type})")
        if not outcome.get("ok"):
            failed = True
            err = outcome.get("error") or outcome.get("stdout", "")[:200]
            lines.append(f"       {err}")
            break

    try:
        from pipeline.capability_metrics import log_capability_event

        log_capability_event("workflow", slug, ok=not failed, detail=f"backend={backend}")
    except Exception:
        pass

    prefix = "FAIL" if failed else "OK"
    return prefix + ":\n" + "\n".join(lines)


def format_workflow_result_for_agent(text: str) -> str:
    if len(text) > 4000:
        return text[:4000] + "\n...(truncated)"
    return text
