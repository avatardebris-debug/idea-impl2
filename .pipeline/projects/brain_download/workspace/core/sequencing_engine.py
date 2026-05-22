"""Sequencing engine — prerequisite-aware ordering of skills into modules."""

from __future__ import annotations

from brain_download.core.models import CourseModule, CourseOutline, SkillTree, Topic


def _topological_sort(nodes: list, all_nodes_map: dict[str, any]) -> list:
    """Topological sort of nodes by prerequisites."""
    in_degree = {n.id: 0 for n in nodes}
    adj = {n.id: [] for n in nodes}

    for n in nodes:
        for prereq in n.prerequisites:
            if prereq in in_degree:
                adj[prereq].append(n.id)
                in_degree[n.id] += 1

    queue = [n.id for n in nodes if in_degree[n.id] == 0]
    result = []

    while queue:
        queue.sort()  # deterministic ordering
        current = queue.pop(0)
        result.append(current)
        for neighbor in adj[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result


def _group_into_modules(
    ordered_ids: list[str],
    all_nodes_map: dict[str, any],
    module_size: int = 4,
) -> list[CourseModule]:
    """Group ordered skills into modules."""
    modules: list[CourseModule] = []
    module_id = 0

    for i in range(0, len(ordered_ids), module_size):
        chunk = ordered_ids[i : i + module_size]
        skills_in_module = [all_nodes_map[nid] for nid in chunk if nid in all_nodes_map]

        # Calculate module metadata
        total_minutes = sum(s.estimated_minutes for s in skills_in_module)
        max_level = max((s.level for s in skills_in_module), default=1)
        module_prereqs = []

        if modules:
            # Depends on the last module
            module_prereqs = [modules[-1].id]

        # Generate module title from skills
        skill_names = [s.name for s in skills_in_module]
        if len(skill_names) == 1:
            title = skill_names[0]
        else:
            title = f"Module {module_id + 1}: {' & '.join(skill_names[:2])}"
            if len(skill_names) > 2:
                title += f" + {len(skill_names) - 2} more"

        module = CourseModule(
            id=f"module_{module_id:03d}",
            title=title,
            description=f"Learn key concepts: {', '.join(skill_names[:3])}",
            skills=chunk,
            estimated_minutes=total_minutes,
            prerequisites=module_prereqs,
            order=module_id,
        )
        modules.append(module)
        module_id += 1

    return modules


def sequence_skills(
    tree: SkillTree,
    module_size: int = 4,
) -> CourseOutline:
    """Sequence skills into a CourseOutline using prerequisite-aware ordering.

    Args:
        tree: The SkillTree (should already have Pareto filtering applied).
        module_size: Number of skills per module.

    Returns:
        A CourseOutline with modules ordered by prerequisites.
    """
    topic = tree.topic
    all_nodes = tree.all_nodes
    all_nodes_map = {n.id: n for n in all_nodes}

    # Topological sort
    ordered_ids = _topological_sort(all_nodes, all_nodes_map)

    # Group into modules
    modules = _group_into_modules(ordered_ids, all_nodes_map, module_size)

    # Calculate total time
    total_minutes = sum(m.estimated_minutes for m in modules)

    # Add Pareto info to metadata
    essential_count = sum(1 for n in all_nodes if n.is_pareto_essential)
    non_essential_count = sum(1 for n in all_nodes if not n.is_pareto_essential)

    outline = CourseOutline(
        topic=topic,
        modules=modules,
        total_estimated_minutes=total_minutes,
        metadata={
            "total_modules": len(modules),
            "module_count": len(modules),
            "total_skills": len(all_nodes),
            "pareto_essential_count": essential_count,
            "pareto_non_essential_count": non_essential_count,
            "module_size": module_size,
            "sequencing_method": "topological_sort_with_module_grouping",
        },
    )

    return outline
