"""
test_harness_capabilities.py — Validate all agent tools work correctly.

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

from tools import (
    TOOLS,
    TOOL_SCHEMAS,
    call_tool,
    read_file,
    write_file,
    append_file,
    list_tree,
    delete_file,
    run_shell,
    search_in_files,
    patch_file,
)


class TestToolsExistence(unittest.TestCase):
    """Test that all required tools exist and are callable."""

    def test_all_tools_present(self):
        required = ["read_file", "write_file", "append_file", "list_tree",
                     "delete_file", "run_shell", "search_in_files", "patch_file"]
        for tool in required:
            self.assertIn(tool, TOOLS, f"Tool '{tool}' missing from TOOLS dict")
            self.assertTrue(callable(TOOLS[tool]), f"Tool '{tool}' is not callable")

    def test_tool_schemas_exist(self):
        schema_names = [s["function"]["name"] for s in TOOL_SCHEMAS]
        required = ["read_file", "write_file", "append_file", "list_tree",
                     "delete_file", "run_shell", "search_in_files", "patch_file"]
        for tool in required:
            self.assertIn(tool, schema_names, f"Schema for '{tool}' missing")

    def test_call_tool_dispatch(self):
        """Test that call_tool dispatches to the right function."""
        import tempfile, os
        fd, tmp = tempfile.mkstemp()
        os.close(fd)
        result = call_tool("read_file", path=tmp)
        os.unlink(tmp)
        self.assertIsInstance(result, str)


class TestReadFile(unittest.TestCase):
    """Test read_file tool."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_read_existing_file(self):
        test_file = pathlib.Path(self.tmpdir) / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")
        result = read_file(str(test_file))
        self.assertEqual(result, "hello world")

    def test_read_missing_file(self):
        result = read_file("/nonexistent/path/file.txt")
        self.assertTrue(result.startswith("ERROR"))

    def test_read_utf8_file(self):
        test_file = pathlib.Path(self.tmpdir) / "utf8.txt"
        test_file.write_text("こんにちは 🌍", encoding="utf-8")
        result = read_file(str(test_file))
        self.assertEqual(result, "こんにちは 🌍")


class TestWriteFile(unittest.TestCase):
    """Test write_file tool."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_write_new_file(self):
        test_file = pathlib.Path(self.tmpdir) / "subdir" / "file.txt"
        result = write_file(str(test_file), "content")
        self.assertTrue(result.startswith("OK"))
        self.assertTrue(test_file.exists())
        self.assertEqual(test_file.read_text(encoding="utf-8"), "content")

    def test_write_overwrite(self):
        test_file = pathlib.Path(self.tmpdir) / "file.txt"
        test_file.write_text("old", encoding="utf-8")
        result = write_file(str(test_file), "new")
        self.assertEqual(test_file.read_text(encoding="utf-8"), "new")

    def test_write_creates_parents(self):
        test_file = pathlib.Path(self.tmpdir) / "a" / "b" / "c" / "file.txt"
        result = write_file(str(test_file), "deep")
        self.assertTrue(test_file.exists())


class TestAppendFile(unittest.TestCase):
    """Test append_file tool."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_append_creates_file(self):
        test_file = pathlib.Path(self.tmpdir) / "new.txt"
        result = append_file(str(test_file), "first\n")
        self.assertTrue(result.startswith("OK"))
        self.assertTrue(test_file.exists())

    def test_append_to_existing(self):
        test_file = pathlib.Path(self.tmpdir) / "file.txt"
        test_file.write_text("line1\n", encoding="utf-8")
        append_file(str(test_file), "line2\n")
        self.assertEqual(test_file.read_text(encoding="utf-8"), "line1\nline2\n")


class TestListTree(unittest.TestCase):
    """Test list_tree tool."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        # Create a small tree
        (self.tmpdir / "file1.txt").write_text("a", encoding="utf-8")
        (self.tmpdir / "subdir").mkdir()
        (self.tmpdir / "subdir" / "file2.txt").write_text("b", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_list_tree_returns_string(self):
        result = list_tree(str(self.tmpdir))
        self.assertIsInstance(result, str)
        self.assertIn("file1.txt", result)
        self.assertIn("subdir", result)

    def test_list_tree_nonexistent(self):
        result = list_tree("/nonexistent/path")
        self.assertTrue(result.startswith("ERROR"))


class TestDeleteFile(unittest.TestCase):
    """Test delete_file tool."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_delete_existing(self):
        test_file = pathlib.Path(self.tmpdir) / "file.txt"
        test_file.write_text("delete me", encoding="utf-8")
        result = delete_file(str(test_file))
        self.assertTrue(result.startswith("OK"))
        self.assertFalse(test_file.exists())

    def test_delete_missing(self):
        result = delete_file("/nonexistent/file.txt")
        self.assertTrue(result.startswith("ERROR"))


class TestRunShell(unittest.TestCase):
    """Test run_shell tool."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_run_echo(self):
        result = run_shell("echo hello", cwd=self.tmpdir)
        self.assertIn("hello", result)

    def test_run_ls(self):
        test_file = pathlib.Path(self.tmpdir) / "test.txt"
        test_file.write_text("x", encoding="utf-8")
        # Use 'dir' on Windows, 'ls' on Unix
        import platform
        cmd = "dir" if platform.system() == "Windows" else "ls"
        result = run_shell(cmd, cwd=self.tmpdir)
        self.assertIn("test.txt", result)

    def test_run_nonexistent_cmd(self):
        result = run_shell("nonexistent_command_xyz")
        self.assertTrue(result.startswith("ERROR"))

    def test_run_with_timeout(self):
        # Use cross-platform python sleep instead of Unix sleep
        import sys as _sys
        cmd = f'"{_sys.executable}" -c "import time; time.sleep(0.05); print(\'done\')"'
        result = run_shell(cmd, timeout=5)
        self.assertIn("done", result)


class TestSearchInFiles(unittest.TestCase):
    """Test search_in_files tool."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        (self.tmpdir / "a.txt").write_text("hello world\nfoo bar\n", encoding="utf-8")
        (self.tmpdir / "b.py").write_text("print('hello')\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_search_finds_matches(self):
        result = search_in_files("hello", str(self.tmpdir))
        self.assertIn("a.txt", result)
        self.assertIn("b.py", result)

    def test_search_no_matches(self):
        result = search_in_files("zzzzz", str(self.tmpdir))
        self.assertIn("No matches", result)

    def test_search_with_glob(self):
        result = search_in_files("hello", str(self.tmpdir), "*.txt")
        self.assertIn("a.txt", result)
        self.assertNotIn("b.py", result)


class TestPatchFile(unittest.TestCase):
    """Test patch_file tool."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_patch_replaces(self):
        test_file = pathlib.Path(self.tmpdir) / "file.txt"
        test_file.write_text("hello world", encoding="utf-8")
        result = patch_file(str(test_file), "world", "universe")
        self.assertTrue(result.startswith("OK"))
        self.assertEqual(test_file.read_text(encoding="utf-8"), "hello universe")

    def test_patch_not_found(self):
        test_file = pathlib.Path(self.tmpdir) / "file.txt"
        test_file.write_text("hello", encoding="utf-8")
        result = patch_file(str(test_file), "xyz", "abc")
        self.assertTrue(result.startswith("ERROR"))

    def test_patch_only_first(self):
        test_file = pathlib.Path(self.tmpdir) / "file.txt"
        test_file.write_text("aaa aaa", encoding="utf-8")
        patch_file(str(test_file), "aaa", "bbb")
        self.assertEqual(test_file.read_text(encoding="utf-8"), "bbb aaa")


class TestCallTool(unittest.TestCase):
    """Test the call_tool dispatcher."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_call_tool_unknown(self):
        result = call_tool("nonexistent_tool")
        self.assertTrue(result.startswith("ERROR"))

    def test_call_tool_write_and_read(self):
        test_file = pathlib.Path(self.tmpdir) / "test.txt"
        call_tool("write_file", path=str(test_file), content="test content")
        result = call_tool("read_file", path=str(test_file))
        self.assertEqual(result, "test content")


if __name__ == "__main__":
    unittest.main()
