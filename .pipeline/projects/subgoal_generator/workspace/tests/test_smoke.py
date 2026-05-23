"""Smoke test for the subgoal generator pipeline."""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure workspace is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subgoal_generator import Subgoal, DependencyGraph, SubgoalGenerator
from subgoal_generator.parser import parse_response
from subgoal_generator.prompt_builder import build_prompt
from subgoal_generator.output import write_pipeline_entries


class TestSmoke(unittest.TestCase):
    """Verify importability and core functionality."""

    # ---- Task 1: models ----

    def test_import_subgoal(self) -> None:
        s = Subgoal(title="test", description="desc", dependencies=["a"], priority=2)
        self.assertEqual(s.title, "test")
        self.assertEqual(s.dependencies, ["a"])
        self.assertEqual(s.priority, 2)

    def test_import_dependency_graph(self) -> None:
        g = DependencyGraph()
        g.add_edge("B", "A")
        self.assertIn("A", g.get_dependencies("B"))
        self.assertIn("B", g.get_dependents("A"))

    def test_subgoal_to_pipeline_entry(self) -> None:
        s = Subgoal(title="x", description="y", dependencies=[], priority=1)
        entry = s.to_pipeline_entry()
        # to_pipeline_entry returns YAML; check key fields are present
        self.assertIn("title: x", entry)
        self.assertIn("description: y", entry)

    # ---- Task 2: prompt builder + parser ----

    def test_build_prompt_returns_string(self) -> None:
        prompt = build_prompt("learn French")
        self.assertIsInstance(prompt, str)
        self.assertIn("learn French", prompt)

    def test_parse_response(self) -> None:
        sample = (
            "title: Step one\n"
            "description: Do the first thing\n"
            "dependencies: []\n"
            "priority: 1\n\n"
            "title: Step two\n"
            "description: Do the second thing\n"
            "dependencies: [Step one]\n"
            "priority: 2\n"
        )
        subs = parse_response(sample)
        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[0].title, "Step one")
        self.assertEqual(subs[1].dependencies, ["Step one"])

    # ---- Task 3: generator (mocked LLM) ----

    @patch.object(SubgoalGenerator, "__init__", lambda self, **kw: None)
    def test_generate_returns_subgoals(self) -> None:
        gen = SubgoalGenerator()
        gen.llm_client = MagicMock()
        gen.llm_client.complete.return_value = (
            "title: A\n"
            "description: First\n"
            "dependencies: []\n"
            "priority: 1\n\n"
            "title: B\n"
            "description: Second\n"
            "dependencies: [A]\n"
            "priority: 2\n"
        )
        subs = gen.generate("test goal")
        self.assertEqual(len(subs), 2)
        self.assertEqual(subs[0].title, "A")
        self.assertEqual(subs[1].title, "B")

    # ---- Task 4: output ----

    def test_write_pipeline_entries_creates_file(self, tmp_path: str = "/tmp/test_master_ideas.md") -> None:
        subs = [
            Subgoal(title="x", description="y", dependencies=[], priority=1),
        ]
        write_pipeline_entries(subs, tmp_path)
        self.assertTrue(os.path.exists(tmp_path))
        with open(tmp_path) as f:
            content = f.read()
        self.assertIn("x", content)
        os.remove(tmp_path)

    # ---- Task 5: CLI ----

    def test_cli_help_exits_cleanly(self) -> None:
        """Verify the CLI module is importable and --help works."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "subgoal_generator", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--goal", result.stdout)


if __name__ == "__main__":
    unittest.main()
