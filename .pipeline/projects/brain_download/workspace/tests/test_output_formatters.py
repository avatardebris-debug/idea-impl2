"""Tests for brain_download output formatters."""

import json
import pytest
from brain_download.core.models import SkillNode, SkillTree, Topic
from brain_download.core.sequencing_engine import sequence_skills
from brain_download.core.output_formatters import to_json, to_markdown


class TestToJson:
    def test_basic_json_output(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        json_str = to_json(outline, tree)

        data = json.loads(json_str)
        assert "topic" in data
        assert "skill_tree" in data
        assert "course_outline" in data
        assert "modules" in data["course_outline"]
        assert len(data["course_outline"]["modules"]) > 0

    def test_json_contains_stakes(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        json_str = to_json(outline, tree, stakes=[])
        data = json.loads(json_str)
        assert "stakes" in data

    def test_json_contains_compression_maps(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        json_str = to_json(outline, tree, compression_maps=[])
        data = json.loads(json_str)
        assert "compression_maps" in data

    def test_json_is_valid(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        json_str = to_json(outline, tree)
        # Should not raise
        data = json.loads(json_str)
        assert isinstance(data, dict)


class TestToMarkdown:
    def test_basic_markdown_output(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        md_str = to_markdown(outline, tree)

        assert "# Test" in md_str
        assert "## Course Outline" in md_str
        assert "## Skill Tree" in md_str
        assert "### Module" in md_str

    def test_markdown_contains_module_titles(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        md_str = to_markdown(outline, tree)

        for module in outline.modules:
            assert module.title in md_str

    def test_markdown_contains_skill_names(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        md_str = to_markdown(outline, tree)

        for node in tree.all_nodes:
            assert node.name in md_str

    def test_markdown_contains_stakes(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        md_str = to_markdown(outline, tree, stakes=[])
        assert "## Stakes" in md_str

    def test_markdown_contains_compression_maps(self):
        nodes = [
            SkillNode(id=f"n{i}", name=f"Skill {i}", importance=0.5, level=1, prerequisites=[])
            for i in range(5)
        ]
        tree = SkillTree(topic=Topic(name="Test"), root_nodes=nodes, metadata={})
        outline = sequence_skills(tree, module_size=2)

        md_str = to_markdown(outline, tree, compression_maps=[])
        assert "## Compression Maps" in md_str
