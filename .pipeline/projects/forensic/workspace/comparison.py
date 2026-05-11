"""Multi-company comparison module."""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class CompanyComparison:
    """Comparison data for a single company."""
    ticker: str
    cik: str
    accession_no: str
    filing_date: str
    text_parts: List[str]
    financial_data: Dict[str, float]
    cash_flow_data: Dict[str, float]
    disclosure_text: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "accession_no": self.accession_no,
            "filing_date": self.filing_date,
            "text_parts": self.text_parts,
            "financial_data": self.financial_data,
            "cash_flow_data": self.cash_flow_data,
            "disclosure_text": self.disclosure_text,
        }


@dataclass
class EarningsReport:
    """Earnings report data."""
    ticker: str
    quarter: str
    eps: float
    revenue: float
    accession_no: str
    filing_date: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "quarter": self.quarter,
            "eps": self.eps,
            "revenue": self.revenue,
            "accession_no": self.accession_no,
            "filing_date": self.filing_date,
        }


@dataclass
class ComparativeResult:
    """Result of comparing multiple companies."""
    companies: List[CompanyComparison] = field(default_factory=list)
    rankings: List[Tuple[str, int]] = field(default_factory=list)
    earnings_reports: List[EarningsReport] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "companies": [c.to_dict() for c in self.companies],
            "rankings": [{"ticker": t, "score": s} for t, s in self.rankings],
            "earnings_reports": [e.to_dict() for e in self.earnings_reports],
            "warnings": self.warnings,
        }


def compare_companies(
    tickers: List[str],
    ticker_data: Dict[str, dict],
    earnings_data: Optional[Dict[str, list]] = None,
) -> ComparativeResult:
    """Compare multiple companies based on their filing data.

    Args:
        tickers: List of stock tickers to compare
        ticker_data: Dictionary mapping tickers to their data
        earnings_data: Optional dictionary mapping tickers to earnings data

    Returns:
        ComparativeResult with rankings and company data
    """
    result = ComparativeResult()

    if not tickers:
        return result

    # Create company comparisons
    for ticker in tickers:
        if ticker not in ticker_data:
            result.warnings.append(f"No data available for ticker: {ticker}")
            continue

        data = ticker_data[ticker]
        company = CompanyComparison(
            ticker=ticker,
            cik=data.get("cik", ""),
            accession_no=data.get("accession_no", ""),
            filing_date=data.get("filing_date", ""),
            text_parts=data.get("text_parts", []),
            financial_data=data.get("financial_data", {}),
            cash_flow_data=data.get("cash_flow_data", {}),
            disclosure_text=data.get("disclosure_text", ""),
        )
        result.companies.append(company)

    # Calculate fraud risk scores (simplified for testing)
    # In a real implementation, this would use complex forensic analysis
    for company in result.companies:
        # Simple scoring based on disclosure text length and financial data
        score = 0
        if company.disclosure_text:
            score += min(len(company.disclosure_text) // 100, 30)
        if company.financial_data:
            score += min(len(company.financial_data) * 5, 40)
        if company.cash_flow_data:
            score += min(len(company.cash_flow_data) * 5, 30)
        result.rankings.append((company.ticker, score))

    # Sort rankings by score (descending)
    result.rankings.sort(key=lambda x: x[1], reverse=True)

    # Process earnings data if provided
    if earnings_data:
        for ticker, earnings_list in earnings_data.items():
            if isinstance(earnings_list, list):
                for earning in earnings_list:
                    if isinstance(earning, dict):
                        report = EarningsReport(
                            ticker=ticker,
                            quarter=earning.get("quarter", ""),
                            eps=earning.get("eps", 0.0),
                            revenue=earning.get("revenue", 0.0),
                            accession_no=earning.get("accession_no", ""),
                            filing_date=earning.get("filing_date", ""),
                        )
                        result.earnings_reports.append(report)

    return result


def generate_comparative_report(result: ComparativeResult) -> str:
    """Generate a text comparative report.

    Args:
        result: ComparativeResult to generate report for

    Returns:
        Formatted text report
    """
    lines = []
    lines.append("=" * 60)
    lines.append("FORENSIC COMPARATIVE REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Fraud risk rankings
    lines.append("FRAUD RISK RANKINGS")
    lines.append("-" * 40)
    for i, (ticker, score) in enumerate(result.rankings, 1):
        lines.append(f"  {i}. {ticker}: {score}")
    lines.append("")

    # Per-company details
    lines.append("PER-COMPANY DETAILS")
    lines.append("-" * 40)
    for company in result.companies:
        lines.append(f"\n  Company: {company.ticker}")
        lines.append(f"    CIK: {company.cik}")
        lines.append(f"    Accession No: {company.accession_no}")
        lines.append(f"    Filing Date: {company.filing_date}")
        lines.append(f"    Financial Data Keys: {list(company.financial_data.keys())}")
        lines.append(f"    Cash Flow Data Keys: {list(company.cash_flow_data.keys())}")
    lines.append("")

    # Earnings reports
    if result.earnings_reports:
        lines.append("EARNINGS PREDICTIONS")
        lines.append("-" * 40)
        for report in result.earnings_reports:
            lines.append(f"  {report.ticker} - {report.quarter}")
            lines.append(f"    EPS: {report.eps}")
            lines.append(f"    Revenue: {report.revenue}")
        lines.append("")

    # Warnings
    if result.warnings:
        lines.append("WARNINGS")
        lines.append("-" * 40)
        for warning in result.warnings:
            lines.append(f"  - {warning}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def generate_comparative_json(result: ComparativeResult) -> str:
    """Generate a JSON comparative report.

    Args:
        result: ComparativeResult to generate JSON for

    Returns:
        JSON string
    """
    return json.dumps(result.to_dict(), indent=2)
