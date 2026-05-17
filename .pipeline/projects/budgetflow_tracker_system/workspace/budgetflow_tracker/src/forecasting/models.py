"""Pydantic models for the forecasting module."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IntervalType(str, Enum):
    """Time interval types for bucketing."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class RecurringPatternType(str, Enum):
    """Types of recurring patterns."""
    SUBSCRIPTION = "subscription"
    RENT = "rent"
    SALARY = "salary"
    UTILITY = "utility"
    OTHER = "other"


class TimeSeriesBucket(BaseModel):
    """A bucket of transactions within a time interval."""
    interval_type: IntervalType
    start_date: date
    end_date: date
    total_income: float = 0.0
    total_expenses: float = 0.0
    net_flow: float = 0.0
    transaction_count: int = 0
    transactions: list[dict] = Field(default_factory=list)

    @property
    def is_positive_flow(self) -> bool:
        return self.net_flow > 0

    @property
    def is_negative_flow(self) -> bool:
        return self.net_flow < 0


class RecurringPattern(BaseModel):
    """Detected recurring transaction pattern."""
    description: str
    category_name: Optional[str] = None
    frequency_days: int  # Average interval in days
    interval_tolerance_days: int = 3  # Tolerance for matching
    amount_mean: float = 0.0
    amount_std: float = 0.0
    occurrence_count: int = 0
    first_seen: Optional[date] = None
    last_seen: Optional[date] = None
    pattern_type: str = "unknown"  # subscription, rent, salary, utility, other
    confidence: float = 0.0  # 0.0-1.0 confidence in the pattern

    def __repr__(self) -> str:
        return (
            f"RecurringPattern(description='{self.description}', "
            f"freq={self.frequency_days}d, amount=${self.amount_mean:.2f}, "
            f"type={self.pattern_type}, confidence={self.confidence:.2f})"
        )


class AnomalyFlag(BaseModel):
    """Flagged anomalous transaction."""
    transaction_id: Optional[int] = None
    date: date
    description: str
    amount: float
    category_name: Optional[str] = None
    deviation_sigma: float  # How many standard deviations from mean
    category_mean: float = 0.0
    category_std: float = 0.0
    anomaly_type: str = "amount_deviation"  # amount_deviation, outlier
    severity: str = "medium"  # low, medium, high, critical

    def __repr__(self) -> str:
        return (
            f"AnomalyFlag(date={self.date}, amount=${self.amount:.2f}, "
            f"deviation={self.deviation_sigma:.1f}σ, severity={self.severity})"
        )


class CategoryProjection(BaseModel):
    """Projection for a single month/day in the forecast."""
    date: date
    income: float = 0.0
    expenses: float = 0.0
    net_flow: float = 0.0
    method: str = ""  # holt_winters, linear_regression
    confidence_lower: float = 0.0
    confidence_upper: float = 0.0


class CashFlowProjection(BaseModel):
    """Complete cash flow projection for a time horizon."""
    start_date: date
    end_date: date
    window_days: int
    aggregate_daily: list[ForecastPoint] = Field(default_factory=list)
    aggregate_cumulative_income: float = 0.0
    aggregate_cumulative_expenses: float = 0.0
    aggregate_cumulative_net: float = 0.0
    category_projections: list[CategoryProjection] = Field(default_factory=list)
    recurring_patterns: list[RecurringPattern] = Field(default_factory=list)
    anomalies: list[AnomalyFlag] = Field(default_factory=list)


class ChartOutput(BaseModel):
    """Output from chart generation."""
    chart_type: str  # trend, category, forecast, cash_position
    title: str
    file_path: str
    width: int = 800
    height: int = 600
    format: str = "png"  # png, html
    data_points: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class ForecastPoint(BaseModel):
    """A single point in a forecast series."""
    date: date
    predicted_value: float = 0.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    confidence_level: float = 0.95


class ForecastResult(BaseModel):
    """Complete forecast result."""
    start_date: date
    end_date: date
    forecast_end: date
    projections: list[CategoryProjection]
    total_forecasted_income: float = 0.0
    total_forecasted_expenses: float = 0.0
    net_forecast: float = 0.0
    confidence_lower: float = 0.0
    confidence_upper: float = 0.0


class ForecastTrend(BaseModel):
    """Trend analysis result."""
    category: str
    trend: str  # income_increasing_expenses_decreasing, etc.
    monthly_avg_income: float = 0.0
    monthly_avg_expenses: float = 0.0
    income_trend_slope: float = 0.0
    expense_trend_slope: float = 0.0
    r_squared: float = 0.0
