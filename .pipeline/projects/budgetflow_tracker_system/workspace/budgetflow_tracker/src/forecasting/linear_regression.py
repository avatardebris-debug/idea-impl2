"""Linear Regression forecaster."""

from __future__ import annotations

import math
from typing import Optional

from src.forecasting.models import ForecastPoint, ForecastResult


class LinearRegressionForecaster:
    """Simple linear regression forecaster."""

    def __init__(self):
        self._slope: float = 0.0
        self._intercept: float = 0.0
        self._r_squared: float = 0.0
        self._training_rmse: float = 0.0
        self._test_rmse: float = 0.0

    def fit_predict(
        self, data: list[float], n_steps: int = 5
    ) -> ForecastResult:
        """Fit a linear regression model and generate forecasts.

        Args:
            data: Historical time series data.
            n_steps: Number of future periods to forecast.

        Returns:
            ForecastResult with predictions and model metrics.
        """
        if not data:
            raise ValueError("Data cannot be empty")

        n = len(data)
        x = list(range(n))

        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(data) / n

        # Calculate slope and intercept
        numerator = sum((x[i] - x_mean) * (data[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            self._slope = 0.0
            self._intercept = y_mean
        else:
            self._slope = numerator / denominator
            self._intercept = y_mean - self._slope * x_mean

        # Calculate R-squared
        y_pred = [self._slope * x[i] + self._intercept for i in range(n)]
        ss_res = sum((data[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((data[i] - y_mean) ** 2 for i in range(n))
        self._r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Calculate training RMSE
        self._training_rmse = math.sqrt(ss_res / n) if n > 0 else 0.0

        # Generate forecasts
        forecasts = []
        for i in range(n_steps):
            forecast_value = self._slope * (n + i) + self._intercept
            forecasts.append(forecast_value)

        # Calculate test RMSE (using last 20% as validation)
        test_start = max(int(n * 0.8), 1)
        test_mse = sum(
            (data[i] - (self._slope * i + self._intercept)) ** 2
            for i in range(test_start, n)
        ) / (n - test_start)
        self._test_rmse = math.sqrt(test_mse)

        # Create ForecastResult
        forecast_points = [
            ForecastPoint(
                predicted_value=fp,
                lower_bound=fp - 2 * self._test_rmse if self._test_rmse > 0 else fp - 10,
                upper_bound=fp + 2 * self._test_rmse if self._test_rmse > 0 else fp + 10,
            )
            for fp in forecasts
        ]

        return ForecastResult(
            forecasts=forecast_points,
            training_rmse=self._training_rmse,
            test_rmse=self._test_rmse,
            trend_slope=self._slope,
            seasonal_pattern="none",
        )

    @property
    def trend_slope(self) -> float:
        """Return the current trend slope."""
        return self._slope

    @property
    def r_squared(self) -> float:
        """Return the R-squared value."""
        return self._r_squared
