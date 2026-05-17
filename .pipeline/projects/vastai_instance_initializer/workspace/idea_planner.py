"""VAST.ai instance idea planner agent.

Plans and organizes ideas for VAST.ai instance configurations.
"""

import json
from pathlib import Path
from typing import Any


class IdeaPlannerAgent:
    """Plans and organizes ideas for VAST.ai instance configurations."""

    def __init__(self, run_dir: Path, current_slug: str) -> None:
        """Initialize the idea planner.

        Args:
            run_dir: Directory for running the pipeline.
            current_slug: Current project slug.
        """
        self._run_dir = run_dir
        self._current_slug = current_slug
        self._ideas: list[dict[str, Any]] = []

    def plan(self, ideas: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """Plan the execution of ideas.

        Args:
            ideas: List of idea dictionaries. Defaults to empty list.

        Returns:
            List of planned ideas with execution order.
        """
        if ideas is None:
            ideas = []

        # Sort ideas by dependencies
        planned = []
        for idea in ideas:
            planned.append({
                "title": idea.get("title", "Untitled"),
                "description": idea.get("description", ""),
                "requires": idea.get("requires"),
                "priority": self._calculate_priority(idea),
            })

        # Sort by priority (higher first)
        planned.sort(key=lambda x: x["priority"], reverse=True)
        self._ideas = planned
        return planned

    def _calculate_priority(self, idea: dict[str, Any]) -> int:
        """Calculate priority for an idea.

        Args:
            idea: The idea dictionary.

        Returns:
            Priority score (higher = more important).
        """
        priority = 0
        if idea.get("requires"):
            priority += 10  # Dependencies have higher priority
        if idea.get("title"):
            priority += 5
        return priority

    def save_plan(self, output_path: Path | None = None) -> Path:
        """Save the current plan to a file.

        Args:
            output_path: Path to save the plan. Defaults to run_dir/plan.json.

        Returns:
            Path to the saved plan.
        """
        if output_path is None:
            output_path = self._run_dir / "plan.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self._ideas, f, indent=2)

        return output_path

    def load_plan(self, input_path: Path | None = None) -> list[dict[str, Any]]:
        """Load a plan from a file.

        Args:
            input_path: Path to load the plan from. Defaults to run_dir/plan.json.

        Returns:
            List of planned ideas.
        """
        if input_path is None:
            input_path = self._run_dir / "plan.json"

        if not input_path.exists():
            return []

        with open(input_path, "r") as f:
            self._ideas = json.load(f)

        return self._ideas
