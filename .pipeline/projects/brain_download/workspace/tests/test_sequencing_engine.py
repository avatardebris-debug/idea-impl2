"""Tests for brain_download sequencing engine."""

import pytest
from brain_download.core.models import SkillNode, SkillTree, Topic
from brain_download.core.sequencing_engine import sequence_skills


class TestSequenceSkills:
    def test_basic_sequence(self):
        nodes = [
            SkillNode(id="n1", name="Basics", importance=0.9, level=1, prerequisites=[]),
            SkillNode(id="n2", name="Intermediate", importance=0.8, level=2, prerequisites=["n1"]),
            SkillNode(id="n3", name="Advanced", importance=0.7, level=3, prerequisites=["n2"]),
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        outline = sequence_skills(tree, module_size=2)

        assert len(outline.modules) > 0
        assert outline.total_estimated_minutes > 0
        assert outline.metadata["total_skills"] == 3

    def test_modules_ordered_by_prerequisites(self):
        nodes = [
            SkillNode(id="n1", name="Basics", importance=0.9, level=1, prerequisites=[]),
            SkillNode(id="n2", name="Intermediate", importance=0.8, level=2, prerequisites=["n1"]),
            SkillNode(id="n3", name="Advanced", importance=0.7, level=3, prerequisites=["n2"]),
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        outline = sequence_skills(tree, module_size=1)

        # n1 should come before n2, n2 before n3
        all_ids = []
        for module in outline.modules:
            all_ids.extend(module.skills)

        assert all_ids.index("n1") < all_ids.index("n2")
        assert all_ids.index("n2") < all_ids.index("n3")

    def test_empty_tree(self):
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=[], metadata={})
        outline = sequence_skills(tree, module_size=2)
        assert len(outline.modules) == 0
        assert outline.total_estimated_minutes == 0

    def test_module_size_respected(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(10)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        outline = sequence_skills(tree, module_size=3)

        # 10 skills / 3 per module = 4 modules (3, 3, 3, 1)
        assert len(outline.modules) == 4
        for module in outline.modules:
            assert len(module.skills) <= 3

    def test_all_skills_included(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        outline = sequence_skills(tree, module_size=2)

        all_skills = []
        for module in outline.modules:
            all_skills.extend(module.skills)

        assert set(all_skills) == {"n0", "n1", "n2", "n3", "n4"}

    def test_metadata_contains_module_count(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        outline = sequence_skills(tree, module_size=2)

        assert outline.metadata["module_count"] == 3
