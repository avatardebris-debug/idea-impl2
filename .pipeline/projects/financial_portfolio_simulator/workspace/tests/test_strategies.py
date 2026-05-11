"""Tests for Strategy classes."""

import pytest
from financial_portfolio_simulator.strategies.base import Strategy
from financial_portfolio_simulator.strategies.buy_and_hold import BuyAndHold
from financial_portfolio_simulator.models.portfolio import Portfolio
from financial_portfolio_simulator.models.asset import Asset
import numpy as np


class TestStrategy:
    def test_base_strategy_is_abstract(self):
        with pytest.raises(TypeError):
            Strategy()

    def test_buy_and_hold_repr(self):
        strategy = BuyAndHold()
        assert "buy_and_hold" in repr(strategy)


class TestBuyAndHold:
    def test_apply_does_nothing(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        initial_value = portfolio.total_value
        price_paths = {"AAPL": np.array([100.0, 101.0, 102.0])}
        strategy = BuyAndHold()
        strategy.apply(portfolio, price_paths, 1/252)
        # Buy and hold should not change the portfolio
        assert portfolio.total_value == initial_value

    def test_apply_with_multiple_assets(self):
        assets = [
            Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0),
            Asset(ticker="BTC", asset_type="crypto", quantity=1, price=30000.0),
        ]
        portfolio = Portfolio(name="Test", assets=assets)
        initial_value = portfolio.total_value
        price_paths = {
            "AAPL": np.array([100.0, 101.0]),
            "BTC": np.array([30000.0, 30500.0]),
        }
        strategy = BuyAndHold()
        strategy.apply(portfolio, price_paths, 1/252)
        assert portfolio.total_value == initial_value
