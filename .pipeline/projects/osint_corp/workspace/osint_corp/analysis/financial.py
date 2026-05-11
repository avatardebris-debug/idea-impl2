"""Financial analysis module — extracts and analyzes financial data from SEC filings."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from osint_corp.models.entities import Filing

logger = logging.getLogger(__name__)


@dataclass
class FinancialRatio:
    """A single financial ratio."""
    name: str
    value: float
    description: str
    benchmark: Optional[float] = None  # Industry benchmark
    trend: Optional[str] = None  # "up", "down", "stable"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "description": self.description,
            "benchmark": self.benchmark,
            "trend": self.trend,
        }


@dataclass
class FinancialSummary:
    """Summary of financial analysis for a company."""
    company_name: str
    ticker: Optional[str]
    filing_date: str
    ratios: list[FinancialRatio] = field(default_factory=list)
    revenue_trend: list[tuple[str, float]] = field(default_factory=list)
    net_income_trend: list[tuple[str, float]] = field(default_factory=list)
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    total_equity: float = 0.0
    operating_cash_flow: float = 0.0
    free_cash_flow: float = 0.0
    debt_to_equity: float = 0.0
    current_ratio: float = 0.0
    quick_ratio: float = 0.0
    roe: float = 0.0
    roa: float = 0.0
    gross_margin: float = 0.0
    operating_margin: float = 0.0
    net_margin: float = 0.0
    warnings: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "ticker": self.ticker,
            "filing_date": self.filing_date,
            "ratios": [r.to_dict() for r in self.ratios],
            "revenue_trend": self.revenue_trend,
            "net_income_trend": self.net_income_trend,
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "total_equity": self.total_equity,
            "operating_cash_flow": self.operating_cash_flow,
            "free_cash_flow": self.free_cash_flow,
            "debt_to_equity": self.debt_to_equity,
            "current_ratio": self.current_ratio,
            "quick_ratio": self.quick_ratio,
            "roe": self.roe,
            "roa": self.roa,
            "gross_margin": self.gross_margin,
            "operating_margin": self.operating_margin,
            "net_margin": self.net_margin,
            "warnings": self.warnings,
            "insights": self.insights,
        }


def _extract_number(text: str, pattern: str) -> Optional[float]:
    """Extract a numeric value from text using a regex pattern."""
    if not text:
        return None
    match = re.search(pattern, text)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return None
    return None


def _parse_financials(filing: Filing) -> dict[str, Any]:
    """Parse financial data from a filing's metadata or content."""
    financials = {}

    # Try to extract from filing metadata
    if filing.financials:
        financials.update(filing.financials)

    # Try to extract from metadata raw_filing
    if filing.metadata and "raw_filing" in filing.metadata:
        raw = filing.metadata["raw_filing"]
        if isinstance(raw, dict):
            financials.update(raw)

    return financials


def _extract_from_text(text: str, key: str) -> Optional[float]:
    """Extract a financial value from filing text content."""
    if not text:
        return None

    # Common patterns for financial values
    patterns = [
        rf"{key}\s*[:\s]*\$?([\d,]+(?:\.\d+)?)",
        rf"{key}\s*:\s*\$?([\d,]+(?:\.\d+)?)",
        rf"{key}\s+([\d,]+(?:\.\d+)?)",
    ]

    for pattern in patterns:
        value = _extract_number(text, pattern)
        if value is not None:
            # Clean up commas
            return value
    return None


class FinancialAnalyzer:
    """Analyzes financial data from SEC filings."""

    def __init__(self):
        self._cache: dict[str, FinancialSummary] = {}

    def analyze(self, filing: Filing) -> FinancialSummary:
        """Analyze the financial data in a filing.

        Args:
            filing: A Filing model instance (typically 10-K or 10-Q).

        Returns:
            FinancialSummary with extracted ratios and insights.
        """
        cache_key = f"{filing.accession_number}_{filing.filing_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        summary = self._analyze_filing(filing)
        self._cache[cache_key] = summary
        return summary

    def analyze_multiple(self, filings: list[Filing]) -> list[FinancialSummary]:
        """Analyze multiple filings and return summaries.

        Args:
            filings: List of Filing model instances.

        Returns:
            List of FinancialSummary instances.
        """
        return [self.analyze(f) for f in filings]

    def compare_filings(self, filings: list[Filing]) -> dict[str, Any]:
        """Compare financial data across multiple filings.

        Args:
            filings: List of Filing model instances (same company, different periods).

        Returns:
            Dictionary with comparison data.
        """
        if len(filings) < 2:
            return {"error": "Need at least 2 filings for comparison"}

        summaries = [self.analyze(f) for f in filings]

        # Extract trends
        revenue_trend = [(s.filing_date, s.total_assets) for s in summaries]
        equity_trend = [(s.filing_date, s.total_equity) for s in summaries]

        return {
            "company_name": filings[0].company_name,
            "ticker": filings[0].ticker,
            "num_filings": len(filings),
            "periods": [s.filing_date for s in summaries],
            "revenue_trend": revenue_trend,
            "equity_trend": equity_trend,
            "ratios_by_period": [s.to_dict() for s in summaries],
        }

    def _analyze_filing(self, filing: Filing) -> FinancialSummary:
        """Internal method to analyze a single filing."""
        financials = _parse_financials(filing)
        summary = FinancialSummary(
            company_name=filing.company_name,
            ticker=filing.ticker,
            filing_date=filing.filing_date,
        )

        # Extract key financial figures
        summary.total_assets = financials.get("total_assets", 0) or 0
        summary.total_liabilities = financials.get("total_liabilities", 0) or 0
        summary.total_equity = financials.get("total_equity", 0) or 0
        summary.operating_cash_flow = financials.get("operating_cash_flow", 0) or 0
        summary.free_cash_flow = financials.get("free_cash_flow", 0) or 0

        # Calculate ratios
        if summary.total_equity != 0:
            summary.debt_to_equity = summary.total_liabilities / summary.total_equity
        if summary.total_assets != 0:
            summary.roa = (financials.get("net_income", 0) or 0) / summary.total_assets
        if summary.total_equity != 0:
            summary.roe = (financials.get("net_income", 0) or 0) / summary.total_equity

        # Gross margin
        revenue = financials.get("revenue", 0) or financials.get("total_revenue", 0) or 0
        cogs = financials.get("cost_of_revenue", 0) or financials.get("cost_of_goods_sold", 0) or 0
        if revenue != 0:
            summary.gross_margin = (revenue - cogs) / revenue

        # Operating margin
        operating_income = financials.get("operating_income", 0) or financials.get("operating_profit", 0) or 0
        if revenue != 0:
            summary.operating_margin = operating_income / revenue

        # Net margin
        net_income = financials.get("net_income", 0) or 0
        if revenue != 0:
            summary.net_margin = net_income / revenue

        # Current ratio
        current_assets = financials.get("current_assets", 0) or 0
        current_liabilities = financials.get("current_liabilities", 0) or 0
        if current_liabilities != 0:
            summary.current_ratio = current_assets / current_liabilities

        # Quick ratio
        inventory = financials.get("inventory", 0) or 0
        if current_liabilities != 0:
            summary.quick_ratio = (current_assets - inventory) / current_liabilities

        # Generate ratios list
        summary.ratios = [
            FinancialRatio(
                name="Debt-to-Equity",
                value=summary.debt_to_equity,
                description="Total liabilities divided by total equity",
                benchmark=1.0,
            ),
            FinancialRatio(
                name="Return on Assets (ROA)",
                value=summary.roa,
                description="Net income divided by total assets",
                benchmark=0.05,
            ),
            FinancialRatio(
                name="Return on Equity (ROE)",
                value=summary.roe,
                description="Net income divided by total equity",
                benchmark=0.15,
            ),
            FinancialRatio(
                name="Gross Margin",
                value=summary.gross_margin,
                description="(Revenue - Cost of Goods Sold) / Revenue",
                benchmark=0.40,
            ),
            FinancialRatio(
                name="Operating Margin",
                value=summary.operating_margin,
                description="Operating income divided by revenue",
                benchmark=0.10,
            ),
            FinancialRatio(
                name="Net Margin",
                value=summary.net_margin,
                description="Net income divided by revenue",
                benchmark=0.05,
            ),
            FinancialRatio(
                name="Current Ratio",
                value=summary.current_ratio,
                description="Current assets divided by current liabilities",
                benchmark=1.5,
            ),
            FinancialRatio(
                name="Quick Ratio",
                value=summary.quick_ratio,
                description="(Current assets - Inventory) / Current liabilities",
                benchmark=1.0,
            ),
        ]

        # Generate warnings
        if summary.debt_to_equity > 2.0:
            summary.warnings.append("High debt-to-equity ratio (>2.0) — potential solvency risk")
        if summary.current_ratio < 1.0:
            summary.warnings.append("Current ratio below 1.0 — potential liquidity risk")
        if summary.net_margin < 0:
            summary.warnings.append("Negative net margin — company is losing money")
        if summary.roe < 0.05:
            summary.warnings.append("Low return on equity (<5%) — poor shareholder returns")

        # Generate insights
        if summary.gross_margin > 0.60:
            summary.insights.append("Strong gross margins (>60%) — pricing power or low-cost structure")
        if summary.operating_cash_flow > 0 and summary.free_cash_flow > 0:
            summary.insights.append("Positive operating and free cash flow — healthy cash generation")
        if summary.roe > 0.20:
            summary.insights.append("Excellent return on equity (>20%) — efficient use of shareholder capital")

        return summary

    def clear_cache(self):
        """Clear the analysis cache."""
        self._cache.clear()
