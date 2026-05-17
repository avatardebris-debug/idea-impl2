"""Holt-Winters (Triple Exponential Smoothing) forecaster."""

from __future__ import annotations

import math
from typing import Optional

from src.forecasting.models import ForecastPoint, ForecastResult


class HoltWintersForecaster:
    """Implements Holt-Winters triple exponential smoothing for forecasting."""

    def __init__(
        self,
        alpha: float = 0.3,
        beta: float = 0.1,
        gamma: float = 0.1,
        seasonal_period: int = 4,
    ):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.seasonal_period = seasonal_period
        self._level: float = 0.0
        self._trend: float = 0.0
        self._seasonal: list[float] = []
        self._training_rmse: float = 0.0
        self._test_rmse: float = 0.0
        self._fitted_values: list[float] = []

    def fit_predict(
        self, data: list[float], n_steps: int = 5
    ) -> ForecastResult:
        """Fit the Holt-Winters model and generate forecasts.

        Args:
            data: Historical time series data.
            n_steps: Number of future periods to forecast.

        Returns:
            ForecastResult with predictions and model metrics.
        """
        if not data:
            raise ValueError("Data cannot be empty")

        n = len(data)
        m = self.seasonal_period

        # Initialize level, trend, and seasonal components
        self._level = data[0]
        self._trend = (data[m] - data[0]) / m if n > m else 0.0

        # Initialize seasonal indices
        if n >= m:
            avg_seasonal = sum(data[:m]) / m
            self._seasonal = [data[i] - avg_seasonal for i in range(m)]
        else:
            self._seasonal = [0.0] * m

        # Fit the model
        self._fitted_values = []
        for i in range(n):
            level = self._level
            trend = self._trend
            seasonal = self._seasonal[i % m]

            # Store fitted value
            self._fitted_values.append(level + trend + seasonal)

            # Update components
            new_level = self.alpha * (data[i] - seasonal) + (1 - self.alpha) * (level + trend)
            new_trend = self.beta * (new_level - level) + (1 - self.beta) * trend
            new_seasonal = self.gamma * (data[i] - new_level) + (1 - self.gamma) * seasonal

            self._level = new_level
            self._trend = new_trend
            self._seasonal[i % m] = new_seasonal

        # Calculate training RMSE
        if n > 0:
            mse = sum((data[i] - self._fitted_values[i]) ** 2 for i in range(n)) / n
            self._training_rmse = math.sqrt(mse)

        # Generate forecasts
        forecasts = []
        for i in range(n_steps):
            forecast_value = self._level + (i + 1) * self._trend + self._seasonal[i % m]
            forecasts.append(forecast_value)

        # Calculate test RMSE (using last portion as validation)
        if n > m:
            test_start = max(n - m, 1)
            test_mse = sum(
                (data[i] - self._fitted_values[i]) ** 2 for i in range(test_start, n)
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
            trend_slope=self._trend,
            seasonal_pattern="periodic",
        )

    @property
    def trend_slope(self) -> float:
        """Return the current trend slope."""
        return self._trend

    @property
    def seasonal_pattern(self) -> str:
        """Return the detected seasonal pattern."""
        return "periodic"
