"""Forecasting engine for BudgetFlow Tracker.

Implements Holt-Winters (Triple Exponential Smoothing) and Linear Regression
for time-series forecasting of income and expenses.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from src.core.database import Database
from src.forecasting.models import (
    CategoryProjection,
    ForecastResult,
    ForecastTrend,
    IntervalType,
    TimeSeriesBucket,
)
from src.forecasting.time_bucket import TimeBucketEngine

logger = logging.getLogger(__name__)


@dataclass
class _HWParams:
    """Holt-Winters parameters."""
    alpha: float = 0.3  # Level smoothing
    beta: float = 0.1  # Trend smoothing
    gamma: float = 0.1  # Seasonal smoothing
    seasonal_period: int = 4  # Quarterly seasonality


class ForecastingEngine:
    """Forecast future income and expenses using multiple methods."""

    def __init__(self, db: Database):
        self.db = db
        self.bucket_engine = TimeBucketEngine(db)

    def forecast(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        horizon_days: int = 90,
        method: str = "hw",  # 'hw' or 'linear'
        category: Optional[str] = None,
    ) -> ForecastResult:
        """Generate a forecast for income and expenses.

        Args:
            start_date: Start of historical data. Defaults to 365 days ago.
            end_date: End of historical data. Defaults to today.
            horizon_days: Number of days to forecast into the future.
            method: Forecasting method ('hw' for Holt-Winters, 'linear' for regression).
            category: Optional category filter.

        Returns:
            ForecastResult with projections and confidence intervals.
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        # Get historical data
        buckets = self._get_historical_data(start_date, end_date, category)

        if len(buckets) < 5:
            logger.warning("Insufficient data for forecasting (got %d buckets)", len(buckets))
            return self._empty_forecast(end_date, horizon_days)

        # Forecast using selected method
        if method == "hw":
            projections = self._forecast_holt_winters(buckets, horizon_days)
        elif method == "linear":
            projections = self._forecast_linear(buckets, horizon_days)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Calculate confidence intervals
        projections = self._calculate_confidence_intervals(projections, buckets)

        # Build result
        total_income = sum(p.income for p in projections)
        total_expenses = sum(p.expenses for p in projections)

        return ForecastResult(
            start_date=start_date,
            end_date=end_date,
            forecast_end=end_date + timedelta(days=horizon_days),
            projections=projections,
            total_forecasted_income=round(total_income, 2),
            total_forecasted_expenses=round(total_expenses, 2),
            net_forecast=round(total_income - total_expenses, 2),
            confidence_lower=projections[-1].confidence_lower if projections else 0.0,
            confidence_upper=projections[-1].confidence_upper if projections else 0.0,
        )

    def _get_historical_data(
        self,
        start_date: date,
        end_date: date,
        category: Optional[str] = None,
    ) -> list[TimeSeriesBucket]:
        """Get historical monthly buckets."""
        if category:
            # Get data for specific category
            query = """
                SELECT strftime('%Y-%m-01', date) as month,
                       SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                       SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses
                FROM transactions
                WHERE date >= ? AND date <= ?
                  AND category_name = ?
                GROUP BY month
                ORDER BY month ASC
            """
            rows = self.db.fetchall(query, (start_date.isoformat(), end_date.isoformat(), category))
        else:
            query = """
                SELECT strftime('%Y-%m-01', date) as month,
                       SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                       SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses
                FROM transactions
                WHERE date >= ? AND date <= ?
                GROUP BY month
                ORDER BY month ASC
            """
            rows = self.db.fetchall(query, (start_date.isoformat(), end_date.isoformat()))

        buckets = []
        for row in rows:
            buckets.append(TimeSeriesBucket(
                interval_type=IntervalType.MONTHLY,
                start_date=date.fromisoformat(row["month"]),
                end_date=date.fromisoformat(row["month"]).replace(day=28) + timedelta(days=4),
                total_income=float(row["income"]),
                total_expenses=float(row["expenses"]),
                net_flow=float(row["income"]) - float(row["expenses"]),
                transaction_count=0,
            ))

        return buckets

    def _forecast_holt_winters(
        self,
        buckets: list[TimeSeriesBucket],
        horizon_days: int,
    ) -> list[CategoryProjection]:
        """Forecast using Holt-Winters triple exponential smoothing.

        Args:
            buckets: Historical monthly data.
            horizon_days: Forecast horizon.

        Returns:
            List of CategoryProjection for each future month.
        """
        if not buckets:
            return []

        # Extract income and expense series
        income_series = [b.total_income for b in buckets]
        expense_series = [b.total_expenses for b in buckets]

        # Determine seasonal period (quarterly = 4 months)
        seasonal_period = 4
        if len(buckets) < 2 * seasonal_period:
            # Not enough data for seasonality, use simple exponential smoothing
            logger.info("Insufficient data for seasonality, using simple smoothing")
            seasonal_period = 0

        # Forecast income
        income_forecast = self._hw_forecast(income_series, horizon_days, seasonal_period)

        # Forecast expenses
        expense_forecast = self._hw_forecast(expense_series, horizon_days, seasonal_period)

        # Build projections
        projections = []
        current_date = buckets[-1].end_date + timedelta(days=1)

        for i in range(horizon_days):
            if i > 0 and i % 30 == 0:
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)

            month_idx = i // 30
            income = income_forecast[month_idx] if month_idx < len(income_forecast) else income_forecast[-1]
            expenses = expense_forecast[month_idx] if month_idx < len(expense_forecast) else expense_forecast[-1]

            projections.append(CategoryProjection(
                date=current_date,
                income=round(income, 2),
                expenses=round(expenses, 2),
                net_flow=round(income - expenses, 2),
                method="holt_winters",
                confidence_lower=0.0,  # Filled later
                confidence_upper=0.0,  # Filled later
            ))

        return projections

    def _hw_forecast(
        self,
        series: list[float],
        horizon: int,
        seasonal_period: int,
    ) -> list[float]:
        """Apply Holt-Winters forecasting to a series.

        Args:
            series: Historical data points.
            horizon: Number of future points to forecast.
            seasonal_period: Seasonal period (0 for no seasonality).

        Returns:
            Forecasted values.
        """
        if not series:
            return [0.0] * horizon

        # Initialize parameters
        alpha = 0.3
        beta = 0.1
        gamma = 0.1

        n = len(series)

        if seasonal_period == 0 or n < 2:
            # Simple exponential smoothing
            level = series[0]
            forecast = [level]
            for i in range(1, n):
                level = alpha * series[i] + (1 - alpha) * level
                forecast.append(level)

            # Extend forecast
            current_level = level
            for _ in range(horizon):
                current_level = alpha * current_level + (1 - alpha) * current_level
                forecast.append(current_level)

            return forecast[1:]  # Remove the last historical point

        # Triple exponential smoothing
        # Initialize level, trend, and seasonal components
        level = sum(series[:seasonal_period]) / seasonal_period
        trend = (sum(series[seasonal_period:]) / (n - seasonal_period) -
                 sum(series[:seasonal_period]) / seasonal_period) / (n - seasonal_period)

        # Initialize seasonal indices
        seasonal = [0.0] * seasonal_period
        for i in range(seasonal_period):
            indices = list(range(i, n, seasonal_period))
            if indices:
                seasonal[i] = (series[i] - level) if len(indices) == 1 else \
                    sum(series[j] - level for j in indices) / len(indices)

        # Fit the model
        for i in range(n):
            s_idx = i % seasonal_period
            old_level = level
            level = alpha * (series[i] - seasonal[s_idx]) + (1 - alpha) * (level + trend)
            trend = beta * (level - old_level) + (1 - beta) * trend
            seasonal[s_idx] = gamma * (series[i] - level) + (1 - gamma) * seasonal[s_idx]

        # Forecast future values
        forecast = []
        for h in range(horizon):
            s_idx = (n + h) % seasonal_period
            value = level + (h + 1) * trend + seasonal[s_idx]
            forecast.append(max(0.0, value))  # No negative income/expenses

        return forecast

    def _forecast_linear(
        self,
        buckets: list[TimeSeriesBucket],
        horizon_days: int,
    ) -> list[CategoryProjection]:
        """Forecast using linear regression.

        Args:
            buckets: Historical monthly data.
            horizon_days: Forecast horizon.

        Returns:
            List of CategoryProjection for each future month.
        """
        if len(buckets) < 2:
            return self._forecast_holt_winters(buckets, horizon_days)

        # Prepare data for regression
        x = list(range(len(buckets)))
        y_income = [b.total_income for b in buckets]
        y_expenses = [b.total_expenses for b in buckets]

        # Linear regression: y = mx + b
        income_slope, income_intercept = self._linear_regression(x, y_income)
        expense_slope, expense_intercept = self._linear_regression(x, y_expenses)

        # Determine trend direction
        income_trend = "increasing" if income_slope > 0 else "decreasing"
        expense_trend = "increasing" if expense_slope > 0 else "decreasing"

        # Build projections
        projections = []
        current_date = buckets[-1].end_date + timedelta(days=1)

        for i in range(horizon_days):
            if i > 0 and i % 30 == 0:
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)

            month_idx = len(buckets) + (i // 30)
            income = max(0.0, income_slope * month_idx + income_intercept)
            expenses = max(0.0, expense_slope * month_idx + expense_intercept)

            projections.append(CategoryProjection(
                date=current_date,
                income=round(income, 2),
                expenses=round(expenses, 2),
                net_flow=round(income - expenses, 2),
                method="linear_regression",
                confidence_lower=0.0,
                confidence_upper=0.0,
            ))

        return projections

    def _linear_regression(
        self,
        x: list[int],
        y: list[float],
    ) -> tuple[float, float]:
        """Calculate linear regression coefficients.

        Returns:
            (slope, intercept)
        """
        n = len(x)
        if n < 2:
            return (0.0, y[0] if y else 0.0)

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return (0.0, sum_y / n)

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        return slope, intercept

    def _calculate_confidence_intervals(
        self,
        projections: list[CategoryProjection],
        historical: list[TimeSeriesBucket],
    ) -> list[CategoryProjection]:
        """Calculate confidence intervals for projections.

        Uses historical variance to estimate uncertainty.
        """
        if not projections or not historical:
            return projections

        # Calculate historical standard deviation
        income_std = self._std([b.total_income for b in historical])
        expense_std = self._std([b.total_expenses for b in historical])

        # Confidence intervals widen with time
        for i, proj in enumerate(projections):
            time_factor = math.sqrt(i + 1)
            proj.confidence_lower = round(proj.income - 1.96 * income_std * time_factor, 2)
            proj.confidence_upper = round(proj.income + 1.96 * income_std * time_factor, 2)

        return projections

    def _std(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _empty_forecast(
        self,
        end_date: date,
        horizon_days: int,
    ) -> ForecastResult:
        """Return an empty forecast when insufficient data."""
        projections = []
        current_date = end_date + timedelta(days=1)
        for i in range(horizon_days):
            if i > 0 and i % 30 == 0:
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)
            projections.append(CategoryProjection(
                date=current_date,
                income=0.0,
                expenses=0.0,
                net_flow=0.0,
                method="insufficient_data",
                confidence_lower=0.0,
                confidence_upper=0.0,
            ))

        return ForecastResult(
            start_date=end_date - timedelta(days=365),
            end_date=end_date,
            forecast_end=end_date + timedelta(days=horizon_days),
            projections=projections,
            total_forecasted_income=0.0,
            total_forecasted_expenses=0.0,
            net_forecast=0.0,
            confidence_lower=0.0,
            confidence_upper=0.0,
        )

    def get_trend_analysis(
        self,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ForecastTrend:
        """Analyze income/expense trends for a category.

        Args:
            category: Category to analyze.
            start_date: Start of analysis window.
            end_date: End of analysis window.

        Returns:
            ForecastTrend with trend direction and statistics.
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        buckets = self._get_historical_data(start_date, end_date, category)

        if len(buckets) < 3:
            return ForecastTrend(
                category=category or "All",
                trend="insufficient_data",
                monthly_avg_income=0.0,
                monthly_avg_expenses=0.0,
                income_trend_slope=0.0,
                expense_trend_slope=0.0,
                r_squared=0.0,
            )

        income_series = [b.total_income for b in buckets]
        expense_series = [b.total_expenses for b in buckets]
        x = list(range(len(buckets)))

        income_slope, _ = self._linear_regression(x, income_series)
        expense_slope, _ = self._linear_regression(x, expense_series)

        # Calculate R-squared for income
        income_r2 = self._r_squared(x, income_series)
        expense_r2 = self._r_squared(x, expense_series)

        # Determine trend direction
        income_trend = "increasing" if income_slope > 0 else "decreasing" if income_slope < 0 else "stable"
        expense_trend = "increasing" if expense_slope > 0 else "decreasing" if expense_slope < 0 else "stable"

        return ForecastTrend(
            category=category or "All",
            trend=f"income_{income_trend}_expenses_{expense_trend}",
            monthly_avg_income=round(sum(income_series) / len(income_series), 2),
            monthly_avg_expenses=round(sum(expense_series) / len(expense_series), 2),
            income_trend_slope=round(income_slope, 2),
            expense_trend_slope=round(expense_slope, 2),
            r_squared=round((income_r2 + expense_r2) / 2, 4),
        )

    def _r_squared(self, x: list[int], y: list[float]) -> float:
        """Calculate R-squared for a regression."""
        n = len(x)
        if n < 2:
            return 0.0

        y_mean = sum(y) / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)

        slope, intercept = self._linear_regression(x, y)
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((yi - ypi) ** 2 for yi, ypi in zip(y, y_pred))

        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0

        return 1.0 - (ss_res / ss_tot)
