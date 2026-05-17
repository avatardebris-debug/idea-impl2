"""Tests for brain_download stakes calculator."""

import pytest
from brain_download.core.models import CourseOutline, SkillNode, SkillTree, StakesConfig, Topic
from brain_download.core.sequencing_engine import sequence_skills
from brain_download.core.stakes_calculator import generate_stakes, get_recommended_stakes


class TestGenerateStakes:
    def test_basic_stakes_generation(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        stakes = generate_stakes(outline)

        assert len(stakes) > 0
        assert len(stakes) <= 5  # default max

    def test_stakes_have_required_fields(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        stakes = generate_stakes(outline)

        for mechanism in stakes:
            assert mechanism.name
            assert mechanism.description
            assert mechanism.type in ("social", "financial", "portfolio", "credential")
            assert 0 <= mechanism.impact_score <= 1
            assert mechanism.effort_required in ("low", "medium", "high")
            assert len(mechanism.implementation_steps) > 0

    def test_stakes_sorted_by_impact(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        stakes = generate_stakes(outline)

        for i in range(len(stakes) - 1):
            assert stakes[i].impact_score >= stakes[i + 1].impact_score

    def test_max_mechanisms_respected(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        config = StakesConfig(max_mechanisms=2)
        stakes = generate_stakes(outline, config)

        assert len(stakes) == 2

    def test_social_preference(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        config = StakesConfig(prefer_social=True)
        stakes = generate_stakes(outline, config)

        # Top stakes should be social
        if stakes:
            assert stakes[0].type == "social"

    def test_financial_preference(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        config = StakesConfig(prefer_financial=True)
        stakes = generate_stakes(outline, config)

        if stakes:
            assert stakes[0].type == "financial"


class TestGetRecommendedStakes:
    def test_recommended_stakes(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        recommended = get_recommended_stakes(outline)

        assert len(recommended) > 0
        assert len(recommended) <= 5
