"""
pipeline/goal_attempt.py
Attempt to achieve decomposed goals using built capabilities or Hermes.
"""

from __future__ import annotations

from typing import Any

from pipeline.goal_backlog import mark_goal_achieved
from pipeline.goal_tree import (
    GoalBranch,
    completion_branches,
    goals_dir,
    load_goal_tree,
    save_goal_tree,
)
from pipeline.project_complete import is_project_complete


def _branch_runnable(branch: GoalBranch) -> bool:
    btype = branch.type
    if btype == "hermes_task":
        return bool(branch.hermes_prompt)
    if btype == "compound":
        return False
    return all(is_project_complete(r) for r in branch.requires)


def attempt_goal(
    goal_id: str,
    *,
    branch_id: str | None = None,
    provider: str = "ollama",
    model: str | None = None,
) -> dict[str, Any]:
    """Try to achieve runnable branches for a goal tree. Returns summary dict."""
    tree = load_goal_tree(goal_id)
    if not tree:
        return {"ok": False, "error": f"goal not found: {goal_id}"}

    branches = list(tree.branches)
    if branch_id:
        branches = [b for b in branches if b.id == branch_id]
        if not branches:
            return {"ok": False, "error": f"branch not found: {branch_id}"}

    results: list[dict[str, Any]] = []
    achieved = 0

    for branch in branches:
        bid = branch.id or "?"
        if branch.status == "achieved":
            results.append({"branch": bid, "status": "already_achieved"})
            continue
        if not _branch_runnable(branch):
            results.append({"branch": bid, "status": "not_runnable", "type": branch.type})
            continue

        if branch.type == "hermes_task":
            r = _attempt_hermes(branch, provider=provider, model=model)
        elif branch.type in ("software", "robot_skill", "capability_gap"):
            r = _attempt_capability(branch)
        else:
            r = {"branch": bid, "status": "skipped", "reason": f"type={branch.type}"}
            results.append(r)
            continue

        results.append(r)
        if r.get("status") == "achieved":
            achieved += 1
            branch.status = "achieved"
            save_goal_tree(tree)

    required = completion_branches(tree)
    if required and all(b.status == "achieved" for b in required):
        tree.status = "complete"
        save_goal_tree(tree)
        mark_goal_achieved(goal_id)
        try:
            from pipeline.ship_provenance import mark_goal_proven_for_goal

            n = mark_goal_proven_for_goal(goal_id)
            if n:
                print(f"  [ship] M4 maturity set on {n} project(s) for goal {goal_id}")
        except Exception:
            pass

    return {"ok": True, "goal_id": goal_id, "achieved": achieved, "results": results}


def _attempt_capability(branch: GoalBranch) -> dict[str, Any]:
    """Capability path via thin goal policy (reuse | compose | build | yield).

    Always writes goal_trace.v1 (durable; survives runner shutdown).
    """
    bid = branch.id or "?"
    text = branch.description or branch.subgoal or ""
    try:
        from pipeline.pipeline_mode import legacy_mode

        if legacy_mode():
            return {"branch": bid, "status": "skipped", "reason": "legacy_mode"}
        from pipeline.capability_router import route_task
        from pipeline.goal_policy import (
            POLICY_BUILD,
            POLICY_COMPOSE,
            POLICY_REUSE,
            POLICY_YIELD,
            append_policy_history,
            classify_goal_branch,
            execute_policy,
        )

        hits = route_task(text, limit=5) if text else []
        requires = list(getattr(branch, "requires", None) or [])
        decision = classify_goal_branch(
            branch_type=str(branch.type or "capability"),
            text=text,
            requires=requires,
            hermes_prompt=str(getattr(branch, "hermes_prompt", "") or ""),
            route_hits=hits if isinstance(hits, list) else [],
        )
        exec_out = execute_policy(
            decision,
            goal_text=text or f"branch {bid}",
            branch_id=bid,
        )
        try:
            append_policy_history(
                {
                    "branch": bid,
                    "policy": decision.policy,
                    "reason": decision.reason,
                    "status": exec_out.get("status"),
                    "goal_trace_id": exec_out.get("goal_id"),
                    "capability": decision.capability_slug,
                    "connector": decision.connector_slug,
                }
            )
        except Exception:
            pass

        status = str(exec_out.get("status") or "failed")
        if decision.policy == POLICY_REUSE and status == "achieved":
            return {
                "branch": bid,
                "status": "achieved",
                "policy": POLICY_REUSE,
                "capability": exec_out.get("capability") or decision.capability_slug,
                "output": (exec_out.get("output") or "")[:500],
                "goal_trace_id": exec_out.get("goal_id"),
            }
        if decision.policy == POLICY_COMPOSE and status == "achieved":
            return {
                "branch": bid,
                "status": "achieved",
                "policy": POLICY_COMPOSE,
                "connector": exec_out.get("connector") or decision.connector_slug,
                "output": (exec_out.get("output") or "")[:500],
                "goal_trace_id": exec_out.get("goal_id"),
            }
        if decision.policy == POLICY_COMPOSE:
            return {
                "branch": bid,
                "status": "failed",
                "policy": POLICY_COMPOSE,
                "reason": exec_out.get("reason") or "compose deeper_work_needed",
                "connector": decision.connector_slug,
                "goal_trace_id": exec_out.get("goal_id"),
            }
        if decision.policy == POLICY_BUILD:
            return {
                "branch": bid,
                "status": "failed",
                "policy": POLICY_BUILD,
                "reason": "build_needed",
                "goal_trace_id": exec_out.get("goal_id"),
            }
        if decision.policy == POLICY_YIELD:
            return {
                "branch": bid,
                "status": "failed",
                "policy": POLICY_YIELD,
                "reason": decision.reason,
                "goal_trace_id": exec_out.get("goal_id"),
            }
        return {
            "branch": bid,
            "status": "failed",
            "policy": decision.policy,
            "reason": exec_out.get("reason") or decision.reason,
            "goal_trace_id": exec_out.get("goal_id"),
        }
    except Exception as exc:
        return {"branch": bid, "status": "failed", "reason": str(exc)}


def _attempt_hermes(
    branch: GoalBranch,
    *,
    provider: str,
    model: str | None,
) -> dict[str, Any]:
    bid = branch.id or "?"
    prompt = branch.hermes_prompt or branch.description or ""
    goal_check = branch.hermes_goal_check or f"Was '{branch.subgoal}' completed?"
    try:
        from pipeline.hermes_runner import HermesGoalRunner, resolve_hermes_route

        route = resolve_hermes_route(model=model, provider=provider)
        if route.action == "skip":
            print(f"  [hermes:{bid}] {route.log_label}")
            return {
                "branch": bid,
                "status": "skipped",
                "reason": route.reason,
            }
        runner = HermesGoalRunner(model=model, provider=provider, route=route)
        result = runner.run(
            prompt=prompt,
            goal_check=goal_check,
            time_budget_min=30,
            branch_id=bid,
        )
        if result.get("status") == "skipped":
            return {
                "branch": bid,
                "status": "skipped",
                "reason": result.get("reason") or route.reason,
            }
        status = "achieved" if result.get("status") == "achieved" else "failed"
        return {
            "branch": bid,
            "status": status,
            "attempts": result.get("attempts"),
            "output": (result.get("output") or "")[:500],
        }
    except Exception as exc:
        return {"branch": bid, "status": "failed", "reason": str(exc)}


def list_attemptable_goals() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    gdir = goals_dir()
    if not gdir.exists():
        return out
    for path in sorted(gdir.glob("*.json")):
        tree = load_goal_tree(path.stem)
        if not tree:
            continue
        runnable = sum(
            1 for b in tree.branches if _branch_runnable(b) and b.status != "achieved"
        )
        out.append({
            "goal_id": tree.goal_id,
            "status": tree.status,
            "branches": len(tree.branches),
            "runnable": runnable,
        })
    return out
