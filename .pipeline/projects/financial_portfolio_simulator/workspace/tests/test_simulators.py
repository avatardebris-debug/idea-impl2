"""Tests for GBM, MarketSimulator, and PortfolioSimulator."""

import numpy as np
import pytest
from financial_portfolio_simulator.simulators.gbm import GBM
from financial_portfolio_simulator.simulators.market_simulator import MarketSimulator
from financial_portfolio_simulator.simulators.portfolio_simulator import PortfolioSimulator, SimulationResult
from financial_portfolio_simulator.models.asset import Asset
from financial_portfolio_simulator.models.portfolio import Portfolio


class TestGBM:
    def test_simulate_single_path(self):
        gbm = GBM(drift=0.05, volatility=0.2, seed=42)
        path = gbm.simulate_single(100.0, 10)
        assert len(path) == 11
        assert path[0] == 100.0

    def test_simulate_multiple_paths(self):
        gbm = GBM(drift=0.05, volatility=0.2, seed=42)
        paths = gbm.simulate(100.0, 10, n_paths=5)
        assert paths.shape == (5, 11)
        assert np.all(paths[:, 0] == 100.0)

    def test_deterministic_with_seed(self):
        gbm1 = GBM(drift=0.05, volatility=0.2, seed=42)
        gbm2 = GBM(drift=0.05, volatility=0.2, seed=42)
        p1 = gbm1.simulate_single(100.0, 10)
        p2 = gbm2.simulate_single(100.0, 10)
        np.testing.assert_array_equal(p1, p2)

    def test_different_seeds_different_results(self):
        gbm1 = GBM(drift=0.05, volatility=0.2, seed=42)
        gbm2 = GBM(drift=0.05, volatility=0.2, seed=99)
        p1 = gbm1.simulate_single(100.0, 10)
        p2 = gbm2.simulate_single(100.0, 10)
        assert not np.allclose(p1, p2)

    def test_prices_always_positive(self):
        gbm = GBM(drift=-0.5, volatility=0.5, seed=42)
        path = gbm.simulate(100.0, 1000, n_paths=100)
        assert np.all(path > 0)


class TestMarketSimulator:
    def test_simulate_correlated(self):
        sim = MarketSimulator(seed=42)
        assets = [
            {"ticker": "AAPL", "initial_price": 100.0, "drift": 0.08, "volatility": 0.2, "correlation": 0.5},
            {"ticker": "MSFT", "initial_price": 200.0, "drift": 0.06, "volatility": 0.15, "correlation": 0.5},
        ]
        paths = sim.simulate_correlated(assets, time_steps=10)
        assert "AAPL" in paths
        assert "MSFT" in paths
        assert len(paths["AAPL"]) == 11
        assert len(paths["MSFT"]) == 11

    def test_simulate_single_asset(self):
        sim = MarketSimulator(seed=42)
        assets = [
            {"ticker": "AAPL", "initial_price": 100.0, "drift": 0.08, "volatility": 0.2},
        ]
        paths = sim.simulate_correlated(assets, time_steps=10)
        assert "AAPL" in paths
        assert paths["AAPL"][0] == 100.0

    def test_simulate_empty(self):
        sim = MarketSimulator(seed=42)
        paths = sim.simulate_correlated([], time_steps=10)
        assert paths == {}


class TestPortfolioSimulator:
    def test_simulate_single_asset(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(portfolio, time_steps=10, n_iterations=100)
        assert result.initial_value == 1500.0
        assert result.n_iterations == 100
        assert len(result.final_values) == 100
        assert result.mean_final_value > 0

    def test_simulate_multi_asset(self):
        assets = [
            Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0),
            Asset(ticker="BTC", asset_type="crypto", quantity=1, price=30000.0),
        ]
        portfolio = Portfolio(name="Test", assets=assets)
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(portfolio, time_steps=10, n_iterations=100)
        assert result.initial_value == 1500.0 + 30000.0
        assert result.n_iterations == 100

    def test_simulate_empty_portfolio(self):
        portfolio = Portfolio(name="Test", assets=[])
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(portfolio, time_steps=10, n_iterations=100)
        assert result.initial_value == 0.0
        assert result.mean_final_value == 0.0

    def test_simulate_with_correlated_assets(self):
        assets = [
            Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0, metadata={"correlation": 0.5}),
            Asset(ticker="MSFT", asset_type="stock", quantity=5, price=200.0, metadata={"correlation": 0.5}),
        ]
        portfolio = Portfolio(name="Test", assets=assets)
        sim = PortfolioSimulator(seed=42, use_correlated=True)
        corr = np.array([[1.0, 0.5], [0.5, 1.0]])
        result = sim.simulate(portfolio, time_steps=10, n_iterations=100, correlation_matrix=corr)
        assert result.n_iterations == 100

    def test_simulation_result_attributes(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(portfolio, time_steps=10, n_iterations=100)
        assert hasattr(result, "final_values")
        assert hasattr(result, "mean_final_value")
        assert hasattr(result, "var_95")
        assert hasattr(result, "var_99")
        assert hasattr(result, "expected_return")
        assert hasattr(result, "summary")

    def test_simulation_result_summary(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(portfolio, time_steps=10, n_iterations=100)
        summary = result.summary()
        assert "initial_value" in summary
        assert "mean_final_value" in summary
        assert "var_95" in summary
        assert "expected_return_pct" in summary

    def test_deterministic_with_same_seed(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        sim1 = PortfolioSimulator(seed=42)
        sim2 = PortfolioSimulator(seed=42)
        r1 = sim1.simulate(portfolio, time_steps=10, n_iterations=100)
        r2 = sim2.simulate(portfolio, time_steps=10, n_iterations=100)
        np.testing.assert_array_equal(r1.final_values, r2.final_values)

    def test_var_95_less_than_mean(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(portfolio, time_steps=252, n_iterations=1000)
        assert result.var_95 < result.mean_final_value

    def test_best_case_greater_than_mean(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        sim = PortfolioSimulator(seed=42)
        result = sim.simulate(portfolio, time_steps=252, n_iterations=1000)
        assert result.best_case_95 > result.mean_final_value
