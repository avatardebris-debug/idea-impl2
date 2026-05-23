"""
pipeline/n8n_bridge.py
Self-hosted n8n integration: webhook/API trigger + export to n8n workflow JSON.

Native runner remains the default; set workflow backend to n8n or hybrid to delegate
execution to a self-hosted n8n instance, or export YAML workflows for import in n8n UI.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from pipeline.workflow_schema import N8nConfig, WorkflowDefinition, WorkflowStep


def _resolve_env(value: str) -> str:
    """Expand ${VAR} and ${VAR:-default} in config strings."""
    if not value:
        return value
    out = value
    if "${" in out:
        import re

        for m in re.finditer(r"\$\{([^}:]+)(?::-([^}]*))?\}", out):
            key = m.group(1)
            default = m.group(2) if m.group(2) is not None else ""
            out = out.replace(m.group(0), os.environ.get(key, default))
    return out


def _api_key(cfg: N8nConfig) -> str:
    return os.environ.get(cfg.api_key_env, "").strip()


def n8n_health(base_url: str, api_key: str = "") -> tuple[bool, str]:
    """Ping n8n REST API (requires API key on most self-hosted installs)."""
    url = _resolve_env(base_url.rstrip("/")) + "/api/v1/workflows?limit=1"
    req = urllib.request.Request(url, method="GET")
    if api_key:
        req.add_header("X-N8N-API-KEY", api_key)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True, f"n8n reachable (HTTP {resp.status})"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, f"n8n reachable but API key rejected (HTTP {e.code})"
        return False, f"n8n HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, str(e)


def trigger_webhook(
    cfg: N8nConfig,
    payload: dict[str, Any],
    *,
    webhook_path: str = "",
) -> dict[str, Any]:
    """POST payload to n8n webhook (production or test path)."""
    base = _resolve_env(cfg.base_url).rstrip("/")
    path = _resolve_env(webhook_path or cfg.webhook_path)
    if not path:
        raise ValueError("n8n webhook_path is required")
    if not path.startswith("/"):
        path = "/" + path
    url = base + path
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    api_key = _api_key(cfg)
    if api_key:
        req.add_header("X-N8N-API-KEY", api_key)
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                parsed = {"raw": raw}
            return {"ok": True, "status": resp.status, "body": parsed, "url": url}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:2000]
        return {"ok": False, "status": e.code, "error": err_body, "url": url}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url}


def execute_workflow_api(cfg: N8nConfig, input_data: dict[str, Any]) -> dict[str, Any]:
    """Trigger workflow via n8n public API (self-hosted, API key required).

    Uses POST /api/v1/workflows/{id}/run when workflow_id is set.
    Falls back to webhook if only webhook_path is configured.
    """
    wf_id = _resolve_env(cfg.workflow_id)
    if wf_id:
        base = _resolve_env(cfg.base_url).rstrip("/")
        url = f"{base}/api/v1/workflows/{wf_id}/run"
        api_key = _api_key(cfg)
        if not api_key:
            return {"ok": False, "error": f"Missing API key env {cfg.api_key_env}"}
        body = json.dumps(input_data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-N8N-API-KEY": api_key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(raw) if raw.strip() else {}
                except json.JSONDecodeError:
                    parsed = {"raw": raw}
                return {"ok": True, "status": resp.status, "body": parsed, "url": url}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:2000]
            return {"ok": False, "status": e.code, "error": err_body, "url": url}
        except Exception as e:
            return {"ok": False, "error": str(e), "url": url}
    return trigger_webhook(cfg, input_data)


def run_n8n_backend(wf: WorkflowDefinition, input_data: dict[str, Any]) -> dict[str, Any]:
    """Delegate entire workflow to n8n (replacement mode)."""
    payload = {
        "workflow_slug": wf.slug,
        "workflow_title": wf.title,
        "input": input_data,
        "steps": [{"id": s.id, "type": s.type, "capability": s.capability} for s in wf.steps],
    }
    if wf.n8n.workflow_id:
        return execute_workflow_api(wf.n8n, payload)
    return trigger_webhook(wf.n8n, payload)


def run_n8n_step(step: WorkflowStep, cfg: N8nConfig, context: dict[str, Any]) -> dict[str, Any]:
    """Run a single n8n step inside hybrid/native workflows."""
    from pipeline.workflow_schema import render_template

    if step.type == "n8n_webhook":
        url = render_template(step.url, context) if step.url else ""
        body = step.body or {"context": context.get("steps", {})}
        if step.url:
            # Custom URL overrides cfg webhook
            import urllib.request

            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                method=step.method,
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=step.timeout_s) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                    return {"ok": True, "status": resp.status, "stdout": raw[:4000]}
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return trigger_webhook(cfg, body, webhook_path=cfg.webhook_path)

    if step.type == "n8n_execute":
        payload = step.body or {"step_id": step.id, "context": context.get("steps", {})}
        return execute_workflow_api(cfg, payload)

    return {"ok": False, 'error': f"unknown n8n step type {step.type}"}


def _node_position(index: int) -> list[int]:
    return [280 + index * 220, 300]


def export_to_n8n_json(wf: WorkflowDefinition) -> dict[str, Any]:
    """Export pipeline workflow YAML to n8n-importable workflow JSON (subset).

    Generated workflow:
    - Webhook trigger (path = slug)
    - One Execute Command node per native step (calls pipeline CLI)
    - Optional sticky note with n8n self-host config

    After import: set n8n credentials / paths, activate workflow, copy webhook URL
    back into workflow YAML `n8n.webhook_path`.
    """
    nodes: list[dict[str, Any]] = []
    connections: dict[str, Any] = {}

    webhook_name = "Pipeline Webhook"
    nodes.append(
        {
            "parameters": {
                "httpMethod": "POST",
                "path": wf.slug.replace("_", "-"),
                "responseMode": "lastNode",
                "options": {},
            },
            "id": "webhook-trigger",
            "name": webhook_name,
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": _node_position(0),
            "webhookId": wf.slug,
        }
    )

    prev_name = webhook_name
    for i, step in enumerate(wf.steps):
        node_name = f"Step {step.id}"
        if step.type in ("n8n_webhook", "n8n_execute"):
            nodes.append(
                {
                    "parameters": {
                        "method": step.method,
                        "url": step.url or f"={{{{ $env.N8N_BASE_URL }}}}/webhook/{wf.slug}",
                        "sendBody": True,
                        "specifyBody": "json",
                        "jsonBody": json.dumps(step.body or {"step": step.id}),
                        "options": {},
                    },
                    "id": f"http-{step.id}",
                    "name": node_name,
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 4,
                    "position": _node_position(i + 1),
                }
            )
        elif step.type == "capability":
            cmd = (
                f"python scripts/run_workflow.py {wf.slug} "
                f"--step {step.id} --json-input '{{{{ JSON.stringify($json) }}}}'"
            )
            nodes.append(
                {
                    "parameters": {
                        "command": cmd,
                    },
                    "id": f"exec-{step.id}",
                    "name": node_name,
                    "type": "n8n-nodes-base.executeCommand",
                    "typeVersion": 1,
                    "position": _node_position(i + 1),
                    "notes": f"capability={step.capability} args={step.args}",
                }
            )
        else:
            cmd = step.command or f"python scripts/run_workflow.py {wf.slug} --step {step.id}"
            nodes.append(
                {
                    "parameters": {"command": cmd},
                    "id": f"exec-{step.id}",
                    "name": node_name,
                    "type": "n8n-nodes-base.executeCommand",
                    "typeVersion": 1,
                    "position": _node_position(i + 1),
                }
            )

        connections[prev_name] = {
            "main": [[{"node": node_name, "type": "main", "index": 0}]]
        }
        prev_name = node_name

    return {
        "name": wf.title,
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
        "meta": {
            "pipeline_slug": wf.slug,
            "pipeline_backend": wf.backend,
            "pipeline_requires": wf.requires,
            "export_note": (
                "Imported from idea-pipeline workflow YAML. "
                "Set N8N_BASE_URL and pipeline cwd on execute nodes; "
                "activate workflow; set n8n.webhook_path in .pipeline/workflows/*.yaml"
            ),
        },
        "pinData": {},
    }
