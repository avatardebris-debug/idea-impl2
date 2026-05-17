"""Output formatters — JSON and Markdown output for course outlines."""

from __future__ import annotations

import json
from datetime import datetime

from brain_download.core.models import (
    CompressionMap,
    CourseModule,
    CourseOutline,
    SkillNode,
    SkillTree,
    StakesMechanism,
    Topic,
)


def _serialize_skill_node(node: SkillNode) -> dict:
    """Serialize a SkillNode to a dict."""
    return {
        "id": node.id,
        "name": node.name,
        "description": node.description,
        "importance": node.importance,
        "level": node.level,
        "estimated_minutes": node.estimated_minutes,
        "tags": node.tags,
        "prerequisites": node.prerequisites,
        "is_pareto_essential": node.is_pareto_essential,
    }


def _serialize_module(module: CourseModule) -> dict:
    """Serialize a CourseModule to a dict."""
    return {
        "id": module.id,
        "title": module.title,
        "description": module.description,
        "skills": module.skills,
        "estimated_minutes": module.estimated_minutes,
        "prerequisites": module.prerequisites,
        "order": module.order,
    }


def _serialize_stakes(mechanism: StakesMechanism) -> dict:
    """Serialize a StakesMechanism to a dict."""
    return {
        "id": mechanism.id,
        "name": mechanism.name,
        "description": mechanism.description,
        "type": mechanism.type,
        "impact_score": mechanism.impact_score,
        "effort_required": mechanism.effort_required,
        "implementation_steps": mechanism.implementation_steps,
    }


def _serialize_compression(compression: CompressionMap) -> dict:
    """Serialize a CompressionMap to a dict."""
    return {
        "module_id": compression.module_id,
        "skip_list": compression.skip_list,
        "emphasize_list": compression.emphasize_list,
        "compress_ratio": compression.compress_ratio,
        "estimated_time_savings": compression.estimated_time_savings,
        "density_target": compression.density_target,
    }


def to_json(
    outline: CourseOutline,
    tree: SkillTree,
    stakes: list[StakesMechanism] | None = None,
    compression_maps: list[CompressionMap] | None = None,
) -> str:
    """Serialize the complete course to JSON."""
    data = {
        "topic": {
            "name": outline.topic.name,
            "domain": outline.topic.domain,
            "description": outline.topic.description,
            "target_audience": outline.topic.target_audience,
            "desired_outcome": outline.topic.desired_outcome,
        },
        "skill_tree": {
            "root_nodes": [_serialize_skill_node(n) for n in tree.root_nodes],
            "all_nodes": [_serialize_skill_node(n) for n in tree.all_nodes],
            "metadata": tree.metadata,
        },
        "course_outline": {
            "modules": [_serialize_module(m) for m in outline.modules],
            "total_estimated_minutes": outline.total_estimated_minutes,
            "metadata": outline.metadata,
        },
        "stakes": [_serialize_stakes(s) for s in (stakes or [])],
        "compression_maps": [_serialize_compression(c) for c in (compression_maps or [])],
        "generated_at": datetime.now().isoformat(),
    }
    return json.dumps(data, indent=2)


def to_markdown(
    outline: CourseOutline,
    tree: SkillTree,
    stakes: list[StakesMechanism] | None = None,
    compression_maps: list[CompressionMap] | None = None,
) -> str:
    """Serialize the complete course to Markdown."""
    lines = []
    lines.append(f"# 🧠 Brain Download: {outline.topic.name}")
    lines.append("")
    lines.append(f"**Domain:** {outline.topic.domain}")
    lines.append(f"**Target Audience:** {outline.topic.target_audience}")
    lines.append(f"**Desired Outcome:** {outline.topic.desired_outcome}")
    lines.append(f"**Total Estimated Time:** {outline.total_estimated_minutes} minutes ({outline.total_estimated_minutes / 60:.1f} hours)")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")

    # Skill Tree Summary
    lines.append("## Skill Tree")
    lines.append("")
    lines.append(f"- **Total Skills:** {len(tree.all_nodes)}")
    lines.append(f"- **Root Skills:** {len(tree.root_nodes)}")
    essential_count = sum(1 for n in tree.all_nodes if n.is_pareto_essential)
    lines.append(f"- **Pareto-Essential Skills:** {essential_count} ({essential_count / len(tree.all_nodes) * 100:.0f}%)")
    lines.append("")

    # Root Skills
    lines.append("## 🌱 Root Skills (Level 1)")
    lines.append("")
    for node in tree.root_nodes:
        essential_tag = " ⭐ ESSENTIAL" if node.is_pareto_essential else ""
        lines.append(f"- **{node.name}** ({node.estimated_minutes} min){essential_tag}")
    lines.append("")

    # Course Outline
    lines.append("## 📚 Course Outline")
    lines.append("")

    for module in outline.modules:
        lines.append(f"### Module {module.order + 1}: {module.title}")
        lines.append("")
        lines.append(f"**Duration:** {module.estimated_minutes} minutes")
        lines.append(f"**Skills:**")
        for skill_id in module.skills:
            node = next((n for n in tree.all_nodes if n.id == skill_id), None)
            if node:
                essential_tag = " ⭐" if node.is_pareto_essential else ""
                lines.append(f"  - {node.name} ({node.estimated_minutes} min){essential_tag}")
        lines.append("")

    # Stakes
    if stakes:
        lines.append("## Stakes")
        lines.append("")
        for mechanism in stakes:
            lines.append(f"### {mechanism.name} ({mechanism.type})")
            lines.append(f"**Impact Score:** {mechanism.impact_score}")
            lines.append(f"**Effort Required:** {mechanism.effort_required}")
            lines.append(f"**Description:** {mechanism.description}")
            lines.append("")
            lines.append("**Steps:**")
            for step in mechanism.implementation_steps:
                lines.append(f"1. {step}")
            lines.append("")

    # Compression
    if compression_maps:
        lines.append("## Compression Maps")
        lines.append("")
        for comp in compression_maps:
            lines.append(f"### {comp.module_id}")
            lines.append(f"- **Skip List:** {len(comp.skip_list)} skills")
            lines.append(f"- **Emphasize List:** {len(comp.emphasize_list)} skills")
            lines.append(f"- **Compression Ratio:** {comp.compress_ratio}")
            lines.append(f"- **Time Savings:** {comp.estimated_time_savings} min")
            lines.append(f"- **Density Target:** {comp.density_target}")
            lines.append("")

    return "\n".join(lines)
