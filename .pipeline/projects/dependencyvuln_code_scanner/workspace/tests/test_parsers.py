"""Unit tests for dependency parsers."""
import json
import os
import tempfile
import unittest

from depvuln.parsers.npm_parser import NpmParser
from depvuln.parsers.pip_parser import PipParser


class TestNpmParser(unittest.TestCase):
    def setUp(self):
        self.parser = NpmParser()
        self.tmpdir = tempfile.mkdtemp()

    def _write_file(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_parse_package_lock_v3(self):
        data = {
            "name": "test",
            "lockfileVersion": 3,
            "packages": {
                "": {"name": "test", "version": "1.0.0"},
                "node_modules/express": {"name": "express", "version": "4.17.1"},
                "node_modules/lodash": {"name": "lodash", "version": "4.17.20"},
                "node_modules/axios": {"name": "axios", "version": "0.21.1"},
                "node_modules/minimist": {"name": "minimist", "version": "1.2.5"},
            }
        }
        path = self._write_file("package-lock.json", json.dumps(data))
        deps = self.parser.parse(path)
        names = [d["name"] for d in deps]
        self.assertIn("express", names)
        self.assertIn("lodash", names)
        self.assertIn("axios", names)
        self.assertIn("minimist", names)
        self.assertEqual(len(deps), 4)
        for d in deps:
            self.assertEqual(d["ecosystem"], "npm")

    def test_parse_package_lock_v1(self):
        data = {
            "name": "test",
            "lockfileVersion": 1,
            "dependencies": {
                "express": {"version": "4.17.1"},
                "lodash": {"version": "4.17.20"},
                "axios": "0.21.1",
            }
        }
        path = self._write_file("package-lock.json", json.dumps(data))
        deps = self.parser.parse(path)
        self.assertEqual(len(deps), 3)
        names = [d["name"] for d in deps]
        self.assertIn("express", names)
        self.assertIn("lodash", names)
        self.assertIn("axios", names)

    def test_missing_file(self):
        deps = self.parser.parse("/nonexistent/package-lock.json")
        self.assertEqual(deps, [])

    def test_empty_file(self):
        path = self._write_file("package-lock.json", "")
        deps = self.parser.parse(path)
        self.assertEqual(deps, [])

    def test_malformed_json(self):
        path = self._write_file("package-lock.json", "{bad json")
        deps = self.parser.parse(path)
        self.assertEqual(deps, [])


class TestPipParser(unittest.TestCase):
    def setUp(self):
        self.parser = PipParser()
        self.tmpdir = tempfile.mkdtemp()

    def _write_file(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_parse_requirements_txt(self):
        content = "requests==2.28.0\nflask==2.2.0\npyyaml==5.4\njinja2>=3.0.0\n"
        path = self._write_file("requirements.txt", content)
        deps = self.parser.parse(path)
        self.assertEqual(len(deps), 4)
        names = [d["name"] for d in deps]
        self.assertIn("requests", names)
        self.assertIn("flask", names)
        self.assertIn("pyyaml", names)
        self.assertIn("jinja2", names)
        for d in deps:
            self.assertEqual(d["ecosystem"], "pip")

    def test_parse_requirements_txt_with_comments(self):
        content = "# This is a comment\nrequests==2.28.0\n\n# Another comment\nflask==2.2.0\n"
        path = self._write_file("requirements.txt", content)
        deps = self.parser.parse(path)
        self.assertEqual(len(deps), 2)

    def test_parse_pipfile_lock(self):
        data = {
            "default": {
                "requests": {"version": "==2.28.0"},
                "flask": {"version": "==2.2.0"},
            },
            "develop": {
                "pytest": {"version": "==7.0.0"},
            }
        }
        path = self._write_file("Pipfile.lock", json.dumps(data))
        deps = self.parser.parse(path)
        self.assertEqual(len(deps), 3)
        names = [d["name"] for d in deps]
        self.assertIn("requests", names)
        self.assertIn("flask", names)
        self.assertIn("pytest", names)

    def test_missing_file(self):
        deps = self.parser.parse("/nonexistent/requirements.txt")
        self.assertEqual(deps, [])

    def test_empty_file(self):
        path = self._write_file("requirements.txt", "")
        deps = self.parser.parse(path)
        self.assertEqual(deps, [])


if __name__ == "__main__":
    unittest.main()
