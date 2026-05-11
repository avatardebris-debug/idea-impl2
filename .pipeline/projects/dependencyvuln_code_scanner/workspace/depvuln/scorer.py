"""Vulnerability scorer — maps CVSS scores to severity labels."""


class VulnScorer:
    """Score vulnerabilities by CVSS v3.1 severity."""

    def __init__(self, threshold: str = "LOW"):
        """Initialize the scorer with an optional severity threshold."""
        self.threshold = threshold.upper()

    def score(self, findings: list[dict]) -> list[dict]:
        """Score each finding and return enriched list.

        Each finding dict must have 'cvss' key (or 'cve' key with 'cvss').
        Returns findings with an added 'severity' key.
        """
        scored: list[dict] = []
        for f in findings:
            # Support both flat format (from CLI) and nested format (from tests)
            if "cve" in f and isinstance(f["cve"], dict):
                cvss = f["cve"].get("cvss", 0.0)
                cve_id = f["cve"].get("id", "UNKNOWN")
                description = f["cve"].get("description", "")
                fix = f["cve"].get("fix", "")
            else:
                cvss = f.get("cvss", 0.0)
                cve_id = f.get("cve_id", "UNKNOWN")
                description = f.get("description", "")
                fix = f.get("fix", "")

            severity = self._cvss_to_severity(cvss)
            scored.append({
                "package": f.get("package", "UNKNOWN"),
                "version": f.get("version", "UNKNOWN"),
                "ecosystem": f.get("ecosystem", "UNKNOWN"),
                "cve_id": cve_id,
                "cvss": cvss,
                "severity": severity,
                "description": description,
                "fix": fix,
            })

        # Sort descending by severity (CRITICAL > HIGH > MEDIUM > LOW)
        order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        scored.sort(key=lambda x: order.get(x["severity"], 4))
        return scored

    @staticmethod
    def _cvss_to_severity(cvss: float) -> str:
        """Map a CVSS score to a severity label."""
        if cvss >= 9.0:
            return "CRITICAL"
        elif cvss >= 7.0:
            return "HIGH"
        elif cvss >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"
