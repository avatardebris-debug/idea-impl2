"""Tests for earnings prediction module."""

import pytest
from forensic.earnings import (
    EarningsPoint,
    PredictionResult,
    EarningsPredictionReport,
    predict_earnings,
    predict_with_linear_regression,
    predict_with_moving_average,
    _linear_regression,
    _standard_error,
    _t_value,
)


class TestLinearRegression:
    def test_perfect_line(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        intercept, slope = _linear_regression(x, y)
        assert intercept == pytest.approx(0.0)
        assert slope == pytest.approx(2.0)

    def test_line_with_intercept(self):
        x = [1.0, 2.0, 3.0]
        y = [3.0, 5.0, 7.0]
        intercept, slope = _linear_regression(x, y)
        assert intercept == pytest.approx(1.0)
        assert slope == pytest.approx(2.0)

    def test_insufficient_data(self):
        x = [1.0]
        y = [2.0]
        intercept, slope = _linear_regression(x, y)
        assert intercept == 0.0
        assert slope == 0.0

    def test_constant_y(self):
        x = [1.0, 2.0, 3.0]
        y = [5.0, 5.0, 5.0]
        intercept, slope = _linear_regression(x, y)
        assert slope == pytest.approx(0.0)
        assert intercept == pytest.approx(5.0)


class TestStandardError:
    def test_perfect_fit(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        se = _standard_error(x, y, 0.0, 2.0)
        assert se == pytest.approx(0.0)

    def test_with_noise(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.1, 3.9, 6.2, 7.8, 10.1]
        intercept, slope = _linear_regression(x, y)
        se = _standard_error(x, y, intercept, slope)
        assert se > 0

    def test_insufficient_data(self):
        x = [1.0, 2.0]
        y = [2.0, 4.0]
        se = _standard_error(x, y, 0.0, 2.0)
        assert se == pytest.approx(0.0)


class TestTValue:
    def test_90_percent(self):
        assert _t_value(0.90, 10) == pytest.approx(1.645)

    def test_95_percent(self):
        assert _t_value(0.95, 10) == pytest.approx(1.96)

    def test_99_percent(self):
        assert _t_value(0.99, 10) == pytest.approx(2.576)

    def test_default(self):
        assert _t_value(0.97, 10) == pytest.approx(1.96)


class TestPredictWithLinearRegression:
    def test_basic_prediction(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, 110.0),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", 2.0, 120.0),
            EarningsPoint("AAPL", "001", "004", "2023-Q4", "2023-12-01", 2.2, 130.0),
        ]
        result = predict_with_linear_regression(points, 4, 0.95)
        assert result is not None
        assert result.predicted_eps is not None
        assert result.predicted_revenue is not None
        assert result.model == "linear_regression"
        assert result.data_points == 4

    def test_insufficient_data(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, 110.0),
        ]
        result = predict_with_linear_regression(points, 2, 0.95)
        assert result is None

    def test_eps_only(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, None),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, None),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", 2.0, None),
        ]
        result = predict_with_linear_regression(points, 3, 0.95)
        assert result is not None
        assert result.predicted_eps is not None
        assert result.predicted_revenue is None

    def test_revenue_only(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", None, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", None, 110.0),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", None, 120.0),
        ]
        result = predict_with_linear_regression(points, 3, 0.95)
        assert result is not None
        assert result.predicted_eps is None
        assert result.predicted_revenue is not None


class TestPredictWithMovingAverage:
    def test_basic_prediction(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, 110.0),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", 2.0, 120.0),
            EarningsPoint("AAPL", "001", "004", "2023-Q4", "2023-12-01", 2.2, 130.0),
        ]
        result = predict_with_moving_average(points, 4, 0.95)
        assert result is not None
        assert result.predicted_eps == pytest.approx((1.5 + 1.8 + 2.0 + 2.2) / 4)
        assert result.predicted_revenue == pytest.approx((100 + 110 + 120 + 130) / 4)
        assert result.model == "moving_average"

    def test_insufficient_data(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
        ]
        result = predict_with_moving_average(points, 4, 0.95)
        assert result is None

    def test_window_less_than_data(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, 110.0),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", 2.0, 120.0),
        ]
        result = predict_with_moving_average(points, 2, 0.95)
        assert result is not None
        assert result.predicted_eps == pytest.approx((1.8 + 2.0) / 2)


class TestPredictEarnings:
    def test_linear_regression_model(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, 110.0),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", 2.0, 120.0),
        ]
        report = predict_earnings(points, model="linear_regression", confidence=0.95)
        assert report.ticker == "AAPL"
        assert len(report.predictions) == 1
        assert report.predictions[0].model == "linear_regression"

    def test_moving_average_model(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, 110.0),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", 2.0, 120.0),
        ]
        report = predict_earnings(points, model="moving_average", confidence=0.95)
        assert report.ticker == "AAPL"
        assert len(report.predictions) == 1
        assert report.predictions[0].model == "moving_average"

    def test_insufficient_data(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
        ]
        report = predict_earnings(points, model="linear_regression", confidence=0.95)
        assert len(report.warnings) > 0

    def test_empty_data(self):
        report = predict_earnings([], model="linear_regression", confidence=0.95)
        assert len(report.warnings) > 0
        assert report.ticker == ""

    def test_unknown_model(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, 110.0),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", 2.0, 120.0),
        ]
        report = predict_earnings(points, model="unknown", confidence=0.95)
        assert len(report.warnings) > 0

    def test_to_dict(self):
        points = [
            EarningsPoint("AAPL", "001", "001", "2023-Q1", "2023-03-01", 1.5, 100.0),
            EarningsPoint("AAPL", "001", "002", "2023-Q2", "2023-06-01", 1.8, 110.0),
            EarningsPoint("AAPL", "001", "003", "2023-Q3", "2023-09-01", 2.0, 120.0),
        ]
        report = predict_earnings(points, model="linear_regression", confidence=0.95)
        d = report.to_dict()
        assert d["ticker"] == "AAPL"
        assert "predictions" in d
        assert "warnings" in d


class TestPredictionResult:
    def test_to_dict(self):
        result = PredictionResult(
            ticker="AAPL",
            cik="001",
            predicted_eps=2.0,
            predicted_revenue=100.0,
            eps_confidence_low=1.5,
            eps_confidence_high=2.5,
            revenue_confidence_low=90.0,
            revenue_confidence_high=110.0,
            model="linear_regression",
            data_points=4,
            confidence_level=0.95,
        )
        d = result.to_dict()
        assert d["ticker"] == "AAPL"
        assert d["predicted_eps"] == 2.0
        assert d["eps_confidence_interval"] == [1.5, 2.5]
        assert d["revenue_confidence_interval"] == [90.0, 110.0]
