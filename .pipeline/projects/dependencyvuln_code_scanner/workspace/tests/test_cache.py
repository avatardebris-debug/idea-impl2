"""Unit tests for CVE cache."""
import os
import tempfile
import unittest

from depvuln.cve.cache import CveCache


class TestCveCache(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.db")
        self.cache = CveCache(self.db_path, ttl=3600)

    def test_set_and_get(self):
        self.cache.set("key1", {"data": "value1"})
        result = self.cache.get("key1")
        self.assertEqual(result, {"data": "value1"})

    def test_get_missing_key(self):
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)

    def test_invalidate(self):
        self.cache.set("key1", {"data": "value1"})
        self.cache.invalidate("key1")
        result = self.cache.get("key1")
        self.assertIsNone(result)

    def test_ttl_expiration(self):
        cache = CveCache(os.path.join(self.tmpdir, "ttl.db"), ttl=0)
        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
