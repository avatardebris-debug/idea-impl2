"""Multi-company comparison logic for forensic analysis.

Compares multiple companies on:
- Fraud scores (from Phase 1 red-flag checks)
- Normalized financial ratios
- Earnings predictions
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from forensic.earnings import EarningsPoint, EarningsPredictionReport, predict_earnings
from forensic.fraud import FraudAnalyzer
from forensic.models import RedFlag
from forensic.normalization import NormalizedCompany, normalize_items, normalize_multiple
from forensic.scoring import compute_fraud_score, get_risk_level, generate_report


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class ComparativeResult:
    """Result of a multi-company comparison."""

    def __init__(self):
        self.companies: List[Dict] = []  # per-company data
        self.rankings: List[Tuple[str, float]] = []  # (ticker, score) sorted
        self.earnings_reports: List[EarningsPredictionReport] = []
        self.warnings: List[str] = []

    def to_dict(self) -> dict:
        return {
            "companies": self.companies,
            "rankings": [{"ticker": t, "score": s} for t, s in self.rankings],
            "earnings_reports": [r.to_dict() for r in self.earnings_reports],
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Core comparison logic
# ---------------------------------------------------------------------------

def compare_companies(
    tickers: List[str],
    ticker_data: Dict[str, Dict],
    earnings_data: Optional[Dict[str, List[Dict]]] = None,
    model: str = "linear_regression",
    confidence: float = 0.95,
) -> ComparativeResult:
    """Compare multiple companies on fraud scores and financials.

    Parameters
    ----------
    tickers : list[str]
        Ticker symbols to compare.
    ticker_data : dict
        Mapping ticker -> {
            "cik": str,
            "accession_no": str,
            "filing_date": str,
            "text_parts": list[str],
            "financial_data": dict,
            "cash_flow_data": dict,
            "disclosure_text": str,
        }
    earnings_data : dict, optional
        Mapping ticker -> list of dicts with keys:
        "quarter", "eps", "revenue", "accession_no", "filing_date"
    model : str
        Earnings prediction model: "linear_regression" or "moving_average".
    confidence : float
        Confidence level for prediction intervals.

    Returns
    -------
    ComparativeResult
    """
    result = ComparativeResult()

    if not tickers:
        result.warnings.append("No tickers provided")
        return result

    # ---- Normalize financial line items ----
    normalized_companies: List[NormalizedCompany] = []
    for ticker in tickers:
        data = ticker_data.get(ticker, {})
        text_parts = data.get("text_parts", [])
        cik = data.get("cik", "")
        accession_no = data.get("accession_no", "")
        filing_date = data.get("filing_date", "")

        norm = normalize_items(ticker, cik, accession_no, filing_date, text_parts)
        normalized_companies.append(norm)

    # Use global normalizer across all companies
    normalized_companies = normalize_multiple(normalized_companies)

    # ---- Run fraud analysis ----
    fraud_analyzer = FraudAnalyzer()
    company_results: List[Dict] = []
    scores: List[Tuple[str, float]] = []

    for i, ticker in enumerate(tickers):
        data = ticker_data.get(ticker, {})
        text = "\n".join(data.get("text_parts", []))
        financial_data = data.get("financial_data", {})
        cash_flow_data = data.get("cash_flow_data", {})
        disclosure_text = data.get("disclosure_text", "")

        fraud_score, red_flags = fraud_analyzer.analyze(
            text=text,
            financial_data=financial_data,
            cash_flow_data=cash_flow_data,
            disclosure_text=disclosure_text,
        )

        risk_level = get_risk_level(fraud_score)

        # Build normalized company info
        norm = normalized_companies[i] if i < len(normalized_companies) else None
        norm_dict = norm.to_dict() if norm else {"items": {}, "normalized": {}}

        company_results.append({
            "ticker": ticker,
            "cik": data.get("cik", ""),
            "accession_no": data.get("accession_no", ""),
            "filing_date": data.get("filing_date", ""),
            "fraud_score": fraud_score,
            "risk_level": risk_level.value,
            "red_flags": [f.to_dict() for f in red_flags],
            "normalized_financials": norm_dict,
        })
        scores.append((ticker, fraud_score))

    # Sort by fraud score descending (highest risk first)
    result.rankings = sorted(scores, key=lambda x: x[1], reverse=True)
    result.companies = company_results

    # ---- Earnings prediction ----
    if earnings_data:
        for ticker in tickers:
            earnings_list = earnings_data.get(ticker, [])
            if not earnings_list:
                result.warnings.append(f"No earnings data for {ticker}")
                continue

            points = EarningsPredictionReport(
                ticker=ticker,
                cik="",
            )
            # Convert dicts to EarningsPoint objects
            eps_points = []
            for ed in earnings_list:
                eps_points.append(EarningsPoint(
                    ticker=ticker,
                    cik=ed.get("cik", ""),
                    accession_no=ed.get("accession_no", ""),
                    quarter=ed.get("quarter", ""),
                    filing_date=ed.get("filing_date", ""),
                    eps=ed.get("eps"),
                    revenue=ed.get("revenue"),
                ))

            # Sort by quarter
            eps_points.sort(key=lambda p: p.quarter)

            report = predict_earnings(eps_points, model=model, confidence=confidence)
            result.earnings_reports.append(report)
    else:
        result.warnings.append("No earnings data provided — skipping earnings predictions")

    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_comparative_report(result: ComparativeResult) -> str:
    """Generate a human-readable comparative report."""
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append("FORENSIC COMPARATIVE REPORT")
    lines.append("=" * 70)
    lines.append("")

    # Rankings
    lines.append("FRAUD RISK RANKINGS (highest risk first)")
    lines.append("-" * 50)
    for rank, (ticker, score) in enumerate(result.rankings, 1):
        lines.append(f"  {rank}. {ticker}: {score:.2f}")
    lines.append("")

    # Per-company details
    lines.append("PER-COMPANY DETAILS")
    lines.append("-" * 50)
    for comp in result.companies:
        lines.append(f"\n  Ticker: {comp['ticker']}")
        lines.append(f"  CIK: {comp['cik']}")
        lines.append(f"  Accession: {comp['accession_no']}")
        lines.append(f"  Filing Date: {comp['filing_date']}")
        lines.append(f"  Fraud Score: {comp['fraud_score']:.2f}")
        lines.append(f"  Risk Level: {comp['risk_level']}")
        lines.append(f"  Red Flags ({len(comp['red_flags'])}):")
        for flag in comp["red_flags"]:
            lines.append(f"    - [{flag['severity']}] {flag['description']}")

        # Normalized financials
        norm = comp.get("normalized_financials", {})
        normalized = norm.get("normalized", {})
        if normalized:
            lines.append("  Normalized Financials (as fraction of revenue):")
            for item, val in sorted(normalized.items()):
                lines.append(f"    {item}: {val:.4f}")

    # Earnings predictions
    if result.earnings_reports:
        lines.append("\n" + "=" * 70)
        lines.append("EARNINGS PREDICTIONS")
        lines.append("=" * 70)
        for report in result.earnings_reports:
            lines.append(f"\n  Ticker: {report.ticker}")
            for pred in report.predictions:
                lines.append(f"  Model: {pred.model}")
                lines.append(f"  Data Points: {pred.data_points}")
                if pred.predicted_eps is not None:
                    lines.append(f"  Predicted EPS: {pred.predicted_eps:.4f}")
                    if pred.eps_confidence_low is not None and pred.eps_confidence_high is not None:
                        lines.append(f"  EPS 95% CI: [{pred.eps_confidence_low:.4f}, {pred.eps_confidence_high:.4f}]")
                if pred.predicted_revenue is not None:
                    lines.append(f"  Predicted Revenue: {pred.predicted_revenue:.2f}")
                    if pred.revenue_confidence_low is not None and pred.revenue_confidence_high is not None:
                        lines.append(f"  Revenue 95% CI: [{pred.revenue_confidence_low:.2f}, {pred.revenue_confidence_high:.2f}]")

    # Warnings
    if result.warnings:
        lines.append("\n" + "=" * 70)
        lines.append("WARNINGS")
        lines.append("=" * 70)
        for w in result.warnings:
            lines.append(f"  - {w}")

    lines.append("")
    return "\n".join(lines)


def generate_comparative_json(result: ComparativeResult) -> str:
    """Generate a JSON comparative report."""
    import json
    return json.dumps(result.to_dict(), indent=2)
