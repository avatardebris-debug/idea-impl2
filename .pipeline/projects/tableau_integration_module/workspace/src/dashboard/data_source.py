"""DashboardDataSource class extending MockDataSource.

Generates card-game simulation metrics (win rate, bankroll curve,
Nash equilibrium shift) as ticker updates on a configurable interval.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict

from src.data_source import MockDataSource

from src.dashboard.models import (
    BankrollCurvePoint,
    DashboardState,
    NashEquilibriumShift,
    WinRateMetric,
)
from src.dashboard.tickers import DashboardTicker


@dataclass
class DashboardDataSource(MockDataSource):
    """Data source that produces card-game simulation metrics.

    Extends ``MockDataSource`` and overrides ``_generate_update()`` to
    produce a ``DashboardState`` containing three metric types:
      1. WinRateMetric  – simulated win rate
      2. BankrollCurvePoint – simulated bankroll curve point
      3. NashEquilibriumShift – simulated distance from Nash equilibrium

    Attributes:
        interval: Seconds between updates (inherited from MockDataSource).
        initial_bankroll: Starting bankroll value.
        seed: Random seed for reproducibility.
        _bankroll: Running bankroll accumulator.
        _peak_bankroll: Running peak bankroll.
        _total_games: Total games played counter.
        _wins: Total wins counter.
        _step: Simulation step counter.
        _ticker: The current DashboardTicker instance.
    """

    initial_bankroll: float = 1000.0
    seed: int = 42
    interval: float = 1.0  # seconds between updates
    _bankroll: float = field(default=0.0, init=False)
    _peak_bankroll: float = field(default=0.0, init=False)
    _total_games: int = field(default=0, init=False)
    _wins: int = field(default=0, init=False)
    _step: int = field(default=0, init=False)
    _ticker: DashboardTicker = field(default_factory=DashboardTicker, init=False)

    def __post_init__(self) -> None:
        """Initialize internal state after dataclass construction."""
        # Initialize MockDataSource base class
        MockDataSource.__init__(self, interval=self.interval)
        self._bankroll = self.initial_bankroll
        self._peak_bankroll = self.initial_bankroll
        self._rng = random.Random(self.seed)

    def _generate_update(self) -> Dict[str, Any]:
        """Generate a single DashboardState update payload."""
        self._step += 1

        # --- Win Rate ---
        # Simulate a game outcome and update win rate
        game_won = self._rng.random() < 0.52  # slight edge
        self._total_games += 1
        if game_won:
            self._wins += 1
        win_rate_value = self._wins / self._total_games if self._total_games > 0 else 0.0

        win_rate = WinRateMetric(
            value=round(win_rate_value, 4),
            total_games=self._total_games,
            wins=self._wins,
            losses=self._total_games - self._wins,
            timestamp=time.time(),
        )

        # --- Bankroll Curve ---
        # Simulate a bet outcome
        bet_size = self._bankroll * 0.05  # 5% of current bankroll
        if game_won:
            self._bankroll += bet_size
        else:
            self._bankroll -= bet_size
        self._bankroll = max(self._bankroll, 0.0)

        if self._bankroll > self._peak_bankroll:
            self._peak_bankroll = self._bankroll

        drawdown = (self._bankroll - self._peak_bankroll) / self._peak_bankroll if self._peak_bankroll > 0 else 0.0

        bankroll_point = BankrollCurvePoint(
            step=self._step,
            bankroll=round(self._bankroll, 2),
            peak_bankroll=round(self._peak_bankroll, 2),
            drawdown=round(drawdown, 4),
            timestamp=time.time(),
        )

        # --- Nash Equilibrium Shift ---
        # Simulate distance from Nash equilibrium (random walk)
        nash_distance = max(0.0, self._rng.gauss(0.15, 0.05))

        nash_shift = NashEquilibriumShift(
            distance=round(nash_distance, 4),
            current_strategy=f"strategy_v{self._step}",
            nash_strategy="nash_equilibrium",
            timestamp=time.time(),
        )

        # --- Aggregate ---
        state = DashboardState(
            win_rate=win_rate,
            bankroll=bankroll_point,
            nash_shift=nash_shift,
            timestamp=time.time(),
        )

        # Update internal ticker
        self._ticker.update_from_state(state)

        return state.to_dict()

    @property
    def ticker(self) -> DashboardTicker:
        """Return the current DashboardTicker."""
        return self._ticker

    def get_latest_state(self) -> DashboardState:
        """Return the latest DashboardState from the ticker."""
        return DashboardState(
            win_rate=self._ticker.current_win_rate,
            bankroll=self._ticker.bankroll_history,
            nash_shift=self._ticker.nash_distance,
            timestamp=self._ticker.timestamp,
        )
