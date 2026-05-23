"""Unit tests for the subgoal generator data models."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import yaml

# Ensure workspace is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subgoal_generator.models import Subgoal, DependencyGraph


class TestSubgoal(unittest.TestCase):
    """Tests for the Subgoal dataclass."""

    def test_subgoal_creation_defaults(self):
        """Subgoal should have correct defaults."""
        sg = Subgoal(title="Test", description="A test subgoal")
        self.assertEqual(sg.title, "Test")
        self.assertEqual(sg.description, "A test subgoal")
        self.assertEqual(sg.dependencies, [])
        self.assertEqual(sg.priority, 1)

    def test_subgoal_creation_with_all_fields(self):
        """Subgoal should accept all fields."""
        sg = Subgoal(
            title="Build",
            description="Build the thing",
            dependencies=["Design", "Plan"],
            priority=5,
        )
        self.assertEqual(sg.title, "Build")
        self.assertEqual(sg.description, "Build the thing")
        self.assertEqual(sg.dependencies, ["Design", "Plan"])
        self.assertEqual(sg.priority, 5)

    def test_to_pipeline_entry(self):
        """to_pipeline_entry should produce valid YAML with all fields."""
        sg = Subgoal(
            title="Design",
            description="Design the system",
            dependencies=[],
            priority=3,
        )
        entry = sg.to_pipeline_entry()
        parsed = yaml.safe_load(entry)
        self.assertEqual(parsed["title"], "Design")
        self.assertEqual(parsed["description"], "Design the system")
        self.assertEqual(parsed["dependencies"], [])
        self.assertEqual(parsed["priority"], 3)

    def test_to_pipeline_entry_with_dependencies(self):
        """to_pipeline_entry should include dependencies in YAML."""
        sg = Subgoal(
            title="Build",
            description="Build it",
            dependencies=["Design"],
            priority=2,
        )
        entry = sg.to_pipeline_entry()
        parsed = yaml.safe_load(entry)
        self.assertEqual(parsed["dependencies"], ["Design"])

    def test_from_pipeline_entry(self):
        """from_pipeline_entry should reconstruct a Subgoal from YAML."""
        sg = Subgoal(
            title="Test",
            description="Test desc",
            dependencies=["A", "B"],
            priority=4,
        )
        entry = sg.to_pipeline_entry()
        restored = Subgoal.from_pipeline_entry(entry)
        self.assertEqual(restored.title, sg.title)
        self.assertEqual(restored.description, sg.description)
        self.assertEqual(restored.dependencies, sg.dependencies)
        self.assertEqual(restored.priority, sg.priority)

    def test_from_pipeline_entry_minimal(self):
        """from_pipeline_entry should handle minimal YAML entries."""
        yaml_str = "title: Minimal\ndescription: Just a title\n"
        sg = Subgoal.from_pipeline_entry(yaml_str)
        self.assertEqual(sg.title, "Minimal")
        self.assertEqual(sg.description, "Just a title")
        self.assertEqual(sg.dependencies, [])
        self.assertEqual(sg.priority, 1)

    def test_from_pipeline_entry_invalid_yaml(self):
        """from_pipeline_entry should raise ValueError on invalid YAML."""
        with self.assertRaises(ValueError):
            Subgoal.from_pipeline_entry("{{invalid yaml: [")

    def test_from_pipeline_entry_missing_title(self):
        """from_pipeline_entry should raise ValueError if title is missing."""
        yaml_str = "description: No title here\n"
        with self.assertRaises(ValueError):
            Subgoal.from_pipeline_entry(yaml_str)


class TestDependencyGraph(unittest.TestCase):
    """Tests for the DependencyGraph class."""

    def test_add_subgoal(self):
        """add_subgoal should add a subgoal to the graph."""
        graph = DependencyGraph()
        graph.add_subgoal(Subgoal(title="A", description="First"))
        self.assertIn("A", graph.subgoals)

    def test_add_subgoal_with_dependencies(self):
        """add_subgoal should store dependencies."""
        graph = DependencyGraph()
        graph.add_subgoal(Subgoal(title="B", description="Second", dependencies=["A"]))
        graph.add_subgoal(Subgoal(title="A", description="First"))
        self.assertEqual(graph.subgoals["B"].dependencies, ["A"])

    def test_validate_no_cycles(self):
        """validate should pass when there are no cycles."""
        graph = DependencyGraph()
        graph.add_subgoal(Subgoal(title="A", description="First"))
        graph.add_subgoal(Subgoal(title="B", description="Second", dependencies=["A"]))
        # Should not raise
        graph.validate()

    def test_validate_detects_cycle(self):
        """validate should raise ValueError when a cycle exists."""
        graph = DependencyGraph()
        graph.add_subgoal(Subgoal(title="A", description="First", dependencies=["B"]))
        graph.add_subgoal(Subgoal(title="B", description="Second", dependencies=["A"]))
        with self.assertRaises(ValueError):
            graph.validate()

    def test_validate_missing_dependency(self):
        """validate should raise ValueError for missing dependencies."""
        graph = DependencyGraph()
        graph.add_subgoal(Subgoal(title="A", description="First", dependencies=["NonExistent"]))
        with self.assertRaises(ValueError):
            graph.validate()

    def test_topological_sort(self):
        """topological_sort should return subgoals in dependency order."""
        graph = DependencyGraph()
        graph.add_subgoal(Subgoal(title="C", description="Third"))
        graph.add_subgoal(Subgoal(title="B", description="Second", dependencies=["A"]))
        graph.add_subgoal(Subgoal(title="A", description="First"))
        order = graph.topological_sort()
        titles = [sg.title for sg in order]
        # A must come before B
        self.assertLess(titles.index("A"), titles.index("B"))
        # C can be anywhere (no deps)
        self.assertIn("C", titles)

    def test_topological_sort_empty(self):
        """topological_sort should return empty list for empty graph."""
        graph = DependencyGraph()
        self.assertEqual(graph.topological_sort(), [])

    def test_topological_sort_single(self):
        """topological_sort should return single subgoal for single-item graph."""
        graph = DependencyGraph()
        graph.add_subgoal(Subgoal(title="Only", description="Solo"))
        order = graph.topological_sort()
        self.assertEqual(len(order), 1)
        self.assertEqual(order[0].title, "Only")


if __name__ == "__main__":
    unittest.main()
