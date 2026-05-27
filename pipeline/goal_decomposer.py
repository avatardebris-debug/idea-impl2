"""
pipeline/goal_decomposer.py
Goal Decomposer — decomposes a --goal entry into a YAML dependency tree,
then injects each leaf as a new idea entry into master_ideas.md.

Called by seed_from_master_list() when it encounters a line ending with --goal.
This module is imported by runner.py — it does NOT run as a subprocess.

Output format:
  Each leaf becomes a master_ideas.md line:
    - [ ] **[Title]** — [Description. requires: dep1, dep2]
  Each compound branch spawns a new --goal entry for recursive decomposition.
"""

from __future__ import annotations

import json
import logging
import pathlib
import re
import sys
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from pipeline.pipeline_config import PROJECT_ROOT  # noqa: E402
from pipeline.goal_tree import GoalBranch, GoalTree, goals_dir, save_goal_tree


# ---------------------------------------------------------------------------
# LLM decomposition
# ---------------------------------------------------------------------------

_DECOMPOSE_PROMPT = """\
You are a Goal Decomposer. Your job is to break a high-level goal into independently
buildable sub-tasks that can each be completed by an autonomous software pipeline.

GOAL: {goal_text}

## Already-complete projects (reuse these, do NOT re-queue them):
{completed_projects}

## Currently pending ideas (do NOT duplicate these):
{pending_ideas}

## Rules:
1. Classify each branch as one of:
   - software: A concrete Python tool/library the pipeline can build
   - compound: Still too big — needs further decomposition (max depth: 2)
   - hermes_task: Open-ended research/exploration/benchmarking (no fixed output format)
   - robot_skill: A physical robot movement primitive (only for actual motor control)
   - capability_gap: A needed tool exists in the registry but is draft/blocked, OR no verified
     capability covers the task — queue a normal pipeline project to build or verify it

2. For software branches: be specific. Name files, classes, I/O formats.
3. For hermes_task: write a clear `hermes_goal_check` question the critic can evaluate.
4. Declare dependencies with `requires:` using existing project slugs.
5. Do NOT include already-complete projects as branches.
6. Produce 3-8 branches. More is worse — prefer fewer, more specific branches.
7. Prefer reusing verified capabilities from the registry (listed below) via `requires:` slugs
   instead of rebuilding equivalent software.

## Output format (JSON only, no other text):
{{
  "branches": [
    {{
      "id": "b001",
      "subgoal": "Short branch title (3-7 words)",
      "type": "software",
      "description": "Detailed description of what to build. Include I/O format, key classes/functions.",
      "requires": ["existing_slug_if_needed"],
      "hermes_prompt": "",
      "hermes_goal_check": ""
    }},
    {{
      "id": "b002",
      "subgoal": "Research MuJoCo URDF options",
      "type": "hermes_task",
      "description": "Find and evaluate robot URDF models for MuJoCo 3.x.",
      "requires": [],
      "hermes_prompt": "Find 3 production-quality robot URDF models compatible with MuJoCo 3.x. Evaluate joint count, articulation quality, and license. Write a ranked comparison table to .pipeline/goals/urdf_research.md.",
      "hermes_goal_check": "Has the agent produced a ranked comparison of at least 3 URDF models with MuJoCo compatibility confirmed and written to .pipeline/goals/urdf_research.md?"
    }}
  ]
}}
"""


def _call_llm(prompt: str) -> str:
    """Call the LLM synchronously via the existing agent_process infrastructure."""
    # Import here to avoid circular imports — runner.py imports us, agent_process
    # imports pipeline.message_bus, so the import chain is fine as long as we
    # don't import at module level.
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from pipeline.agent_process import AgentProcess

        class _TempAgent(AgentProcess):
            role = "goal_decomposer"
            max_steps = 5
            temperature = 0.3
            think = False

            def handle(self, msg):  # pragma: no cover
                pass  # not used directly

        agent = _TempAgent.__new__(_TempAgent)
        AgentProcess.__init__(agent)
        result = agent.call_agent(task=prompt, verbose=False)
        return result.raw_output if hasattr(result, "raw_output") else str(result)
    except Exception as exc:
        logger.error("LLM call failed in goal_decomposer: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# Core decomposition logic
# ---------------------------------------------------------------------------

def _completed_project_slugs() -> list[str]:
    """Return slugs of all pipeline projects with status=complete."""
    projects_dir = PIPELINE_DIR / "projects"
    if not projects_dir.exists():
        return []
    slugs = []
    for p in projects_dir.iterdir():
        if not p.is_dir():
            continue
        sf = p / "state" / "current_idea.json"
        if sf.exists():
            try:
                state = json.loads(sf.read_text(encoding="utf-8"))
                if state.get("status") == "complete":
                    slugs.append(p.name)
            except Exception:
                pass
    return slugs


def _pending_idea_titles(mi_path: pathlib.Path) -> list[str]:
    """Return titles of unchecked (not yet done) ideas in master_ideas.md."""
    if not mi_path.exists():
        return []
    titles = []
    for line in mi_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"- \[ \]\s+\*\*(.+?)\*\*", line)
        if m:
            titles.append(m.group(1).strip())
    return titles


def _parse_llm_branches(raw: str) -> list[dict]:
    """Extract the JSON branches list from raw LLM output."""
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    # Find the first {...} block
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        logger.warning("goal_decomposer: no JSON found in LLM output")
        return []
    try:
        data = json.loads(m.group(0))
        return data.get("branches", [])
    except json.JSONDecodeError as exc:
        logger.error("goal_decomposer: JSON parse error: %s", exc)
        return []


def decompose_goal(
    goal_text: str,
    goal_title: str,
    mi_path: pathlib.Path,
    parent_goal_id: str | None = None,
    parent_branch_id: str | None = None,
) -> GoalTree:
    """Decompose a natural-language goal into a GoalTree and persist to disk."""
    goals_dir().mkdir(parents=True, exist_ok=True)

    goal_id = re.sub(r"[^\w]", "_", goal_title.lower())[:40].strip("_")
    ts = datetime.now(timezone.utc).isoformat()

    completed = _completed_project_slugs()
    pending = _pending_idea_titles(mi_path)

    registry_block = ""
    try:
        from pipeline.pipeline_mode import legacy_mode
        if not legacy_mode():
            from pipeline.capability_registry import capabilities_summary
            registry_block = capabilities_summary(max_rows=20) or ""
    except Exception:
        pass

    prompt = _DECOMPOSE_PROMPT.format(
        goal_text=goal_text,
        completed_projects=", ".join(completed[:60]) or "(none yet)",
        pending_ideas=", ".join(pending[:40]) or "(none yet)",
    )
    if registry_block:
        prompt += f"\n\n## Verified capabilities (reuse via requires:)\n{registry_block}\n"

    raw = _call_llm(prompt)
    branch_dicts = _parse_llm_branches(raw)

    valid_types = frozenset(
        {"software", "compound", "hermes_task", "robot_skill", "capability_gap"}
    )
    branches = []
    for b in branch_dicts:
        btype = b.get("type", "software")
        if btype not in valid_types:
            btype = "software"
        branches.append(GoalBranch(
            id=b.get("id", f"b{len(branches):03d}"),
            subgoal=b.get("subgoal", "unknown"),
            type=btype,
            description=b.get("description", ""),
            requires=b.get("requires", []),
            hermes_prompt=b.get("hermes_prompt", ""),
            hermes_goal_check=b.get("hermes_goal_check", ""),
        ))

    tree = GoalTree(
        goal_id=goal_id,
        goal_text=goal_text,
        created_at=ts,
        parent_goal_id=parent_goal_id,
        parent_branch_id=parent_branch_id,
        branches=branches,
    )

    save_goal_tree(tree)
    logger.info("goal_decomposer: decomposed '%s' → %d branches", goal_title, len(branches))
    return tree


# ---------------------------------------------------------------------------
# Injection into master_ideas.md
# ---------------------------------------------------------------------------

def inject_branches_into_ideas(tree: GoalTree, mi_path: pathlib.Path) -> int:
    """
    Write each leaf branch from the goal tree into master_ideas.md as new
    unchecked idea entries. Parent --goal line stays unchecked; see goals/backlog.md.

    Returns the number of branches injected.
    """
    injected = 0
    new_lines: list[str] = []

    for branch in tree.branches:
        if branch.type == "compound":
            # Will be recursively decomposed when the runner picks it up
            tag = "--goal"
        elif branch.type == "hermes_task":
            tag = "--hermes"
        elif branch.type == "robot_skill":
            tag = "--robot"
        elif branch.type == "capability_gap":
            tag = ""
        else:
            tag = ""

        requires_clause = ""
        desc = branch.description
        if branch.type == "capability_gap":
            try:
                from pipeline.pipeline_mode import legacy_mode
                if not legacy_mode():
                    from pipeline.capability_router import route_task

                    hits = route_task(branch.description or branch.subgoal, limit=3)
                    usable = [h for h in hits if h.get("requires_ok")]
                    if usable:
                        reuse = usable[0]["slug"]
                        requires_clause = f". requires: {reuse}"
                        desc = (
                            f"Reuse verified capability `{reuse}` before building new code. "
                            f"{branch.description}"
                        )
                    else:
                        desc = (
                            f"[capability_gap] Build or verify tooling for: {branch.subgoal}. "
                            f"{branch.description}"
                        )
            except Exception:
                pass
        elif branch.requires:
            requires_clause = f". requires: {', '.join(branch.requires)}"

        suggest_clause = ""
        if branch.type != "capability_gap":
            try:
                from pipeline.pipeline_mode import legacy_mode
                if not legacy_mode():
                    from pipeline.capability_router import route_task
                    hits = route_task(branch.description or branch.subgoal, limit=2)
                    usable = [h["slug"] for h in hits if h.get("requires_ok")]
                    if usable:
                        suggest_clause = f". suggested_reuse: {', '.join(usable)}"
            except Exception:
                pass

        line = (
            f"- [ ] **[{branch.subgoal}]** — "
            f"[[goal:{tree.goal_id}:{branch.id}] {desc}{requires_clause}{suggest_clause}]"
        )
        if tag:
            line += f" {tag}"
        new_lines.append(line)
        injected += 1

    if not new_lines:
        logger.warning("goal_decomposer: no branches to inject for goal '%s'", tree.goal_id)
        return 0

    content = mi_path.read_text(encoding="utf-8")

    # Parent --goal stays unchecked; track in goals/backlog.md
    tree.status = "decomposed"
    for branch in tree.branches:
        if branch.status == "pending":
            branch.status = "decomposed"
    try:
        from pipeline.goal_backlog import append_decomposed_goal

        tree_path = goals_dir() / f"{tree.goal_id}.json"
        append_decomposed_goal(
            tree.goal_id,
            tree.goal_text,
            branch_count=len(tree.branches),
            tree_path=tree_path,
        )
        save_goal_tree(tree)
    except Exception as exc:
        logger.debug("goal backlog update skipped: %s", exc)

    # Append the new entries under a ## Goal Decompositions section
    section_header = "## Goal Decompositions"
    if section_header not in content:
        content += f"\n\n{section_header}\n\n"

    injection_block = (
        f"\n<!-- goal:{tree.goal_id} decomposed {tree.created_at[:10]} -->\n"
        + "\n".join(new_lines)
        + "\n"
    )

    # Insert before the end of the Goal Decompositions section (or append)
    if section_header in content:
        insert_pos = content.rfind(section_header) + len(section_header)
        content = content[:insert_pos] + injection_block + content[insert_pos:]
    else:
        content += injection_block

    mi_path.write_text(content, encoding="utf-8")
    print(f"  🎯 Goal '{tree.goal_id}': injected {injected} branches into {mi_path.name}")
    return injected


# ---------------------------------------------------------------------------
# Public entry point called from runner.py
# ---------------------------------------------------------------------------

def process_goal_line(
    goal_title: str,
    goal_description: str,
    mi_path: pathlib.Path,
) -> bool:
    """
    Full pipeline: decompose a --goal entry and inject children into ideas file.
    Returns True if at least one branch was injected.
    """
    print(f"\n  🎯 Decomposing goal: {goal_title}")
    tree = decompose_goal(
        goal_text=goal_description,
        goal_title=goal_title,
        mi_path=mi_path,
    )
    if not tree.branches:
        logger.warning("goal_decomposer: LLM produced no branches for '%s'", goal_title)
        print(f"  ⚠  Goal decomposition returned no branches — check .pipeline/goals/{tree.goal_id}.json")
        return False

    injected = inject_branches_into_ideas(tree, mi_path)
    save_goal_tree(tree)
    return injected > 0
