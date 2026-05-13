"""Tests for SimulationResult dataclass and its properties."""

import numpy as np
import pytest
from financial_portfolio_simulator.simulators.portfolio_simulator import SimulationResult


class TestSimulationResultProperties:
    """Test percentile-based properties of SimulationResult."""

    def _make_result(self, final_values):
        """Helper to create a SimulationResult with given final_values."""
        fv = np.array(final_values)
        return SimulationResult(
            final_values=fv,
            mean_final_value=float(np.mean(fv)),
            median_final_value=float(np.median(fv)),
            std_final_value=float(np.std(fv)),
            var_95=float(np.percentile(fv, 5)),
            var_99=float(np.percentile(fv, 1)),
            expected_return=(np.mean(fv) - fv[0]) / fv[0] if fv[0] > 0 else 0.0,
            confidence_intervals={
                (5, 95): (float(np.percentile(fv, 5)), float(np.percentile(fv, 95))),
                (1, 99): (float(np.percentile(fv, 1)), float(np.percentile(fv, 99))),
            },
            initial_value=float(fv[0]),
            n_iterations=len(fv),
            time_horizon=10,
        )

    def test_worst_case_95(self):
        """worst_case_95 should be the 5th percentile."""
        values = list(range(1, 101))  # 1 to 100
        result = self._make_result(values)
        expected = float(np.percentile(values, 5))
        assert result.worst_case_95 == pytest.approx(expected)

    def test_worst_case_99(self):
        """worst_case_99 should be the 1st percentile."""
        values = list(range(1, 101))
        result = self._make_result(values)
        expected = float(np.percentile(values, 1))
        assert result.worst_case_99 == pytest.approx(expected)

    def test_best_case_95(self):
        """best_case_95 should be the 95th percentile."""
        values = list(range(1, 101))
        result = self._make_result(values)
        expected = float(np.percentile(values, 95))
        assert result.best_case_95 == pytest.approx(expected)

    def test_best_case_99(self):
        """best_case_99 should be the 99th percentile."""
        values = list(range(1, 101))
        result = self._make_result(values)
        expected = float(np.percentile(values, 99))
        assert result.best_case_99 == pytest.approx(expected)

    def test_worst_case_less_than_best_case(self):
        """Worst case should always be less than best case."""
        values = [100 + i for i in range(1000)]
        result = self._make_result(values)
        assert result.worst_case_99 < result.worst_case_95
        assert result.best_case_95 < result.best_case_99
        assert result.worst_case_95 < result.best_case_95

    def test_worst_case_with_negative_returns(self):
        """Test worst case with negative returns."""
        values = [-500, -300, -100, 0, 100, 300, 500]
        result = self._make_result(values)
        assert result.worst_case_99 == pytest.approx(float(np.percentile(values, 1)))
        assert result.worst_case_95 == pytest.approx(float(np.percentile(values, 5)))

    def test_best_case_with_negative_returns(self):
        """Test best case with negative returns."""
        values = [-500, -300, -100, 0, 100, 300, 500]
        result = self._make_result(values)
        assert result.best_case_95 == pytest.approx(float(np.percentile(values, 95)))
        assert result.best_case_99 == pytest.approx(float(np.percentile(values, 99)))

    def test_confidence_intervals_5_95(self):
        """Test 5-95 confidence interval."""
        values = list(range(1, 101))
        result = self._make_result(values)
        ci = result.confidence_intervals[(5, 95)]
        assert ci[0] == pytest.approx(float(np.percentile(values, 5)))
        assert ci[1] == pytest.approx(float(np.percentile(values, 95)))
        assert ci[0] < ci[1]

    def test_confidence_intervals_1_99(self):
        """Test 1-99 confidence interval."""
        values = list(range(1, 101))
        result = self._make_result(values)
        ci = result.confidence_intervals[(1, 99)]
        assert ci[0] == pytest.approx(float(np.percentile(values, 1)))
        assert ci[1] == pytest.approx(float(np.percentile(values, 99)))
        assert ci[0] < ci[1]

    def test_confidence_intervals_wider_than_5_95(self):
        """1-99 CI should be wider than 5-95 CI."""
        values = list(range(1, 101))
        result = self._make_result(values)
        ci_1_99 = result.confidence_intervals[(1, 99)]
        ci_5_95 = result.confidence_intervals[(5, 95)]
        assert ci_1_99[0] < ci_5_95[0]
        assert ci_1_99[1] > ci_5_95[1]

    def test_expected_return_positive(self):
        """Expected return should be positive for upward trending."""
        values = [100 + i * 2 for i in range(100)]
        result = self._make_result(values)
        assert result.expected_return > 0

    def test_expected_return_negative(self):
        """Expected return should be negative for downward trending."""
        values = [100 - i * 2 for i in range(100)]
        result = self._make_result(values)
        assert result.expected_return < 0

    def test_expected_return_zero(self):
        """Expected return should be zero for constant values."""
        values = [100.0] * 100
        result = self._make_result(values)
        assert result.expected_return == 0.0

    def test_std_final_value(self):
        """std_final_value should match numpy std."""
        values = list(range(1, 101))
        result = self._make_result(values)
        assert result.std_final_value == pytest.approx(float(np.std(values)))

    def test_median_final_value(self):
        """median_final_value should match numpy median."""
        values = list(range(1, 101))
        result = self._make_result(values)
        assert result.median_final_value == pytest.approx(float(np.median(values)))

    def test_initial_value_matches_first_final_value(self):
        """initial_value should equal the first element of final_values."""
        values = [100, 105, 110, 115]
        result = self._make_result(values)
        assert result.initial_value == 100.0

    def test_n_iterations_matches_array_length(self):
        """n_iterations should match the length of final_values."""
        values = list(range(1, 501))
        result = self._make_result(values)
        assert result.n_iterations == 500

    def test_mean_final_value_matches_mean(self):
        """mean_final_value should match numpy mean."""
        values = list(range(1, 101))
        result = self._make_result(values)
        assert result.mean_final_value == pytest.approx(float(np.mean(values)))

    def test_summary_includes_percentile_values(self):
        """summary() should include worst/best case values."""
        values = list(range(1, 101))
        result = self._make_result(values)
        summary = result.summary()
        assert "worst_case_95" in summary
        assert "worst_case_99" in summary
        assert "best_case_95" in summary
        assert "best_case_99" in summary
        assert summary["worst_case_95"] == pytest.approx(float(np.percentile(values, 5)))
        assert summary["best_case_95"] == pytest.approx(float(np.percentile(values, 95)))

    def test_summary_includes_confidence_intervals(self):
        """summary() should include confidence intervals."""
        values = list(range(1, 101))
        result = self._make_result(values)
        summary = result.summary()
        assert "confidence_intervals" in summary
        assert (5, 95) in summary["confidence_intervals"]
        assert (1, 99) in summary["confidence_intervals"]

    def test_summary_includes_all_statistics(self):
        """summary() should include all key statistics."""
        values = list(range(1, 101))
        result = self._make_result(values)
        summary = result.summary()
        expected_keys = {
            "initial_value",
            "mean_final_value",
            "median_final_value",
            "std_final_value",
            "var_95",
            "var_99",
            "worst_case_95",
            "worst_case_99",
            "best_case_95",
            "best_case_99",
            "expected_return",
            "expected_return_pct",
            "confidence_intervals",
            "n_iterations",
            "time_horizon",
        }
        assert expected_keys.issubset(set(summary.keys()))

    def test_empty_final_values(self):
        """Test with empty final_values array."""
        result = SimulationResult(
            final_values=np.array([]),
            mean_final_value=0.0,
            median_final_value=0.0,
            std_final_value=0.0,
            var_95=0.0,
            var_99=0.0,
            expected_return=0.0,
            confidence_intervals={},
            initial_value=0.0,
            n_iterations=0,
            time_horizon=10,
        )
        assert result.mean_final_value == 0.0
        assert result.n_iterations == 0

    def test_single_iteration(self):
        """Test with a single iteration."""
        result = SimulationResult(
            final_values=np.array([1500.0]),
            mean_final_value=1500.0,
            median_final_value=1500.0,
            std_final_value=0.0,
            var_95=1500.0,
            var_99=1500.0,
            expected_return=0.0,
            confidence_intervals={
                (5, 95): (1500.0, 1500.0),
                (1, 99): (1500.0, 1500.0),
            },
            initial_value=1500.0,
            n_iterations=1,
            time_horizon=10,
        )
        assert result.worst_case_95 == 1500.0
        assert result.best_case_95 == 1500.0
        assert result.std_final_value == 0.0


class TestSimulationResultSummary:
    """Test the summary() method of SimulationResult."""

    def test_summary_returns_dict(self):
        """summary() should return a dictionary."""
        result = SimulationResult(
            final_values=np.array([100, 105, 110]),
            mean_final_value=105.0,
            median_final_value=105.0,
            std_final_value=5.0,
            var_95=100.0,
            var_99=100.0,
            expected_return=0.05,
            confidence_intervals={},
            initial_value=100.0,
            n_iterations=3,
            time_horizon=10,
        )
        assert isinstance(result.summary(), dict)

    def test_summary_expected_return_pct(self):
        """expected_return_pct should be expected_return * 100."""
        result = SimulationResult(
            final_values=np.array([100, 105, 110]),
            mean_final_value=105.0,
            median_final_value=105.0,
            std_final_value=5.0,
            var_95=100.0,
            var_99=100.0,
            expected_return=0.05,
            confidence_intervals={},
            initial_value=100.0,
            n_iterations=3,
            time_horizon=10,
        )
        summary = result.summary()
        assert summary["expected_return_pct"] == pytest.approx(5.0)

    def test_summary_with_negative_return(self):
        """Test summary with negative expected return."""
        result = SimulationResult(
            final_values=np.array([100, 95, 90]),
            mean_final_value=95.0,
            median_final_value=95.0,
            std_final_value=5.0,
            var_95=90.0,
            var_99=90.0,
            expected_return=-0.05,
            confidence_intervals={},
            initial_value=100.0,
            n_iterations=3,
            time_horizon=10,
        )
        summary = result.summary()
        assert summary["expected_return_pct"] == pytest.approx(-5.0)

    def test_summary_all_values_are_numbers(self):
        """All summary values should be numbers (not strings or None)."""
        result = SimulationResult(
            final_values=np.array([100, 105, 110]),
            mean_final_value=105.0,
            median_final_value=105.0,
            std_final_value=5.0,
            var_95=100.0,
            var_99=100.0,
            expected_return=0.05,
            confidence_intervals={},
            initial_value=100.0,
            n_iterations=3,
            time_horizon=10,
        )
        summary = result.summary()
        for key, value in summary.items():
            if key == "confidence_intervals":
                continue
            assert isinstance(value, (int, float)), f"{key} is {type(value)}"
