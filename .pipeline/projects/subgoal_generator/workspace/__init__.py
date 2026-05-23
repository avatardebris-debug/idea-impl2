"""Subgoal Generator — LLM-powered goal decomposition engine."""

from __future__ import annotations

from typing import Any

from subgoal_generator.models import Subgoal, DependencyGraph
from subgoal_generator.generator import SubgoalGenerator


def generate_subgoals(
    goal: str,
    *,
    model: str = "gpt-4o-mini",
    provider: str = "openai",
    output_path: str | None = None,
    format: str = "md",
) -> list[Subgoal]:
    """Decompose a high-level goal into a list of subgoals.

    This is the simplest way to use the library programmatically.

    Args:
        goal: The high-level goal to decompose (e.g. "build a house").
        model: LLM model name to use (default: "gpt-4o-mini").
        provider: LLM provider name (default: "openai").
        output_path: Optional path to append subgoals as pipeline entries.
        format: Output format — "md" for markdown, "json" for JSON.

    Returns:
        A list of :class:`Subgoal` objects representing the decomposed subgoals.
    """
    generator = SubgoalGenerator(provider=provider, model=model)
    return generator.generate(goal, master_ideas_path=output_path)


__all__ = ["Subgoal", "DependencyGraph", "SubgoalGenerator", "generate_subgoals"]
