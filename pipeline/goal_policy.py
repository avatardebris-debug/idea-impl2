"""
Thin goal compose policy (v0/v1) — aligned with notes/agi-lmaooo.md.

Classify how to pursue a goal branch before execution:

  reuse    — invoke an existing verified capability
  compose  — run a connector / multi-capability workflow
  build    — needs software factory (not executed here; signal only)
  research — Hermes / knowledge task
  mcp      — enqueue MCP factory wrap job (never invent server here)
  yield    — cannot act now (blocked requires, unknown)

Durable goal_trace.v1 when KEEP_GOAL_TRACES is default-on (unset/1/true/yes/on).
Set KEEP_GOAL_TRACES=0/false/no/off to skip writing new traces (in-memory only).
"""


from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.goal_trace import (
    FAILURE_CAPABILITY,
    FAILURE_COMPOSE,
    FAILURE_MCP_ENQUEUED,
    FAILURE_POLICY_YIELD,
    OUTCOME_DEEPER,
    OUTCOME_FAILED,
    OUTCOME_PROVEN,
    append_event,
    finalize_trace,
    start_trace,
)
from pipeline.paths import connectors_dir, get_pipeline_dir

POLICY_REUSE = "reuse"
POLICY_COMPOSE = "compose"
POLICY_BUILD = "build"
POLICY_RESEARCH = "research"
POLICY_MCP = "mcp"
POLICY_YIELD = "yield"

POLICIES = frozenset(
    {
        POLICY_REUSE,
        POLICY_COMPOSE,
        POLICY_BUILD,
        POLICY_RESEARCH,
        POLICY_MCP,
        POLICY_YIELD,
    }
)

# Text suggests wrapping / exposing something as MCP
_MCP_TEXT_RE = re.compile(
    r"\b(as\s+)?mcp\b|\bmodel context protocol\b|\bwrap\b.*\bmcp\b",
    re.IGNORECASE,
)


@dataclass
class GoalPolicyDecision:
    policy: str
    reason: str
    capability_slug: str | None = None
    connector_slug: str | None = None
    hits: list[dict[str, Any]] | None = None


def _list_connector_slugs() -> list[tuple[str, list[str]]]:
    """Return (slug, requires) for connector YAMLs."""
    root = connectors_dir()
    if not root.is_dir():
        return []
    out: list[tuple[str, list[str]]] = []
    try:
        from pipeline.workflow_schema import WorkflowDefinition

        for path in sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml")):
            if path.name.startswith("."):
                continue
            try:
                wf = WorkflowDefinition.from_yaml_file(path)
            except Exception:
                continue
            if wf.kind != "connector" and path.parent.name != "connectors":
                continue
            out.append((wf.slug, list(wf.requires or [])))
    except Exception:
        pass
    return out


def classify_goal_branch(
    *,
    branch_type: str,
    text: str,
    requires: list[str] | None = None,
    hermes_prompt: str = "",
    route_hits: list[dict[str, Any]] | None = None,
) -> GoalPolicyDecision:
    """Map branch metadata + router hits → policy (no side effects)."""
    btype = (branch_type or "").strip().lower()
    requires = list(requires or [])
    hits = list(route_hits or [])

    if btype == "hermes_task" or hermes_prompt:
        return GoalPolicyDecision(
            policy=POLICY_RESEARCH,
            reason="hermes_task or hermes_prompt set",
        )

    # MCP: router hit with kind=mcp and requires_ok
    for hit in hits:
        if hit.get("requires_ok") and hit.get("slug"):
            kind = str(hit.get("kind") or "").lower()
            if kind == "mcp":
                slug = str(hit["slug"])
                # Prefer explicit connector_slug on hit; else treat slug as capability
                if hit.get("connector_slug"):
                    return GoalPolicyDecision(
                        policy=POLICY_MCP,
                        reason=f"router hit mcp {slug}",
                        connector_slug=str(hit["connector_slug"]),
                        hits=hits,
                    )
                return GoalPolicyDecision(
                    policy=POLICY_MCP,
                    reason=f"router hit mcp {slug}",
                    capability_slug=slug,
                    hits=hits,
                )

    # MCP: text suggests wrap/as MCP (prefer first reuse-capable hit as wrap target)
    text_raw = text or ""
    if _MCP_TEXT_RE.search(text_raw):
        wrap_slug: str | None = None
        wrap_connector = False
        for hit in hits:
            if hit.get("requires_ok") and hit.get("slug"):
                wrap_slug = str(hit["slug"])
                kind = str(hit.get("kind") or "").lower()
                wrap_connector = kind in ("workflow", "connector")
                break
        if wrap_slug:
            if wrap_connector:
                return GoalPolicyDecision(
                    policy=POLICY_MCP,
                    reason=f"text requests mcp wrap of connector {wrap_slug}",
                    connector_slug=wrap_slug,
                    hits=hits,
                )
            return GoalPolicyDecision(
                policy=POLICY_MCP,
                reason=f"text requests mcp wrap of {wrap_slug}",
                capability_slug=wrap_slug,
                hits=hits,
            )
        return GoalPolicyDecision(
            policy=POLICY_MCP,
            reason="text requests mcp wrap; no reuse-capable hit (needs wrap target)",
            hits=hits,
        )

    # Prefer invokable capability hits
    for hit in hits:
        if hit.get("requires_ok") and hit.get("slug"):
            kind = str(hit.get("kind") or "").lower()
            slug = str(hit["slug"])
            if kind in ("workflow", "connector"):
                return GoalPolicyDecision(
                    policy=POLICY_COMPOSE,
                    reason=f"router hit connector/workflow {slug}",
                    connector_slug=slug,
                    hits=hits,
                )
            return GoalPolicyDecision(
                policy=POLICY_REUSE,
                reason=f"router hit capability {slug}",
                capability_slug=slug,
                hits=hits,
            )

    # Compose: connector whose requires are subset of branch requires / mentioned slugs
    text_l = text_raw.lower()
    mentioned = set(requires)
    for m in re.finditer(r"\b([a-z][a-z0-9_]{2,})\b", text_l):
        mentioned.add(m.group(1))

    for cslug, creq in _list_connector_slugs():
        if not creq:
            continue
        if all(r in mentioned or r.replace("-", "_") in mentioned for r in creq):
            return GoalPolicyDecision(
                policy=POLICY_COMPOSE,
                reason=f"connector {cslug} requires matched in goal text/requires",
                connector_slug=cslug,
                hits=hits,
            )
        # also: all requires projects exist as field_proven / complete later — v0 text match only

    if btype in ("software", "robot_skill", "capability_gap"):
        return GoalPolicyDecision(
            policy=POLICY_BUILD,
            reason=f"type={btype} and no reusable capability/connector",
            hits=hits,
        )

    if requires and not hits:
        return GoalPolicyDecision(
            policy=POLICY_YIELD,
            reason="has requires but nothing invokable yet",
            hits=hits,
        )

    return GoalPolicyDecision(
        policy=POLICY_YIELD,
        reason=f"unclassified type={btype or 'unknown'}",
        hits=hits,
    )


def execute_policy(
    decision: GoalPolicyDecision,
    *,
    goal_text: str,
    branch_id: str = "",
    force_compose: bool = True,
) -> dict[str, Any]:
    """Execute reuse/compose (build/research/yield are signals). Always goal_trace."""
    plan = [
        {"step": 1, "intent": "classify", "tool": "goal_policy.classify"},
        {"step": 2, "intent": f"act_{decision.policy}", "tool": f"policy.{decision.policy}"},
    ]
    tr = start_trace(
        goal_text or f"branch {branch_id}",
        mode="goal_policy",
        plan=plan,
        budget={"max_tokens": 0, "max_minutes": 15},
    )
    append_event(
        tr,
        type="think",
        content=f"policy={decision.policy} reason={decision.reason}",
    )
    append_event(
        tr,
        type="tool",
        tool="goal_policy.classify",
        args={
            "policy": decision.policy,
            "capability": decision.capability_slug,
            "connector": decision.connector_slug,
        },
        result_snip=decision.reason[:500],
        ok=True,
    )

    result: dict[str, Any] = {
        "policy": decision.policy,
        "reason": decision.reason,
        "goal_id": tr.get("goal_id"),
        "status": "failed",
    }

    if decision.policy == POLICY_REUSE and decision.capability_slug:
        try:
            from pipeline.capability_tools import invoke_capability

            out = invoke_capability(decision.capability_slug, args="")
            ok = str(out).startswith("OK")
            append_event(
                tr,
                type="tool",
                tool="invoke_capability",
                args={"slug": decision.capability_slug},
                result_snip=str(out)[:1500],
                ok=ok,
            )
            result["output"] = str(out)[:500]
            result["capability"] = decision.capability_slug
            result["status"] = "achieved" if ok else "failed"
            finalize_trace(
                tr,
                status="goal_proven" if ok else "goal_failed",
                outcome=OUTCOME_PROVEN if ok else OUTCOME_FAILED,
                failure_class=None if ok else FAILURE_CAPABILITY,
                oracle={
                    "name": "capability_invoke",
                    "pass": ok,
                    "evidence": decision.capability_slug,
                },
                claim="capability_invoke",
                train_weight=4.0 if ok else 0.1,
            )
            return result
        except Exception as exc:
            append_event(tr, type="observe", content=str(exc), ok=False)
            finalize_trace(
                tr,
                status="goal_failed",
                outcome=OUTCOME_FAILED,
                failure_class=FAILURE_CAPABILITY,
                oracle={"name": "capability_invoke", "pass": False, "evidence": str(exc)},
                claim="capability_invoke",
            )
            result["reason"] = str(exc)
            return result

    if decision.policy == POLICY_COMPOSE and decision.connector_slug:
        try:
            from pipeline.workflow_runner import run_workflow

            out = run_workflow(
                decision.connector_slug,
                force=force_compose,
                backend_override="native",
            )
            ok = str(out).startswith("OK")
            append_event(
                tr,
                type="tool",
                tool="run_workflow",
                args={"slug": decision.connector_slug, "force": force_compose},
                result_snip=str(out)[:1500],
                ok=ok,
            )
            result["output"] = str(out)[:500]
            result["connector"] = decision.connector_slug
            # Compose often deeper_work until product oracles exist
            if ok:
                result["status"] = "achieved"
                finalize_trace(
                    tr,
                    status="goal_proven",
                    outcome=OUTCOME_PROVEN,
                    oracle={
                        "name": "connector_compose",
                        "pass": True,
                        "evidence": decision.connector_slug,
                    },
                    claim="connector_compose",
                    train_weight=3.0,
                )
            else:
                result["status"] = "deeper_work_needed"
                finalize_trace(
                    tr,
                    status="deeper_work_needed",
                    outcome=OUTCOME_DEEPER,
                    failure_class=FAILURE_COMPOSE,
                    oracle={
                        "name": "connector_compose",
                        "pass": False,
                        "evidence": str(out)[:400],
                    },
                    claim="connector_compose",
                    train_weight=0.2,
                )
            return result
        except Exception as exc:
            append_event(tr, type="observe", content=str(exc), ok=False)
            finalize_trace(
                tr,
                status="goal_failed",
                outcome=OUTCOME_FAILED,
                failure_class=FAILURE_COMPOSE,
                oracle={"name": "connector_compose", "pass": False, "evidence": str(exc)},
                claim="connector_compose",
            )
            result["reason"] = str(exc)
            result["status"] = "failed"
            return result

    if decision.policy == POLICY_MCP:
        # Do NOT invent an MCP server here — enqueue factory job only.
        slug = decision.capability_slug or decision.connector_slug
        if not slug:
            append_event(
                tr,
                type="observe",
                content="mcp policy: no capability/connector slug to wrap",
                ok=False,
            )
            # mcp_enqueued is NOT proven — deeper work for factory loop
            finalize_trace(
                tr,
                status="deeper_work_needed",
                outcome=OUTCOME_DEEPER,
                failure_class=FAILURE_MCP_ENQUEUED,
                oracle={
                    "name": "mcp_factory_enqueued",
                    "pass": False,
                    "evidence": "missing wrap target slug",
                },
                train_weight=0.0,
            )
            result["status"] = "mcp_enqueued"
            result["reason"] = "mcp policy but no wrap target slug"
            return result
        try:
            from pipeline.mcp_queue import enqueue_wrap

            job_path = enqueue_wrap(
                slug,
                goal_id=branch_id or None,
                reason=decision.reason,
            )
            append_event(
                tr,
                type="tool",
                tool="mcp_queue.enqueue_wrap",
                args={"slug": slug, "goal_id": branch_id or None},
                result_snip=str(job_path),
                ok=True,
            )
            # Enqueue success is still deeper (factory must smoke later) — not proven
            finalize_trace(
                tr,
                status="deeper_work_needed",
                outcome=OUTCOME_DEEPER,
                failure_class=FAILURE_MCP_ENQUEUED,
                oracle={
                    "name": "mcp_factory_enqueued",
                    "pass": True,
                    "evidence": str(job_path),
                },
                train_weight=0.0,
            )
            result["status"] = "mcp_enqueued"
            result["job_path"] = str(job_path)
            result["capability"] = slug
            return result
        except Exception as exc:
            append_event(tr, type="observe", content=str(exc), ok=False)
            finalize_trace(
                tr,
                status="goal_failed",
                outcome=OUTCOME_FAILED,
                failure_class=FAILURE_MCP_ENQUEUED,
                oracle={
                    "name": "mcp_factory_enqueued",
                    "pass": False,
                    "evidence": str(exc),
                },
                train_weight=0.0,
            )
            result["reason"] = str(exc)
            result["status"] = "failed"
            return result

    if decision.policy == POLICY_BUILD:
        append_event(
            tr,
            type="observe",
            content="build policy: software factory should seed/implement this brick",
            ok=None,
        )
        # Durable handoff signal for software factory (metrics only; no invent)
        try:
            metrics = get_pipeline_dir() / "metrics"
            metrics.mkdir(parents=True, exist_ok=True)
            handoff = {
                "branch_id": branch_id or None,
                "goal_text": (goal_text or "")[:500],
                "reason": decision.reason,
                "policy": POLICY_BUILD,
            }
            with (metrics / "goal_build_handoffs.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(handoff, ensure_ascii=False) + "\n")
        except Exception:
            pass
        finalize_trace(
            tr,
            status="deeper_work_needed",
            outcome=OUTCOME_DEEPER,
            oracle={"name": "policy_build", "pass": False, "evidence": decision.reason},
            train_weight=0.0,
        )
        result["status"] = "build_needed"
        return result

    if decision.policy == POLICY_RESEARCH:
        append_event(
            tr,
            type="observe",
            content="research policy: hand off to Hermes path",
            ok=None,
        )
        finalize_trace(
            tr,
            status="deeper_work_needed",
            outcome=OUTCOME_DEEPER,
            oracle={"name": "policy_research", "pass": False, "evidence": "hermes"},
            train_weight=0.0,
        )
        result["status"] = "research"
        return result

    # yield
    append_event(tr, type="observe", content=decision.reason, ok=False)
    finalize_trace(
        tr,
        status="deeper_work_needed",
        outcome=OUTCOME_DEEPER,
        failure_class=FAILURE_POLICY_YIELD,
        oracle={"name": "policy_yield", "pass": False, "evidence": decision.reason},
        train_weight=0.0,
    )
    result["status"] = "yielded"
    return result


def append_policy_history(row: dict[str, Any]) -> Path | None:
    """Append durable policy decision log under metrics (never truncate)."""
    try:
        metrics = get_pipeline_dir() / "metrics"
        metrics.mkdir(parents=True, exist_ok=True)
        path = metrics / "goal_policy_history.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path
    except Exception:
        return None
