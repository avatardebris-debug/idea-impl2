"""Unit tests for the prompt builder module."""

from __future__ import annotations

import os
import sys
import unittest

# Ensure workspace is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subgoal_generator.prompt_builder import build_prompt


class TestBuildPrompt(unittest.TestCase):
    """Tests for build_prompt function."""

    def test_build_prompt_contains_goal(self):
        """Prompt should contain the goal text."""
        prompt = build_prompt("Learn Python")
        self.assertIn("Learn Python", prompt)

    def test_build_prompt_contains_instructions(self):
        """Prompt should contain decomposition instructions."""
        prompt = build_prompt("Test goal")
        self.assertIn("Decompose", prompt)
        self.assertIn("subgoals", prompt)

    def test_build_prompt_format_specification(self):
        """Prompt should specify the expected output format."""
        prompt = build_prompt("Any goal")
        self.assertIn("title:", prompt)
        self.assertIn("description:", prompt)
        self.assertIn("dependencies:", prompt)

    def test_build_prompt_empty_goal(self):
        """Should handle empty goal string."""
        prompt = build_prompt("")
        self.assertIn("Goal:", prompt)

    def test_build_prompt_long_goal(self):
        """Should handle long goal strings."""
        long_goal = " ".join([f"Step {i}" for i in range(100)])
        prompt = build_prompt(long_goal)
        self.assertIn(long_goal, prompt)

    def test_build_prompt_special_characters(self):
        """Should handle special characters in goal."""
        prompt = build_prompt("Build a $10k/month app & learn {new} skills!")
        self.assertIn("Build a $10k/month app & learn {new} skills!", prompt)

    def test_build_prompt_returns_string(self):
        """Should return a string."""
        prompt = build_prompt("Test")
        self.assertIsInstance(prompt, str)

    def test_build_prompt_non_empty(self):
        """Should return a non-empty prompt."""
        prompt = build_prompt("Test")
        self.assertTrue(len(prompt.strip()) > 0)


if __name__ == "__main__":
    unittest.main()
