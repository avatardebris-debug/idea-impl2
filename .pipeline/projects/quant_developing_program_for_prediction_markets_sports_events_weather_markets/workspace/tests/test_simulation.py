"""Tests for quant_developing_program.core.simulation."""

import pytest
import numpy as np

from quant_developing_program.core.simulation import (
    SharpeRatioSimulator,
    MonteCarloEngine,
)


class TestSharpeRatioSimulator:
    def test_calculate_sharpe(self):
        simulator = SharpeRatioSimulator()
        returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        sharpe = simulator.calculate_sharpe(returns)
        assert sharpe > 0

    def test_calculate_sharpe_zero_std(self):
        simulator = SharpeRatioSimulator()
        returns = [0.01, 0.01, 0.01, 0.01]
        sharpe = simulator.calculate_sharpe(returns)
        assert sharpe == 0.0

    def test_calculate_sharpe_insufficient_data(self):
        simulator = SharpeRatioSimulator()
        returns = [0.01]
        sharpe = simulator.calculate_sharpe(returns)
        assert sharpe == 0.0

    def test_simulate(self):
        simulator = SharpeRatioSimulator()
        result = simulator.simulate(
            num_simulations=1000,
            num_periods=252,
            mean_return=0.001,
            std_return=0.02,
            seed=42,
        )
        assert result.mean_sharpe is not None
        assert result.std_sharpe > 0
        assert result.median_sharpe is not None
        assert result.percentile_5 < result.percentile_95
        assert result.num_simulations == 1000

    def test_simulate_with_correlation(self):
        simulator = SharpeRatioSimulator()
        result = simulator.simulate(
            num_simulations=1000,
            num_periods=252,
            mean_return=0.001,
            std_return=0.02,
            correlation=0.5,
            seed=42,
        )
        assert result.mean_sharpe is not None

    def test_simulate_with_risk_free_rate(self):
        simulator = SharpeRatioSimulator()
        result = simulator.simulate(
            num_simulations=1000,
            num_periods=252,
            mean_return=0.001,
            std_return=0.02,
            risk_free_rate=0.0001,
            seed=42,
        )
        assert result.mean_sharpe is not None

    def test_simulate_reproducibility(self):
        simulator = SharpeRatioSimulator()
        result1 = simulator.simulate(
            num_simulations=1000,
            num_periods=252,
            mean_return=0.001,
            std_return=0.02,
            seed=42,
        )
        result2 = simulator.simulate(
            num_simulations=1000,
            num_periods=252,
            mean_return=0.001,
            std_return=0.02,
            seed=42,
        )
        assert result1.mean_sharpe == result2.mean_sharpe


class TestMonteCarloEngine:
    def test_run(self):
        engine = MonteCarloEngine(seed=42)

        def sim_func(rng, **kwargs):
            return rng.normal(0, 1)

        result = engine.run(1000, sim_func)
        assert result.mean is not None
        assert result.std > 0
        assert result.min_val < result.max_val
        assert result.percentile_5 < result.percentile_95
        assert result.num_simulations == 1000

    def test_run_with_kwargs(self):
        engine = MonteCarloEngine(seed=42)

        def sim_func(rng, mean=0, std=1, **kwargs):
            return rng.normal(mean, std)

        result = engine.run(1000, sim_func, mean=5, std=2)
        assert result.mean == pytest.approx(5, abs=0.5)

    def test_run_reproducibility(self):
        engine = MonteCarloEngine(seed=42)

        def sim_func(rng, **kwargs):
            return rng.normal(0, 1)

        result1 = engine.run(1000, sim_func)
        engine2 = MonteCarloEngine(seed=42)
        result2 = engine2.run(1000, sim_func)
        assert result1.mean == result2.mean

    def test_run_with_callback(self):
        engine = MonteCarloEngine(seed=42)

        def sim_func(rng, **kwargs):
            return rng.normal(0, 1)

        def callback(outcome, index):
            return outcome * 2

        results = engine.run_with_callback(1000, sim_func, callback)
        assert len(results) == 1000
        assert all(isinstance(r, float) for r in results)

    def test_run_no_successful_simulations(self):
        engine = MonteCarloEngine(seed=42)

        def sim_func(rng, **kwargs):
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            engine.run(1000, sim_func)

    def test_run_with_different_distributions(self):
        engine = MonteCarloEngine(seed=42)

        def uniform_sim(rng, **kwargs):
            return rng.uniform(0, 1)

        result = engine.run(1000, uniform_sim)
        assert result.mean == pytest.approx(0.5, abs=0.1)
        assert result.min_val >= 0
        assert result.max_val <= 1
