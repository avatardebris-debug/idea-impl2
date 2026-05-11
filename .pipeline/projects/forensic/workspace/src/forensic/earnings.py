"""Earnings prediction module for forensic analysis.

Provides simple linear-regression and moving-average models to predict
next-quarter EPS and revenue from historical quarterly earnings data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class EarningsPoint:
    """A single quarterly earnings observation."""
    ticker: str
    cik: str
    accession_no: str
    quarter: str          # e.g. "2024-Q1"
    filing_date: str
    eps: Optional[float]
    revenue: Optional[float]


@dataclass
class PredictionResult:
    """Prediction output for one ticker."""
    ticker: str
    cik: str
    predicted_eps: Optional[float]
    predicted_revenue: Optional[float]
    eps_confidence_low: Optional[float]
    eps_confidence_high: Optional[float]
    revenue_confidence_low: Optional[float]
    revenue_confidence_high: Optional[float]
    model: str            # "linear_regression" or "moving_average"
    data_points: int
    confidence_level: float  # e.g. 0.95

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "predicted_eps": self.predicted_eps,
            "predicted_revenue": self.predicted_revenue,
            "eps_confidence_interval": [self.eps_confidence_low, self.eps_confidence_high],
            "revenue_confidence_interval": [self.revenue_confidence_low, self.revenue_confidence_high],
            "model": self.model,
            "data_points": self.data_points,
            "confidence_level": self.confidence_level,
        }


@dataclass
class EarningsPredictionReport:
    """Full report for one company."""
    ticker: str
    cik: str
    predictions: List[PredictionResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "cik": self.cik,
            "predictions": [p.to_dict() for p in self.predictions],
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Linear regression helpers (pure Python, no numpy dependency)
# ---------------------------------------------------------------------------

def _linear_regression(
    x: List[float],
    y: List[float],
) -> Tuple[float, float]:
    """Simple least-squares linear regression: y = a + b*x.

    Returns (intercept, slope).
    """
    n = len(x)
    if n < 2:
        return (0.0, 0.0)

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)

    denom = n * sum_x2 - sum_x ** 2
    if abs(denom) < 1e-12:
        return (sum_y / n, 0.0)

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return (intercept, slope)


def _standard_error(
    x: List[float],
    y: List[float],
    intercept: float,
    slope: float,
) -> float:
    """Compute residual standard error."""
    n = len(x)
    if n < 3:
        return float("inf")
    residuals = [yi - (intercept + slope * xi) for xi, yi in zip(x, y)]
    mse = sum(r ** 2 for r in residuals) / (n - 2)
    return math.sqrt(mse)


def _t_value(confidence: float, df: int) -> float:
    """Approximate t-value for two-tailed test.

    Uses a simple lookup for common confidence levels.
    """
    # Approximation for common confidence levels
    t_lookup = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }
    if confidence in t_lookup:
        return t_lookup[confidence]
    # Default to 1.96 for 95% confidence
    return 1.96


# ---------------------------------------------------------------------------
# Prediction models
# ---------------------------------------------------------------------------

def predict_with_linear_regression(
    points: List[EarningsPoint],
    target_quarter_index: int,
    confidence: float = 0.95,
) -> Optional[PredictionResult]:
    """Predict next quarter using linear regression on EPS and revenue.

    Parameters
    ----------
    points : list[EarningsPoint]
        Historical quarterly data, sorted by quarter.
    target_quarter_index : int
        The index of the target quarter (e.g., len(points) for next quarter).
    confidence : float
        Confidence level for intervals (default 0.95).

    Returns
    -------
    PredictionResult or None if insufficient data.
    """
    if len(points) < 3:
        return None

    # Use EPS if available, else revenue
    eps_points = [p for p in points if p.eps is not None]
    rev_points = [p for p in points if p.revenue is not None]

    # Build x values (quarter indices)
    x = list(range(len(points)))

    results: List[PredictionResult] = []

    # EPS prediction
    if len(eps_points) >= 3:
        eps_x = [x[points.index(p)] for p in eps_points]
        eps_y = [p.eps for p in eps_points]
        intercept, slope = _linear_regression(eps_x, eps_y)
        predicted_eps = intercept + slope * target_quarter_index

        se = _standard_error(eps_x, eps_y, intercept, slope)
        t = _t_value(confidence, len(eps_x) - 2)
        margin = t * se * math.sqrt(1 + 1 / len(eps_x) + ((target_quarter_index - sum(eps_x) / len(eps_x)) ** 2) / sum((xi - sum(eps_x) / len(eps_x)) ** 2 for xi in eps_x)) if sum((xi - sum(eps_x) / len(eps_x)) ** 2 for xi in eps_x) > 0 else t * se

        results.append(PredictionResult(
            ticker=eps_points[0].ticker,
            cik=eps_points[0].cik,
            predicted_eps=predicted_eps,
            predicted_revenue=None,
            eps_confidence_low=predicted_eps - margin,
            eps_confidence_high=predicted_eps + margin,
            revenue_confidence_low=None,
            revenue_confidence_high=None,
            model="linear_regression",
            data_points=len(eps_x),
            confidence_level=confidence,
        ))

    # Revenue prediction
    if len(rev_points) >= 3:
        rev_x = [x[points.index(p)] for p in rev_points]
        rev_y = [p.revenue for p in rev_points]
        intercept, slope = _linear_regression(rev_x, rev_y)
        predicted_rev = intercept + slope * target_quarter_index

        se = _standard_error(rev_x, rev_y, intercept, slope)
        t = _t_value(confidence, len(rev_x) - 2)
        margin = t * se * math.sqrt(1 + 1 / len(rev_x) + ((target_quarter_index - sum(rev_x) / len(rev_x)) ** 2) / sum((xi - sum(rev_x) / len(rev_x)) ** 2 for xi in rev_x)) if sum((xi - sum(rev_x) / len(rev_x)) ** 2 for xi in rev_x) > 0 else t * se

        # Find the EPS result to update it, or create a new one
        eps_result = next((r for r in results if r.predicted_eps is not None), None)
        if eps_result:
            eps_result.predicted_revenue = predicted_rev
            eps_result.revenue_confidence_low = predicted_rev - margin
            eps_result.revenue_confidence_high = predicted_rev + margin
        else:
            results.append(PredictionResult(
                ticker=rev_points[0].ticker,
                cik=rev_points[0].cik,
                predicted_eps=None,
                predicted_revenue=predicted_rev,
                eps_confidence_low=None,
                eps_confidence_high=None,
                revenue_confidence_low=predicted_rev - margin,
                revenue_confidence_high=predicted_rev + margin,
                model="linear_regression",
                data_points=len(rev_x),
                confidence_level=confidence,
            ))

    return results[0] if results else None


def predict_with_moving_average(
    points: List[EarningsPoint],
    window: int = 4,
    confidence: float = 0.95,
) -> Optional[PredictionResult]:
    """Predict next quarter using moving average of EPS and revenue.

    Parameters
    ----------
    points : list[EarningsPoint]
        Historical quarterly data, sorted by quarter.
    window : int
        Number of quarters to average (default 4).
    confidence : float
        Confidence level for intervals (default 0.95).

    Returns
    -------
    PredictionResult or None if insufficient data.
    """
    if len(points) < 2:
        return None

    eps_points = [p for p in points if p.eps is not None]
    rev_points = [p for p in points if p.revenue is not None]

    results: List[PredictionResult] = []

    # EPS prediction
    if len(eps_points) >= 2:
        recent_eps = [p.eps for p in eps_points[-window:]]
        predicted_eps = sum(recent_eps) / len(recent_eps)

        # Standard deviation for confidence interval
        if len(recent_eps) > 1:
            mean_eps = predicted_eps
            variance = sum((e - mean_eps) ** 2 for e in recent_eps) / (len(recent_eps) - 1)
            std_eps = math.sqrt(variance)
        else:
            std_eps = 0.0

        t = _t_value(confidence, max(1, len(recent_eps) - 1))
        margin_eps = t * std_eps * math.sqrt(1 + 1 / len(recent_eps))

        results.append(PredictionResult(
            ticker=eps_points[0].ticker,
            cik=eps_points[0].cik,
            predicted_eps=predicted_eps,
            predicted_revenue=None,
            eps_confidence_low=predicted_eps - margin_eps,
            eps_confidence_high=predicted_eps + margin_eps,
            revenue_confidence_low=None,
            revenue_confidence_high=None,
            model="moving_average",
            data_points=len(recent_eps),
            confidence_level=confidence,
        ))

    # Revenue prediction
    if len(rev_points) >= 2:
        recent_rev = [p.revenue for p in rev_points[-window:]]
        predicted_rev = sum(recent_rev) / len(recent_rev)

        if len(recent_rev) > 1:
            mean_rev = predicted_rev
            variance = sum((r - mean_rev) ** 2 for r in recent_rev) / (len(recent_rev) - 1)
            std_rev = math.sqrt(variance)
        else:
            std_rev = 0.0

        t = _t_value(confidence, max(1, len(recent_rev) - 1))
        margin_rev = t * std_rev * math.sqrt(1 + 1 / len(recent_rev))

        eps_result = next((r for r in results if r.predicted_eps is not None), None)
        if eps_result:
            eps_result.predicted_revenue = predicted_rev
            eps_result.revenue_confidence_low = predicted_rev - margin_rev
            eps_result.revenue_confidence_high = predicted_rev + margin_rev
        else:
            results.append(PredictionResult(
                ticker=rev_points[0].ticker,
                cik=rev_points[0].cik,
                predicted_eps=None,
                predicted_revenue=predicted_rev,
                eps_confidence_low=None,
                eps_confidence_high=None,
                revenue_confidence_low=predicted_rev - margin_rev,
                revenue_confidence_high=predicted_rev + margin_rev,
                model="moving_average",
                data_points=len(recent_rev),
                confidence_level=confidence,
            ))

    return results[0] if results else None


# ---------------------------------------------------------------------------
# Main prediction engine
# ---------------------------------------------------------------------------

def predict_earnings(
    points: List[EarningsPoint],
    model: str = "linear_regression",
    confidence: float = 0.95,
) -> EarningsPredictionReport:
    """Run earnings prediction on historical data.

    Parameters
    ----------
    points : list[EarningsPoint]
        Historical quarterly earnings data, sorted by quarter.
    model : str
        Model to use: "linear_regression" or "moving_average".
    confidence : float
        Confidence level for intervals (default 0.95).

    Returns
    -------
    EarningsPredictionReport
    """
    report = EarningsPredictionReport(
        ticker=points[0].ticker if points else "",
        cik=points[0].cik if points else "",
    )

    if not points:
        report.warnings.append("No earnings data available for prediction")
        return report

    if len(points) < 3:
        report.warnings.append("Insufficient data points (< 3) for reliable prediction")

    target_index = len(points)  # next quarter

    if model == "linear_regression":
        result = predict_with_linear_regression(points, target_index, confidence)
    elif model == "moving_average":
        result = predict_with_moving_average(points, confidence=confidence)
    else:
        report.warnings.append(f"Unknown model: {model}")
        return report

    if result:
        report.predictions.append(result)
    else:
        report.warnings.append("Prediction failed — insufficient data or computation error")

    return report


def extract_earnings_points(
    filings: List[Dict],
) -> List[EarningsPoint]:
    """Extract earnings data points from filing records.

    Looks for EPS and revenue in the filing data.

    Parameters
    ----------
    filings : list[dict]
        List of filing dicts with keys like 'eps', 'revenue', 'quarter', etc.

    Returns
    -------
    list[EarningsPoint]
    """
    points: List[EarningsPoint] = []
    for f in filings:
        point = EarningsPoint(
            ticker=f.get("ticker", ""),
            cik=f.get("cik", ""),
            accession_no=f.get("accession_no", ""),
            quarter=f.get("quarter", ""),
            filing_date=f.get("filing_date", ""),
            eps=f.get("eps"),
            revenue=f.get("revenue"),
        )
        points.append(point)
    return points
