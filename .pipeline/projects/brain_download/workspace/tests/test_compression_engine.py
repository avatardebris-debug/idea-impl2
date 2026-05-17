"""Tests for brain_download compression engine."""

import pytest
from brain_download.core.models import SkillNode, SkillTree, Topic
from brain_download.core.compression_engine import generate_compression_map, get_compression_map_for_module
from brain_download.core.sequencing_engine import sequence_skills
from brain_download.core.selection_matrix import pareto_filter


class TestGenerateCompressionMap:
    def test_basic_compression(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(10)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=3)

        maps = generate_compression_map(outline, tree, target_density="high")

        assert len(maps) == len(outline.modules)

    def test_compression_maps_have_required_fields(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(10)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=3)

        maps = generate_compression_map(outline, tree, target_density="high")

        for comp_map in maps:
            assert comp_map.module_id
            assert comp_map.module_title
            assert isinstance(comp_map.essential_skills, list)
            assert isinstance(comp_map.compressed_skills, list)
            assert isinstance(comp_map.skipped_skills, list)
            assert comp_map.total_skills_in_module > 0
            assert comp_map.compression_ratio >= 0

    def test_high_density_more_compression(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(10)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=3)

        high_maps = generate_compression_map(outline, tree, target_density="high")
        low_maps = generate_compression_map(outline, tree, target_density="low")

        # High density should have more compressed/skipped skills
        high_total = sum(m.compressed_count + m.skipped_count for m in high_maps)
        low_total = sum(m.compressed_count + m.skipped_count for m in low_maps)

        assert high_total >= low_total

    def test_empty_outline(self):
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=[], metadata={})
        outline = sequence_skills(tree, module_size=3)

        maps = generate_compression_map(outline, tree, target_density="high")
        assert len(maps) == 0


class TestGetCompressionMapForModule:
    def test_single_module_compression(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        comp_map = get_compression_map_for_module(outline, tree, outline.modules[0].id, target_density="high")

        assert comp_map.module_id == outline.modules[0].id
        assert comp_map.total_skills_in_module == len(outline.modules[0].skills)
