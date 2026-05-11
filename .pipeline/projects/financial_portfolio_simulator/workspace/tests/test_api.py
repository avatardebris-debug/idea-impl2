"""Tests for the high-level API."""

import pytest
from financial_portfolio_simulator import run_simulation
from financial_portfolio_simulator.simulators.portfolio_simulator import SimulationResult


class TestRunSimulation:
    def test_basic_simulation(self):
        result = run_simulation(
            assets=[
                {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0},
            ],
            time_steps=10,
            n_iterations=100,
            seed=42,
        )
        assert isinstance(result, SimulationResult)
        assert result.initial_value == 1500.0
        assert result.n_iterations == 100

    def test_multi_asset_simulation(self):
        result = run_simulation(
            assets=[
                {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0},
                {"ticker": "BTC", "asset_type": "crypto", "quantity": 1, "price": 30000.0},
            ],
            time_steps=10,
            n_iterations=100,
            seed=42,
        )
        assert result.initial_value == 1500.0 + 30000.0

    def test_custom_drift_volatility(self):
        result = run_simulation(
            assets=[
                {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0, "drift": 0.15, "volatility": 0.3},
            ],
            time_steps=10,
            n_iterations=100,
            seed=42,
        )
        assert result.mean_final_value > 0

    def test_correlated_simulation(self):
        result = run_simulation(
            assets=[
                {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0, "correlation": 0.5},
                {"ticker": "MSFT", "asset_type": "stock", "quantity": 5, "price": 200.0, "correlation": 0.5},
            ],
            time_steps=10,
            n_iterations=100,
            seed=42,
            use_correlated=True,
        )
        assert result.n_iterations == 100

    def test_with_strategy(self):
        result = run_simulation(
            assets=[
                {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0},
            ],
            time_steps=10,
            n_iterations=100,
            seed=42,
            strategy="buy_and_hold",
        )
        assert result.n_iterations == 100

    def test_empty_assets(self):
        result = run_simulation(
            assets=[],
            time_steps=10,
            n_iterations=100,
            seed=42,
        )
        assert result.initial_value == 0.0
        assert result.mean_final_value == 0.0

    def test_result_has_all_attributes(self):
        result = run_simulation(
            assets=[
                {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0},
            ],
            time_steps=10,
            n_iterations=100,
            seed=42,
        )
        assert hasattr(result, "final_values")
        assert hasattr(result, "mean_final_value")
        assert hasattr(result, "var_95")
        assert hasattr(result, "var_99")
        assert hasattr(result, "expected_return")
        assert hasattr(result, "summary")
        assert hasattr(result, "initial_value")
        assert hasattr(result, "n_iterations")
        assert hasattr(result, "time_horizon")

    def test_summary_returns_dict(self):
        result = run_simulation(
            assets=[
                {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0},
            ],
            time_steps=10,
            n_iterations=100,
            seed=42,
        )
        summary = result.summary()
        assert isinstance(summary, dict)
        assert "initial_value" in summary
        assert "mean_final_value" in summary
        assert "var_95" in summary
        assert "expected_return_pct" in summary
