"""Shared pipeline paths and constants."""
from __future__ import annotations

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

PIPELINE_DIR = PROJECT_ROOT / ".pipeline"
AGENTS_DIR = pathlib.Path(__file__).parent / "agents"

AGENT_ROLES = [
    "idea_planner",
    "phase_planner",
    "executor",
    "validator",
    "reviewer",
    "manager",
    "ideator",
]

DEFAULT_BASE_BUDGET = 90
DEFAULT_PHASE_BUDGET = 30
MAX_PHASE_RETRIES = 5
MAX_PROJECT_LIFETIME_RETRIES = 80
