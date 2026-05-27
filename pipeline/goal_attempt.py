"""
pipeline/goal_attempt.py
Attempt to achieve decomposed goals using built capabilities or Hermes.
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any

from pipeline.goal_backlog import GOALS_DIR, load_goal_tree, mark_goal_achieved
from pipeline.pipeline_config import PIPELINE_DIR, PROJECT_ROOT


def _project_complete(slug: str) -> bool:
    state_file = PIPELINE_DIR / "projects" / slug / "state" / "current_idea.json"
    if not state_file.exists():
        return False
    try:
        st = json.loads(state_file.read_text(encoding="utf-8"))
        return (
            st.get("status") == "complete"
            and int(st.get("phase", 0)) >= int(st.get("total_phases", 1))
        )
    except Exception:
        return False


def _branch_runnable(branch: dict[str, Any]) -> bool:
    btype = branch.get("type", "software")
    if btype == "hermes_task":
        return bool(branch.get("hermes_prompt"))
    if btype in ("compound",):
        return False
    requires = branch.get("requires") or []
    return all(_project_complete(r) for r in requires)


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

    branches = tree.get("branches") or []
    if branch_id:
        branches = [b for b in branches if b.get("id") == branch_id]
        if not branches:
            return {"ok": False, "error": f"branch not found: {branch_id}"}

    results: list[dict[str, Any]] = []
    achieved = 0

    for branch in branches:
        bid = branch.get("id", "?")
        if branch.get("status") == "achieved":
            results.append({"branch": bid, "status": "already_achieved"})
            continue
        if not _branch_runnable(branch):
            results.append({"branch": bid, "status": "not_runnable", "type": branch.get("type")})
            continue

        btype = branch.get("type", "software")
        if btype == "hermes_task":
            r = _attempt_hermes(branch, provider=provider, model=model)
        elif btype in ("software", "robot_skill", "capability_gap"):
            r = _attempt_capability(branch)
        else:
            r = {"branch": bid, "status": "skipped", "reason": f"type={btype}"}
            results.append(r)
            continue

        results.append(r)
        if r.get("status") == "achieved":
            achieved += 1
            branch["status"] = "achieved"
            _save_tree(goal_id, tree)

    if achieved and all(b.get("status") == "achieved" for b in tree.get("branches") or []):
        tree["status"] = "complete"
        _save_tree(goal_id, tree)
        mark_goal_achieved(goal_id)

    return {"ok": True, "goal_id": goal_id, "achieved": achieved, "results": results}


def _save_tree(goal_id: str, tree: dict[str, Any]) -> None:
    path = GOALS_DIR / f"{goal_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree, indent=2), encoding="utf-8")


def _attempt_capability(branch: dict[str, Any]) -> dict[str, Any]:
    bid = branch.get("id", "?")
    text = branch.get("description") or branch.get("subgoal") or ""
    try:
        from pipeline.pipeline_mode import legacy_mode

        if legacy_mode():
            return {"branch": bid, "status": "skipped", "reason": "legacy_mode"}
        from pipeline.capability_router import route_task
        from pipeline.capability_tools import invoke_capability

        hits = route_task(text, limit=3)
        for hit in hits:
            if not hit.get("requires_ok"):
                continue
            slug = hit.get("slug", "")
            if not slug:
                continue
            out = invoke_capability(slug, args="")
            if out and "error" not in out.lower()[:200]:
                return {"branch": bid, "status": "achieved", "capability": slug, "output": out[:500]}
        return {"branch": bid, "status": "failed", "reason": "no invokable capability"}
    except Exception as exc:
        return {"branch": bid, "status": "failed", "reason": str(exc)}


def _attempt_hermes(
    branch: dict[str, Any],
    *,
    provider: str,
    model: str | None,
) -> dict[str, Any]:
    bid = branch.get("id", "?")
    prompt = branch.get("hermes_prompt") or branch.get("description") or ""
    goal_check = branch.get("hermes_goal_check") or f"Was '{branch.get('subgoal')}' completed?"
    try:
        from pipeline.hermes_runner import HermesGoalRunner

        runner = HermesGoalRunner(model=model, provider=provider)
        result = runner.run(
            prompt=prompt,
            goal_check=goal_check,
            time_budget_min=30,
            branch_id=bid,
        )
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
    if not GOALS_DIR.exists():
        return out
    for path in sorted(GOALS_DIR.glob("*.json")):
        try:
            tree = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        gid = tree.get("goal_id") or path.stem
        branches = tree.get("branches") or []
        runnable = sum(1 for b in branches if _branch_runnable(b) and b.get("status") != "achieved")
        out.append({
            "goal_id": gid,
            "status": tree.get("status", "?"),
            "branches": len(branches),
            "runnable": runnable,
        })
    return out
