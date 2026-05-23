"""Unit tests for the output module."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

# Ensure workspace is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subgoal_generator.models import Subgoal
from subgoal_generator.output import write_pipeline_entries


class TestWritePipelineEntries(unittest.TestCase):
    """Tests for write_pipeline_entries function."""

    def test_write_creates_file(self):
        """Should create the file if it doesn't exist."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        os.remove(path)
        try:
            write_pipeline_entries(
                [Subgoal(title="A", description="First")],
                master_ideas_path=path,
            )
            self.assertTrue(os.path.exists(path))
        finally:
            os.remove(path)

    def test_write_appends_to_existing_file(self):
        """Should append to an existing file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Master Ideas\n")
            path = f.name
        try:
            write_pipeline_entries(
                [Subgoal(title="A", description="First")],
                master_ideas_path=path,
            )
            with open(path) as f:
                content = f.read()
            self.assertIn("# Master Ideas", content)
            self.assertIn("title: A", content)
        finally:
            os.remove(path)

    def test_write_multiple_subgoals(self):
        """Should write multiple subgoals."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            subgoals = [
                Subgoal(title="A", description="First"),
                Subgoal(title="B", description="Second"),
            ]
            write_pipeline_entries(subgoals, master_ideas_path=path)
            with open(path) as f:
                content = f.read()
            self.assertIn("title: A", content)
            self.assertIn("title: B", content)
        finally:
            os.remove(path)

    def test_write_includes_all_fields(self):
        """Should include all subgoal fields in output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            path = f.name
        try:
            sg = Subgoal(
                title="Test",
                description="Desc",
                dependencies=["Dep1"],
                priority=3,
            )
            write_pipeline_entries([sg], master_ideas_path=path)
            with open(path) as f:
                content = f.read()
            self.assertIn("title: Test", content)
            self.assertIn("description: Desc", content)
            self.assertIn("dependencies: [Dep1]", content)
            self.assertIn("priority: 3", content)
        finally:
            os.remove(path)

    def test_write_empty_list(self):
        """Should handle empty subgoal list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Master Ideas\n")
            path = f.name
        try:
            write_pipeline_entries([], master_ideas_path=path)
            with open(path) as f:
                content = f.read()
            # Should not add anything
            self.assertNotIn("title:", content)
        finally:
            os.remove(path)

    def test_write_default_path(self):
        """Should use default master_ideas.md path."""
        default_path = os.path.join(os.getcwd(), "master_ideas.md")
        try:
            write_pipeline_entries([Subgoal(title="A", description="B")])
            self.assertTrue(os.path.exists(default_path))
            with open(default_path) as f:
                content = f.read()
            self.assertIn("title: A", content)
        finally:
            if os.path.exists(default_path):
                os.remove(default_path)


if __name__ == "__main__":
    unittest.main()
