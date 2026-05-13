"""
test_dependency_system.py — Validate dependency ordering logic.

Tests run without Ollama or network access. Uses temp directories.
"""
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

# Add workspace to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from runner import (
    parse_master_ideas,
    save_master_ideas,
    check_deps_complete,
    build_dep_workspace_map,
    is_idea_blocked,
    slugify,
)


class TestSlugify(unittest.TestCase):
    """Test slugify utility."""

    def test_simple_title(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_with_special_chars(self):
        self.assertEqual(slugify("Test: It's a [demo]!"), "test-its-a-demo")

    def test_with_spaces(self):
        self.assertEqual(slugify("  Multiple   Spaces  "), "multiple-spaces")

    def test_empty(self):
        self.assertEqual(slugify(""), "untitled")

    def test_already_kebab(self):
        self.assertEqual(slugify("already-kebab"), "already-kebab")

    def test_with_underscores(self):
        self.assertEqual(slugify("hello_world_test"), "hello-world-test")


class TestMasterIdeasParsing(unittest.TestCase):
    """Test parsing master_ideas.md."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ideas_file = pathlib.Path(self.tmpdir) / "master_ideas.md"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_parse_empty_file(self):
        self.ideas_file.write_text("# Master Ideas List\n\n", encoding="utf-8")
        ideas = parse_master_ideas(str(self.ideas_file))
        self.assertEqual(len(ideas), 0)

    def test_parse_single_idea(self):
        content = """# Master Ideas List

## Build a Web Scraper
Slug: build-a-web-scraper
Status: pending
Phase: 2
Description: Create a web scraper tool
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        ideas = parse_master_ideas(str(self.ideas_file))
        self.assertEqual(len(ideas), 1)
        self.assertEqual(ideas[0]['title'], "Build a Web Scraper")
        self.assertEqual(ideas[0]['slug'], "build-a-web-scraper")
        self.assertEqual(ideas[0]['status'], "pending")
        self.assertEqual(ideas[0]['phase'], 2)

    def test_parse_multiple_ideas(self):
        content = """# Master Ideas List

## Idea One
Slug: idea-one
Status: pending

## Idea Two
Slug: idea-two
Status: complete
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        ideas = parse_master_ideas(str(self.ideas_file))
        self.assertEqual(len(ideas), 2)
        self.assertEqual(ideas[0]['status'], "pending")
        self.assertEqual(ideas[1]['status'], "complete")

    def test_parse_with_requires(self):
        content = """# Master Ideas List

## Dependent Idea
Slug: dependent
Status: pending
Requires: idea-one, idea-two
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        ideas = parse_master_ideas(str(self.ideas_file))
        self.assertEqual(ideas[0]['requires'], ["idea-one", "idea-two"])

    def test_roundtrip(self):
        ideas = [
            {"title": "Test Idea", "slug": "test-idea", "status": "pending",
             "phase": 1, "requires": [], "description": "A test"},
        ]
        save_master_ideas(ideas, str(self.ideas_file))
        parsed = parse_master_ideas(str(self.ideas_file))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['title'], "Test Idea")


class TestDependencyChecking(unittest.TestCase):
    """Test dependency checking logic."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ideas_file = pathlib.Path(self.tmpdir) / "master_ideas.md"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_deps_always_complete(self):
        self.assertTrue(check_deps_complete("test", [], self.tmpdir))

    def test_all_deps_complete(self):
        content = """# Master Ideas List

## Dep One
Slug: dep-one
Status: complete

## Dep Two
Slug: dep-two
Status: complete

## Main Idea
Slug: main
Status: pending
Requires: dep-one, dep-two
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        self.assertTrue(check_deps_complete("main", ["dep-one", "dep-two"], self.tmpdir))

    def test_incomplete_dep_blocks(self):
        content = """# Master Ideas List

## Dep One
Slug: dep-one
Status: pending

## Main Idea
Slug: main
Status: pending
Requires: dep-one
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        self.assertFalse(check_deps_complete("main", ["dep-one"], self.tmpdir))

    def test_budget_exceeded_treated_as_complete(self):
        content = """# Master Ideas List

## Dep One
Slug: dep-one
Status: budget_exceeded

## Main Idea
Slug: main
Status: pending
Requires: dep-one
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        self.assertTrue(check_deps_complete("main", ["dep-one"], self.tmpdir))

    def test_external_dep_treated_as_complete(self):
        """Dependencies not in master list are treated as complete."""
        self.assertTrue(check_deps_complete("main", ["external-dep"], self.tmpdir))


class TestIsIdeaBlocked(unittest.TestCase):
    """Test is_idea_blocked function."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.ideas_file = pathlib.Path(self.tmpdir) / "master_ideas.md"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_deps_not_blocked(self):
        content = """# Master Ideas List

## Free Idea
Slug: free
Status: pending
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        self.assertFalse(is_idea_blocked("free", self.tmpdir))

    def test_blocked_by_incomplete_dep(self):
        content = """# Master Ideas List

## Dep One
Slug: dep-one
Status: pending

## Main Idea
Slug: main
Status: pending
Requires: dep-one
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        self.assertTrue(is_idea_blocked("main", self.tmpdir))

    def test_not_blocked_when_deps_complete(self):
        content = """# Master Ideas List

## Dep One
Slug: dep-one
Status: complete

## Main Idea
Slug: main
Status: pending
Requires: dep-one
"""
        self.ideas_file.write_text(content, encoding="utf-8")
        self.assertFalse(is_idea_blocked("main", self.tmpdir))

    def test_nonexistent_slug_not_blocked(self):
        self.assertFalse(is_idea_blocked("nonexistent", self.tmpdir))


class TestBuildDepWorkspaceMap(unittest.TestCase):
    """Test build_dep_workspace_map function."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.project_dir = pathlib.Path(self.tmpdir) / "projects" / "osint_corp2"
        self.project_dir.mkdir(parents=True)
        (self.project_dir / "workspace").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_deps_returns_empty(self):
        result = build_dep_workspace_map("test", [], self.tmpdir)
        self.assertEqual(result, {})

    def test_existing_workspace_mapped(self):
        dep_workspace = self.project_dir / "workspace" / "dep-one"
        dep_workspace.mkdir()
        result = build_dep_workspace_map("test", ["dep-one"], self.tmpdir)
        self.assertIn("dep-one", result)
        self.assertEqual(result["dep-one"], str(dep_workspace))

    def test_missing_workspace_not_mapped(self):
        result = build_dep_workspace_map("test", ["dep-one"], self.tmpdir)
        self.assertNotIn("dep-one", result)


if __name__ == "__main__":
    unittest.main()
