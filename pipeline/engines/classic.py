"""
Classic engine stub.

Classic execution is owned by the multi-agent runner (executor / validator /
reviewer via message bus). This module documents that contract and provides a
no-op adapter so callers can branch on engine name without importing agents.

Do **not** replace classic with Grok Build. Classic remains default + fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.engines.base import EngineResult


class ClassicEngine:
    """Pass-through documenting that classic work happens in runner agents."""

    name = "classic"

    def run_phase_step(
        self,
        slug: str,
        phase: int,
        step: str,
        *,
        project_dir: Path | None = None,
        workspace: Path | None = None,
        prompt_file: Path | None = None,
        extra: dict[str, Any] | None = None,
    ) -> EngineResult:
        return EngineResult(
            success=True,
            step=step,
            summary=(
                f"classic engine is runner agents (not invoked via engines package); "
                f"slug={slug} phase={phase} step={step}"
            ),
            extra={"delegated_to": "runner_agents"},
        )


def get_classic_engine() -> ClassicEngine:
    return ClassicEngine()
