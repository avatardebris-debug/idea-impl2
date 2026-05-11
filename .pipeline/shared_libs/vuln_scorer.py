"""Vulnerability scorer — maps CVSS scores to severity labels."""


class VulnScorer:
    """Score vulnerabilities by CVSS v3.1 severity."""

    def score(self, findings: list[dict]) -> list[dict]:
        """Score each finding and return enriched list.

        Each finding dict must have a 'cve' key with at least 'cvss'.
        Returns findings with an added 'severity' key.
        """
        scored: list[dict] = []
        for f in findings:
            cvss = f["cve"].get("cvss", 0.0)
            severity = self._cvss_to_severity(cvss)
            scored.append({
                "package": f["package"],
                "version": f["version"],
                "ecosystem": f["ecosystem"],
                "cve_id": f["cve"].get("id", "UNKNOWN"),
                "cvss": cvss,
                "severity": severity,
                "description": f["cve"].get("description", ""),
                "fix": f["cve"].get("fix", ""),
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
