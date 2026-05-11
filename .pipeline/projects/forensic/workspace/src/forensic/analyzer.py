"""Fraud detection analyzers for SEC filings."""

import re
import math
from typing import List, Dict, Optional, Tuple
from forensic.models import RedFlag, RedFlagSeverity


class TextPatternAnalyzer:
    """Analyzes filing text for suspicious patterns."""

    SUSPICIOUS_PATTERNS = [
        (r"\b(?:fraud|fraudulent|fraudulence)\b", "Mention of fraud"),
        (r"\b(?:restatement|restated|restatements)\b", "Financial restatement"),
        (r"\b(?:material\s+weakness)\b", "Material weakness"),
        (r"\b(?:going\s+concern)\b", "Going concern"),
        (r"\b(?:litigation|litigate|litigations)\b", "Litigation"),
        (r"\b(?:investigation|investigate|investigations)\b", "Investigation"),
        (r"\b(?:sanction|sanctions)\b", "Sanctions"),
        (r"\b(?:penalty|penalties)\b", "Penalties"),
        (r"\b(?:violation|violations)\b", "Violations"),
        (r"\b(?:misstatement|misstatements)\b", "Misstatements"),
        (r"\b(?:improper|improperly)\b", "Improper accounting"),
        (r"\b(?:aggressive\s+accounting)\b", "Aggressive accounting"),
        (r"\b(?:cookie\s+jar)\b", "Cookie jar reserves"),
        (r"\b(?:channel\s+stuffing)\b", "Channel stuffing"),
        (r"\b(?:round\s+tripping)\b", "Round-tripping"),
        (r"\b(?:off\s+balance\s+sheet)\b", "Off-balance sheet"),
        (r"\b(?:special\s+purpose\s+entity)\b", "Special purpose entity"),
        (r"\b(?:related\s+party\s+transaction)\b", "Related party transaction"),
        (r"\b(?:conflict\s+of\s+interest)\b", "Conflict of interest"),
        (r"\b(?:self\s+dealing)\b", "Self-dealing"),
    ]

    def analyze(self, text: str) -> List[RedFlag]:
        """Analyze text for suspicious patterns."""
        flags = []
        text_lower = text.lower()

        for pattern, description in self.SUSPICIOUS_PATTERNS:
            matches = re.findall(pattern, text_lower)
            if matches:
                severity = RedFlagSeverity.CRITICAL if any(
                    word in description.lower() for word in ["fraud", "restatement", "misstatement"]
                ) else RedFlagSeverity.WARNING
                flags.append(RedFlag(
                    category="text_pattern",
                    description=f"Found {len(matches)} instance(s) of: {description}",
                    severity=severity,
                    evidence=f"Pattern: {pattern}",
                ))

        return flags


class FinancialRatioAnalyzer:
    """Analyzes financial ratios for anomalies."""

    def analyze(self, financial_data: Dict[str, float]) -> List[RedFlag]:
        """Analyze financial ratios for anomalies."""
        flags = []

        # Check for declining revenue with increasing expenses
        revenue = financial_data.get("revenue", 0)
        expenses = financial_data.get("expenses", 0)
        if revenue > 0 and expenses > 0:
            expense_ratio = expenses / revenue
            if expense_ratio > 0.95:
                flags.append(RedFlag(
                    category="financial_ratio",
                    description="Expense ratio exceeds 95% of revenue",
                    severity=RedFlagSeverity.WARNING,
                    evidence=f"Expense ratio: {expense_ratio:.2%}",
                ))

        # Check for declining revenue trend
        revenues = financial_data.get("revenue_trend", [])
        if len(revenues) >= 3:
            declines = sum(1 for i in range(1, len(revenues)) if revenues[i] < revenues[i-1])
            if declines >= 2:
                flags.append(RedFlag(
                    category="financial_ratio",
                    description="Revenue declining for 2+ consecutive periods",
                    severity=RedFlagSeverity.WARNING,
                    evidence=f"Revenue trend: {revenues}",
                ))

        # Check for increasing receivables vs revenue
        revenue_growth = financial_data.get("revenue_growth", 0)
        receivables_growth = financial_data.get("receivables_growth", 0)
        if revenue_growth < 0.1 and receivables_growth > revenue_growth * 2:
            flags.append(RedFlag(
                category="financial_ratio",
                description="Receivables growing faster than revenue",
                severity=RedFlagSeverity.WARNING,
                evidence=f"Revenue growth: {revenue_growth:.2%}, Receivables growth: {receivables_growth:.2%}",
            ))

        # Check for declining gross margin
        gross_margins = financial_data.get("gross_margin_trend", [])
        if len(gross_margins) >= 3:
            declines = sum(1 for i in range(1, len(gross_margins)) if gross_margins[i] < gross_margins[i-1])
            if declines >= 2:
                flags.append(RedFlag(
                    category="financial_ratio",
                    description="Gross margin declining for 2+ consecutive periods",
                    severity=RedFlagSeverity.WARNING,
                    evidence=f"Gross margin trend: {gross_margins}",
                ))

        return flags


class CashFlowAnalyzer:
    """Analyzes cash flow patterns for anomalies."""

    def analyze(self, cash_flow_data: Dict[str, float]) -> List[RedFlag]:
        """Analyze cash flow data for anomalies."""
        flags = []

        # Check for net income vs operating cash flow divergence
        net_income = cash_flow_data.get("net_income", 0)
        operating_cash_flow = cash_flow_data.get("operating_cash_flow", 0)
        if net_income > 0 and operating_cash_flow < 0:
            flags.append(RedFlag(
                category="cash_flow",
                description="Net income positive but operating cash flow negative",
                severity=RedFlagSeverity.CRITICAL,
                evidence=f"Net income: {net_income}, Operating cash flow: {operating_cash_flow}",
            ))
        elif net_income < 0 and operating_cash_flow > 0:
            flags.append(RedFlag(
                category="cash_flow",
                description="Net income negative but operating cash flow positive",
                severity=RedFlagSeverity.WARNING,
                evidence=f"Net income: {net_income}, Operating cash flow: {operating_cash_flow}",
            ))

        # Check for declining operating cash flow
        ocf_trend = cash_flow_data.get("operating_cash_flow_trend", [])
        if len(ocf_trend) >= 3:
            declines = sum(1 for i in range(1, len(ocf_trend)) if ocf_trend[i] < ocf_trend[i-1])
            if declines >= 2:
                flags.append(RedFlag(
                    category="cash_flow",
                    description="Operating cash flow declining for 2+ consecutive periods",
                    severity=RedFlagSeverity.WARNING,
                    evidence=f"OCF trend: {ocf_trend}",
                ))

        # Check for increasing capital expenditures vs revenue
        capex = cash_flow_data.get("capital_expenditures", 0)
        revenue = cash_flow_data.get("revenue", 0)
        if revenue > 0 and capex > 0:
            capex_ratio = capex / revenue
            if capex_ratio > 0.3:
                flags.append(RedFlag(
                    category="cash_flow",
                    description="Capital expenditures exceed 30% of revenue",
                    severity=RedFlagSeverity.INFO,
                    evidence=f"CapEx/Revenue ratio: {capex_ratio:.2%}",
                ))

        return flags


class DisclosureAnalyzer:
    """Analyzes disclosure quality and completeness."""

    def analyze(self, disclosure_text: str) -> List[RedFlag]:
        """Analyze disclosure text for quality issues."""
        flags = []

        # Check for vague language
        vague_terms = [
            r"\b(?:approximately|about|around|roughly)\b",
            r"\b(?:estimat|approximat|project|forecast)\b",
            r"\b(?:may|might|could|would)\b",
            r"\b(?:uncertain|uncertainty|uncertainties)\b",
        ]

        vague_count = 0
        for term in vague_terms:
            vague_count += len(re.findall(term, disclosure_text, re.IGNORECASE))

        if vague_count > 10:
            flags.append(RedFlag(
                category="disclosure",
                description="Excessive use of vague or uncertain language",
                severity=RedFlagSeverity.WARNING,
                evidence=f"Found {vague_count} vague terms",
            ))

        # Check for missing required disclosures
        required_disclosures = [
            (r"\b(?:risk\s+factors)\b", "Risk factors"),
            (r"\b(?:management\s+discussion)\b", "Management discussion"),
            (r"\b(?:internal\s+control)\b", "Internal controls"),
            (r"\b(?:related\s+party)\b", "Related party transactions"),
        ]

        for pattern, description in required_disclosures:
            if not re.search(pattern, disclosure_text, re.IGNORECASE):
                flags.append(RedFlag(
                    category="disclosure",
                    description=f"Missing {description} disclosure",
                    severity=RedFlagSeverity.WARNING,
                    evidence=f"Pattern not found: {pattern}",
                ))

        # Check for short, incomplete sections
        sections = re.split(r"\b\d+\.\s+\w+", disclosure_text)
        short_sections = [s for s in sections if len(s.strip()) < 100 and len(s.strip()) > 0]
        if len(short_sections) > 5:
            flags.append(RedFlag(
                category="disclosure",
                description="Multiple sections appear incomplete or unusually short",
                severity=RedFlagSeverity.WARNING,
                evidence=f"Found {len(short_sections)} short sections",
            ))

        return flags


class FraudAnalyzer:
    """Main fraud analysis orchestrator."""

    def __init__(self):
        self.text_analyzer = TextPatternAnalyzer()
        self.ratio_analyzer = FinancialRatioAnalyzer()
        self.cash_flow_analyzer = CashFlowAnalyzer()
        self.disclosure_analyzer = DisclosureAnalyzer()

    def analyze(
        self,
        text: str = "",
        financial_data: Optional[Dict[str, float]] = None,
        cash_flow_data: Optional[Dict[str, float]] = None,
        disclosure_text: str = "",
    ) -> Tuple[float, List[RedFlag]]:
        """Run all analyzers and return fraud risk score and red flags."""
        red_flags = []

        # Run text analysis
        if text:
            red_flags.extend(self.text_analyzer.analyze(text))

        # Run financial ratio analysis
        if financial_data:
            red_flags.extend(self.ratio_analyzer.analyze(financial_data))

        # Run cash flow analysis
        if cash_flow_data:
            red_flags.extend(self.cash_flow_analyzer.analyze(cash_flow_data))

        # Run disclosure analysis
        if disclosure_text:
            red_flags.extend(self.disclosure_analyzer.analyze(disclosure_text))

        # Calculate fraud risk score
        fraud_score = self._calculate_fraud_score(red_flags)

        return fraud_score, red_flags

    def _calculate_fraud_score(self, red_flags: List[RedFlag]) -> float:
        """Calculate fraud risk score from red flags."""
        if not red_flags:
            return 0.0

        # Weight by severity
        severity_weights = {
            RedFlagSeverity.CRITICAL: 15.0,
            RedFlagSeverity.WARNING: 5.0,
            RedFlagSeverity.INFO: 1.0,
        }

        total_score = sum(severity_weights.get(flag.severity, 1.0) for flag in red_flags)

        # Cap at 100
        return min(total_score, 100.0)
