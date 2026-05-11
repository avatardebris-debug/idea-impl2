"""JSON report generator."""
import json
from typing import Any


class JsonReportGenerator:
    """Generate JSON-formatted vulnerability reports."""

    def generate(self, findings: list[dict]) -> str:
        """Return a JSON string of the findings."""
        output = []
        for f in findings:
            output.append({
                "severity": f["severity"],
                "package": f["package"],
                "version": f["version"],
                "cve_id": f["cve_id"],
                "cvss": f["cvss"],
                "description": f["description"],
                "fix": f["fix"],
            })
        return json.dumps(output, indent=2)
