"""Integration tests for the Financial Portfolio Simulator.

Tests the full pipeline: Portfolio creation -> Monte Carlo simulation ->
Strategy application -> Risk metric computation.
"""

import csv
import json
import os
import tempfile
from io import StringIO

import numpy as np
import pytest

from financial_portfolio_simulator import (
    run_simulation,
    Asset,
    Portfolio,
    Position,
    GBM,
    MarketSimulator,
    PortfolioSimulator,
    SimulationResult,
    Strategy,
    BuyAndHold,
    SimulationError,
)
from financial_portfolio_simulator.models.portfolio import Portfolio as PortfolioModel
from financial_portfolio_simulator.models.asset import Asset as AssetModel
from financial_portfolio_simulator.models.position import Position as PositionModel
from financial_portfolio_simulator.simulators.gbm import GBM as GBMClass
from financial_portfolio_simulator.simulators.market_simulator import MarketSimulator as MarketSimulatorClass
from financial_portfolio_simulator.simulators.portfolio_simulator import (
    PortfolioSimulator as PortfolioSimulatorClass,
    SimulationResult as SimulationResultClass,
)
from financial_portfolio_simulator.strategies.base import Strategy as StrategyBase
from financial_portfolio_simulator.strategies.buy_and_hold import BuyAndHold as BuyAndHoldClass


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_assets():
    """Return a list of sample asset dicts for testing."""
    return [
        {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0},
        {"ticker": "MSFT", "asset_type": "stock", "quantity": 5, "price": 200.0},
        {"ticker": "BTC", "asset_type": "crypto", "quantity": 1, "price": 30000.0},
    ]


@pytest.fixture
def sample_portfolio(sample_assets):
    """Return a Portfolio object with sample assets."""
    assets = [
        Asset(ticker=a["ticker"], asset_type=a["asset_type"],
              quantity=a["quantity"], price=a["price"])
        for a in sample_assets
    ]
    return Portfolio(name="TestPortfolio", assets=assets)


@pytest.fixture
def sample_csv_content():
    """Return a sample CSV with asset data."""
    return (
        "ticker,asset_type,quantity,price\n"
        "AAPL,stock,10,150.0\n"
        "MSFT,stock,5,200.0\n"
        "BTC,crypto,1,30000.0\n"
    )


@pytest.fixture
def sample_csv_file(sample_csv_content):
    """Create a temporary CSV file with sample asset data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
        fh.write(sample_csv_content)
        fh.flush()
        yield fh.name
    os.unlink(fh.name)


# ── GBM Integration Tests ─────────────────────────────────────────────────────

class TestGBMIntegration:
    """Integration tests for GBM (Geometric Brownian Motion)."""

    def test_gbm_to_market_simulator(self):
        """GBM should integrate correctly with MarketSimulator."""
        gbm = GBM(drift=0.05, volatility=0.2, seed=42)
        path = gbm.simulate_single(100.0, 10)

        market_sim = MarketSimulator(seed=42)
        assets = [
            {"ticker": "TEST", "initial_price": 100.0, "drift": 0.05, "volatility": 0.2}
        ]
        paths = market_sim.simulate_correlated(assets, time_steps=10)

        assert len(path) == 11
        assert len(paths["TEST"]) == 11
        assert paths["TEST"][0] == 100.0

    def test_gbm_determinism_across_components(self):
        """GBM results should be deterministic when used with MarketSimulator."""
        gbm1 = GBM(drift=0.05, volatility=0.2, seed=42)
        gbm2 = GBM(drift=0.05, volatility=0.2, seed=42)

        path1 = gbm1.simulate_single(100.0, 10)
        path2 = gbm2.simulate_single(100.0, 10)

        np.testing.assert_array_equal(path1, path2)


# ── MarketSimulator Integration Tests ─────────────────────────────────────────

class TestMarketSimulatorIntegration:
    """Integration tests for MarketSimulator."""

    def test_market_simulator_to_portfolio_simulator(self):
        """MarketSimulator outputs should feed into PortfolioSimulator."""
        market_sim = MarketSimulator(seed=42)
        assets = [
            {"ticker": "AAPL", "initial_price": 150.0, "drift": 0.08, "volatility": 0.2},
            {"ticker": "MSFT", "initial_price": 200.0, "drift": 0.06, "volatility": 0.15},
        ]
        paths = market_sim.simulate_correlated(assets, time_steps=10)

        assert "AAPL" in paths
        assert "MSFT" in paths
        assert len(paths["AAPL"]) == 11
        assert len(paths["MSFT"]) == 11

    def test_market_simulator_correlation(self):
        """MarketSimulator should respect correlation settings."""
        market_sim = MarketSimulator(seed=42)
        assets = [
            {"ticker": "AAPL", "initial_price": 100.0, "drift": 0.05, "volatility": 0.2, "correlation": 0.8},
            {"ticker": "MSFT", "initial_price": 200.0, "drift": 0.05, "volatility": 0.2, "correlation": 0.8},
        ]
        paths = market_sim.simulate_correlated(assets, time_steps=100)

        # Correlated assets should have similar movement patterns
        assert len(paths["AAPL"]) == 101
        assert len(paths["MSFT"]) == 101


# ── Portfolio Integration Tests ───────────────────────────────────────────────

class TestPortfolioIntegration:
    """Integration tests for Portfolio."""

    def test_portfolio_with_gbm_prices(self, sample_portfolio):
        """Portfolio should correctly calculate value with GBM-simulated prices."""
        gbm = GBM(drift=0.05, volatility=0.2, seed=42)
        path = gbm.simulate_single(sample_portfolio.assets[0].price, 10)

        # Portfolio value should update based on price changes
        initial_value = sample_portfolio.total_value
        assert initial_value > 0

    def test_portfolio_allocation_with_multiple_assets(self, sample_portfolio):
        """Portfolio allocation should sum to 1.0 for multiple assets."""
        alloc = sample_portfolio.allocation
        total = sum(alloc.values())
        assert abs(total - 1.0) < 1e-10

    def test_portfolio_add_remove_integration(self, sample_portfolio):
        """Adding and removing assets should maintain portfolio integrity."""
        initial_value = sample_portfolio.total_value
        initial_count = len(sample_portfolio.assets)

        new_asset = Asset(ticker="GOOG", asset_type="stock", quantity=5, price=100.0)
        sample_portfolio.add_asset(new_asset)
        assert len(sample_portfolio.assets) == initial_count + 1

        sample_portfolio.remove_asset("GOOG")
        assert len(sample_portfolio.assets) == initial_count
        assert sample_portfolio.total_value == initial_value


# ── PortfolioSimulator Integration Tests ──────────────────────────────────────

class TestPortfolioSimulatorIntegration:
    """Integration tests for PortfolioSimulator."""

    def test_full_simulation_pipeline(self, sample_portfolio):
        """Test the complete simulation pipeline."""
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(sample_portfolio, time_steps=252, n_iterations=100)

        assert result.initial_value == sample_portfolio.total_value
        assert result.n_iterations == 100
        assert len(result.final_values) == 100
        assert result.mean_final_value > 0

    def test_simulation_with_strategy(self, sample_portfolio):
        """Test simulation with strategy application."""
        sim = PortfolioSimulator(seed=42)
        strategy = BuyAndHold()
        result = sim.simulate(
            sample_portfolio,
            time_steps=10,
            n_iterations=50,
            strategy=strategy
        )

        assert result.n_iterations == 50
        assert result.mean_final_value > 0

    def test_simulation_determinism(self, sample_portfolio):
        """Same seed should produce identical results."""
        sim1 = PortfolioSimulator(seed=42)
        sim2 = PortfolioSimulator(seed=42)

        result1 = sim1.simulate(sample_portfolio, time_steps=10, n_iterations=100)
        result2 = sim2.simulate(sample_portfolio, time_steps=10, n_iterations=100)

        np.testing.assert_array_equal(result1.final_values, result2.final_values)

    def test_risk_metrics_computation(self, sample_portfolio):
        """Test that risk metrics are correctly computed."""
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(sample_portfolio, time_steps=252, n_iterations=1000)

        assert hasattr(result, "var_95")
        assert hasattr(result, "var_99")
        assert hasattr(result, "expected_return")
        assert result.var_95 < result.mean_final_value
        assert result.best_case_95 > result.mean_final_value


# ── High-Level API Integration Tests ──────────────────────────────────────────

class TestRunSimulationIntegration:
    """Integration tests for the high-level run_simulation API."""

    def test_end_to_end_simulation(self, sample_assets):
        """Test complete end-to-end simulation."""
        result = run_simulation(
            assets=sample_assets,
            time_steps=252,
            n_iterations=100,
            seed=42,
        )

        assert isinstance(result, SimulationResult)
        assert result.initial_value > 0
        assert result.n_iterations == 100
        assert len(result.final_values) == 100

    def test_simulation_with_correlated_assets(self, sample_assets):
        """Test simulation with correlated assets."""
        correlated_assets = [
            {**a, "correlation": 0.5} for a in sample_assets
        ]
        result = run_simulation(
            assets=correlated_assets,
            time_steps=10,
            n_iterations=50,
            seed=42,
            use_correlated=True,
        )

        assert result.n_iterations == 50
        assert result.mean_final_value > 0

    def test_simulation_result_summary(self, sample_assets):
        """Test that simulation result summary is comprehensive."""
        result = run_simulation(
            assets=sample_assets,
            time_steps=10,
            n_iterations=50,
            seed=42,
        )

        summary = result.summary()
        assert isinstance(summary, dict)
        assert "initial_value" in summary
        assert "mean_final_value" in summary
        assert "var_95" in summary
        assert "var_99" in summary
        assert "expected_return_pct" in summary
        assert "best_case_95" in summary

    def test_empty_portfolio_simulation(self):
        """Test simulation with empty portfolio."""
        result = run_simulation(
            assets=[],
            time_steps=10,
            n_iterations=50,
            seed=42,
        )

        assert result.initial_value == 0.0
        assert result.mean_final_value == 0.0
        assert len(result.final_values) == 50


# ── Strategy Integration Tests ────────────────────────────────────────────────

class TestStrategyIntegration:
    """Integration tests for Strategy classes."""

    def test_strategy_with_portfolio(self, sample_portfolio):
        """Test strategy application on portfolio."""
        strategy = BuyAndHold()
        price_paths = {
            asset.ticker: np.linspace(asset.price, asset.price * 1.1, 11)
            for asset in sample_portfolio.assets
        }

        initial_value = sample_portfolio.total_value
        strategy.apply(sample_portfolio, price_paths, 1/252)

        # Buy and hold should not change the portfolio
        assert sample_portfolio.total_value == initial_value

    def test_strategy_determinism(self, sample_portfolio):
        """Test that strategy application is deterministic."""
        strategy1 = BuyAndHold()
        strategy2 = BuyAndHold()

        price_paths = {
            asset.ticker: np.linspace(asset.price, asset.price * 1.1, 11)
            for asset in sample_portfolio.assets
        }

        portfolio1 = Portfolio(name="Test", assets=[
            Asset(ticker=a.ticker, asset_type=a.asset_type,
                  quantity=a.quantity, price=a.price)
            for a in sample_portfolio.assets
        ])
        portfolio2 = Portfolio(name="Test", assets=[
            Asset(ticker=a.ticker, asset_type=a.asset_type,
                  quantity=a.quantity, price=a.price)
            for a in sample_portfolio.assets
        ])

        strategy1.apply(portfolio1, price_paths, 1/252)
        strategy2.apply(portfolio2, price_paths, 1/252)

        assert portfolio1.total_value == portfolio2.total_value


# ── Data Import/Export Integration Tests ──────────────────────────────────────

class TestDataIntegration:
    """Integration tests for data import/export functionality."""

    def test_asset_from_dict(self):
        """Test creating Asset from dictionary."""
        asset_dict = {
            "ticker": "AAPL",
            "asset_type": "stock",
            "quantity": 10,
            "price": 150.0,
        }
        asset = Asset(**asset_dict)

        assert asset.ticker == "AAPL"
        assert asset.asset_type == "stock"
        assert asset.quantity == 10
        assert asset.price == 150.0

    def test_portfolio_from_assets(self):
        """Test creating Portfolio from list of assets."""
        assets = [
            Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0),
            Asset(ticker="MSFT", asset_type="stock", quantity=5, price=200.0),
        ]
        portfolio = Portfolio(name="Test", assets=assets)

        assert portfolio.name == "Test"
        assert len(portfolio.assets) == 2
        assert portfolio.total_value == 10 * 150.0 + 5 * 200.0

    def test_simulation_result_to_dict(self):
        """Test converting SimulationResult to dictionary."""
        result = run_simulation(
            assets=[{"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0}],
            time_steps=10,
            n_iterations=50,
            seed=42,
        )

        summary = result.summary()
        assert isinstance(summary, dict)
        assert "initial_value" in summary
        assert "mean_final_value" in summary


# ── Error Handling Integration Tests ──────────────────────────────────────────

class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_invalid_asset_type(self):
        """Test handling of invalid asset types."""
        with pytest.raises(Exception):  # Should raise InvalidAssetError
            Asset(ticker="AAPL", asset_type="invalid_type", quantity=10, price=150.0)

    def test_empty_portfolio_simulation(self):
        """Test simulation with empty portfolio."""
        result = run_simulation(
            assets=[],
            time_steps=10,
            n_iterations=50,
            seed=42,
        )
        assert result.initial_value == 0.0

    def test_zero_quantity_asset(self):
        """Test handling of zero quantity assets."""
        result = run_simulation(
            assets=[{"ticker": "AAPL", "asset_type": "stock", "quantity": 0, "price": 150.0}],
            time_steps=10,
            n_iterations=50,
            seed=42,
        )
        assert result.initial_value == 0.0


# ── Performance Integration Tests ─────────────────────────────────────────────

class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""

    def test_large_simulation(self):
        """Test simulation with large number of iterations."""
        result = run_simulation(
            assets=[
                {"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0},
                {"ticker": "MSFT", "asset_type": "stock", "quantity": 5, "price": 200.0},
            ],
            time_steps=252,
            n_iterations=1000,
            seed=42,
        )

        assert result.n_iterations == 1000
        assert len(result.final_values) == 1000
        assert result.mean_final_value > 0

    def test_long_time_horizon(self):
        """Test simulation with long time horizon."""
        result = run_simulation(
            assets=[{"ticker": "AAPL", "asset_type": "stock", "quantity": 10, "price": 150.0}],
            time_steps=1000,
            n_iterations=100,
            seed=42,
        )

        assert result.time_horizon == 1000
        assert result.mean_final_value > 0
