"""Tests for brain_download orchestrator."""

import pytest
from brain_download.core.orchestrator import DESSCOrchestrator, brain_download
from brain_download.config.learning_models import DESSCConfig


class TestDESSCOrchestrator:
    def test_basic_run(self):
        orchestrator = DESSCOrchestrator()
        result = orchestrator.run(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
        )

        assert "outline" in result
        assert "tree" in result
        assert "stakes" in result
        assert "compression_maps" in result
        assert "json" in result
        assert "markdown" in result

    def test_result_outline_valid(self):
        orchestrator = DESSCOrchestrator()
        result = orchestrator.run(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
        )

        outline = result["outline"]
        assert outline is not None
        assert len(outline.modules) > 0
        assert outline.total_estimated_minutes > 0

    def test_result_tree_valid(self):
        orchestrator = DESSCOrchestrator()
        result = orchestrator.run(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
        )

        tree = result["tree"]
        assert tree is not None
        assert len(tree.all_nodes) > 0
        assert len(tree.root_nodes) > 0

    def test_result_json_valid(self):
        orchestrator = DESSCOrchestrator()
        result = orchestrator.run(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
        )

        import json
        data = json.loads(result["json"])
        assert "topic" in data
        assert "skill_tree" in data
        assert "course_outline" in data

    def test_result_markdown_valid(self):
        orchestrator = DESSCOrchestrator()
        result = orchestrator.run(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
        )

        md = result["markdown"]
        assert "# Python Programming" in md
        assert "## Course Outline" in md

    def test_custom_config(self):
        config = DESSCConfig(
            min_skill_importance=0.7,
            max_skill_importance=1.0,
            default_estimated_minutes=45,
        )
        orchestrator = DESSCOrchestrator(config)
        result = orchestrator.run(
            topic_name="Test Topic",
            domain="general",
            target_audience="beginner",
            desired_outcome="Learn",
        )

        outline = result["outline"]
        assert outline is not None
        assert len(outline.modules) > 0

    def test_custom_module_size(self):
        orchestrator = DESSCOrchestrator()
        result = orchestrator.run(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
            module_size=1,
        )

        for module in result["outline"].modules:
            assert len(module.skills) <= 1

    def test_custom_density(self):
        orchestrator = DESSCOrchestrator()
        result = orchestrator.run(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
            target_density="low",
        )

        for comp_map in result["compression_maps"]:
            assert comp_map.target_density == "low"


class TestBrainDownload:
    def test_convenience_function(self):
        result = brain_download(
            topic_name="Python Programming",
            domain="python",
            target_audience="beginner",
            desired_outcome="Build web apps",
        )

        assert "outline" in result
        assert "tree" in result
        assert "json" in result
        assert "markdown" in result

    def test_convenience_function_with_config(self):
        config = DESSCConfig(min_skill_importance=0.8)
        result = brain_download(
            topic_name="Test Topic",
            domain="general",
            config=config,
        )

        assert result["outline"] is not None
