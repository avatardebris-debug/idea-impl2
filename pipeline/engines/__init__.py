"""
Dual-engine package: classic multi-agent path + optional Grok Build skill chain.

Default engine is always classic. Grok Build is opt-in via PIPELINE_ENGINE /
per-project state["engine"]. Planners (idea_planner, phase_planner) stay classic
in v1; grok_build owns implement → validate → review → fix only.
"""

from __future__ import annotations

from pipeline.engines.base import EngineResult
from pipeline.engines.selection import (
    ENGINE_CLASSIC,
    ENGINE_GROK_BUILD,
    get_project_engine,
    resolve_seed_engine,
)

__all__ = [
    "ENGINE_CLASSIC",
    "ENGINE_GROK_BUILD",
    "EngineResult",
    "get_project_engine",
    "resolve_seed_engine",
]
