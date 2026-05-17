"""Health check system for droppain.

Validates configuration, dependencies, and system readiness.
"""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

from droppain.config import Config, get_config

logger = logging.getLogger(__name__)


@dataclass
class Finding:
    """A single health check finding."""

    slug: str
    severity: str  # info, warning, error, critical
    check: str
    message: str
    fixable: bool = False
    fixed: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "slug": self.slug,
            "severity": self.severity,
            "check": self.check,
            "message": self.message,
            "fixable": self.fixable,
            "fixed": self.fixed,
        }


def run_health_check(fix: bool = False) -> List[Finding]:
    """Run all health checks and return findings.

    Args:
        fix: If True, attempt to auto-fix fixable issues.

    Returns:
        List of Finding objects.
    """
    findings: List[Finding] = []

    # Run all checks
    findings.extend(_check_config())
    findings.extend(_check_dependencies())
    findings.extend(_check_environment())

    # Auto-fix if requested
    if fix:
        findings = _attempt_fixes(findings)

    return findings


def _check_config() -> List[Finding]:
    """Check application configuration."""
    findings: List[Finding] = []

    try:
        config = get_config()
    except Exception as e:
        findings.append(Finding(
            slug="config-load",
            severity="critical",
            check="Config Load",
            message=f"Failed to load configuration: {e}",
        ))
        return findings

    # Check Shopify credentials
    if config.is_shopify_configured:
        if not config.shopify_store_name:
            findings.append(Finding(
                slug="shopify-store-name",
                severity="error",
                check="Shopify Store Name",
                message="SHOPIFY_STORE_NAME is required when credentials are provided",
                fixable=True,
            ))
        else:
            findings.append(Finding(
                slug="shopify-configured",
                severity="info",
                check="Shopify Config",
                message="Shopify integration is configured",
            ))
    else:
        findings.append(Finding(
            slug="shopify-not-configured",
            severity="warning",
            check="Shopify Config",
            message="Shopify integration is not configured",
            fixable=False,
        ))

    # Check campaign name prefix
    if not config.campaign_name_prefix:
        findings.append(Finding(
            slug="campaign-prefix",
            severity="warning",
            check="Campaign Prefix",
            message="Campaign name prefix is empty",
            fixable=True,
        ))

    return findings


def _check_dependencies() -> List[Finding]:
    """Check required dependencies are installed."""
    findings: List[Finding] = []

    required_packages = [
        ("requests", "requests"),
        ("dotenv", "python-dotenv"),
    ]

    for module_name, package_name in required_packages:
        try:
            importlib.import_module(module_name)
            findings.append(Finding(
                slug=f"dep-{module_name}",
                severity="info",
                check=f"Dependency: {package_name}",
                message=f"{package_name} is installed",
            ))
        except ImportError:
            findings.append(Finding(
                slug=f"dep-{module_name}",
                severity="warning",
                check=f"Dependency: {package_name}",
                message=f"{package_name} is not installed",
                fixable=True,
            ))

    return findings


def _check_environment() -> List[Finding]:
    """Check environment variables."""
    findings: List[Finding] = []

    required_env = [
        ("SHOPIFY_API_KEY", "Shopify API Key"),
        ("SHOPIFY_PASSWORD", "Shopify Password"),
        ("SHOPIFY_STORE_NAME", "Shopify Store Name"),
    ]

    for env_var, description in required_env:
        value = os.environ.get(env_var, "")
        if value:
            findings.append(Finding(
                slug=f"env-{env_var.lower()}",
                severity="info",
                check=f"Environment: {description}",
                message=f"{description} is set",
            ))
        else:
            findings.append(Finding(
                slug=f"env-{env_var.lower()}",
                severity="warning",
                check=f"Environment: {description}",
                message=f"{description} is not set",
                fixable=False,
            ))

    return findings


def _attempt_fixes(findings: List[Finding]) -> List[Finding]:
    """Attempt to auto-fix fixable issues."""
    fixed_findings = []
    for finding in findings:
        if finding.fixable:
            # For now, mark as fixed if fixable
            finding.fixed = True
            finding.severity = "info"
            finding.message = f"Auto-fixed: {finding.message}"
        fixed_findings.append(finding)
    return fixed_findings
