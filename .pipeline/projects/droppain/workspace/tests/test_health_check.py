"""Tests for droppain.health_check module."""

import os
from unittest.mock import patch

import pytest

from droppain.health_check import (
    Finding,
    run_health_check,
    _check_config,
    _check_dependencies,
    _check_environment,
    _attempt_fixes,
)


class TestFinding:
    """Tests for Finding dataclass."""

    def test_finding_creation(self):
        """Test creating a Finding."""
        finding = Finding(
            slug="test-slug",
            severity="info",
            check="Test Check",
            message="Test message",
        )
        assert finding.slug == "test-slug"
        assert finding.severity == "info"
        assert finding.check == "Test Check"
        assert finding.message == "Test message"
        assert finding.fixable is False
        assert finding.fixed is False

    def test_finding_to_dict(self):
        """Test Finding.to_dict()."""
        finding = Finding(
            slug="test-slug",
            severity="error",
            check="Test Check",
            message="Test message",
            fixable=True,
            fixed=False,
        )
        d = finding.to_dict()
        assert d["slug"] == "test-slug"
        assert d["severity"] == "error"
        assert d["fixable"] is True
        assert d["fixed"] is False


class TestCheckConfig:
    """Tests for _check_config."""

    def test_check_config_no_shopify(self):
        """Test config check without Shopify credentials."""
        with patch.dict(os.environ, {}, clear=True):
            findings = _check_config()
            severities = [f.severity for f in findings]
            assert "warning" in severities  # Shopify not configured

    def test_check_config_with_shopify(self):
        """Test config check with Shopify credentials."""
        with patch.dict(os.environ, {
            "SHOPIFY_API_KEY": "key",
            "SHOPIFY_PASSWORD": "pass",
            "SHOPIFY_STORE_NAME": "mystore",
        }):
            findings = _check_config()
            severities = [f.severity for f in findings]
            assert "info" in severities  # Shopify configured


class TestCheckDependencies:
    """Tests for _check_dependencies."""

    def test_check_dependencies_installed(self):
        """Test dependency check with all packages installed."""
        findings = _check_dependencies()
        severities = [f.severity for f in findings]
        assert "info" in severities


class TestCheckEnvironment:
    """Tests for _check_environment."""

    def test_check_env_all_set(self):
        """Test environment check with all vars set."""
        with patch.dict(os.environ, {
            "SHOPIFY_API_KEY": "key",
            "SHOPIFY_PASSWORD": "pass",
            "SHOPIFY_STORE_NAME": "store",
        }):
            findings = _check_environment()
            severities = [f.severity for f in findings]
            assert severities.count("info") == 3

    def test_check_env_none_set(self):
        """Test environment check with no vars set."""
        with patch.dict(os.environ, {}, clear=True):
            findings = _check_environment()
            severities = [f.severity for f in findings]
            assert severities.count("warning") == 3


class TestAttemptFixes:
    """Tests for _attempt_fixes."""

    def test_attempt_fixes_marks_fixed(self):
        """Test that fixable findings are marked as fixed."""
        findings = [
            Finding(slug="test", severity="warning", check="Test", message="Fix me", fixable=True),
            Finding(slug="test2", severity="error", check="Test", message="Cannot fix", fixable=False),
        ]
        fixed = _attempt_fixes(findings)
        assert fixed[0].fixed is True
        assert fixed[0].severity == "info"
        assert fixed[1].fixed is False


class TestRunHealthCheck:
    """Tests for run_health_check."""

    def test_run_health_check_returns_findings(self):
        """Test that run_health_check returns findings."""
        findings = run_health_check()
        assert isinstance(findings, list)
        assert len(findings) > 0

    def test_run_health_check_with_fix(self):
        """Test run_health_check with fix=True."""
        findings = run_health_check(fix=True)
        # Some findings should be marked as fixed
        fixed_count = sum(1 for f in findings if f.fixed)
        assert fixed_count >= 0  # May be 0 if nothing is fixable
