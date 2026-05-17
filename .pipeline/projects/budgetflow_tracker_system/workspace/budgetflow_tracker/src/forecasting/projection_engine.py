"""Cash flow projection engine for BudgetFlow Tracker."""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from src.forecasting.holt_winters import HoltWintersForecaster
from src.forecasting.linear_regression import LinearRegressionForecaster
from src.forecasting.model_selector import ModelSelector
from src.forecasting.pattern_detector import RecurringPatternDetector
from src.forecasting.anomaly_detector import AnomalyDetector
from src.forecasting.models import (
    CashFlowProjection,
    CategoryProjection,
    ForecastPoint,
    RecurringPattern,
    AnomalyFlag,
)

logger = logging.getLogger(__name__)


class CashFlowProjectionEngine:
    """Combines time-bucketed data, forecasting models, and recurring patterns
    to produce forward-looking cash flow projections."""

    def __init__(
        self,
        seasonal_period: int = 30,
        sigma_threshold: float = 2.0,
        min_recurring_occurrences: int = 3,
    ):
        self.model_selector = ModelSelector(seasonal_period=seasonal_period)
        self.anomaly_detector = AnomalyDetector(sigma_threshold=sigma_threshold)
        self.pattern_detector = RecurringPatternDetector(
            min_occurrences=min_recurring_occurrences
        )

    def generate_projection(
        self,
        transactions: list[dict],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        forecast_days: int = 30,
    ) -> CashFlowProjection:
        """
        Generate a cash flow projection.

        Args:
            transactions: Historical transactions.
            start_date: Start of historical period.
            end_date: End of historical period.
            forecast_days: Number of days to forecast into the future.

        Returns:
            CashFlowProjection with daily forecasts, category breakdowns,
            recurring patterns, and anomalies.
        """
        return self.project(transactions, start_date, end_date, forecast_days)

    def project(
        self,
        transactions: list[dict],
        start_date: date,
        end_date: date,
        forecast_days: int = 30,
    ) -> CashFlowProjection:
        """
        Generate a cash flow projection.

        Args:
            transactions: Historical transactions.
            start_date: Start of historical period.
            end_date: End of historical period.
            forecast_days: Number of days to forecast into the future.

        Returns:
            CashFlowProjection with daily forecasts, category breakdowns,
            recurring patterns, and anomalies.
        """
        # 1. Detect anomalies in historical data
        anomalies = self.anomaly_detector.detect_anomalies(transactions)

        # 2. Detect recurring patterns
        recurring_patterns = self.pattern_detector.detect_patterns(transactions)

        # 3. Prepare time-bucketed data for forecasting
        # Group transactions by date for daily totals
        daily_totals: dict[date, float] = defaultdict(float)
        daily_categories: dict[date, dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for txn in transactions:
            d = txn["date"]
            if isinstance(d, str):
                d = date.fromisoformat(d)
            amount = float(abs(txn["amount"]))
            daily_totals[d] += amount
            category = txn.get("category_name", "uncategorized")
            daily_categories[d][category] += amount

        # Create sorted list of dates and values
        all_dates = sorted(daily_totals.keys())
        if not all_dates:
            raise ValueError("No transactions to forecast")

        # Ensure we have enough data points
        if len(all_dates) < 2:
            raise ValueError("Need at least 2 days of transaction data")

        # Fill in missing dates with zeros for contiguous time series
        first_date = all_dates[0]
        last_date = all_dates[-1]
        full_dates = []
        current = first_date
        while current <= last_date:
            full_dates.append(current)
            current += timedelta(days=1)

        values = [daily_totals.get(d, 0.0) for d in full_dates]
        dates = full_dates

        # 4. Select best forecasting model and generate forecasts
        forecast_steps = forecast_days
        forecast_result = self.model_selector.select_and_forecast(
            values, dates, forecast_steps
        )

        # 5. Build daily forecast points
        daily_forecasts: list[ForecastPoint] = []
        for fp in forecast_result.forecasts:
            daily_forecasts.append(fp)

        # 6. Calculate category projections
        category_projections: list[CategoryProjection] = []
        if daily_categories:
            # Get all unique categories
            all_categories = set()
            for cat_dict in daily_categories.values():
                all_categories.update(cat_dict.keys())

            for category in sorted(all_categories):
                cat_values = [daily_categories[d].get(category, 0.0) for d in dates]
                cat_dates = dates

                # Forecast category values
                if len(cat_values) >= 2:
                    cat_forecasts = self._forecast_category(cat_values, cat_dates, forecast_steps)
                else:
                    cat_forecasts = []

                # Calculate total projected amount
                total_projected = sum(float(fp.predicted_value) for fp in cat_forecasts)

                category_projections.append(CategoryProjection(
                    category_name=category,
                    daily_forecasts=cat_forecasts,
                ))

        # 7. Calculate overall summary statistics
        total_projected_income = Decimal("0")
        total_projected_expenses = Decimal("0")
        for fp in daily_forecasts:
            # Assume positive values are expenses, negative are income (or vice versa)
            # For simplicity, use absolute values
            total_projected_income += fp.predicted_value
            total_projected_expenses += fp.predicted_value

        # Calculate rolling average and trend
        rolling_avg = self._calculate_rolling_average(values, window=7)
        trend_slope = forecast_result.trend_slope or 0.0

        return CashFlowProjection(
            start_date=start_date,
            end_date=end_date,
            window_days=forecast_days,
            category_projections=category_projections,
            aggregate_daily=daily_forecasts,
            recurring_patterns=recurring_patterns,
            anomalies=anomalies,
        )

    def _forecast_category(
        self,
        values: list[float],
        dates: list[date],
        steps: int,
    ) -> list[ForecastPoint]:
        """Forecast a single category's values."""
        if len(values) < 2:
            return []

        try:
            forecaster = HoltWintersForecaster(seasonal_period=min(30, len(values) // 2))
            forecaster.fit(values, dates)
            return forecaster.forecast(steps)
        except Exception:
            try:
                forecaster = LinearRegressionForecaster()
                forecaster.fit(values, dates)
                return forecaster.forecast(steps)
            except Exception:
                return []

    def _calculate_rolling_average(self, values: list[float], window: int = 7) -> float:
        """Calculate the last rolling average."""
        if not values:
            return 0.0
        recent = values[-window:] if len(values) >= window else values
        return sum(recent) / len(recent)

    def _std(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5
