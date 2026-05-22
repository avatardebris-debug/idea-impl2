"""Compression engine — generates compression maps for modules."""

from __future__ import annotations

from brain_download.core.models import CompressionMap, CourseOutline, SkillTree


def generate_compression_map(
    outline: CourseOutline,
    tree: SkillTree,
    target_density: str = "high",
) -> list[CompressionMap]:
    """Generate compression maps for each module.

    Args:
        outline: The CourseOutline to generate compression maps for.
        tree: The SkillTree with Pareto filtering applied.
        target_density: Target density level ('low', 'medium', 'high').

    Returns:
        A list of CompressionMap objects, one per module.
    """
    all_nodes_map = {n.id: n for n in tree.all_nodes}
    essential_ids = {n.id for n in tree.all_nodes if n.is_pareto_essential}

    # Density settings
    density_settings = {
        "low": {"essential_weight": 1.0, "non_essential_weight": 0.3, "max_compression": 0.10},
        "medium": {"essential_weight": 1.0, "non_essential_weight": 0.5, "max_compression": 0.25},
        "high": {"essential_weight": 1.0, "non_essential_weight": 0.7, "max_compression": 0.40},
    }
    settings = density_settings.get(target_density, density_settings["medium"])

    compression_maps: list[CompressionMap] = []

    for module in outline.modules:
        module_skills = [all_nodes_map[nid] for nid in module.skills if nid in all_nodes_map]
        essential_skills = [s for s in module_skills if s.id in essential_ids]
        non_essential_skills = [s for s in module_skills if s.id not in essential_ids]

        # Calculate compression ratio
        total_skills = len(module_skills)
        if total_skills == 0:
            continue

        # Determine which non-essential skills to compress
        n_compress = int(len(non_essential_skills) * settings["max_compression"])
        compressed_skills = non_essential_skills[:n_compress]
        skipped_skills = non_essential_skills[n_compress:]

        # Generate compression tips
        compression_tips = []
        for skill in compressed_skills:
            compression_tips.append({
                "skill_id": skill.id,
                "skill_name": skill.name,
                "compression_strategy": _get_compression_strategy(skill, target_density),
                "estimated_time_saved": int(skill.estimated_minutes * 0.5),
            })

        # Generate skip recommendations
        skip_recommendations = []
        for skill in skipped_skills:
            skip_recommendations.append({
                "skill_id": skill.id,
                "skill_name": skill.name,
                "reason": "Low Pareto importance for this domain",
                "alternative": f"Refer to {skill.name} documentation if needed",
            })

        # Calculate module compression stats
        total_minutes = sum(s.estimated_minutes for s in module_skills)
        compressed_minutes = sum(t["estimated_time_saved"] for t in compression_tips)
        skipped_minutes = sum(s.estimated_minutes for s in skipped_skills)
        time_saved = compressed_minutes + skipped_minutes
        compression_ratio = time_saved / total_minutes if total_minutes > 0 else 0

        compression_map = CompressionMap(
            module_id=module.id,
            module_title=module.title,
            skip_list=[s.id for s in skipped_skills],
            emphasize_list=[s.id for s in essential_skills],
            compress_ratio=round(compression_ratio, 2),
            estimated_time_savings=time_saved,
            density_target=target_density,
            essential_skills=[s.id for s in essential_skills],
            compressed_skills=[s.id for s in compressed_skills],
            skipped_skills=[s.id for s in skipped_skills],
            total_skills_in_module=total_skills,
            compression_ratio=round(compression_ratio, 2),
            compressed_count=len(compressed_skills),
            skipped_count=len(skipped_skills),
        )
        compression_maps.append(compression_map)

    return compression_maps


def _get_compression_strategy(skill, density: str) -> str:
    """Get a compression strategy for a skill."""
    level = skill.level
    name_lower = skill.name.lower()

    if level == 1:
        return "Focus on core concepts only; skip advanced examples"
    elif level == 2:
        if "visualization" in name_lower or "plot" in name_lower:
            return "Use pre-made templates; focus on interpretation"
        elif "testing" in name_lower:
            return "Learn basic test patterns; skip edge cases"
        else:
            return "Focus on common patterns; skip rare edge cases"
    else:
        if "deep" in name_lower or "advanced" in name_lower:
            return "Skim for key concepts; refer to documentation as needed"
        else:
            return "Focus on practical applications; skip theoretical details"


def get_compression_map_for_module(
    outline: CourseOutline,
    tree: SkillTree,
    module_id: str,
    target_density: str = "high",
) -> CompressionMap | None:
    """Get the compression map for a specific module."""
    maps = generate_compression_map(outline, tree, target_density)
    for m in maps:
        if m.module_id == module_id:
            return m
    return None
