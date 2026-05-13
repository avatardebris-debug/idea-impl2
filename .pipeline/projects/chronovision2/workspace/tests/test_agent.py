"""
test_agent.py
Tests for the Chronovision2 agent pipeline.

Run with:
    python -m pytest tests/test_agent.py -v
"""

from __future__ import annotations

import json
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest


def _has_anthropic():
    try:
        import anthropic
        return True
    except ImportError:
        return False

# Add parent to path
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from chronovision2.tools import TOOLS, TOOL_SCHEMAS
from chronovision2.core.hypothesis_manager import HypothesisManager
from chronovision2.memory import MemorySystem


class TestTools(unittest.TestCase):
    """Test tool implementations."""

    def test_read_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("hello world")
            f.flush()
            result = TOOLS["read_file"](f.name)
            self.assertEqual(result, "hello world")

    def test_read_file_not_found(self):
        result = TOOLS["read_file"]("/nonexistent/path/file.txt")
        self.assertTrue(result.startswith("ERROR"))

    def test_write_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "test.txt"
            result = TOOLS["write_file"](str(path), "content here")
            self.assertTrue(result.startswith("OK:"))
            self.assertEqual(path.read_text(), "content here")

    def test_append_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "test.txt"
            path.write_text("first line\n")
            result = TOOLS["append_file"](str(path), "second line\n")
            self.assertTrue(result.startswith("OK:"))
            self.assertEqual(path.read_text(), "first line\nsecond line\n")

    def test_list_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (pathlib.Path(tmpdir) / "a.txt").touch()
            (pathlib.Path(tmpdir) / "b.txt").touch()
            result = TOOLS["list_dir"](tmpdir)
            self.assertIn("a.txt", result)
            self.assertIn("b.txt", result)

    def test_search_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (pathlib.Path(tmpdir) / "test.py").touch()
            (pathlib.Path(tmpdir) / "test.txt").touch()
            result = TOOLS["search_files"]("*.py", tmpdir)
            self.assertIn("test.py", result)

    def test_run_command(self):
        result = TOOLS["run_command"]("echo hello")
        self.assertIn("hello", result)

    def test_read_env(self):
        import os
        os.environ["TEST_VAR"] = "test_value"
        result = TOOLS["read_env"]("TEST_VAR")
        self.assertIn("TEST_VAR=test_value", result)

    def test_set_env(self):
        result = TOOLS["set_env"]("TEST_VAR2", "test_value2")
        self.assertIn("OK:", result)
        import os
        self.assertEqual(os.environ.get("TEST_VAR2"), "test_value2")


class TestHypothesisManager(unittest.TestCase):
    """Test hypothesis management."""

    def setUp(self):
        self.manager = HypothesisManager()

    def test_add_hypothesis(self):
        hid = self.manager.add_hypothesis("test", {"param": 1})
        self.assertIsNotNone(hid)
        self.assertEqual(len(self.manager.hypotheses), 1)

    def test_add_duplicate_hypothesis(self):
        self.manager.add_hypothesis("h1", {"a": 1})
        with self.assertRaises(ValueError):
            self.manager.add_hypothesis("h1", {"a": 2})

    def test_get_best_hypothesis(self):
        """Best hypothesis = lowest score (least surprise)."""
        self.manager.add_hypothesis("h1", {"a": 1})
        self.manager.add_hypothesis("h2", {"a": 2})
        # Score h1 with more surprise than h2
        self.manager.score_hypothesis("h1", {"a": 0.0}, {"a": 1.0})
        self.manager.score_hypothesis("h2", {"a": 0.9}, {"a": 1.0})
        best = self.manager.get_best_hypothesis()
        self.assertEqual(best, "h2")

    def test_update_weights(self):
        self.manager.add_hypothesis("h1", {"a": 1})
        self.manager.add_hypothesis("h2", {"a": 2})
        # Give h1 more surprise (worse)
        self.manager.score_hypothesis("h1", {"a": 0.0}, {"a": 1.0})
        self.manager.score_hypothesis("h2", {"a": 0.9}, {"a": 1.0})
        weights = self.manager.update_weights()
        self.assertEqual(len(weights), 2)
        # h2 should have higher weight (lower score = better)
        self.assertGreater(weights["h2"], weights["h1"])

    def test_get_summary(self):
        self.manager.add_hypothesis("h1", {"a": 1})
        summary = self.manager.get_summary()
        self.assertEqual(summary["count"], 1)
        self.assertIn("best_hypothesis", summary)
        self.assertIn("weights", summary)
        self.assertIn("scores", summary)

    def test_run_reward_cycle(self):
        hid = self.manager.add_hypothesis("h1", {"a": 1})
        predictions = {hid: {"key": 1.0}}
        actual = {"key": 1.0}
        weights = self.manager.run_reward_cycle(predictions, actual)
        self.assertEqual(len(weights), 1)
        self.assertIn(hid, weights)

    def test_remove_hypothesis(self):
        hid = self.manager.add_hypothesis("h1", {"a": 1})
        self.assertTrue(self.manager.remove_hypothesis(hid))
        self.assertFalse(self.manager.remove_hypothesis("nonexistent"))

    def test_get_all_scores(self):
        self.manager.add_hypothesis("h1", {"a": 1})
        self.manager.add_hypothesis("h2", {"a": 2})
        scores = self.manager.get_all_scores()
        self.assertIn("h1", scores)
        self.assertIn("h2", scores)
        self.assertEqual(scores["h1"], 0.0)
        self.assertEqual(scores["h2"], 0.0)


class TestMemorySystem(unittest.TestCase):
    """Test memory system."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.memory = MemorySystem(base_dir=self.tmpdir)

    def test_add_and_read_facts(self):
        self.memory.add_fact("fact1")
        facts = self.memory.read_facts()
        self.assertIn("fact1", facts)

    def test_add_and_read_decisions(self):
        self.memory.add_decision("decision1", "reason1")
        decisions = self.memory.read_decisions()
        self.assertIn("decision1", decisions)
        self.assertIn("reason1", decisions)

    def test_add_and_read_tasks(self):
        self.memory.add_task("task1", priority=3)
        tasks = self.memory.read_tasks()
        self.assertIn("task1", tasks)

    def test_add_multiple_facts(self):
        self.memory.add_fact("fact1")
        self.memory.add_fact("fact2")
        facts = self.memory.read_facts()
        self.assertIn("fact1", facts)
        self.assertIn("fact2", facts)


class TestLLMInterface(unittest.TestCase):
    """Test LLM interface factory."""

    def test_get_llm_factory_openai(self):
        from chronovision2.llm_interface import get_llm

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            llm = get_llm("openai")
            self.assertIsNotNone(llm)
            self.assertTrue(hasattr(llm, 'chat'))

    @pytest.mark.skipif(not _has_anthropic(), reason="anthropic package not installed")
    def test_get_llm_factory_claude(self):
        from chronovision2.llm_interface import get_llm

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            llm = get_llm("claude")
            self.assertIsNotNone(llm)
            self.assertTrue(hasattr(llm, 'chat'))

    def test_get_llm_invalid_provider(self):
        from chronovision2.llm_interface import get_llm
        with self.assertRaises(ValueError):
            get_llm("invalid_provider")

    def test_grok_requires_api_key(self):
        from chronovision2.llm_interface import get_llm
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(EnvironmentError):
                get_llm("grok")


class TestAgent(unittest.TestCase):
    """Test agent class."""

    def test_agent_init(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            from chronovision2.agent import Agent
            agent = Agent(provider="openai")
            self.assertIsNotNone(agent.llm)
            self.assertIsNotNone(agent.hypothesis_manager)
            self.assertIsNotNone(agent.memory)

    def test_build_system_prompt(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            from chronovision2.agent import Agent
            agent = Agent(provider="openai")
            prompt = agent._build_system_prompt()
            self.assertIn("You are a helpful AI agent", prompt)
            self.assertIn("hypothesis state", prompt)


if __name__ == "__main__":
    unittest.main()
