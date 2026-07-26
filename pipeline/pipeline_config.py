"""Shared pipeline paths and constants."""
from __future__ import annotations

import os
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


def resolve_pipeline_dir() -> pathlib.Path:
    """
    Root for pipeline *output* (projects/, state/, shared_libs/, queues/, …).

    Resolution order:
      1. PIPELINE_DIR env (absolute path or relative to PROJECT_ROOT) — highest priority
      2. PIPELINE_CLOUD=1 → PROJECT_ROOT/.pipeline (cloud mode; do not use home factory)
      3. PROJECT_ROOT/../thepipeline if it has projects/ (sibling output repo)
      4. PROJECT_ROOT/.pipeline if it has projects/ — unless empty-ish while
         ~/aicompete/thepipeline has projects/ (worktree footgun: prefer home factory)
      5. ~/aicompete/thepipeline if it has projects/
      6. ../thepipeline if the directory exists, else .pipeline (created on first run)
    """
    env = os.environ.get("PIPELINE_DIR", "").strip()
    if env:
        p = pathlib.Path(env).expanduser()
        if not p.is_absolute():
            p = (PROJECT_ROOT / p).resolve()
        else:
            p = p.resolve()
        return p

    if os.environ.get("PIPELINE_CLOUD", "").strip().lower() in ("1", "true", "yes", "on"):
        return (PROJECT_ROOT / ".pipeline").resolve()

    sibling = PROJECT_ROOT.parent / "thepipeline"
    nested = PROJECT_ROOT / ".pipeline"
    home_factory = pathlib.Path.home() / "aicompete" / "thepipeline"

    def _has_projects(root: pathlib.Path) -> bool:
        return root.is_dir() and (root / "projects").is_dir()

    def _project_count(root: pathlib.Path) -> int:
        p = root / "projects"
        if not p.is_dir():
            return 0
        try:
            return sum(1 for c in p.iterdir() if c.is_dir())
        except OSError:
            return 0

    if _has_projects(sibling):
        return sibling.resolve()

    nested_n = _project_count(nested) if nested.is_dir() else 0
    home_n = _project_count(home_factory) if home_factory.is_dir() else 0

    # Worktree footgun: nested .pipeline often exists with 0–few projects while
    # the live factory output lives at ~/aicompete/thepipeline.
    if _has_projects(nested):
        if home_n > 0 and nested_n < 3 and home_n > nested_n:
            return home_factory.resolve()
        return nested.resolve()

    if home_n > 0:
        return home_factory.resolve()
    if sibling.is_dir():
        return sibling.resolve()
    return nested.resolve()


PIPELINE_DIR = resolve_pipeline_dir()


def get_pipeline_dir() -> pathlib.Path:
    """Live output root — always re-resolves from env and filesystem rules."""
    return resolve_pipeline_dir()


def reload_pipeline_dir() -> pathlib.Path:
    """Re-resolve after bootstrap sets PIPELINE_DIR env (cloud clone)."""
    global PIPELINE_DIR
    PIPELINE_DIR = resolve_pipeline_dir()
    return PIPELINE_DIR


AGENTS_DIR = pathlib.Path(__file__).parent / "agents"

# Default Ollama model for pipeline agents (override via --model or PIPELINE_MODEL).
DEFAULT_PIPELINE_MODEL = os.environ.get(
    "PIPELINE_MODEL", "qwen3.6:35b-a3b-q4_K_M"
)

AGENT_ROLES = [
    "idea_planner",
    "phase_planner",
    "executor",
    "validator",
    "reviewer",
    "manager",
    "ideator",
]

# Subset started by --ship-prove (separate loop).
SHIP_AGENT_ROLES = [
    "field_test_planner",
    "debug_loop",
    "executor",
    "thermo_reviewer",
    "ship_evaluator",
]

DEFAULT_BASE_BUDGET = 90
DEFAULT_PHASE_BUDGET = 30
MAX_PHASE_RETRIES = 5
MAX_PROJECT_LIFETIME_RETRIES = 80
