"""Tests for advanced_flags module."""

import pytest
from forensic.advanced_flags import (
    benford_analysis,
    beneish_m_score,
    altman_z_score,
    run_advanced_flags,
    BenfordResult,
    BeneishResult,
    AltmanZResult,
)


# ---------------------------------------------------------------------------
# Benford's Law
# ---------------------------------------------------------------------------

def test_benford_no_numbers():
    result = benford_analysis("No numbers here.")
    assert result.description == "No numbers found for Benford's Law analysis."


def test_benford_small_numbers():
    result = benford_analysis("1 2 3 4 5")
    assert result.description == "No numbers with 2+ digits found for Benford's Law analysis."


def test_benford_with_numbers():
    result = benford_analysis("10 20 30 40 50 60 70 80 90 100")
    assert result.digit_counts is not None
    assert result.observed_freq is not None
    assert result.expected_freq is not None
    assert result.chi_squared >= 0
    assert isinstance(result.is_violated, bool)


def test_benford_violation():
    """Create a dataset that violates Benford's Law."""
    # All numbers start with 9
    text = " ".join([f"9{i:04d}" for i in range(100)])
    result = benford_analysis(text)
    assert result.is_violated is True


def test_benford_normal_distribution():
    """Create a dataset that follows Benford's Law."""
    import random
    random.seed(42)
    numbers = []
    for _ in range(1000):
        # Generate numbers with leading digits following Benford's distribution
        r = random.random()
        if r < 0.301:
            d = 1
        elif r < 0.477:
            d = 2
        elif r < 0.602:
            d = 3
        elif r < 0.699:
            d = 4
        elif r < 0.778:
            d = 5
        elif r < 0.845:
            d = 6
        elif r < 0.903:
            d = 7
        elif r < 0.949:
            d = 8
        else:
            d = 9
        numbers.append(f"{d}{random.randint(0, 999999):06d}")
    result = benford_analysis(" ".join(numbers))
    assert result.is_violated is False


# ---------------------------------------------------------------------------
# Beneish M-Score
# ---------------------------------------------------------------------------

def test_beneish_m_score():
    result = beneish_m_score(
        revenue_current=1000,
        revenue_prior=900,
        receivables_current=200,
        receivables_prior=180,
        gross_margin_current=0.4,
        gross_margin_prior=0.45,
        current_ratio_current=2.0,
        current_ratio_prior=2.5,
        expenses_current=600,
        expenses_prior=550,
        assets_current=2000,
        assets_prior=1800,
    )
    assert isinstance(result.m_score, float)
    assert isinstance(result.is_manipulator, bool)
    assert result.components is not None
    assert "DSRI" in result.components
    assert "GMI" in result.components


def test_beneish_manipulator():
    """Create a scenario likely to be flagged as manipulator."""
    result = beneish_m_score(
        revenue_current=1000,
        revenue_prior=500,  # Rapid revenue growth
        receivables_current=500,  # Receivables growing faster than revenue
        receivables_prior=100,
        gross_margin_current=0.6,  # Improving margin (suspicious)
        gross_margin_prior=0.3,
        current_ratio_current=3.0,
        current_ratio_prior=1.5,
        expenses_current=400,
        expenses_prior=350,
        assets_current=2000,
        assets_prior=1000,
    )
    assert result.is_manipulator is True


def test_beneish_normal():
    """Create a normal scenario."""
    result = beneish_m_score(
        revenue_current=1000,
        revenue_prior=950,
        receivables_current=200,
        receivables_prior=190,
        gross_margin_current=0.4,
        gross_margin_prior=0.41,
        current_ratio_current=2.0,
        current_ratio_prior=2.1,
        expenses_current=600,
        expenses_prior=580,
        assets_current=2000,
        assets_prior=1950,
    )
    assert result.is_manipulator is False


# ---------------------------------------------------------------------------
# Altman Z-Score
# ---------------------------------------------------------------------------

def test_altman_z_score():
    result = altman_z_score(
        working_capital=500,
        retained_earnings=300,
        ebit=200,
        market_cap=1000,
        total_assets=2000,
        total_liabilities=1000,
        sales=1500,
    )
    assert isinstance(result.z_score, float)
    assert result.risk_category in ("distress", "grey", "safe", "insufficient data")
    assert result.description


def test_altman_z_score_distress():
    result = altman_z_score(
        working_capital=-100,
        retained_earnings=-200,
        ebit=-50,
        market_cap=100,
        total_assets=1000,
        total_liabilities=900,
        sales=500,
    )
    assert result.risk_category == "distress"


def test_altman_z_score_safe():
    result = altman_z_score(
        working_capital=500,
        retained_earnings=300,
        ebit=200,
        market_cap=1200,
        total_assets=2000,
        total_liabilities=500,
        sales=1500,
    )
    assert result.risk_category == "safe"


def test_altman_z_score_insufficient_data():
    result = altman_z_score(
        working_capital=0,
        retained_earnings=0,
        ebit=0,
        market_cap=0,
        total_assets=0,
        total_liabilities=0,
        sales=0,
    )
    assert result.risk_category == "insufficient data"


# ---------------------------------------------------------------------------
# run_advanced_flags
# ---------------------------------------------------------------------------

def test_run_advanced_flags():
    report = run_advanced_flags(
        ticker="TEST",
        filing_text="10 20 30 40 50 60 70 80 90 100",
        financial_data={
            "revenue": 1000,
            "revenue_prior": 900,
            "receivables": 200,
            "receivables_prior": 180,
            "gross_margin": 0.4,
            "gross_margin_prior": 0.45,
            "current_ratio": 2.0,
            "current_ratio_prior": 2.5,
            "expenses": 600,
            "expenses_prior": 550,
            "assets": 2000,
            "assets_prior": 1800,
            "working_capital": 500,
            "retained_earnings": 300,
            "ebit": 200,
            "market_cap": 1000,
            "total_assets": 2000,
            "total_liabilities": 1000,
        },
    )
    assert report.ticker == "TEST"
    assert report.benford is not None
    assert report.beneish is not None
    assert report.altman_z is not None
    assert report.summary


def test_run_advanced_flags_no_financial_data():
    report = run_advanced_flags(
        ticker="TEST",
        filing_text="10 20 30 40 50 60 70 80 90 100",
    )
    assert report.ticker == "TEST"
    assert report.benford is not None
    assert report.beneish is None
    assert report.altman_z is None
