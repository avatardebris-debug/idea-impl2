"""Tests for GBM (Geometric Brownian Motion) simulator."""

import numpy as np
import pytest
from financial_portfolio_simulator.simulators.gbm import GBM
from financial_portfolio_simulator.exceptions import SimulationError


class TestGBMInit:
    """Tests for GBM initialization."""

    def test_default_init(self):
        gbm = GBM()
        assert gbm.drift == 0.05
        assert gbm.volatility == 0.2

    def test_custom_init(self):
        gbm = GBM(drift=0.1, volatility=0.3, seed=42)
        assert gbm.drift == 0.1
        assert gbm.volatility == 0.3

    def test_seed_stored(self):
        gbm = GBM(seed=12345)
        assert gbm.rng is not None

    def test_zero_volatility_allowed(self):
        gbm = GBM(volatility=0.0)
        assert gbm.volatility == 0.0

    def test_negative_volatility_raises(self):
        with pytest.raises(SimulationError):
            GBM(volatility=-0.1)

    def test_non_numeric_drift_raises(self):
        with pytest.raises(SimulationError):
            GBM(drift="high")

    def test_non_numeric_volatility_raises(self):
        with pytest.raises(SimulationError):
            GBM(volatility="high")

    def test_none_seed_allowed(self):
        gbm = GBM(seed=None)
        assert gbm.rng is not None


class TestGBMSimulate:
    """Tests for GBM.simulate method."""

    def test_returns_correct_shape(self):
        gbm = GBM(seed=42)
        paths = gbm.simulate(initial_price=100, time_steps=10, n_paths=5)
        assert paths.shape == (5, 11)  # n_paths, time_steps+1

    def test_first_column_is_initial_price(self):
        gbm = GBM(seed=42)
        paths = gbm.simulate(initial_price=100, time_steps=10)
        assert np.all(paths[:, 0] == 100)

    def test_all_prices_non_negative(self):
        gbm = GBM(drift=0.05, volatility=0.2, seed=42)
        paths = gbm.simulate(initial_price=100, time_steps=100, n_paths=100)
        assert np.all(paths >= 0)

    def test_reproducible_with_seed(self):
        gbm1 = GBM(seed=42)
        gbm2 = GBM(seed=42)
        paths1 = gbm1.simulate(initial_price=100, time_steps=10)
        paths2 = gbm2.simulate(initial_price=100, time_steps=10)
        np.testing.assert_array_equal(paths1, paths2)

    def test_different_seeds_produce_different_results(self):
        gbm1 = GBM(seed=42)
        gbm2 = GBM(seed=99)
        paths1 = gbm1.simulate(initial_price=100, time_steps=10)
        paths2 = gbm2.simulate(initial_price=100, time_steps=10)
        assert not np.array_equal(paths1, paths2)

    def test_n_paths_one(self):
        gbm = GBM(seed=42)
        paths = gbm.simulate(initial_price=100, time_steps=10, n_paths=1)
        assert paths.shape == (1, 11)

    def test_custom_dt(self):
        gbm = GBM(seed=42)
        paths = gbm.simulate(initial_price=100, time_steps=10, dt=1.0)
        assert paths.shape == (1, 11)

    def test_initial_price_zero_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=0, time_steps=10)

    def test_initial_price_negative_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=-10, time_steps=10)

    def test_time_steps_zero_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps=0)

    def test_time_steps_negative_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps=-1)

    def test_dt_zero_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps=10, dt=0)

    def test_dt_negative_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps=10, dt=-0.01)

    def test_n_paths_zero_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps=10, n_paths=0)

    def test_n_paths_negative_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps=10, n_paths=-1)

    def test_non_numeric_initial_price_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price="high", time_steps=10)

    def test_non_numeric_time_steps_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps="10")

    def test_non_integer_time_steps_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps=10.5)

    def test_non_integer_n_paths_raises(self):
        gbm = GBM(seed=42)
        with pytest.raises(SimulationError):
            gbm.simulate(initial_price=100, time_steps=10, n_paths=1.5)

    def test_large_n_paths(self):
        gbm = GBM(seed=42)
        paths = gbm.simulate(initial_price=100, time_steps=10, n_paths=10000)
        assert paths.shape == (10000, 11)
        # Mean of final prices should be roughly near initial * exp(drift * t)
        mean_final = np.mean(paths[:, -1])
        expected_mean = 100 * np.exp(0.05 * (10 / 252))
        # With 10k paths, the mean should be close to expected
        assert abs(mean_final - expected_mean) < expected_mean * 0.1

    def test_zero_volatility_deterministic(self):
        gbm = GBM(drift=0.1, volatility=0.0, seed=42)
        paths = gbm.simulate(initial_price=100, time_steps=10)
        # With zero volatility, all paths should be identical deterministic growth
        expected = 100 * np.exp((0.1 - 0.0) * (10 / 252))
        np.testing.assert_allclose(paths[:, -1], expected, rtol=1e-10)

    def test_high_volatility_still_valid(self):
        gbm = GBM(drift=0.05, volatility=2.0, seed=42)
        paths = gbm.simulate(initial_price=100, time_steps=100, n_paths=100)
        assert np.all(paths >= 0)
        assert paths.shape == (100, 101)


class TestGBMRepr:
    """Tests for GBM string representation."""

    def test_repr_contains_class_name(self):
        gbm = GBM()
        assert "GBM" in repr(gbm)

    def test_repr_contains_drift(self):
        gbm = GBM(drift=0.1)
        assert "0.1" in repr(gbm)

    def test_repr_contains_volatility(self):
        gbm = GBM(volatility=0.3)
        assert "0.3" in repr(gbm)
