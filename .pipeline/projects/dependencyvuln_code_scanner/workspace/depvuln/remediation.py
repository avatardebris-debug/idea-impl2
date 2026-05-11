"""Remediation advisor — generates actionable fix recommendations."""


class RemediationAdvisor:
    """Generate remediation advice for vulnerabilities."""

    def advise(self, findings: list[dict]) -> list[dict]:
        """Generate remediation advice for each finding.

        Args:
            findings: List of finding dicts with keys: package, version, cve_id, severity, fix

        Returns:
            List of advice dicts with keys: package, cve_id, severity, recommended_action, priority
        """
        advice: list[dict] = []
        for f in findings:
            package = f.get("package", "UNKNOWN")
            cve_id = f.get("cve_id", "UNKNOWN")
            severity = f.get("severity", "UNKNOWN")
            fix = f.get("fix", "")

            # Generate recommended action
            if fix:
                recommended_action = fix
            else:
                recommended_action = f"Upgrade {package} to the latest version or apply manual patch"

            # Determine priority
            priority = self._severity_to_priority(severity)

            advice.append({
                "package": package,
                "cve_id": cve_id,
                "severity": severity,
                "recommended_action": recommended_action,
                "priority": priority,
            })

        # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        advice.sort(key=lambda x: order.get(x["priority"], 4))
        return advice

    @staticmethod
    def _severity_to_priority(severity: str) -> str:
        """Map severity to priority label."""
        return severity
