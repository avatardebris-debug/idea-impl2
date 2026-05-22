"""Selection matrix — Pareto-optimal (80/20) filtering of skills."""

from __future__ import annotations

from brain_download.core.models import SkillTree


def pareto_filter(
    tree: SkillTree,
    threshold: float = 0.20,
) -> SkillTree:
    """Apply Pareto filtering to identify the 20% of skills that deliver 80% of outcomes.

    Args:
        tree: The SkillTree to filter.
        threshold: The Pareto threshold (default 0.20 = 20%).

    Returns:
        A new SkillTree with is_pareto Essential flags set on the selected nodes.
    """
    nodes = tree.all_nodes
    if not nodes:
        return tree

    # Sort by importance descending
    sorted_nodes = sorted(nodes, key=lambda n: n.importance, reverse=True)

    # Select top threshold fraction
    n_select = max(1, int(len(sorted_nodes) * threshold))
    selected_ids = {n.id for n in sorted_nodes[:n_select]}

    # Create a copy with flags set
    for node in tree.all_nodes:
        node.is_pareto_essential = node.id in selected_ids

    # Update metadata
    tree.metadata["pareto_threshold"] = threshold
    tree.metadata["pareto_selected_count"] = len(selected_ids)
    tree.metadata["pareto_total_count"] = len(nodes)
    tree.metadata["pareto_percentage"] = round(len(selected_ids) / len(nodes) * 100, 1)

    return tree


def get_pareto_essential_nodes(tree: SkillTree) -> list[str]:
    """Get the IDs of Pareto-essential nodes."""
    return [n.id for n in tree.all_nodes if n.is_pareto_essential]


def get_pareto_non_essential_nodes(tree: SkillTree) -> list[str]:
    """Get the IDs of non-essential nodes (can be skipped or compressed)."""
    return [n.id for n in tree.all_nodes if not n.is_pareto_essential]
