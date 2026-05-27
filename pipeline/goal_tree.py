"""Canonical goal tree model and persistence (goals/*.json)."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Literal

from pipeline.pipeline_config import get_pipeline_dir

GoalBranchType = Literal[
    "software", "compound", "hermes_task", "robot_skill", "capability_gap"
]


def goals_dir() -> pathlib.Path:
    return get_pipeline_dir() / "goals"


def tree_path(goal_id: str) -> pathlib.Path:
    return goals_dir() / f"{goal_id}.json"


@dataclass
class GoalBranch:
    id: str
    subgoal: str
    type: GoalBranchType
    description: str = ""
    requires: list[str] = field(default_factory=list)
    hermes_prompt: str = ""
    hermes_goal_check: str = ""
    status: str = "pending"  # pending | decomposed | achieved | skipped
    pipeline_slug: str | None = None
    mirofish_score: float | None = None


@dataclass
class GoalTree:
    goal_id: str
    goal_text: str
    created_at: str
    parent_goal_id: str | None = None
    parent_branch_id: str | None = None
    status: str = "active"  # active | decomposed | complete | abandoned
    branches: list[GoalBranch] = field(default_factory=list)


def _branch_to_dict(b: GoalBranch) -> dict:
    return {
        "id": b.id,
        "subgoal": b.subgoal,
        "type": b.type,
        "description": b.description,
        "requires": b.requires,
        "hermes_prompt": b.hermes_prompt,
        "hermes_goal_check": b.hermes_goal_check,
        "status": b.status,
        "pipeline_slug": b.pipeline_slug,
    }


def _branch_from_dict(d: dict) -> GoalBranch:
    return GoalBranch(
        id=d.get("id", ""),
        subgoal=d.get("subgoal", ""),
        type=d.get("type", "software"),  # type: ignore[arg-type]
        description=d.get("description", ""),
        requires=list(d.get("requires") or []),
        hermes_prompt=d.get("hermes_prompt", ""),
        hermes_goal_check=d.get("hermes_goal_check", ""),
        status=d.get("status", "pending"),
        pipeline_slug=d.get("pipeline_slug"),
        mirofish_score=d.get("mirofish_score"),
    )


def tree_to_dict(tree: GoalTree) -> dict:
    return {
        "goal_id": tree.goal_id,
        "goal_text": tree.goal_text,
        "created_at": tree.created_at,
        "parent_goal_id": tree.parent_goal_id,
        "parent_branch_id": tree.parent_branch_id,
        "status": tree.status,
        "branches": [_branch_to_dict(b) for b in tree.branches],
    }


def tree_from_dict(data: dict) -> GoalTree:
    return GoalTree(
        goal_id=data.get("goal_id", ""),
        goal_text=data.get("goal_text", ""),
        created_at=data.get("created_at", ""),
        parent_goal_id=data.get("parent_goal_id"),
        parent_branch_id=data.get("parent_branch_id"),
        status=data.get("status", "active"),
        branches=[_branch_from_dict(b) for b in (data.get("branches") or [])],
    )


def load_goal_tree(goal_id: str) -> GoalTree | None:
    path = tree_path(goal_id)
    if not path.exists():
        return None
    try:
        return tree_from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def save_goal_tree(tree: GoalTree) -> None:
    path = tree_path(tree.goal_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree_to_dict(tree), indent=2), encoding="utf-8")


def completion_branches(tree: GoalTree) -> list[GoalBranch]:
    """Branches that must be achieved before the parent goal is complete."""
    return [b for b in tree.branches if b.type != "compound"]
