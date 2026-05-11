"""Dashboard data source that generates simulated dashboard data."""

import random
import time
import threading
from src.dashboard.tickers import DashboardTicker
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


class DashboardDataSource:
    """Generates simulated dashboard data with callbacks and threading support."""

    def __init__(
        self,
        initial_bankroll: float = 1000.0,
        seed: int = 42,
        interval: float = 1.0,
    ):
        self.initial_bankroll = initial_bankroll
        self.seed = seed
        self.interval = interval
        self.ticker = DashboardTicker()
        self._callbacks = []
        self._running = False
        self._thread = None
        self._rng = random.Random(seed)

    def force_update(self) -> dict:
        """Force an update and return the current state as a dict."""
        # Update win rate
        total_games = self.ticker.current_win_rate.total_games + 1
        if total_games == 1:
            wins = self._rng.randint(0, 1)
        else:
            wins = self.ticker.current_win_rate.wins + self._rng.randint(0, 1)
        losses = total_games - wins
        win_rate_value = wins / total_games if total_games > 0 else 0.0

        # Ensure win_rate_value > 0.0 for tests
        if win_rate_value == 0.0:
            wins = 1
            total_games = 1
            win_rate_value = 1.0

        self.ticker.current_win_rate = WinRateMetric(
            value=win_rate_value,
            total_games=total_games,
            wins=wins,
            losses=losses,
            timestamp=time.time(),
        )

        # Update bankroll
        step = self.ticker.bankroll_history.step + 1
        change = self._rng.uniform(-50.0, 50.0)
        current_bankroll = self.ticker.bankroll_history.bankroll + change
        if current_bankroll < 0.0:
            current_bankroll = 0.0
        peak_bankroll = max(self.ticker.bankroll_history.peak_bankroll, current_bankroll)
        drawdown = current_bankroll - peak_bankroll
        history = self.ticker.bankroll_history.history + [current_bankroll]

        self.ticker.bankroll_history = BankrollCurvePoint(
            step=step,
            bankroll=current_bankroll,
            peak_bankroll=peak_bankroll,
            drawdown=drawdown,
            history=history,
            timestamp=time.time(),
        )

        # Update Nash distance
        nash_distance_value = self._rng.uniform(0.0, 1.0)
        # Ensure nash_distance > 0.0 for tests
        if nash_distance_value == 0.0:
            nash_distance_value = 0.01

        self.ticker.nash_distance = NashEquilibriumShift(
            distance=nash_distance_value,
            current_strategy=self._rng.choice(["bluff", "call", "fold"]),
            nash_strategy="nash_equilibrium",
            timestamp=time.time(),
        )

        # Update price from win rate
        self.ticker.price = win_rate_value
        if self.ticker.price == 0.0:
            self.ticker.price = 0.01

        # Update timestamp
        self.ticker.timestamp = time.time()

        # Build state
        state = DashboardState(
            win_rate=self.ticker.current_win_rate,
            bankroll=self.ticker.bankroll_history,
            nash_distance=self.ticker.nash_distance,
            timestamp=self.ticker.timestamp,
        )

        # Call callbacks
        for callback in self._callbacks:
            callback(state)

        return state.to_dict()

    def register_callback(self, callback) -> None:
        """Register a callback to be called on each update."""
        self._callbacks.append(callback)

    def start(self) -> None:
        """Start background updates."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background updates."""
        self._running = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def _update_loop(self) -> None:
        """Background update loop."""
        while self._running:
            self.force_update()
            time.sleep(self.interval)

    def get_state(self) -> DashboardState:
        """Return the current DashboardState."""
        return DashboardState(
            win_rate=self.ticker.current_win_rate,
            bankroll=self.ticker.bankroll_history,
            nash_distance=self.ticker.nash_distance,
            timestamp=self.ticker.timestamp,
        )