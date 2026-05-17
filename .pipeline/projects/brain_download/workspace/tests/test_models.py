"""Tests for brain_download models."""

import pytest
from brain_download.core.models import (
    CompressionMap,
    CourseModule,
    CourseOutline,
    SkillNode,
    SkillTree,
    StakesConfig,
    StakesMechanism,
    Topic,
)


class TestTopic:
    def test_create_topic(self):
        topic = Topic(
            name="Python Programming",
            domain="python",
            description="Learn Python from scratch",
            target_audience="beginner",
            desired_outcome="Build web applications",
        )
        assert topic.name == "Python Programming"
        assert topic.domain == "python"
        assert topic.description == "Learn Python from scratch"
        assert topic.target_audience == "beginner"
        assert topic.desired_outcome == "Build web applications"

    def test_topic_defaults(self):
        topic = Topic(name="Test")
        assert topic.name == "Test"
        assert topic.domain == "general"
        assert topic.target_audience == "beginner"


class TestSkillNode:
    def test_create_skill_node(self):
        node = SkillNode(
            id="test_1",
            name="Test Skill",
            description="A test skill",
            importance=0.8,
            level=2,
            estimated_minutes=60,
            tags=["test"],
            prerequisites=[],
        )
        assert node.id == "test_1"
        assert node.name == "Test Skill"
        assert node.importance == 0.8
        assert node.level == 2
        assert node.estimated_minutes == 60
        assert node.tags == ["test"]
        assert node.prerequisites == []
        assert node.is_pareto_essential is False

    def test_skill_node_defaults(self):
        node = SkillNode(id="test_1", name="Test")
        assert node.importance == 0.5
        assert node.level == 1
        assert node.estimated_minutes == 30
        assert node.tags == []
        assert node.prerequisites == []
        assert node.is_pareto_essential is False


class TestSkillTree:
    def test_create_skill_tree(self):
        topic = Topic(name="Python", domain="python")
        tree = SkillTree(topic=topic, root_nodes=[], metadata={})
        assert tree.topic.name == "Python"
        assert tree.root_nodes == []
        assert tree.all_nodes == []

    def test_all_nodes_property(self):
        nodes = [
            SkillNode(id="n1", name="N1"),
            SkillNode(id="n2", name="N2"),
        ]
        tree = SkillTree(topic=Topic(name="Test"), all_nodes=nodes, metadata={})
        assert len(tree.all_nodes) == 2


class TestCourseModule:
    def test_create_module(self):
        module = CourseModule(
            id="mod_1",
            title="Test Module",
            description="A test module",
            skills=["n1", "n2"],
            estimated_minutes=60,
            prerequisites=[],
            order=0,
        )
        assert module.id == "mod_1"
        assert module.title == "Test Module"
        assert module.skills == ["n1", "n2"]
        assert module.estimated_minutes == 60
        assert module.order == 0


class TestCourseOutline:
    def test_create_outline(self):
        outline = CourseOutline(
            topic=Topic(name="Python"),
            modules=[],
            total_estimated_minutes=0,
            metadata={},
        )
        assert outline.topic.name == "Python"
        assert outline.modules == []
        assert outline.total_estimated_minutes == 0


class TestStakesConfig:
    def test_default_config(self):
        config = StakesConfig(module_id="mod_1")
        assert config.module_id == "mod_1"
        assert config.mechanisms == []

    def test_config_with_mechanisms(self):
        mech = StakesMechanism(
            id="m1",
            name="Test Mechanism",
            description="A test",
            type="social",
            impact_score=0.8,
            effort_required="low",
            implementation_steps=["step1"],
        )
        config = StakesConfig(module_id="mod_1", mechanisms=[mech])
        assert config.module_id == "mod_1"
        assert len(config.mechanisms) == 1
        assert config.mechanisms[0].name == "Test Mechanism"


class TestStakesMechanism:
    def test_create_mechanism(self):
        mech = StakesMechanism(
            id="m1",
            name="Test Mechanism",
            description="A test",
            type="social",
            impact_score=0.8,
            effort_required="low",
            implementation_steps=["step1"],
        )
        assert mech.id == "m1"
        assert mech.name == "Test Mechanism"
        assert mech.description == "A test"
        assert mech.type == "social"
        assert mech.impact_score == 0.8
        assert mech.effort_required == "low"
        assert mech.implementation_steps == ["step1"]

    def test_mechanism_defaults(self):
        mech = StakesMechanism(
            id="m1",
            name="Test",
            description="Test",
            type="social",
            impact_score=0.5,
            effort_required="medium",
        )
        assert mech.id == "m1"
        assert mech.implementation_steps == []


class TestCompressionMap:
    def test_create_compression_map(self):
        comp = CompressionMap(
            module_id="mod_1",
            skip_list=["n1", "n2"],
            emphasize_list=["n3"],
            compress_ratio=0.5,
            estimated_time_savings=30,
            density_target="high",
        )
        assert comp.module_id == "mod_1"
        assert comp.skip_list == ["n1", "n2"]
        assert comp.emphasize_list == ["n3"]
        assert comp.compress_ratio == 0.5
        assert comp.estimated_time_savings == 30
        assert comp.density_target == "high"

    def test_compression_map_defaults(self):
        comp = CompressionMap(module_id="mod_1")
        assert comp.skip_list == []
        assert comp.emphasize_list == []
        assert comp.compress_ratio == 1.0
        assert comp.estimated_time_savings == 0
        assert comp.density_target == "high"
