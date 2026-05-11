"""Tests for remediation advisor."""
import pytest
from depvuln.remediation import RemediationAdvisor


class TestRemediationAdvisor:
    """Test suite for RemediationAdvisor."""

    def setup_method(self):
        """Create a RemediationAdvisor instance for each test."""
        self.advisor = RemediationAdvisor()

    def test_advise_single_finding(self):
        """Test advising on a single finding."""
        findings = [{
            "package": "requests",
            "version": "2.25.1",
            "cve_id": "CVE-2023-1234",
            "severity": "HIGH",
            "fix": "upgrade to requests>=2.31.0",
        }]
        advice = self.advisor.advise(findings)
        assert len(advice) == 1
        assert advice[0]["package"] == "requests"
        assert advice[0]["cve_id"] == "CVE-2023-1234"
        assert advice[0]["severity"] == "HIGH"
        assert "2.31.0" in advice[0]["recommended_action"]

    def test_advise_multiple_findings(self):
        """Test advising on multiple findings."""
        findings = [
            {"package": "requests", "version": "2.25.1", "cve_id": "CVE-2023-1234", "severity": "HIGH", "fix": "upgrade to requests>=2.31.0"},
            {"package": "flask", "version": "2.0.0", "cve_id": "CVE-2023-5678", "severity": "CRITICAL", "fix": "upgrade to flask>=2.3.0"},
        ]
        advice = self.advisor.advise(findings)
        assert len(advice) == 2
        # CRITICAL should come first
        assert advice[0]["severity"] == "CRITICAL"
        assert advice[1]["severity"] == "HIGH"

    def test_advise_empty_findings(self):
        """Test advising on empty findings."""
        advice = self.advisor.advise([])
        assert advice == []

    def test_advise_no_fix_available(self):
        """Test advising when no fix is available."""
        findings = [{
            "package": "old-lib",
            "version": "1.0.0",
            "cve_id": "CVE-2023-9999",
            "severity": "MEDIUM",
            "fix": "",
        }]
        advice = self.advisor.advise(findings)
        assert len(advice) == 1
        assert "no fix available" in advice[0]["recommended_action"].lower() or "upgrade" in advice[0]["recommended_action"].lower()

    def test_advise_sorting_by_severity(self):
        """Test that advice is sorted by severity (CRITICAL > HIGH > MEDIUM > LOW)."""
        findings = [
            {"package": "a", "version": "1.0", "cve_id": "CVE-1", "severity": "LOW", "fix": "upgrade to a>=2.0"},
            {"package": "b", "version": "1.0", "cve_id": "CVE-2", "severity": "CRITICAL", "fix": "upgrade to b>=2.0"},
            {"package": "c", "version": "1.0", "cve_id": "CVE-3", "severity": "HIGH", "fix": "upgrade to c>=2.0"},
            {"package": "d", "version": "1.0", "cve_id": "CVE-4", "severity": "MEDIUM", "fix": "upgrade to d>=2.0"},
        ]
        advice = self.advisor.advise(findings)
        severities = [a["severity"] for a in advice]
        assert severities == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    def test_advise_format(self):
        """Test that advice has the correct format."""
        findings = [{
            "package": "test-pkg",
            "version": "1.0.0",
            "cve_id": "CVE-2023-0001",
            "severity": "HIGH",
            "fix": "upgrade to test-pkg>=2.0.0",
        }]
        advice = self.advisor.advise(findings)
        assert "package" in advice[0]
        assert "cve_id" in advice[0]
        assert "severity" in advice[0]
        assert "recommended_action" in advice[0]
        assert "priority" in advice[0]
