"""Tests for custom Gymnasium spaces."""

import pytest
import numpy as np
import gymnasium as gym

from rl_dropshipping.src.env.spaces import (
    DropshippingActionSpace,
    MarketConditionSpace,
    InventorySpace,
    AdPerformanceSpace,
    CompetitorPricingSpace,
)


class TestDropshippingActionSpace:
    """Tests for DropshippingActionSpace."""

    def test_init(self):
        """Test action space initialization."""
        space = DropshippingActionSpace(n_products=10, n_channels=2, n_budget_buckets=10)
        assert space.n_products == 10
        assert space.n_channels == 2
        assert space.n_budget_buckets == 10
        assert space.n_actions == 200
        assert isinstance(space, gym.spaces.Discrete)

    def test_decode(self):
        """Test action decoding."""
        space = DropshippingActionSpace()
        action = space.encode(product_index=5, channel_index=1, budget_pct=0.5)
        decoded = space.decode(action)
        assert decoded["product_index"] == 5
        assert decoded["channel_index"] == 1
        assert decoded["budget_pct"] == pytest.approx(0.5)

    def test_encode_decode_roundtrip(self):
        """Test encode/decode roundtrip."""
        space = DropshippingActionSpace()
        for p in range(10):
            for c in range(2):
                for b in range(10):
                    pct = b / 10.0
                    action = space.encode(p, c, pct)
                    decoded = space.decode(action)
                    assert decoded["product_index"] == p
                    assert decoded["channel_index"] == c
                    assert decoded["budget_pct"] == pytest.approx(pct)

    def test_decode_all_actions(self):
        """Test decoding all possible actions."""
        space = DropshippingActionSpace()
        for action in range(space.n_actions):
            decoded = space.decode(action)
            assert 0 <= decoded["product_index"] < space.n_products
            assert 0 <= decoded["channel_index"] < space.n_channels
            assert 0.0 <= decoded["budget_pct"] <= 1.0


class TestMarketConditionSpace:
    """Tests for MarketConditionSpace."""

    def test_bounds(self):
        """Test market condition space bounds."""
        space = MarketConditionSpace()
        assert space.low.shape == (4,)
        assert space.high.shape == (4,)
        assert np.all(space.low == 0.0)
        assert np.all(space.high == 1.0)


class TestInventorySpace:
    """Tests for InventorySpace."""

    def test_bounds(self):
        """Test inventory space bounds."""
        space = InventorySpace(max_inventory=100)
        assert space.low.shape == (3,)
        assert space.high.shape == (3,)
        assert space.low[0] == 0.0
        assert space.high[0] == 100.0


class TestAdPerformanceSpace:
    """Tests for AdPerformanceSpace."""

    def test_bounds(self):
        """Test ad performance space bounds."""
        space = AdPerformanceSpace()
        assert space.low.shape == (6,)
        assert space.high.shape == (6,)


class TestCompetitorPricingSpace:
    """Tests for CompetitorPricingSpace."""

    def test_bounds(self):
        """Test competitor pricing space bounds."""
        space = CompetitorPricingSpace()
        assert space.low.shape == (4,)
        assert space.high.shape == (4,)
