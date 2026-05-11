"""Unit tests for vulnerability scorer."""
import unittest

from depvuln.scorer import VulnScorer


class TestVulnScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = VulnScorer()

    def test_score_critical(self):
        findings = [{"cve": {"cvss": 9.8}, "package": "test", "version": "1.0", "ecosystem": "pip"}]
        scored = self.scorer.score(findings)
        self.assertEqual(scored[0]["severity"], "CRITICAL")

    def test_score_high(self):
        findings = [{"cve": {"cvss": 7.5}, "package": "test", "version": "1.0", "ecosystem": "pip"}]
        scored = self.scorer.score(findings)
        self.assertEqual(scored[0]["severity"], "HIGH")

    def test_score_medium(self):
        findings = [{"cve": {"cvss": 5.0}, "package": "test", "version": "1.0", "ecosystem": "pip"}]
        scored = self.scorer.score(findings)
        self.assertEqual(scored[0]["severity"], "MEDIUM")

    def test_score_low(self):
        findings = [{"cve": {"cvss": 2.0}, "package": "test", "version": "1.0", "ecosystem": "pip"}]
        scored = self.scorer.score(findings)
        self.assertEqual(scored[0]["severity"], "LOW")

    def test_sorting(self):
        findings = [
            {"cve": {"cvss": 5.0}, "package": "a", "version": "1.0", "ecosystem": "pip"},
            {"cve": {"cvss": 9.5}, "package": "b", "version": "1.0", "ecosystem": "pip"},
            {"cve": {"cvss": 7.0}, "package": "c", "version": "1.0", "ecosystem": "pip"},
            {"cve": {"cvss": 1.0}, "package": "d", "version": "1.0", "ecosystem": "pip"},
        ]
        scored = self.scorer.score(findings)
        severities = [f["severity"] for f in scored]
        self.assertEqual(severities, ["CRITICAL", "HIGH", "MEDIUM", "LOW"])


if __name__ == "__main__":
    unittest.main()
