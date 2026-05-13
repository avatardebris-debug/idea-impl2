"""Tests for Asset model."""

import pytest
from financial_portfolio_simulator.models.asset import Asset
from financial_portfolio_simulator.exceptions import ModelError


class TestAsset:
    """Tests for the Asset dataclass."""

    def test_create_valid_asset(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.0)
        assert asset.ticker == "AAPL"
        assert asset.asset_type == "stock"
        assert asset.quantity == 100
        assert asset.price == 150.0

    def test_create_crypto_asset(self):
        asset = Asset(ticker="BTC", asset_type="crypto", quantity=1.5, price=50000.0)
        assert asset.asset_type == "crypto"
        assert asset.quantity == 1.5

    def test_value_property(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.0)
        assert asset.value == 15000.0

    def test_value_with_zero_quantity(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=0, price=150.0)
        assert asset.value == 0.0

    def test_update_price(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.0)
        asset.update_price(160.0)
        assert asset.price == 160.0
        assert asset.value == 16000.0

    def test_update_price_to_zero(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.0)
        asset.update_price(0.0)
        assert asset.price == 0.0

    def test_update_price_negative_raises(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.0)
        with pytest.raises(ModelError):
            asset.update_price(-1.0)

    def test_update_price_non_number_raises(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.0)
        with pytest.raises(ModelError):
            asset.update_price("high")

    def test_empty_ticker_raises(self):
        with pytest.raises(ModelError):
            Asset(ticker="", asset_type="stock", quantity=100, price=150.0)

    def test_whitespace_ticker_raises(self):
        with pytest.raises(ModelError):
            Asset(ticker="   ", asset_type="stock", quantity=100, price=150.0)

    def test_invalid_asset_type_raises(self):
        with pytest.raises(ModelError):
            Asset(ticker="AAPL", asset_type="bond", quantity=100, price=150.0)

    def test_negative_quantity_raises(self):
        with pytest.raises(ModelError):
            Asset(ticker="AAPL", asset_type="stock", quantity=-1, price=150.0)

    def test_zero_quantity_allowed(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=0, price=150.0)
        assert asset.quantity == 0

    def test_zero_price_allowed(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=0.0)
        assert asset.price == 0.0

    def test_negative_price_raises(self):
        with pytest.raises(ModelError):
            Asset(ticker="AAPL", asset_type="stock", quantity=100, price=-10.0)

    def test_non_numeric_quantity_raises(self):
        with pytest.raises(ModelError):
            Asset(ticker="AAPL", asset_type="stock", quantity="100", price=150.0)

    def test_non_numeric_price_raises(self):
        with pytest.raises(ModelError):
            Asset(ticker="AAPL", asset_type="stock", quantity=100, price="150")

    def test_metadata_default(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.0)
        assert asset.metadata == {}

    def test_metadata_custom(self):
        asset = Asset(
            ticker="AAPL",
            asset_type="stock",
            quantity=100,
            price=150.0,
            metadata={"sector": "Technology"},
        )
        assert asset.metadata["sector"] == "Technology"

    def test_repr(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.0)
        assert "AAPL" in repr(asset)

    def test_float_price(self):
        asset = Asset(ticker="AAPL", asset_type="stock", quantity=100, price=150.75)
        assert asset.price == 150.75

    def test_float_quantity(self):
        asset = Asset(ticker="BTC", asset_type="crypto", quantity=1.5, price=50000.0)
        assert asset.quantity == 1.5
