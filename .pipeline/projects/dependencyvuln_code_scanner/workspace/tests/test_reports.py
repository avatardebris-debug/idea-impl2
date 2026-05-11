"""Unit tests for report generators."""
import json
import unittest

from depvuln.reports.json_report import JsonReportGenerator
from depvuln.reports.text_report import TextReportGenerator


class TestJsonReportGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = JsonReportGenerator()

    def test_generate(self):
        findings = [
            {
                "severity": "HIGH",
                "package": "lodash",
                "version": "4.17.20",
                "cve_id": "CVE-2021-23337",
                "cvss": 7.2,
                "description": "Prototype pollution in lodash",
                "fix": "upgrade to lodash>4.17.21",
            }
        ]
        result = self.generator.generate(findings)
        data = json.loads(result)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["severity"], "HIGH")
        self.assertEqual(data[0]["package"], "lodash")

    def test_empty_findings(self):
        result = self.generator.generate([])
        self.assertEqual(result, "[]")


class TestTextReportGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = TextReportGenerator()

    def test_generate(self):
        findings = [
            {
                "severity": "HIGH",
                "package": "lodash",
                "version": "4.17.20",
                "cve_id": "CVE-2021-23337",
                "cvss": 7.2,
                "description": "Prototype pollution in lodash",
                "fix": "upgrade to lodash>4.17.21",
            }
        ]
        result = self.generator.generate(findings)
        self.assertIn("[HIGH]", result)
        self.assertIn("lodash==4.17.20", result)
        self.assertIn("CVE-2021-23337", result)
        self.assertIn("Prototype pollution", result)

    def test_empty_findings(self):
        result = self.generator.generate([])
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
