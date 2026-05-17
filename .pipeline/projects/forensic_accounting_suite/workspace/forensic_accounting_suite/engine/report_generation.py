"""Report generation for forensic accounting findings."""

from __future__ import annotations

from typing import Any

from forensic_accounting_suite.engine.correlation import CorrelationLink
from forensic_accounting_suite.engine.anomaly_detection import Anomaly


class ReportGenerator:
    """Generate human-readable reports from correlation and anomaly data."""

    def __init__(
        self,
        links: list[CorrelationLink] | None = None,
        anomalies: list[Anomaly] | None = None,
    ):
        self.links = links or []
        self.anomalies = anomalies or []

    def generate_text_report(self) -> str:
        """Generate a plain-text forensic report."""
        lines: list[str] = []
        lines.append("=" * 72)
        lines.append("FORENSIC ACCOUNTING ANALYSIS REPORT")
        lines.append("=" * 72)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total correlation links found: {len(self.links)}")
        lines.append(f"Total anomalies detected: {len(self.anomalies)}")
        lines.append("")

        # Anomalies
        if self.anomalies:
            lines.append("ANOMALIES")
            lines.append("-" * 40)
            severity_counts: dict[str, int] = {}
            for a in self.anomalies:
                severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
            for sev in ["critical", "high", "medium", "low"]:
                if sev in severity_counts:
                    lines.append(f"  {sev.upper()}: {severity_counts[sev]}")
            lines.append("")

            for i, anomaly in enumerate(self.anomalies, 1):
                lines.append(f"  [{i}] {anomaly.anomaly_type}")
                lines.append(f"      Entity: {anomaly.entity_type} ({anomaly.entity_id})")
                lines.append(f"      Severity: {anomaly.severity.upper()}")
                lines.append(f"      Description: {anomaly.description}")
                if anomaly.details:
                    lines.append("      Details:")
                    for k, v in anomaly.details.items():
                        lines.append(f"        {k}: {v}")
                lines.append("")

        # Correlation links
        if self.links:
            lines.append("CORRELATION LINKS")
            lines.append("-" * 40)

            # Group by link type
            by_type: dict[str, list[CorrelationLink]] = {}
            for link in self.links:
                by_type.setdefault(link.link_type, []).append(link)

            for link_type, type_links in sorted(by_type.items()):
                lines.append(f"\n  Type: {link_type} ({len(type_links)} links)")
                for link in type_links:
                    lines.append(f"    {link.source_entity} <-> {link.target_entity}")
                    lines.append(f"      Confidence: {link.confidence:.2f}")
                    if link.details:
                        for k, v in link.details.items():
                            lines.append(f"      {k}: {v}")
                lines.append("")

        # Key findings
        lines.append("KEY FINDINGS")
        lines.append("-" * 40)
        findings = self._extract_key_findings()
        for i, finding in enumerate(findings, 1):
            lines.append(f"  {i}. {finding}")
        lines.append("")
        lines.append("=" * 72)
        lines.append("END OF REPORT")
        lines.append("=" * 72)

        return "\n".join(lines)

    def generate_json_report(self) -> dict:
        """Generate a JSON-serializable report."""
        return {
            "summary": {
                "total_links": len(self.links),
                "total_anomalies": len(self.anomalies),
            },
            "anomalies": [a.to_dict() for a in self.anomalies],
            "correlation_links": [l.to_dict() for l in self.links],
            "key_findings": self._extract_key_findings(),
        }

    def _extract_key_findings(self) -> list[str]:
        """Extract key findings from the data."""
        findings: list[str] = []

        # High-severity anomalies
        high_sev = [a for a in self.anomalies if a.severity in ("high", "critical")]
        if high_sev:
            types = set(a.anomaly_type for a in high_sev)
            findings.append(
                f"Detected {len(high_sev)} high/critical anomalies: "
                f"{', '.join(types)}"
            )

        # Companies with multiple links
        company_links: dict[str, int] = {}
        for link in self.links:
            for entity in [link.source_entity, link.target_entity]:
                if ":" in entity:
                    company_name = entity.split(":")[1]
                    company_links[company_name] = company_links.get(company_name, 0) + 1

        for company, count in sorted(company_links.items(), key=lambda x: x[1], reverse=True):
            if count >= 3:
                findings.append(f"Company '{company}' has {count} correlation links")

        # Shell company indicators
        shells = [a for a in self.anomalies if a.anomaly_type == "shell_company_indicator"]
        if shells:
            findings.append(
                f"Identified {len(shells)} potential shell companies"
            )

        # Value outliers
        outliers = [a for a in self.anomalies if a.anomaly_type == "value_outlier"]
        if outliers:
            max_val = max(
                (a.details.get("value", 0) for a in outliers), default=0
            )
            findings.append(
                f"Found {len(outliers)} value outliers, max: ${max_val:,.2f}"
            )

        if not findings:
            findings.append("No significant findings detected")

        return findings
