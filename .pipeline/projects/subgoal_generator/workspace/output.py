"""Output formatting and master_ideas.md injection."""

from __future__ import annotations

import os
from subgoal_generator.models import Subgoal


def write_pipeline_entries(
    subgoals: list[Subgoal],
    master_ideas_path: str = "master_ideas.md",
) -> None:
    """Append each subgoal as a YAML pipeline entry to *master_ideas_path*."""
    # Ensure the file exists
    if not os.path.exists(master_ideas_path):
        with open(master_ideas_path, "w") as f:
            f.write("# Master Ideas\n\n")

    with open(master_ideas_path, "a") as f:
        for subgoal in subgoals:
            f.write(subgoal.to_pipeline_entry())
            f.write("\n---\n\n")
