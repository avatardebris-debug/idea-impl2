"""Tests for report generation."""

import unittest
import json

from forensic_accounting_suite.engine.report_generation import ReportGenerator
from forensic_accounting_suite.engine.correlation import CorrelationLink
from forensic_accounting_suite.engine.anomaly_detection import Anomaly


class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        """Create test data."""
        self.links = [
            CorrelationLink(
                link_type="shared_director",
                source_entity="REG-001:Acme Corp",
                target_entity="REG-002:Beta LLC",
                confidence=0.85,
                description="Shared director: John Doe",
                details={"shared_director": "John Doe"},
            ),
            CorrelationLink(
                link_type="shared_address",
                source_entity="REG-001:Acme Corp",
                target_entity="REG-002:Beta LLC",
                confidence=0.75,
                description="Shared address: 123 Main St",
                details={"address": "123 Main St"},
            ),
        ]
        self.anomalies = [
            Anomaly(
                entity_type="company",
                entity_id="SHELL-001",
                anomaly_type="shell_company_indicator",
                severity="high",
                description="Potential shell company",
                details={"indicators": 3},
            ),
            Anomaly(
                entity_type="procurement",
                entity_id="PROC-001",
                anomaly_type="value_outlier",
                severity="medium",
                description="Unusually high procurement value",
                details={"value": 500000.0},
            ),
        ]

    def test_generate_text_report(self):
        generator = ReportGenerator(links=self.links, anomalies=self.anomalies)
        report = generator.generate_text_report()
        self.assertIsInstance(report, str)
        self.assertIn("FORENSIC ACCOUNTING ANALYSIS REPORT", report)
        self.assertIn("SUMMARY", report)
        self.assertIn("ANOMALIES", report)
        self.assertIn("CORRELATION LINKS", report)
        self.assertIn("KEY FINDINGS", report)
        self.assertIn("SHELL-001", report)
        self.assertIn("Acme Corp", report)

    def test_text_report_contains_summary(self):
        generator = ReportGenerator(links=self.links, anomalies=self.anomalies)
        report = generator.generate_text_report()
        self.assertIn("Total correlation links found: 2", report)
        self.assertIn("Total anomalies detected: 2", report)

    def test_text_report_contains_anomalies(self):
        generator = ReportGenerator(links=self.links, anomalies=self.anomalies)
        report = generator.generate_text_report()
        self.assertIn("shell_company_indicator", report)
        self.assertIn("value_outlier", report)
        self.assertIn("HIGH", report)
        self.assertIn("MEDIUM", report)

    def test_text_report_contains_links(self):
        generator = ReportGenerator(links=self.links, anomalies=self.anomalies)
        report = generator.generate_text_report()
        self.assertIn("shared_director", report)
        self.assertIn("shared_address", report)
        self.assertIn("Acme Corp", report)
        self.assertIn("Beta LLC", report)

    def test_generate_json_report(self):
        generator = ReportGenerator(links=self.links, anomalies=self.anomalies)
        report = generator.generate_json_report()
        self.assertIsInstance(report, dict)
        self.assertIn("summary", report)
        self.assertIn("anomalies", report)
        self.assertIn("correlation_links", report)
        self.assertIn("key_findings", report)
        self.assertEqual(report["summary"]["total_links"], 2)
        self.assertEqual(report["summary"]["total_anomalies"], 2)

    def test_json_report_serializable(self):
        generator = ReportGenerator(links=self.links, anomalies=self.anomalies)
        report = generator.generate_json_report()
        # Should not raise
        json_str = json.dumps(report)
        self.assertIsInstance(json_str, str)
        self.assertGreater(len(json_str), 0)

    def test_empty_report(self):
        generator = ReportGenerator()
        report = generator.generate_text_report()
        self.assertIn("Total correlation links found: 0", report)
        self.assertIn("Total anomalies detected: 0", report)

    def test_json_report_empty(self):
        generator = ReportGenerator()
        report = generator.generate_json_report()
        self.assertEqual(report["summary"]["total_links"], 0)
        self.assertEqual(report["summary"]["total_anomalies"], 0)

    def test_key_findings_shell_company(self):
        generator = ReportGenerator(links=self.links, anomalies=self.anomalies)
        report = generator.generate_json_report()
        findings = report["key_findings"]
        self.assertGreater(len(findings), 0)
        # Should mention shell companies
        self.assertTrue(
            any("shell" in f.lower() for f in findings),
            f"Expected shell company finding, got: {findings}",
        )

    def test_key_findings_value_outlier(self):
        generator = ReportGenerator(links=self.links, anomalies=self.anomalies)
        report = generator.generate_json_report()
        findings = report["key_findings"]
        # Should mention value outliers
        self.assertTrue(
            any("outlier" in f.lower() for f in findings),
            f"Expected outlier finding, got: {findings}",
        )

    def test_key_findings_no_findings(self):
        generator = ReportGenerator()
        report = generator.generate_json_report()
        findings = report["key_findings"]
        self.assertEqual(len(findings), 1)
        self.assertIn("No significant findings detected", findings[0])


if __name__ == "__main__":
    unittest.main()
