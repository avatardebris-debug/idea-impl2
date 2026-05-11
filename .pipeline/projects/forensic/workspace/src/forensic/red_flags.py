"""Red-flag detection rules for forensic analysis."""

from typing import List
from forensic.models import RedFlag, RedFlagSeverity


def check_revenue_receivables_mismatch(items: list) -> List[RedFlag]:
    """Check for revenue vs. receivables growth mismatch.

    Only flags when both revenue and receivables growth rates are present
    and receivables growth exceeds revenue growth.
    """
    flags = []
    revenue_growth = None
    receivables_growth = None

    for item in items:
        content = getattr(item, "item_content", "") or ""
        lower = content.lower()

        # Look for revenue growth rate
        if "revenue growth" in lower or "revenue growth rate" in lower:
            import re
            match = re.search(r'revenue\s+growth\s+(?:rate\s+)?(?:of\s+)?([\d.]+)\s*%', lower)
            if match:
                revenue_growth = float(match.group(1))

        # Look for receivables growth rate
        if "receivables growth" in lower or "receivable growth" in lower:
            import re
            match = re.search(r'receivables?\s+growth\s+(?:rate\s+)?(?:of\s+)?([\d.]+)\s*%', lower)
            if match:
                receivables_growth = float(match.group(1))

    if revenue_growth is not None and receivables_growth is not None:
        if receivables_growth > revenue_growth * 1.5:
            flags.append(RedFlag(
                category="financial_ratio",
                description="Receivables growth exceeds revenue growth by >50%",
                severity=RedFlagSeverity.WARNING,
                evidence=f"Revenue growth: {revenue_growth}%, Receivables growth: {receivables_growth}%",
            ))
    return flags


def check_related_party_transactions(items: list) -> List[RedFlag]:
    """Check for related-party transaction flags."""
    flags = []
    for item in items:
        content = getattr(item, "item_content", "") or ""
        if "related party" in content.lower() or "related-party" in content.lower():
            flags.append(RedFlag(
                category="related_party",
                description="Related-party transaction detected",
                severity=RedFlagSeverity.WARNING,
                evidence="Related-party language found in filing",
            ))
    return flags


def check_auditor_change(items: list) -> List[RedFlag]:
    """Check for auditor change / going-concern warnings."""
    flags = []
    for item in items:
        content = getattr(item, "item_content", "") or ""
        lower = content.lower()
        if "going concern" in lower:
            flags.append(RedFlag(
                category="auditor",
                description="Going-concern warning detected",
                severity=RedFlagSeverity.CRITICAL,
                evidence="Going-concern language found in filing",
            ))
        if "auditor" in lower and ("resign" in lower or "dismiss" in lower or "change" in lower):
            flags.append(RedFlag(
                category="auditor",
                description="Auditor change or resignation detected",
                severity=RedFlagSeverity.WARNING,
                evidence="Auditor change language found in filing",
            ))
    return flags


def check_text_patterns(items: list) -> List[RedFlag]:
    """Check for suspicious text patterns."""
    flags = []
    suspicious_patterns = [
        ("fraud", "Fraud mention detected", RedFlagSeverity.CRITICAL),
        ("misstatement", "Misstatement language detected", RedFlagSeverity.WARNING),
        ("restatement", "Financial restatement detected", RedFlagSeverity.WARNING),
        ("manipulat", "Manipulation language detected", RedFlagSeverity.CRITICAL),
        ("cook the books", "Cook the books phrase detected", RedFlagSeverity.CRITICAL),
        ("off-balance sheet", "Off-balance sheet arrangement detected", RedFlagSeverity.WARNING),
        ("channel stuffing", "Channel stuffing detected", RedFlagSeverity.CRITICAL),
        ("cookie jar", "Cookie jar reserve detected", RedFlagSeverity.WARNING),
        ("big bath", "Big bath restructuring detected", RedFlagSeverity.WARNING),
        ("earnings management", "Earnings management detected", RedFlagSeverity.WARNING),
    ]
    for item in items:
        content = getattr(item, "item_content", "") or ""
        lower = content.lower()
        for pattern, description, severity in suspicious_patterns:
            if pattern in lower:
                flags.append(RedFlag(
                    category="text_pattern",
                    description=description,
                    severity=severity,
                    evidence=f"Pattern '{pattern}' found in filing text",
                ))
    return flags


def run_all_checks(items: list) -> List[RedFlag]:
    """Run all red-flag checks and return combined results."""
    all_flags: List[RedFlag] = []
    all_flags.extend(check_revenue_receivables_mismatch(items))
    all_flags.extend(check_related_party_transactions(items))
    all_flags.extend(check_auditor_change(items))
    all_flags.extend(check_text_patterns(items))
    return all_flags
