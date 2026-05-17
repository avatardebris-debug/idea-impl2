"""Tests for brain_download deconstruction engine."""

import pytest
from brain_download.config.learning_models import DESSCConfig
from brain_download.core.deconstruction_engine import deconstruct_topic
from brain_download.core.models import Topic


class TestDeconstructTopic:
    def test_basic_deconstruction(self):
        tree = deconstruct_topic(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
            config=DESSCConfig(),
        )
        assert tree is not None
        assert tree.topic.name == "Python Programming"
        assert len(tree.all_nodes) > 0
        assert len(tree.root_nodes) > 0

    def test_domain_profile_applied(self):
        tree = deconstruct_topic(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
            config=DESSCConfig(),
        )
        # Python domain profile should add skills
        skill_names = [n.name for n in tree.all_nodes]
        assert any("Python" in name or "Syntax" in name for name in skill_names)

    def test_empty_domain(self):
        tree = deconstruct_topic(
            topic_name="Unknown Topic",
            domain="nonexistent",
            target_audience="beginner",
            desired_outcome="Learn it",
            config=DESSCConfig(),
        )
        assert tree is not None
        assert len(tree.all_nodes) > 0

    def test_config_parameters(self):
        config = DESSCConfig(
            min_skill_importance=0.5,
            max_skill_importance=1.0,
            default_estimated_minutes=60,
        )
        tree = deconstruct_topic(
            topic_name="Test Topic",
            domain="general",
            target_audience="beginner",
            desired_outcome="Learn",
            config=config,
        )
        # All skills should have importance >= 0.5
        for node in tree.all_nodes:
            assert node.importance >= 0.5

    def test_root_nodes_have_no_prerequisites(self):
        tree = deconstruct_topic(
            topic_name="Test Topic",
            domain="general",
            target_audience="beginner",
            desired_outcome="Learn",
            config=DESSCConfig(),
        )
        for node in tree.root_nodes:
            assert len(node.prerequisites) == 0

    def test_non_root_nodes_have_prerequisites(self):
        tree = deconstruct_topic(
            topic_name="Test Topic",
            domain="general",
            target_audience="beginner",
            desired_outcome="Learn",
            config=DESSCConfig(),
        )
        root_ids = {n.id for n in tree.root_nodes}
        for node in tree.all_nodes:
            if node.id not in root_ids:
                assert len(node.prerequisites) > 0
