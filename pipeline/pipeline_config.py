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
      1. PIPELINE_DIR env (absolute path or relative to PROJECT_ROOT)
      2. PROJECT_ROOT/../thepipeline if it has projects/ (sibling output repo)
      3. PROJECT_ROOT/.pipeline if it has projects/
      4. ../thepipeline if the directory exists, else .pipeline (created on first run)
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

    def _has_projects(root: pathlib.Path) -> bool:
        return root.is_dir() and (root / "projects").is_dir()

    if _has_projects(sibling):
        return sibling.resolve()
    if _has_projects(nested):
        return nested.resolve()
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

DEFAULT_BASE_BUDGET = 90
DEFAULT_PHASE_BUDGET = 30
MAX_PHASE_RETRIES = 5
MAX_PROJECT_LIFETIME_RETRIES = 80
