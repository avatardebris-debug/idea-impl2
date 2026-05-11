"""Reporting module for Forensic Suite.

Generates structured fraud risk reports in multiple formats (JSON, Markdown,
and plain-text summaries) from analysis results.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional

from forensic.models import (
    FraudReport,
    RedFlag,
    Recommendation,
    RedFlagSeverity,
)

logger = logging.getLogger("forensic.reporting")


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    ticker: str,
    cik: str,
    filing_date: str,
    risk_score: float,
    overall_risk: str,
    red_flags: List[RedFlag],
    recommendations: List[Recommendation],
) -> FraudReport:
    """Create a FraudReport from raw analysis data.

    This is a convenience wrapper around the FraudReport dataclass.
    """
    return FraudReport(
        ticker=ticker,
        cik=cik,
        filing_date=filing_date,
        risk_score=risk_score,
        overall_risk=overall_risk,
        red_flags=red_flags,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------

def report_to_json(report: FraudReport) -> str:
    """Serialize a FraudReport to a JSON string."""
    return report.to_json()


def report_to_dict(report: FraudReport) -> dict:
    """Serialize a FraudReport to a Python dict."""
    return report.to_dict()


def save_report(report: FraudReport, filepath: str) -> None:
    """Save a FraudReport to a JSON file."""
    report.to_json(filepath)
    logger.info("Report saved to %s", filepath)


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def report_to_markdown(report: FraudReport) -> str:
    """Generate a Markdown-formatted fraud risk report."""
    lines: List[str] = []
    lines.append(f"# Fraud Risk Report: {report.ticker}")
    lines.append("")
    lines.append(f"**CIK:** {report.cik}")
    lines.append(f"**Filing Date:** {report.filing_date}")
    lines.append(f"**Risk Score:** {report.risk_score:.1f}/100")
    lines.append(f"**Overall Risk:** {report.overall_risk.upper()}")
    lines.append("")

    # Red flags
    lines.append("## Red Flags")
    lines.append("")
    if report.red_flags:
        lines.append("| Category | Severity | Description | Evidence |")
        lines.append("|----------|----------|-------------|----------|")
        for flag in report.red_flags:
            lines.append(
                f"| {flag.category} | {flag.severity.value} | "
                f"{flag.description} | {flag.evidence} |"
            )
    else:
        lines.append("No red flags detected.")
    lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    if report.recommendations:
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. **[{rec.category}]** {rec.description} (Priority: {rec.priority})")
    else:
        lines.append("No specific recommendations at this time.")
    lines.append("")

    # Timestamp
    lines.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Plain-text summary
# ---------------------------------------------------------------------------

def report_to_summary(report: FraudReport) -> str:
    """Generate a plain-text summary of the fraud risk report."""
    lines: List[str] = []
    lines.append(f"Fraud Risk Report: {report.ticker}")
    lines.append(f"CIK: {report.cik}")
    lines.append(f"Filing Date: {report.filing_date}")
    lines.append(f"Risk Score: {report.risk_score:.1f}/100")
    lines.append(f"Overall Risk: {report.overall_risk.upper()}")
    lines.append("")
    lines.append("Red Flags:")
    for flag in report.red_flags:
        lines.append(f"  - [{flag.severity.value.upper()}] {flag.category}: {flag.description}")
    lines.append("")
    lines.append("Recommendations:")
    for rec in report.recommendations:
        lines.append(f"  - [{rec.category}] {rec.description}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Multi-format report generation
# ---------------------------------------------------------------------------

def generate_full_report(
    ticker: str,
    cik: str,
    filing_date: str,
    risk_score: float,
    overall_risk: str,
    red_flags: List[RedFlag],
    recommendations: List[Recommendation],
    output_dir: Optional[str] = None,
) -> FraudReport:
    """Generate a full fraud report in all formats.

    Parameters
    ----------
    ticker, cik, filing_date, risk_score, overall_risk, red_flags, recommendations :
        Core report data.
    output_dir : optional directory to save reports to.

    Returns
    -------
    FraudReport
    """
    report = FraudReport(
        ticker=ticker,
        cik=cik,
        filing_date=filing_date,
        risk_score=risk_score,
        overall_risk=overall_risk,
        red_flags=red_flags,
        recommendations=recommendations,
    )

    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)
        base = f"{ticker}_{filing_date.replace('-', '_')}"
        save_report(report, os.path.join(output_dir, f"{base}.json"))
        with open(os.path.join(output_dir, f"{base}.md"), "w") as f:
            f.write(report_to_markdown(report))
        with open(os.path.join(output_dir, f"{base}.txt"), "w") as f:
            f.write(report_to_summary(report))
        logger.info("Full report saved to %s", output_dir)

    return report
