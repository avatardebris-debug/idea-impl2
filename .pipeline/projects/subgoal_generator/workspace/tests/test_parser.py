"""Unit tests for the parser module."""

from __future__ import annotations

import os
import sys
import unittest

# Ensure workspace is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subgoal_generator.parser import parse_response
from subgoal_generator.models import Subgoal


class TestParseResponse(unittest.TestCase):
    """Tests for parse_response function."""

    def test_parse_single_subgoal(self):
        """Should parse a single subgoal block."""
        text = """title: Build the house
description: Construct a two-story house
dependencies: [Design the house]
priority: 5"""
        result = parse_response(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Build the house")
        self.assertEqual(result[0].description, "Construct a two-story house")
        self.assertEqual(result[0].dependencies, ["Design the house"])
        self.assertEqual(result[0].priority, 5)

    def test_parse_multiple_subgoals(self):
        """Should parse multiple subgoal blocks separated by blank lines."""
        text = """title: Design the house
description: Create blueprints
dependencies: []
priority: 3

title: Build the house
description: Construct the house
dependencies: [Design the house]
priority: 5"""
        result = parse_response(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].title, "Design the house")
        self.assertEqual(result[1].title, "Build the house")

    def test_parse_empty_dependencies(self):
        """Should handle empty dependencies list."""
        text = """title: Start
description: Begin
dependencies: []
priority: 1"""
        result = parse_response(text)
        self.assertEqual(result[0].dependencies, [])

    def test_parse_missing_dependencies_defaults_to_empty(self):
        """Should default dependencies to empty list if missing."""
        text = """title: Start
description: Begin
priority: 1"""
        result = parse_response(text)
        self.assertEqual(result[0].dependencies, [])

    def test_parse_missing_priority_defaults_to_1(self):
        """Should default priority to 1 if missing."""
        text = """title: Start
description: Begin
dependencies: []"""
        result = parse_response(text)
        self.assertEqual(result[0].priority, 1)

    def test_parse_empty_string(self):
        """Should return empty list for empty string."""
        result = parse_response("")
        self.assertEqual(result, [])

    def test_parse_whitespace_only(self):
        """Should return empty list for whitespace-only string."""
        result = parse_response("   \n\n   ")
        self.assertEqual(result, [])

    def test_parse_multiple_dependencies(self):
        """Should parse multiple dependencies."""
        text = """title: Deploy
description: Deploy to production
dependencies: [Test, Build, Design]
priority: 4"""
        result = parse_response(text)
        self.assertEqual(result[0].dependencies, ["Test", "Build", "Design"])

    def test_parse_with_extra_whitespace(self):
        """Should handle extra whitespace in fields."""
        text = """  title:   Trimmed  
  description:   Trimmed desc  
  dependencies: []
  priority: 2"""
        result = parse_response(text)
        self.assertEqual(result[0].title, "Trimmed")
        self.assertEqual(result[0].description, "Trimmed desc")

    def test_parse_preserves_order(self):
        """Should preserve the order of subgoals as they appear."""
        text = """title: First
description: One
priority: 1

title: Second
description: Two
priority: 2

title: Third
description: Three
priority: 3"""
        result = parse_response(text)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].title, "First")
        self.assertEqual(result[1].title, "Second")
        self.assertEqual(result[2].title, "Third")


if __name__ == "__main__":
    unittest.main()
