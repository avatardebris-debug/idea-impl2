"""Tests for src.dashboard.data_source.DashboardDataSource."""

import time
import threading
import pytest
from src.dashboard.data_source import DashboardDataSource
from src.dashboard.tickers import DashboardTicker
from src.dashboard.models import DashboardState


class TestDashboardDataSourceInit:
    def test_default_values(self):
        ds = DashboardDataSource()
        assert ds.initial_bankroll == 1000.0
        assert ds.seed == 42
        assert ds.interval == 1.0
        assert isinstance(ds.ticker, DashboardTicker)

    def test_custom_values(self):
        ds = DashboardDataSource(initial_bankroll=5000.0, seed=123, interval=0.5)
        assert ds.initial_bankroll == 5000.0
        assert ds.seed == 123
        assert ds.interval == 0.5


class TestDashboardDataSourceForceUpdate:
    def test_force_update_returns_dict(self):
        ds = DashboardDataSource()
        result = ds.force_update()
        assert isinstance(result, dict)
        assert "win_rate" in result
        assert "bankroll" in result
        assert "nash_distance" in result

    def test_force_update_updates_ticker(self):
        ds = DashboardDataSource()
        ds.force_update()
        assert ds.ticker.price > 0.0
        assert ds.ticker.current_win_rate.value > 0.0

    def test_force_update_increments_step(self):
        ds = DashboardDataSource()
        ds.force_update()
        step1 = ds.ticker.bankroll_history.step
        ds.force_update()
        step2 = ds.ticker.bankroll_history.step
        assert step2 == step1 + 1

    def test_force_update_updates_win_rate(self):
        ds = DashboardDataSource()
        ds.force_update()
        wr1 = ds.ticker.current_win_rate.value
        ds.force_update()
        wr2 = ds.ticker.current_win_rate.value
        # Win rate should be between 0 and 1
        assert 0.0 <= wr1 <= 1.0
        assert 0.0 <= wr2 <= 1.0

    def test_force_update_updates_bankroll(self):
        ds = DashboardDataSource()
        ds.force_update()
        assert ds.ticker.bankroll_history.bankroll >= 0.0

    def test_force_update_updates_nash_distance(self):
        ds = DashboardDataSource()
        ds.force_update()
        assert 0.0 <= ds.ticker.nash_distance.distance <= 1.0

    def test_multiple_updates_produce_different_values(self):
        ds = DashboardDataSource()
        values = []
        for _ in range(10):
            ds.force_update()
            values.append(ds.ticker.current_win_rate.value)
        # Values should vary (not all the same)
        assert len(set(values)) > 1

    def test_force_update_updates_timestamp(self):
        ds = DashboardDataSource()
        before = time.time()
        ds.force_update()
        after = time.time()
        assert before <= ds.ticker.timestamp <= after


class TestDashboardDataSourceCallbacks:
    def test_register_callback(self):
        ds = DashboardDataSource()
        received = []
        ds.register_callback(lambda x: received.append(x))
        ds.force_update()
        assert len(received) == 1
        assert isinstance(received[0], DashboardState)

    def test_multiple_callbacks(self):
        ds = DashboardDataSource()
        received1 = []
        received2 = []
        ds.register_callback(lambda x: received1.append(x))
        ds.register_callback(lambda x: received2.append(x))
        ds.force_update()
        assert len(received1) == 1
        assert len(received2) == 1
        assert received1[0] == received2[0]


class TestDashboardDataSourceThreading:
    def test_start_and_stop(self):
        ds = DashboardDataSource(interval=0.01)
        ds.start()
        time.sleep(0.05)
        ds.stop()
        # Ticker should have been updated
        assert ds.ticker.price > 0.0

    def test_background_updates(self):
        ds = DashboardDataSource(interval=0.01)
        ds.start()
        time.sleep(0.05)
        initial_price = ds.ticker.price
        time.sleep(0.05)
        ds.stop()
        # Price should have changed due to background updates
        assert ds.ticker.price != initial_price


class TestDashboardDataSourceGetState:
    def test_get_state_returns_dashboard_state(self):
        ds = DashboardDataSource()
        ds.force_update()
        state = ds.get_state()
        assert isinstance(state, DashboardState)
        assert state.win_rate.value == ds.ticker.current_win_rate.value
        assert state.bankroll.bankroll == ds.ticker.bankroll_history.bankroll
        assert state.nash_distance.distance == ds.ticker.nash_distance.distance
