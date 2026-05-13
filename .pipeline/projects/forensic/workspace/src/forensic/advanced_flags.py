"""Advanced fraud detection flags for SEC filings.

Implements:
- Benford's Law analysis of financial statement numbers
- M-Score (Beneish) model for earnings manipulation detection
- Beneish M-Score computation
- Altman Z-Score for bankruptcy risk assessment
"""

from __future__ import annotations

import math
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("forensic.advanced_flags")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class BenfordResult:
    """Result of Benford's Law analysis."""
    digit_counts: Dict[int, int] = field(default_factory=dict)
    observed_freq: Dict[int, float] = field(default_factory=dict)
    expected_freq: Dict[int, float] = field(default_factory=dict)
    chi_squared: float = 0.0
    is_violated: bool = False
    description: str = ""


@dataclass
class BeneishResult:
    """Result of Beneish M-Score analysis."""
    m_score: float = 0.0
    is_manipulator: bool = False
    components: Dict[str, float] = field(default_factory=dict)
    description: str = ""


@dataclass
class AltmanZResult:
    """Result of Altman Z-Score analysis."""
    z_score: float = 0.0
    risk_category: str = "unknown"
    description: str = ""


@dataclass
class AdvancedFlagsReport:
    """Aggregated advanced flags report."""
    ticker: str
    benford: Optional[BenfordResult] = None
    beneish: Optional[BeneishResult] = None
    altman_z: Optional[AltmanZResult] = None
    summary: str = ""


# ---------------------------------------------------------------------------
# Benford's Law
# ---------------------------------------------------------------------------

# Expected frequency of leading digits per Benford's Law
_BENFORD_EXPECTED: Dict[int, float] = {
    d: math.log10(1 + 1 / d) for d in range(1, 10)
}


def _extract_numbers(text: str) -> List[float]:
    """Extract numeric values from text (integers and floats).

    Excludes 4-digit numbers that look like years (e.g., 2023, 2024)
    to avoid skewing Benford's Law analysis.
    """
    # Match numbers that look like financial figures (at least 1 digit, optional decimal)
    numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", text)
    result: List[float] = []
    for n_str in numbers:
        n = float(n_str)
        # Exclude 4-digit numbers that look like years (1000-2999)
        if n_str.isdigit() and 1000 <= n <= 2999:
            continue
        result.append(n)
    return result


def _leading_digit(n: float) -> int:
    """Return the leading (first) digit of a positive number."""
    s = f"{n:.0f}"
    return int(s[0]) if s[0].isdigit() else 0


def benford_analysis(text: str) -> BenfordResult:
    """Perform Benford's Law analysis on numbers found in *text*.

    Returns a BenfordResult describing whether the distribution of leading
    digits deviates significantly from Benford's expected distribution.
    """
    numbers = _extract_numbers(text)
    if not numbers:
        return BenfordResult(
            description="No numbers found for Benford's Law analysis.",
        )

    # Filter to positive numbers with at least 2 digits
    numbers = [n for n in numbers if n >= 10]
    if not numbers:
        return BenfordResult(
            description="No numbers with 2+ digits found for Benford's Law analysis.",
        )

    # Count leading digits
    digit_counts: Dict[int, int] = {d: 0 for d in range(1, 10)}
    for n in numbers:
        d = _leading_digit(n)
        if 1 <= d <= 9:
            digit_counts[d] += 1

    total = sum(digit_counts.values())
    if total == 0:
        return BenfordResult(
            description="No valid leading digits found.",
        )

    observed_freq = {d: digit_counts[d] / total for d in range(1, 10)}
    expected_freq = {d: _BENFORD_EXPECTED[d] for d in range(1, 10)}

    # Chi-squared test
    chi_squared = 0.0
    for d in range(1, 10):
        expected_count = total * expected_freq[d]
        if expected_count > 0:
            chi_squared += (digit_counts[d] - expected_count) ** 2 / expected_count

    # Critical value for chi-squared with 8 df at alpha=0.05 is ~15.51
    is_violated = chi_squared > 15.51

    if is_violated:
        description = (
            f"Benford's Law violation detected (chi-squared={chi_squared:.2f}). "
            f"Leading digit distribution deviates significantly from expected."
        )
    else:
        description = (
            f"Benford's Law holds (chi-squared={chi_squared:.2f}). "
            f"Leading digit distribution is consistent with natural data."
        )

    return BenfordResult(
        digit_counts=digit_counts,
        observed_freq=observed_freq,
        expected_freq=expected_freq,
        chi_squared=chi_squared,
        is_violated=is_violated,
        description=description,
    )


# ---------------------------------------------------------------------------
# Beneish M-Score
# -----------------------------------------------------------------------------------

def _compute_dsri(
    revenue_current: float,
    revenue_prior: float,
    receivables_current: float,
    receivables_prior: float,
) -> float:
    """Days Sales in Receivables Index."""
    if revenue_prior == 0 or receivables_prior == 0:
        return 1.0
    dsri = (receivables_current / revenue_current) / (receivables_prior / revenue_prior)
    return dsri


def _compute_gmi(
    gross_margin_current: float,
    gross_margin_prior: float,
) -> float:
    """Gross Margin Index."""
    if gross_margin_prior == 0:
        return 1.0
    return gross_margin_current / gross_margin_prior


def _compute_dei(
    current_ratio_current: float,
    current_ratio_prior: float,
) -> float:
    """Debt Equity Index."""
    if current_ratio_prior == 0:
        return 1.0
    return current_ratio_current / current_ratio_prior


def _compute_sgi(
    revenue_current: float,
    revenue_prior: float,
) -> float:
    """Sales Growth Index."""
    if revenue_prior == 0:
        return 1.0
    return revenue_current / revenue_prior


def _compute_dra(
    expenses_current: float,
    expenses_prior: float,
    revenue_current: float,
    revenue_prior: float,
) -> float:
    """Depreciation Index."""
    if revenue_prior == 0 or revenue_current == 0:
        return 1.0
    return (expenses_current / revenue_current) / (expenses_prior / revenue_prior)


def _compute_sgm(
    assets_current: float,
    assets_prior: float,
    revenue_current: float,
    revenue_prior: float,
) -> float:
    """SG&A Index."""
    if revenue_prior == 0 or assets_prior == 0:
        return 1.0
    return (assets_current / revenue_current) / (assets_prior / revenue_prior)


def beneish_m_score(
    revenue_current: float,
    revenue_prior: float,
    receivables_current: float,
    receivables_prior: float,
    gross_margin_current: float,
    gross_margin_prior: float,
    current_ratio_current: float,
    current_ratio_prior: float,
    expenses_current: float,
    expenses_prior: float,
    assets_current: float,
    assets_prior: float,
) -> BeneishResult:
    """Compute the Beneish M-Score for earnings manipulation detection.

    Parameters
    ----------
    All parameters are financial figures for the current and prior periods.

    Returns
    -------
    BeneishResult with the computed M-Score and interpretation.
    """
    # Compute individual indices
    dsri = _compute_dsri(revenue_current, revenue_prior, receivables_current, receivables_prior)
    gmi = _compute_gmi(gross_margin_current, gross_margin_prior)
    dei = _compute_dei(current_ratio_current, current_ratio_prior)
    sgi = _compute_sgi(revenue_current, revenue_prior)
    dra = _compute_dra(expenses_current, expenses_prior, revenue_current, revenue_prior)
    sgm = _compute_sgm(assets_current, assets_prior, revenue_current, revenue_prior)

    # Beneish M-Score formula
    m_score = (
        -4.84
        + 0.92 * dsri
        + 0.528 * gmi
        + 0.404 * dei
        + 0.183 * sgi
        - 0.528 * dra
        + 0.700 * sgm
    )

    is_manipulator = m_score > -1.78  # Higher (more positive) is more suspicious

    description = (
        f"Beneish M-Score: {m_score:.3f}. "
        + ("Likely earnings manipulator." if is_manipulator else "Not a likely manipulator.")
    )

    return BeneishResult(
        m_score=m_score,
        is_manipulator=is_manipulator,
        components={
            "DSRI": dsri,
            "GMI": gmi,
            "DEI": dei,
            "SGI": sgi,
            "DRA": dra,
            "SGM": sgm,
        },
        description=description,
    )


# ---------------------------------------------------------------------------
# Altman Z-Score
# -----------------------------------------------------------------------------------

def altman_z_score(
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    market_cap: float,
    total_assets: float,
    total_liabilities: float,
    sales: float,
) -> AltmanZResult:
    """Compute the Altman Z-Score for bankruptcy risk.

    Parameters
    ----------
    working_capital : current assets - current liabilities
    retained_earnings : accumulated retained earnings
    ebit : earnings before interest and taxes
    market_cap : market value of equity
    total_assets : total assets
    total_liabilities : total liabilities
    sales : total revenue

    Returns
    -------
    AltmanZResult with the Z-Score and risk category.
    """
    if total_assets == 0 or sales == 0:
        return AltmanZResult(
            z_score=0.0,
            risk_category="insufficient data",
            description="Insufficient data to compute Altman Z-Score.",
        )

    z = (
        1.2 * (working_capital / total_assets)
        + 1.4 * (retained_earnings / total_assets)
        + 3.3 * (ebit / total_assets)
        + 0.6 * (market_cap / total_liabilities)
        + 1.0 * (sales / total_assets)
    )

    if z < 1.81:
        risk_category = "distress"
        description = f"Z-Score={z:.2f}: High bankruptcy risk (distress zone)."
    elif z < 2.99:
        risk_category = "grey"
        description = f"Z-Score={z:.2f}: Grey zone (uncertain)."
    else:
        risk_category = "safe"
        description = f"Z-Score={z:.2f}: Low bankruptcy risk (safe zone)."

    return AltmanZResult(
        z_score=z,
        risk_category=risk_category,
        description=description,
    )


# ---------------------------------------------------------------------------
# Aggregated report
# -----------------------------------------------------------------------------------

def run_advanced_flags(
    ticker: str,
    filing_text: str,
    financial_data: Optional[Dict[str, float]] = None,
) -> AdvancedFlagsReport:
    """Run all advanced fraud detection flags.

    Parameters
    ----------
    ticker : ticker symbol
    filing_text : full filing text
    financial_data : optional dict with financial figures for Beneish/Altman

    Returns
    -------
    AdvancedFlagsReport
    """
    report = AdvancedFlagsReport(ticker=ticker)

    # Benford's Law
    report.benford = benford_analysis(filing_text)

    # Beneish M-Score (if financial data is available)
    if financial_data:
        report.beneish = beneish_m_score(
            revenue_current=financial_data.get("revenue", 0),
            revenue_prior=financial_data.get("revenue_prior", 0),
            receivables_current=financial_data.get("receivables", 0),
            receivables_prior=financial_data.get("receivables_prior", 0),
            gross_margin_current=financial_data.get("gross_margin", 0),
            gross_margin_prior=financial_data.get("gross_margin_prior", 0),
            current_ratio_current=financial_data.get("current_ratio", 0),
            current_ratio_prior=financial_data.get("current_ratio_prior", 0),
            expenses_current=financial_data.get("expenses", 0),
            expenses_prior=financial_data.get("expenses_prior", 0),
            assets_current=financial_data.get("assets", 0),
            assets_prior=financial_data.get("assets_prior", 0),
        )

    # Altman Z-Score (if financial data is available)
    if financial_data:
        report.altman_z = altman_z_score(
            working_capital=financial_data.get("working_capital", 0),
            retained_earnings=financial_data.get("retained_earnings", 0),
            ebit=financial_data.get("ebit", 0),
            market_cap=financial_data.get("market_cap", 0),
            total_assets=financial_data.get("total_assets", 0),
            total_liabilities=financial_data.get("total_liabilities", 0),
            sales=financial_data.get("revenue", 0),
        )

    # Build summary
    summary_parts: List[str] = []
    if report.benford:
        summary_parts.append(f"Benford: {'VIOLATION' if report.benford.is_violated else 'OK'}")
    if report.beneish:
        summary_parts.append(f"Beneish: {'MANIPULATOR' if report.beneish.is_manipulator else 'OK'}")
    if report.altman_z:
        summary_parts.append(f"Altman Z: {report.altman_z.risk_category}")
    report.summary = "; ".join(summary_parts)

    return report
