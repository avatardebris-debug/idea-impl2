"""Parse LLM text responses into structured Subgoal objects."""

from __future__ import annotations

import re
from subgoal_generator.models import Subgoal


def parse_response(text: str) -> list[Subgoal]:
    """Parse an LLM response into a list of Subgoal objects.

    Expected format (one block per subgoal):
        title: <string>
        description: <string>
        dependencies: [dep1, dep2]
        priority: <int>

    Blocks are separated by blank lines.
    """
    subgoals: list[Subgoal] = []
    # Split into blocks by double newline
    blocks = re.split(r"\n\s*\n", text.strip())

    for block in blocks:
        title = _extract_field(block, r"title:\s*(.+)")
        description = _extract_field(block, r"description:\s*(.+)")
        deps_match = re.search(r"dependencies:\s*\[([^\]]*)\]", block)
        dependencies = [
            d.strip().strip('"').strip("'")
            for d in deps_match.group(1).split(",")
            if d.strip()
        ] if deps_match else []
        priority_match = re.search(r"priority:\s*(\d+)", block)
        priority = int(priority_match.group(1)) if priority_match else 1

        if title and description:
            subgoals.append(
                Subgoal(
                    title=title.strip(),
                    description=description.strip(),
                    dependencies=dependencies,
                    priority=priority,
                )
            )

    return subgoals


def _extract_field(block: str, pattern: str) -> str | None:
    """Extract the first matching group from *block* using *pattern*."""
    m = re.search(pattern, block, re.IGNORECASE)
    return m.group(1) if m else None
