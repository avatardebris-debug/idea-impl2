"""Tests for Asset, Position, and Portfolio models."""

import pytest
from financial_portfolio_simulator.models.asset import Asset
from financial_portfolio_simulator.models.portfolio import Portfolio
from financial_portfolio_simulator.models.position import Position


class TestAsset:
    def test_create_asset(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)
        assert asset.ticker == "AAPL"
        assert asset.asset_type == "stock"
        assert asset.quantity == 10
        assert asset.price == 150.0
        assert asset.value == 1500.0

    def test_update_price(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)
        asset.update_price(160.0)
        assert asset.price == 160.0
        assert asset.value == 1600.0

    def test_default_metadata(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)
        assert asset.metadata == {}

    def test_custom_metadata(self):
        asset = Asset(
            ticker="AAPL",
            asset_type="stock",
            quantity=10,
            price=150.0,
            metadata={"drift": 0.1, "volatility": 0.25},
        )
        assert asset.metadata["drift"] == 0.1
        assert asset.metadata["volatility"] == 0.25

    def test_repr(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)
        assert "AAPL" in repr(asset)
        assert "stock" in repr(asset)


class TestPosition:
    def test_create_position(self):
        position = Position(ticker="AAPL", quantity=10, price=150.0)
        assert position.ticker == "AAPL"
        assert position.quantity == 10
        assert position.price == 150.0
        assert position.value == 1500.0

    def test_update_price(self):
        position = Position(ticker="AAPL", quantity=10, price=150.0)
        position.update_price(160.0)
        assert position.price == 160.0
        assert position.value == 1600.0

    def test_zero_quantity(self):
        position = Position(ticker="AAPL", quantity=0, price=150.0)
        assert position.value == 0.0


class TestPortfolio:
    def test_create_portfolio(self):
        portfolio = Portfolio(name="Test", assets=[])
        assert portfolio.name == "Test"
        assert portfolio.total_value == 0.0

    def test_portfolio_with_assets(self):
        assets = [
            Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0),
            Asset(ticker="BTC", asset_type="crypto", quantity=1, price=30000.0),
        ]
        portfolio = Portfolio(name="Test", assets=assets)
        assert portfolio.total_value == 1500.0 + 30000.0
        assert len(portfolio.assets) == 2

    def test_total_value_updates(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        assert portfolio.total_value == 1500.0
        assets[0].update_price(160.0)
        assert portfolio.total_value == 1600.0

    def test_add_asset(self):
        portfolio = Portfolio(name="Test", assets=[])
        portfolio.add_asset(Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0))
        assert len(portfolio.assets) == 1
        assert portfolio.total_value == 1500.0

    def test_remove_asset(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        portfolio.remove_asset("AAPL")
        assert len(portfolio.assets) == 0
        assert portfolio.total_value == 0.0

    def test_get_asset(self):
        assets = [Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0)]
        portfolio = Portfolio(name="Test", assets=assets)
        asset = portfolio.get_asset("AAPL")
        assert asset is not None
        assert asset.ticker == "AAPL"

    def test_get_asset_not_found(self):
        portfolio = Portfolio(name="Test", assets=[])
        assert portfolio.get_asset("AAPL") is None

    def test_allocation(self):
        assets = [
            Asset(ticker="AAPL", asset_type="stock", quantity=10, price=150.0),
            Asset(ticker="BTC", asset_type="crypto", quantity=1, price=30000.0),
        ]
        portfolio = Portfolio(name="Test", assets=assets)
        alloc = portfolio.allocation
        assert "AAPL" in alloc
        assert "BTC" in alloc
        total = sum(alloc.values())
        assert abs(total - 1.0) < 1e-10

    def test_empty_allocation(self):
        portfolio = Portfolio(name="Test", assets=[])
        assert portfolio.allocation == {}

    def test_repr(self):
        portfolio = Portfolio(name="Test", assets=[])
        assert "Test" in repr(portfolio)
