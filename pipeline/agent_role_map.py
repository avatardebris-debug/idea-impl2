"""Pipeline agent role ordering (next-role preload map).

Extracted from agent_process to keep the base class smaller and shareable.
"""

from __future__ import annotations

# Maps each agent to the role most likely to receive its output next.
# Preloading context for that role while current LLM generates = zero wait.
NEXT_ROLE_MAP: dict[str, str] = {
    "idea_planner": "phase_planner",
    "phase_planner": "executor",
    "executor": "reviewer",
    "reviewer": "validator",
    "validator": "executor",  # retries go back to executor
    "manager": "phase_planner",
    "documenter": "manager",
    "ideator": "idea_planner",
    "field_test_planner": "executor",
    "debug_loop": "executor",
    "thermo_reviewer": "ship_evaluator",
    "ship_evaluator": "field_test_planner",
}


def next_role(role: str) -> str | None:
    return NEXT_ROLE_MAP.get(role)
