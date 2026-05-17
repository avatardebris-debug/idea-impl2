"""Comprehensive tests for the forecasting module."""

import os
import sys
import unittest
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

# Add workspace to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.forecasting.models import (
    TimeSeriesBucket,
    ForecastPoint,
    ForecastResult,
    RecurringPattern,
    AnomalyFlag,
    CategoryProjection,
    CashFlowProjection,
    ChartOutput,
    RecurringPatternType,
)
from src.forecasting.time_bucket import TimeBucketEngine
from src.forecasting.holt_winters import HoltWintersForecaster
from src.forecasting.linear_regression import LinearRegressionForecaster
from src.forecasting.model_selector import ModelSelector
from src.forecasting.pattern_detector import RecurringPatternDetector
from src.forecasting.anomaly_detector import AnomalyDetector
from src.forecasting.projection_engine import CashFlowProjectionEngine
from src.forecasting.visualization import ChartGenerator


def _make_transaction(
    txn_id: int,
    txn_date: date,
    amount: float,
    description: str = "Test Transaction",
    merchant: str = "Test Merchant",
    category: str = "Food",
    txn_type: str = "debit",
) -> dict:
    """Helper to create a transaction dict."""
    return {
        "id": txn_id,
        "date": txn_date,
        "amount": amount,
        "description": description,
        "merchant": merchant,
        "category_name": category,
        "transaction_type": txn_type,
    }


class TestTimeBucketEngine(unittest.TestCase):
    """Tests for TimeBucketEngine."""

    def setUp(self):
        self.engine = TimeBucketEngine(interval_type="daily")

    def test_daily_bucketing(self):
        """Test daily time bucketing."""
        transactions = [
            _make_transaction(1, date(2024, 1, 1), 100.0, txn_type="debit"),
            _make_transaction(2, date(2024, 1, 1), 50.0, txn_type="credit"),
            _make_transaction(3, date(2024, 1, 2), 75.0, txn_type="debit"),
        ]
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)
        buckets = self.engine.bucket_transactions(transactions, start, end)

        self.assertEqual(len(buckets), 3)
        self.assertEqual(buckets[0].start_date, date(2024, 1, 1))
        self.assertEqual(buckets[0].end_date, date(2024, 1, 1))
        self.assertEqual(buckets[0].total_income, 50.0)
        self.assertEqual(buckets[0].total_expenses, 100.0)
        self.assertEqual(buckets[1].start_date, date(2024, 1, 2))
        self.assertEqual(buckets[1].end_date, date(2024, 1, 2))
        self.assertEqual(buckets[1].total_expenses, 75.0)
        self.assertEqual(buckets[2].start_date, date(2024, 1, 3))
        self.assertEqual(buckets[2].end_date, date(2024, 1, 3))
        self.assertEqual(buckets[2].total_income, 0.0)
        self.assertEqual(buckets[2].total_expenses, 0.0)

    def test_weekly_bucketing(self):
        """Test weekly time bucketing."""
        engine = TimeBucketEngine(interval_type="weekly")
        transactions = [
            _make_transaction(1, date(2024, 1, 1), 100.0, txn_type="debit"),
            _make_transaction(2, date(2024, 1, 5), 50.0, txn_type="debit"),
            _make_transaction(3, date(2024, 1, 8), 75.0, txn_type="debit"),
        ]
        start = date(2024, 1, 1)
        end = date(2024, 1, 14)
        buckets = engine.bucket_transactions(transactions, start, end)

        self.assertGreaterEqual(len(buckets), 2)
        # First bucket should contain transactions from Jan 1
        first_bucket = buckets[0]
        self.assertEqual(first_bucket.start_date, date(2024, 1, 1))
        self.assertIn(first_bucket.interval_type, ("daily", "weekly"))

    def test_monthly_bucketing(self):
        """Test monthly time bucketing."""
        engine = TimeBucketEngine(interval_type="monthly")
        transactions = [
            _make_transaction(1, date(2024, 1, 15), 100.0, txn_type="debit"),
            _make_transaction(2, date(2024, 1, 20), 50.0, txn_type="debit"),
            _make_transaction(3, date(2024, 2, 5), 75.0, txn_type="debit"),
        ]
        start = date(2024, 1, 1)
        end = date(2024, 2, 28)
        buckets = engine.bucket_transactions(transactions, start, end)

        # Should have at least 2 monthly buckets
        self.assertGreaterEqual(len(buckets), 2)
        jan_bucket = [b for b in buckets if b.start_date.month == 1]
        feb_bucket = [b for b in buckets if b.start_date.month == 2]
        self.assertGreater(len(jan_bucket), 0)
        self.assertGreater(len(feb_bucket), 0)

    def test_empty_transactions(self):
        """Test bucketing with no transactions."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)
        buckets = self.engine.bucket_transactions([], start, end)

        self.assertEqual(len(buckets), 3)
        for bucket in buckets:
            self.assertEqual(bucket.total_income, 0.0)
            self.assertEqual(bucket.total_expenses, 0.0)
            self.assertEqual(bucket.transaction_count, 0)


class TestHoltWintersForecaster(unittest.TestCase):
    """Tests for HoltWintersForecaster."""

    def test_forecast_constant(self):
        """Test forecasting with constant data."""
        data = [100.0] * 30
        forecaster = HoltWintersForecaster()
        result = forecaster.fit_predict(data, n_steps=7)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.forecasts), 7)
        # Values should be close to the constant
        for fp in result.forecasts:
            self.assertAlmostEqual(float(fp.predicted_value), 100.0, delta=5.0)

    def test_forecast_simple_trend(self):
        """Test forecasting with linear trend."""
        data = [float(i) for i in range(1, 31)]  # 1, 2, 3, ..., 30
        forecaster = HoltWintersForecaster()
        result = forecaster.fit_predict(data, n_steps=5)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.forecasts), 5)
        # Trend should be positive
        self.assertGreater(result.trend_slope, 0)

    def test_forecast_with_seasonality(self):
        """Test forecasting with seasonal data."""
        # Create seasonal data: 10, 20, 30, 20, 10, 20, 30, 20, ...
        data = []
        for i in range(60):
            cycle = i % 4
            if cycle == 0:
                data.append(10.0)
            elif cycle == 1:
                data.append(20.0)
            elif cycle == 2:
                data.append(30.0)
            else:
                data.append(20.0)

        forecaster = HoltWintersForecaster()
        result = forecaster.fit_predict(data, n_steps=8)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.forecasts), 8)

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        data = [100.0, 100.0]
        forecaster = HoltWintersForecaster()
        result = forecaster.fit_predict(data, n_steps=5)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.forecasts), 5)


class TestLinearRegressionForecaster(unittest.TestCase):
    """Tests for LinearRegressionForecaster."""

    def test_forecast_constant(self):
        """Test forecasting with constant data."""
        data = [100.0] * 30
        forecaster = LinearRegressionForecaster()
        result = forecaster.fit_predict(data, n_steps=7)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.forecasts), 7)
        for fp in result.forecasts:
            self.assertAlmostEqual(float(fp.predicted_value), 100.0, delta=5.0)

    def test_forecast_linear_trend(self):
        """Test forecasting with linear trend."""
        data = [float(i) for i in range(1, 31)]
        forecaster = LinearRegressionForecaster()
        result = forecaster.fit_predict(data, n_steps=5)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.forecasts), 5)
        self.assertGreater(result.trend_slope, 0)

    def test_model_info(self):
        """Test model info output."""
        data = [float(i) for i in range(1, 31)]
        forecaster = LinearRegressionForecaster()
        result = forecaster.fit_predict(data, n_steps=5)

        self.assertEqual(result.model_name, "LinearRegression")
        self.assertGreater(result.training_rmse, 0)
        self.assertGreater(result.test_rmse, 0)


class TestModelSelector(unittest.TestCase):
    """Tests for ModelSelector."""

    def test_select_best_model_linear(self):
        """Test model selection with linear data."""
        data = [float(i) for i in range(1, 31)]
        selector = ModelSelector()
        result = selector.select_best_model(data, n_steps=5)

        self.assertIsNotNone(result)
        self.assertGreater(len(result.forecasts), 0)

    def test_select_best_model_seasonal(self):
        """Test model selection with seasonal data."""
        data = []
        for i in range(60):
            cycle = i % 4
            if cycle == 0:
                data.append(10.0)
            elif cycle == 1:
                data.append(20.0)
            elif cycle == 2:
                data.append(30.0)
            else:
                data.append(20.0)

        selector = ModelSelector()
        result = selector.select_best_model(data, n_steps=8)

        self.assertIsNotNone(result)
        self.assertGreater(len(result.forecasts), 0)


class TestRecurringPatternDetector(unittest.TestCase):
    """Tests for RecurringPatternDetector."""

    def setUp(self):
        self.detector = RecurringPatternDetector()

    def test_detect_monthly_pattern(self):
        """Test detection of monthly recurring pattern."""
        transactions = []
        for i in range(6):
            txn_date = date(2024, 1, 1) + timedelta(days=30 * i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 100.0,
                description="Netflix Subscription",
                merchant="Netflix",
            ))

        patterns = self.detector.detect_patterns(transactions, min_occurrences=3)
        self.assertGreater(len(patterns), 0)

        pattern = patterns[0]
        self.assertEqual(pattern.merchant, "Netflix")
        self.assertEqual(pattern.interval_days, 30)
        self.assertEqual(pattern.pattern_type, RecurringPatternType.SUBSCRIPTION)

    def test_detect_weekly_pattern(self):
        """Test detection of weekly recurring pattern."""
        transactions = []
        for i in range(4):
            txn_date = date(2024, 1, 1) + timedelta(days=7 * i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 50.0,
                description="Weekly Grocery",
                merchant="Whole Foods",
            ))

        patterns = self.detector.detect_patterns(transactions, min_occurrences=3)
        self.assertGreater(len(patterns), 0)

        pattern = patterns[0]
        self.assertEqual(pattern.interval_days, 7)

    def test_no_recurring_pattern(self):
        """Test with no recurring patterns."""
        transactions = [
            _make_transaction(1, date(2024, 1, 1), 100.0),
            _make_transaction(2, date(2024, 1, 15), 50.0),
            _make_transaction(3, date(2024, 2, 1), 75.0),
        ]

        patterns = self.detector.detect_patterns(transactions, min_occurrences=3)
        self.assertEqual(len(patterns), 0)

    def test_pattern_classification(self):
        """Test pattern type classification."""
        transactions = []
        for i in range(12):
            txn_date = date(2024, 1, 1) + timedelta(days=30 * i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 1500.0,
                description="Monthly Rent",
                merchant="Landlord",
            ))

        patterns = self.detector.detect_patterns(transactions, min_occurrences=3)
        self.assertGreater(len(patterns), 0)
        self.assertEqual(patterns[0].pattern_type, RecurringPatternType.RENT)


class TestAnomalyDetector(unittest.TestCase):
    """Tests for AnomalyDetector."""

    def setUp(self):
        self.detector = AnomalyDetector()

    def test_detect_anomaly(self):
        """Test anomaly detection."""
        transactions = []
        for i in range(10):
            txn_date = date(2024, 1, 1) + timedelta(days=i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 100.0,
            ))
        # Add an anomalous transaction
        transactions.append(_make_transaction(
            11, date(2024, 1, 11), 1000.0,
        ))

        flags = self.detector.detect_anomalies(transactions, threshold_sigma=3.0)
        self.assertGreater(len(flags), 0)

        flag = flags[0]
        self.assertEqual(flag.transaction_id, 11)
        self.assertEqual(flag.severity, "critical")
        self.assertEqual(flag.anomaly_type, "amount_deviation")

    def test_multiple_anomalies(self):
        """Test detection of multiple anomalies."""
        transactions = []
        for i in range(10):
            txn_date = date(2024, 1, 1) + timedelta(days=i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 100.0,
            ))
        # Add two anomalous transactions
        transactions.append(_make_transaction(11, date(2024, 1, 11), 1000.0))
        transactions.append(_make_transaction(12, date(2024, 1, 12), -500.0))

        flags = self.detector.detect_anomalies(transactions, threshold_sigma=2.0)
        self.assertGreaterEqual(len(flags), 2)

    def test_no_anomalies(self):
        """Test with no anomalies."""
        transactions = []
        for i in range(10):
            txn_date = date(2024, 1, 1) + timedelta(days=i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 100.0,
            ))

        flags = self.detector.detect_anomalies(transactions, threshold_sigma=3.0)
        self.assertEqual(len(flags), 0)


class TestProjectionEngine(unittest.TestCase):
    """Tests for CashFlowProjectionEngine."""

    def setUp(self):
        self.engine = CashFlowProjectionEngine()

    def test_basic_projection(self):
        """Test basic cash flow projection."""
        transactions = []
        for i in range(30):
            txn_date = date(2024, 1, 1) + timedelta(days=i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 100.0,
            ))

        start = date(2024, 1, 1)
        end = date(2024, 1, 30)
        projection = self.engine.generate_projection(
            transactions, start, end, forecast_days=7
        )

        self.assertIsNotNone(projection)
        self.assertEqual(projection.start_date, start)
        self.assertEqual(projection.end_date, end)
        self.assertGreater(len(projection.aggregate_daily), 0)

    def test_projection_with_categories(self):
        """Test projection with category breakdown."""
        transactions = [
            _make_transaction(1, date(2024, 1, 1), 500.0, category="Food"),
            _make_transaction(2, date(2024, 1, 2), 300.0, category="Rent"),
            _make_transaction(3, date(2024, 1, 3), 200.0, category="Utilities"),
        ]

        start = date(2024, 1, 1)
        end = date(2024, 1, 3)
        projection = self.engine.generate_projection(
            transactions, start, end, forecast_days=3
        )

        self.assertIsNotNone(projection)
        self.assertGreater(len(projection.category_projections), 0)

    def test_projection_with_recurring_patterns(self):
        """Test projection with recurring patterns."""
        transactions = []
        for i in range(6):
            txn_date = date(2024, 1, 1) + timedelta(days=30 * i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 100.0,
                description="Netflix",
                merchant="Netflix",
            ))

        start = date(2024, 1, 1)
        end = date(2024, 1, 180)
        projection = self.engine.generate_projection(
            transactions, start, end, forecast_days=30
        )

        self.assertIsNotNone(projection)
        self.assertGreater(len(projection.recurring_patterns), 0)

    def test_projection_with_anomalies(self):
        """Test projection with anomaly detection."""
        transactions = []
        for i in range(10):
            txn_date = date(2024, 1, 1) + timedelta(days=i)
            transactions.append(_make_transaction(
                i + 1, txn_date, 100.0,
            ))
        transactions.append(_make_transaction(11, date(2024, 1, 11), 1000.0))

        start = date(2024, 1, 1)
        end = date(2024, 1, 11)
        projection = self.engine.generate_projection(
            transactions, start, end, forecast_days=3
        )

        self.assertIsNotNone(projection)
        self.assertGreater(len(projection.anomalies), 0)


class TestChartGenerator(unittest.TestCase):
    """Tests for ChartGenerator."""

    def setUp(self):
        self.generator = ChartGenerator()

    def test_generate_trend_chart(self):
        """Test trend chart generation."""
        dates = [date(2024, 1, i) for i in range(1, 8)]
        values = [100.0, 110.0, 105.0, 120.0, 115.0, 125.0, 130.0]

        chart = self.generator.generate_trend_chart(
            dates, values, "Test Trend",
            output_path="/tmp/test_trend.png"
        )

        self.assertEqual(chart.chart_type, "trend")
        self.assertEqual(chart.data_points, 7)
        self.assertEqual(chart.width, 800)
        self.assertEqual(chart.height, 600)

    def test_generate_category_chart(self):
        """Test category chart generation."""
        categories = [
            CategoryProjection(
                category_name="Food",
                is_income=False,
                daily_forecasts=[],
            ),
            CategoryProjection(
                category_name="Rent",
                is_income=False,
                daily_forecasts=[],
            ),
        ]

        chart = self.generator.generate_category_chart(
            categories, "Test Categories",
            output_path="/tmp/test_categories.png"
        )

        self.assertEqual(chart.chart_type, "category_pie")
        self.assertEqual(chart.data_points, 2)

    def test_generate_forecast_chart(self):
        """Test forecast chart generation."""
        projection = CashFlowProjection(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 30),
            window_days=30,
            aggregate_daily=[
                ForecastPoint(
                    date=date(2024, 1, i),
                    predicted_value=Decimal("100"),
                    lower_bound=Decimal("90"),
                    upper_bound=Decimal("110"),
                    confidence_level=0.95,
                )
                for i in range(1, 8)
            ],
        )

        chart = self.generator.generate_forecast_chart(
            projection, output_path="/tmp/test_forecast.png"
        )

        self.assertEqual(chart.chart_type, "forecast")
        self.assertEqual(chart.data_points, 7)

    def test_generate_all_charts(self):
        """Test generating all charts."""
        projection = CashFlowProjection(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 30),
            window_days=30,
            aggregate_daily=[
                ForecastPoint(
                    date=date(2024, 1, i),
                    predicted_value=Decimal("100"),
                    lower_bound=Decimal("90"),
                    upper_bound=Decimal("110"),
                    confidence_level=0.95,
                )
                for i in range(1, 8)
            ],
            category_projections=[
                CategoryProjection(
                    category_name="Food",
                    is_income=False,
                    daily_forecasts=[],
                ),
            ],
        )

        charts = self.generator.generate_all_charts(projection)
        self.assertEqual(len(charts), 3)


class TestModels(unittest.TestCase):
    """Tests for Pydantic models."""

    def test_time_series_bucket(self):
        """Test TimeSeriesBucket creation."""
        bucket = TimeSeriesBucket(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            interval_type="daily",
            total_income=Decimal("100"),
            total_expenses=Decimal("50"),
            transaction_count=5,
        )
        self.assertEqual(bucket.start_date, date(2024, 1, 1))
        self.assertEqual(bucket.net_flow, Decimal("50"))
        self.assertEqual(bucket.transaction_count, 5)

    def test_forecast_point(self):
        """Test ForecastPoint creation."""
        point = ForecastPoint(
            date=date(2024, 1, 15),
            predicted_value=Decimal("100"),
            lower_bound=Decimal("90"),
            upper_bound=Decimal("110"),
            confidence_level=0.95,
        )
        self.assertEqual(point.date, date(2024, 1, 15))
        self.assertEqual(point.confidence_level, 0.95)

    def test_forecast_result(self):
        """Test ForecastResult creation."""
        result = ForecastResult(
            model_name="HoltWinters",
            forecasts=[],
            training_rmse=5.0,
            test_rmse=6.0,
            trend_slope=10.0,
            seasonal_pattern="monthly",
        )
        self.assertEqual(result.model_name, "HoltWinters")
        self.assertEqual(result.trend_slope, 10.0)

    def test_recurring_pattern(self):
        """Test RecurringPattern creation."""
        pattern = RecurringPattern(
            merchant="Netflix",
            description="Monthly Subscription",
            amount=Decimal("15.99"),
            interval_days=30,
            pattern_type=RecurringPatternType.SUBSCRIPTION,
            confidence=0.95,
            occurrence_count=6,
            first_seen=date(2024, 1, 1),
            last_seen=date(2024, 4, 1),
            next_expected_date=date(2024, 5, 1),
        )
        self.assertEqual(pattern.merchant, "Netflix")
        self.assertEqual(pattern.interval_days, 30)
        self.assertEqual(pattern.pattern_type, RecurringPatternType.SUBSCRIPTION)

    def test_anomaly_flag(self):
        """Test AnomalyFlag creation."""
        flag = AnomalyFlag(
            transaction_id=123,
            date=date(2024, 1, 15),
            description="Unusual Transaction",
            amount=Decimal("1000"),
            category="Food",
            expected_mean=Decimal("100"),
            expected_std=Decimal("10"),
            deviation_sigma=90.0,
            anomaly_type="amount_deviation",
            severity="critical",
        )
        self.assertEqual(flag.transaction_id, 123)
        self.assertEqual(flag.severity, "critical")
        self.assertEqual(flag.anomaly_type, "amount_deviation")

    def test_cash_flow_projection(self):
        """Test CashFlowProjection creation."""
        projection = CashFlowProjection(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 30),
            window_days=30,
            category_projections=[],
            aggregate_daily=[],
            aggregate_cumulative_income=Decimal("5000"),
            aggregate_cumulative_expenses=Decimal("3000"),
            aggregate_cumulative_net=Decimal("2000"),
            recurring_patterns=[],
            anomalies=[],
        )
        self.assertEqual(projection.start_date, date(2024, 1, 1))
        self.assertEqual(projection.window_days, 30)
        self.assertEqual(projection.aggregate_cumulative_net, Decimal("2000"))


if __name__ == "__main__":
    unittest.main()
