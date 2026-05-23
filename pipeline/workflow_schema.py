"""
pipeline/workflow_schema.py
YAML workflow/connector definitions — native runner + optional n8n backend.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from typing import Any

import yaml

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
WORKFLOWS_DIR = PROJECT_ROOT / ".pipeline" / "workflows"

_TEMPLATE_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


@dataclass
class N8nConfig:
    base_url: str = "http://localhost:5678"
    webhook_path: str = ""
    workflow_id: str = ""
    api_key_env: str = "N8N_API_KEY"
    timeout_s: int = 300

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> N8nConfig:
        if not data:
            return cls()
        return cls(
            base_url=str(data.get("base_url") or cls.base_url),
            webhook_path=str(data.get("webhook_path") or ""),
            workflow_id=str(data.get("workflow_id") or ""),
            api_key_env=str(data.get("api_key_env") or "N8N_API_KEY"),
            timeout_s=int(data.get("timeout_s") or 300),
        )


@dataclass
class WorkflowStep:
    id: str
    type: str  # capability | shell | n8n_webhook | n8n_execute
    capability: str = ""
    command: str = ""
    args: str = ""
    cwd: str = ""
    url: str = ""
    method: str = "POST"
    body: dict[str, Any] = field(default_factory=dict)
    save_as: str = ""
    when: str = ""
    timeout_s: int = 120

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowStep:
        sid = str(data.get("id") or "").strip()
        if not sid:
            raise ValueError("workflow step missing id")
        stype = str(data.get("type") or "capability").strip().lower()
        body = data.get("body")
        return cls(
            id=sid,
            type=stype,
            capability=str(data.get("capability") or ""),
            command=str(data.get("command") or ""),
            args=str(data.get("args") or ""),
            cwd=str(data.get("cwd") or ""),
            url=str(data.get("url") or ""),
            method=str(data.get("method") or "POST").upper(),
            body=body if isinstance(body, dict) else {},
            save_as=str(data.get("save_as") or sid),
            when=str(data.get("when") or ""),
            timeout_s=int(data.get("timeout_s") or 120),
        )


@dataclass
class WorkflowDefinition:
    slug: str
    title: str
    kind: str  # workflow | connector
    status: str
    purpose: str
    requires: list[str]
    backend: str  # native | n8n | hybrid
    steps: list[WorkflowStep]
    n8n: N8nConfig
    source_path: pathlib.Path | None = None
    domains: list[str] = field(default_factory=lambda: ["devops"])

    @classmethod
    def from_yaml_file(cls, path: pathlib.Path) -> WorkflowDefinition:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: expected YAML mapping")
        slug = str(raw.get("slug") or path.stem).strip()
        steps_raw = raw.get("steps") or []
        if not isinstance(steps_raw, list) or not steps_raw:
            raise ValueError(f"{path}: workflow must define at least one step")
        steps = [WorkflowStep.from_dict(s) for s in steps_raw if isinstance(s, dict)]
        requires_raw = raw.get("requires") or []
        requires = [str(r).strip() for r in requires_raw if str(r).strip()]
        return cls(
            slug=slug,
            title=str(raw.get("title") or slug.replace("_", " ").title()),
            kind=str(raw.get("kind") or "workflow").strip().lower(),
            status=str(raw.get("status") or "draft").strip().lower(),
            purpose=str(raw.get("purpose") or "")[:400],
            requires=requires,
            backend=str(raw.get("backend") or "native").strip().lower(),
            steps=steps,
            n8n=N8nConfig.from_dict(raw.get("n8n") if isinstance(raw.get("n8n"), dict) else None),
            source_path=path,
            domains=[str(d) for d in (raw.get("domains") or ["devops"])],
        )


def list_workflow_files() -> list[pathlib.Path]:
    if not WORKFLOWS_DIR.exists():
        return []
    out: list[pathlib.Path] = []
    for p in sorted(WORKFLOWS_DIR.rglob("*.yaml")):
        if p.name.startswith("."):
            continue
        out.append(p)
    for p in sorted(WORKFLOWS_DIR.rglob("*.yml")):
        if p.name.startswith("."):
            continue
        out.append(p)
    return out


def load_workflow(slug: str) -> WorkflowDefinition:
    slug = slug.strip().lower()
    for path in list_workflow_files():
        try:
            wf = WorkflowDefinition.from_yaml_file(path)
        except Exception:
            continue
        if wf.slug == slug:
            return wf
    raise FileNotFoundError(f"workflow '{slug}' not found under {WORKFLOWS_DIR}")


def render_template(text: str, context: dict[str, Any]) -> str:
    """Replace {{ dotted.path }} placeholders from context."""

    def _lookup(path: str) -> str:
        cur: Any = context
        for part in path.strip().split("."):
            if isinstance(cur, dict):
                cur = cur.get(part, "")
            else:
                return ""
        if cur is None:
            return ""
        return str(cur)

    def _repl(m: re.Match[str]) -> str:
        return _lookup(m.group(1))

    return _TEMPLATE_RE.sub(_repl, text)


def eval_when(expr: str, context: dict[str, Any]) -> bool:
    if not expr.strip():
        return True
    rendered = render_template(expr, context).strip().lower()
    if rendered in ("", "0", "false", "no", "fail", "failed"):
        return False
    return True
