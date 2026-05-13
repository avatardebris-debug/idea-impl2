"""Fraud scoring engine for forensic analysis."""

from typing import List
from forensic.models import FraudReport, Recommendation, RedFlag, RedFlagSeverity, RiskLevel


# Severity weights for scoring
SEVERITY_WEIGHTS = {
    RedFlagSeverity.CRITICAL: 25,
    RedFlagSeverity.WARNING: 10,
    RedFlagSeverity.INFO: 2,
}


def compute_fraud_score(flags: List[RedFlag]) -> float:
    """Compute a fraud risk score from a list of red flags.

    Each flag contributes its severity weight to the score.
    The score is capped at 100.
    """
    score = sum(SEVERITY_WEIGHTS.get(flag.severity, 0) for flag in flags)
    return min(score, 100.0)


def get_risk_level(score: float) -> RiskLevel:
    """Map a numeric score to a risk level."""
    if score <= 30:
        return RiskLevel.LOW
    elif score <= 69:
        return RiskLevel.MEDIUM
    elif score <= 89:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def generate_report(
    ticker: str,
    cik: str,
    accession_no: str,
    flags: List[RedFlag],
) -> FraudReport:
    """Generate a fraud risk report from red flags."""
    score = compute_fraud_score(flags)
    risk_level = get_risk_level(score)

    recommendations = _generate_recommendations(flags)

    return FraudReport(
        ticker=ticker,
        cik=cik,
        filing_date=accession_no,
        risk_score=score,
        overall_risk=risk_level.value,
        red_flags=flags,
        recommendations=recommendations,
    )


def _generate_recommendations(flags: List[RedFlag]) -> List[Recommendation]:
    """Generate actionable recommendations based on detected flags."""
    recommendations = []
    categories = {flag.category for flag in flags}

    if "text_pattern" in categories:
        recommendations.append(Recommendation(
            category="text_pattern",
            description="Review flagged text patterns with legal counsel",
            priority="high",
        ))
    if "financial_ratio" in categories:
        recommendations.append(Recommendation(
            category="financial_ratio",
            description="Conduct detailed financial ratio analysis",
            priority="high",
        ))
    if "related_party" in categories:
        recommendations.append(Recommendation(
            category="related_party",
            description="Investigate related-party transactions for arm's-length compliance",
            priority="high",
        ))
    if "auditor" in categories:
        recommendations.append(Recommendation(
            category="auditor",
            description="Review auditor communications and going-concern assessments",
            priority="critical",
        ))
    if "off_balance_sheet" in categories:
        recommendations.append(Recommendation(
            category="off_balance_sheet",
            description="Examine off-balance-sheet arrangements for disclosure adequacy",
            priority="high",
        ))

    if not recommendations:
        recommendations.append(Recommendation(
            category="general",
            description="No specific recommendations — continue routine monitoring",
            priority="low",
        ))

    return recommendations
