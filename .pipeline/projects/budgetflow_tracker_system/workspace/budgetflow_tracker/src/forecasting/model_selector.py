"""Model selector that picks the best forecasting model."""

from __future__ import annotations

from src.forecasting.holt_winters import HoltWintersForecaster
from src.forecasting.linear_regression import LinearRegressionForecaster
from src.forecasting.models import ForecastResult


class ModelSelector:
    """Selects the best forecasting model based on data characteristics."""

    def __init__(self):
        self._selected_model: str = "linear_regression"

    def select_best_model(
        self, data: list[float], n_steps: int = 5
    ) -> ForecastResult:
        """Select the best model and generate forecasts.

        Args:
            data: Historical time series data.
            n_steps: Number of future periods to forecast.

        Returns:
            ForecastResult from the best model.
        """
        if not data:
            raise ValueError("Data cannot be empty")

        # Fit both models
        hw_forecaster = HoltWintersForecaster()
        hw_result = hw_forecaster.fit_predict(data, n_steps)

        lr_forecaster = LinearRegressionForecaster()
        lr_result = lr_forecaster.fit_predict(data, n_steps)

        # Select based on RMSE (lower is better)
        if hw_result.test_rmse < lr_result.test_rmse:
            self._selected_model = "HoltWinters"
            return hw_result
        else:
            self._selected_model = "LinearRegression"
            return lr_result

    @property
    def selected_model(self) -> str:
        """Return the name of the selected model."""
        return self._selected_model
