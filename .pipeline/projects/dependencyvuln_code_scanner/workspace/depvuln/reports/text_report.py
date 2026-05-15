"""Text report generator."""
from typing import Any


class TextReportGenerator:
    """Generate human-readable text vulnerability reports."""

    def generate(self, findings: list[dict]) -> str:
        """Return a formatted text report."""
        lines: list[str] = []
        for f in findings:
            lines.append(
                f"[{f['severity']}] {f['package']}=={f['version']}  ->  {f['cve_id']}  (CVSS {f['cvss']})"
            )
            desc = f["description"] or "No description available."
            # Truncate long descriptions
            if len(desc) > 120:
                desc = desc[:117] + "..."
            lines.append(f"  {desc}")
            fix = f["fix"] or "No fix available."
            lines.append(f"  Fix: {fix}")
            lines.append("")
        return "\n".join(lines)
