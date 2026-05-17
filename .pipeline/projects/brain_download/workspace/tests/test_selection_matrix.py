"""Tests for brain_download selection matrix."""

import pytest
from brain_download.core.models import SkillNode, SkillTree, Topic
from brain_download.core.selection_matrix import (
    get_pareto_essential_nodes,
    get_pareto_non_essential_nodes,
    pareto_filter,
)


class TestParetoFilter:
    def test_filter_reduces_nodes(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5 + i * 0.1, level=1)
            for i in range(10)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        filtered = pareto_filter(tree, threshold=0.3)  # top 30%

        essential_count = sum(1 for n in filtered.all_nodes if n.is_pareto_essential)
        # 30% of 10 = 3
        assert essential_count == 3

    def test_filter_selects_highest_importance(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.1 + i * 0.1, level=1)
            for i in range(10)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        filtered = pareto_filter(tree, threshold=0.3)

        essential_ids = get_pareto_essential_nodes(filtered)
        # Top 3 by importance: n9 (0.9), n8 (0.8), n7 (0.7)
        assert "n9" in essential_ids
        assert "n8" in essential_ids
        assert "n7" in essential_ids

    def test_filter_empty_tree(self):
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=[], metadata={})
        filtered = pareto_filter(tree, threshold=0.3)
        assert filtered is tree
        assert len(filtered.all_nodes) == 0

    def test_filter_metadata(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1)
            for i in range(10)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        filtered = pareto_filter(tree, threshold=0.5)

        assert filtered.metadata["pareto_threshold"] == 0.3 or filtered.metadata["pareto_threshold"] == 0.5
        assert filtered.metadata["pareto_selected_count"] == 5
        assert filtered.metadata["pareto_total_count"] == 10

    def test_filter_one_node(self):
        nodes = [SkillNode(id="n1", name="Skill 1", importance=0.5, level=1)]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})

        filtered = pareto_filter(tree, threshold=0.3)
        essential_ids = get_pareto_essential_nodes(filtered)
        assert essential_ids == ["n1"]


class TestGetEssentialNodes:
    def test_get_essential(self):
        nodes = [
            SkillNode(id="n1", name="N1", importance=0.9, level=1),
            SkillNode(id="n2", name="N2", importance=0.3, level=1),
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        filtered = pareto_filter(tree, threshold=0.5)

        essential = get_pareto_essential_nodes(filtered)
        assert essential == ["n1"]

    def test_get_non_essential(self):
        nodes = [
            SkillNode(id="n1", name="N1", importance=0.9, level=1),
            SkillNode(id="n2", name="N2", importance=0.3, level=1),
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        filtered = pareto_filter(tree, threshold=0.5)

        non_essential = get_pareto_non_essential_nodes(filtered)
        assert non_essential == ["n2"]
