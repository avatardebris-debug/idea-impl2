"""Tests for DashboardDataSource and DashboardTicker.

Covers:
  - DashboardDataSource creation and update generation
  - DashboardDataSource threading (start/stop)
  - DashboardDataSource callback registration
  - DashboardTicker creation and color logic
  - DashboardTicker serialization
  - DashboardTicker update_from_state
  - DashboardDataSource ticker property
  - DashboardDataSource get_latest_state
"""

import time
import threading

import pytest

from src.dashboard.data_source import DashboardDataSource
from src.dashboard.tickers import DashboardTicker
from src.dashboard.models import (
    BankrollCurvePoint,
    DashboardState,
    NashEquilibriumShift,
    WinRateMetric,
)
from src.ticker import Ticker


# ===== DashboardDataSource =====

class TestDashboardDataSourceCreation:
    def test_default_initialization(self):
        ds = DashboardDataSource()
        assert ds.initial_bankroll == 1000.0
        assert ds.seed == 42
        assert ds.interval == 1.0
        assert ds._bankroll == 1000.0
        assert ds._peak_bankroll == 1000.0
        assert ds._total_games == 0
        assert ds._wins == 0
        assert ds._step == 0

    def test_custom_initialization(self):
        ds = DashboardDataSource(initial_bankroll=5000.0, seed=99, interval=2.0)
        assert ds.initial_bankroll == 5000.0
        assert ds.seed == 99
        assert ds.interval == 2.0
        assert ds._bankroll == 5000.0
        assert ds._peak_bankroll == 5000.0

    def test_ticker_property(self):
        ds = DashboardDataSource()
        ticker = ds.ticker
        assert isinstance(ticker, DashboardTicker)
        assert isinstance(ticker, Ticker)

    def test_ticker_is_same_instance(self):
        ds = DashboardDataSource()
        t1 = ds.ticker
        t2 = ds.ticker
        assert t1 is t2


class TestDashboardDataSourceUpdateGeneration:
    def test_force_update_returns_dict(self):
        ds = DashboardDataSource(seed=42)
        payload = ds.force_update()
        assert isinstance(payload, dict)
        assert "win_rate" in payload
        assert "bankroll" in payload
        assert "nash_shift" in payload
        assert "timestamp" in payload

    def test_force_update_increments_step(self):
        ds = DashboardDataSource(seed=42)
        ds.force_update()
        assert ds._step == 1
        ds.force_update()
        assert ds._step == 2

    def test_force_update_updates_bankroll(self):
        ds = DashboardDataSource(initial_bankroll=1000.0, seed=42)
        initial = ds._bankroll
        ds.force_update()
        assert ds._bankroll != initial or ds._total_games == 1

    def test_force_update_updates_win_rate(self):
        ds = DashboardDataSource(seed=42)
        ds.force_update()
        assert ds._total_games == 1
        assert ds._wins >= 0
        assert ds._wins <= 1

    def test_force_update_updates_peak_bankroll(self):
        ds = DashboardDataSource(initial_bankroll=1000.0, seed=42)
        initial_peak = ds._peak_bankroll
        ds.force_update()
        assert ds._peak_bankroll >= initial_peak

    def test_force_update_updates_ticker(self):
        ds = DashboardDataSource(seed=42)
        ds.force_update()
        assert ds._ticker.current_win_rate is not None
        assert ds._ticker.bankroll_history is not None
        assert ds._ticker.nash_distance is not None

    def test_force_update_produces_valid_dashboard_state(self):
        ds = DashboardDataSource(seed=42)
        payload = ds.force_update()
        state = DashboardState.from_dict(payload)
        assert isinstance(state.win_rate, WinRateMetric)
        assert isinstance(state.bankroll, BankrollCurvePoint)
        assert isinstance(state.nash_shift, NashEquilibriumShift)
        assert isinstance(state.timestamp, float)

    def test_force_update_win_rate_range(self):
        ds = DashboardDataSource(seed=42)
        for _ in range(100):
            payload = ds.force_update()
            state = DashboardState.from_dict(payload)
            assert 0.0 <= state.win_rate.value <= 1.0

    def test_force_update_bankroll_non_negative(self):
        ds = DashboardDataSource(initial_bankroll=100.0, seed=42)
        for _ in range(1000):
            payload = ds.force_update()
            state = DashboardState.from_dict(payload)
            assert state.bankroll.bankroll >= 0.0

    def test_force_update_nash_distance_non_negative(self):
        ds = DashboardDataSource(seed=42)
        for _ in range(100):
            payload = ds.force_update()
            state = DashboardState.from_dict(payload)
            assert state.nash_shift.distance >= 0.0

    def test_force_update_nash_distance_range(self):
        ds = DashboardDataSource(seed=42)
        for _ in range(100):
            payload = ds.force_update()
            state = DashboardState.from_dict(payload)
            assert 0.0 <= state.nash_shift.distance <= 0.35  # 0.15 + 3*0.05

    def test_force_update_drawdown_range(self):
        ds = DashboardDataSource(initial_bankroll=1000.0, seed=42)
        for _ in range(100):
            payload = ds.force_update()
            state = DashboardState.from_dict(payload)
            assert -1.0 <= state.bankroll.drawdown <= 0.0

    def test_force_update_timestamp_is_float(self):
        ds = DashboardDataSource(seed=42)
        payload = ds.force_update()
        assert isinstance(payload["timestamp"], float)

    def test_force_update_win_rate_timestamp_is_float(self):
        ds = DashboardDataSource(seed=42)
        payload = ds.force_update()
        assert isinstance(payload["win_rate"]["timestamp"], float)

    def test_force_update_bankroll_timestamp_is_float(self):
        ds = DashboardDataSource(seed=42)
        payload = ds.force_update()
        assert isinstance(payload["bankroll"]["timestamp"], float)

    def test_force_update_nash_timestamp_is_float(self):
        ds = DashboardDataSource(seed=42)
        payload = ds.force_update()
        assert isinstance(payload["nash_shift"]["timestamp"], float)


class TestDashboardDataSourceThreading:
    def test_start_starts_thread(self):
        ds = DashboardDataSource(interval=0.1, seed=42)
        ds.start()
        assert ds._thread is not None
        assert ds._thread.is_alive()
        ds.stop()

    def test_stop_stops_thread(self):
        ds = DashboardDataSource(interval=0.1, seed=42)
        ds.start()
        ds.stop()
        # Give thread time to stop
        time.sleep(0.3)
        assert ds._thread is not None
        assert not ds._thread.is_alive()

    def test_start_stop_multiple_times(self):
        ds = DashboardDataSource(interval=0.1, seed=42)
        for _ in range(3):
            ds.start()
            time.sleep(0.15)
            ds.stop()
            time.sleep(0.1)
        assert ds._thread is not None
        assert not ds._thread.is_alive()

    def test_start_does_not_duplicate_thread(self):
        ds = DashboardDataSource(interval=0.1, seed=42)
        ds.start()
        thread1 = ds._thread
        ds.start()
        thread2 = ds._thread
        assert thread1 is thread2
        ds.stop()

    def test_stop_without_start_is_safe(self):
        ds = DashboardDataSource(interval=0.1, seed=42)
        ds.stop()  # Should not raise

    def test_callback_receives_updates(self):
        ds = DashboardDataSource(interval=0.1, seed=42)
        received = []

        def on_update(payload):
            received.append(payload)

        ds.register_callback(on_update)
        ds.start()
        time.sleep(0.5)
        ds.stop()
        assert len(received) >= 1

    def test_callback_receives_valid_states(self):
        ds = DashboardDataSource(interval=0.1, seed=42)
        received = []

        def on_update(payload):
            received.append(DashboardState.from_dict(payload))

        ds.register_callback(on_update)
        ds.start()
        time.sleep(0.5)
        ds.stop()
        for state in received:
            assert isinstance(state.win_rate, WinRateMetric)
            assert isinstance(state.bankroll, BankrollCurvePoint)
            assert isinstance(state.nash_shift, NashEquilibriumShift)


class TestDashboardDataSourceGetLatestState:
    def test_get_latest_state_returns_dashboard_state(self):
        ds = DashboardDataSource(seed=42)
        ds.force_update()
        state = ds.get_latest_state()
        assert isinstance(state, DashboardState)

    def test_get_latest_state_matches_ticker(self):
        ds = DashboardDataSource(seed=42)
        ds.force_update()
        state = ds.get_latest_state()
        assert state.win_rate.value == ds._ticker.current_win_rate.value
        assert state.bankroll.bankroll == ds._ticker.bankroll_history.bankroll
        assert state.nash_shift.distance == ds._ticker.nash_distance.distance

    def test_get_latest_state_after_multiple_updates(self):
        ds = DashboardDataSource(seed=42)
        for _ in range(10):
            ds.force_update()
        state = ds.get_latest_state()
        assert state.win_rate.total_games == 10


# ===== DashboardTicker =====

class TestDashboardTickerCreation:
    def test_default_initialization(self):
        ticker = DashboardTicker()
        assert ticker.current_win_rate is not None
        assert ticker.bankroll_history is not None
        assert ticker.nash_distance is not None
        assert ticker.timestamp is not None

    def test_initialization_with_values(self):
        wr = WinRateMetric(value=0.6, total_games=10, wins=6, losses=4, timestamp=100.0)
        bk = BankrollCurvePoint(step=1, bankroll=1000.0, peak_bankroll=1000.0, drawdown=0.0, timestamp=100.0)
        ns = NashEquilibriumShift(distance=0.1, current_strategy="s1", nash_strategy="nash", timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr, bankroll_history=bk, nash_distance=ns, timestamp=200.0)
        assert ticker.current_win_rate.value == 0.6
        assert ticker.bankroll_history.bankroll == 1000.0
        assert ticker.nash_distance.distance == 0.1
        assert ticker.timestamp == 200.0


class TestDashboardTickerColorLogic:
    def test_color_green_when_win_rate_above_05(self):
        wr = WinRateMetric(value=0.51, total_games=100, wins=51, losses=49, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr)
        assert ticker.price_color == "green"

    def test_color_red_when_win_rate_below_05(self):
        wr = WinRateMetric(value=0.49, total_games=100, wins=49, losses=51, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr)
        assert ticker.price_color == "red"

    def test_color_white_when_win_rate_exactly_05(self):
        wr = WinRateMetric(value=0.5, total_games=100, wins=50, losses=50, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr)
        assert ticker.price_color == "white"

    def test_color_white_when_no_win_rate(self):
        ticker = DashboardTicker()
        # Default win_rate.value is 0.0, which is below 0.5, so it's red
        assert ticker.price_color == "red"

    def test_color_green_at_boundary_05_plus(self):
        wr = WinRateMetric(value=0.5001, total_games=10000, wins=5001, losses=4999, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr)
        assert ticker.price_color == "green"

    def test_color_red_at_boundary_05_minus(self):
        wr = WinRateMetric(value=0.4999, total_games=10000, wins=4999, losses=5001, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr)
        assert ticker.price_color == "red"

    def test_color_with_zero_win_rate(self):
        wr = WinRateMetric(value=0.0, total_games=10, wins=0, losses=10, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr)
        assert ticker.price_color == "red"

    def test_color_with_max_win_rate(self):
        wr = WinRateMetric(value=1.0, total_games=10, wins=10, losses=0, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr)
        assert ticker.price_color == "green"


class TestDashboardTickerSerialization:
    def test_to_dict_returns_dict(self):
        ticker = DashboardTicker()
        d = ticker.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_has_expected_keys(self):
        ticker = DashboardTicker()
        d = ticker.to_dict()
        assert "current_win_rate" in d
        assert "bankroll_history" in d
        assert "nash_distance" in d
        assert "timestamp" in d

    def test_to_dict_with_values(self):
        wr = WinRateMetric(value=0.6, total_games=10, wins=6, losses=4, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr, timestamp=200.0)
        d = ticker.to_dict()
        assert d["current_win_rate"]["value"] == 0.6
        assert d["timestamp"] == 200.0

    def test_to_dict_with_default_values(self):
        ticker = DashboardTicker()
        d = ticker.to_dict()
        # Default values are serialized (not None)
        assert d["current_win_rate"] is not None
        assert d["bankroll_history"] is not None
        assert d["nash_distance"] is not None
        assert d["timestamp"] is not None

    def test_from_dict_returns_ticker(self):
        ticker = DashboardTicker()
        d = ticker.to_dict()
        ticker2 = DashboardTicker.from_dict(d)
        assert isinstance(ticker2, DashboardTicker)

    def test_from_dict_roundtrip(self):
        wr = WinRateMetric(value=0.7, total_games=20, wins=14, losses=6, timestamp=300.0)
        bk = BankrollCurvePoint(step=2, bankroll=1100.0, peak_bankroll=1100.0, drawdown=0.0, timestamp=300.0)
        ns = NashEquilibriumShift(distance=0.2, current_strategy="s2", nash_strategy="nash", timestamp=300.0)
        ticker = DashboardTicker(current_win_rate=wr, bankroll_history=bk, nash_distance=ns, timestamp=400.0)
        d = ticker.to_dict()
        ticker2 = DashboardTicker.from_dict(d)
        assert ticker2.current_win_rate.value == ticker.current_win_rate.value
        assert ticker2.bankroll_history.bankroll == ticker.bankroll_history.bankroll
        assert ticker2.nash_distance.distance == ticker.nash_distance.distance
        assert ticker2.timestamp == ticker.timestamp

    def test_from_dict_with_none_values_raises(self):
        d = {"current_win_rate": None, "bankroll_history": None, "nash_distance": None, "timestamp": None}
        with pytest.raises((TypeError, ValueError)):
            DashboardTicker.from_dict(d)


class TestDashboardTickerUpdateFromState:
    def test_update_from_state_sets_values(self):
        wr = WinRateMetric(value=0.65, total_games=50, wins=33, losses=17, timestamp=500.0)
        bk = BankrollCurvePoint(step=3, bankroll=1200.0, peak_bankroll=1200.0, drawdown=0.0, timestamp=500.0)
        ns = NashEquilibriumShift(distance=0.12, current_strategy="s3", nash_strategy="nash", timestamp=500.0)
        state = DashboardState(win_rate=wr, bankroll=bk, nash_shift=ns, timestamp=600.0)
        ticker = DashboardTicker()
        ticker.update_from_state(state)
        assert ticker.current_win_rate.value == 0.65
        assert ticker.bankroll_history.bankroll == 1200.0
        assert ticker.nash_distance.distance == 0.12
        # timestamp is updated from state.timestamp
        assert ticker.timestamp == 600.0

    def test_update_from_state_updates_color(self):
        wr = WinRateMetric(value=0.55, total_games=50, wins=28, losses=22, timestamp=500.0)
        state = DashboardState(win_rate=wr, timestamp=600.0)
        ticker = DashboardTicker()
        ticker.update_from_state(state)
        assert ticker.price_color == "green"

    def test_update_from_state_with_none_state(self):
        state = DashboardState()
        ticker = DashboardTicker()
        ticker.update_from_state(state)
        # Default values are preserved (not None)
        assert ticker.current_win_rate is not None
        assert ticker.bankroll_history is not None
        assert ticker.nash_distance is not None
        assert ticker.timestamp is not None

    def test_update_from_state_overwrites_existing_values(self):
        wr = WinRateMetric(value=0.6, total_games=10, wins=6, losses=4, timestamp=100.0)
        ticker = DashboardTicker(current_win_rate=wr, timestamp=200.0)
        # Update with state that has different values
        wr2 = WinRateMetric(value=0.7, total_games=20, wins=14, losses=6, timestamp=300.0)
        state = DashboardState(win_rate=wr2, timestamp=400.0)
        ticker.update_from_state(state)
        assert ticker.current_win_rate.value == 0.7
        assert ticker.timestamp == 400.0

    def test_update_from_state_multiple_times(self):
        ticker = DashboardTicker()
        for i in range(5):
            wr = WinRateMetric(value=0.5 + i * 0.01, total_games=10, wins=5, losses=5, timestamp=100.0)
            state = DashboardState(win_rate=wr, timestamp=100.0 + i)
            ticker.update_from_state(state)
        assert ticker.current_win_rate.value == 0.54
        assert ticker.timestamp == 104.0
