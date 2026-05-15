"""Test suite for Phase 1 of Sports Betting Strategy Simulator."""

import pytest
import numpy as np
import time

from engine.market import Market, BetType
from engine.monte_carlo import MonteCarloEngine
from strategies.kelly import KellyStrategy
from backtest.bankroll import Bankroll
from backtest.metrics import MetricsCalculator

class TestMarket:
    def test_decimal_odds_to_implied_prob(self):
        m = Market(bet_type=BetType.MONEYLINE, odds_decimal=2.0, true_probability=0.55)
        assert m.implied_probability == 0.5

    def test_edge(self):
        m = Market(bet_type=BetType.MONEYLINE, odds_decimal=2.0, true_probability=0.55)
        # edge = true_prob - implied_prob = 0.55 - 0.5 = 0.05 (or expected value)
        # Expected value on a $1 bet: 0.55 * 2.0 - 1 = 0.1
        assert m.expected_value == pytest.approx(0.1)

class TestKellyStrategy:
    def test_full_kelly(self):
        m = Market(bet_type=BetType.MONEYLINE, odds_decimal=2.0, true_probability=0.55)
        strategy = KellyStrategy(fractional_factor=1.0)
        # Kelly = (p * b - q) / b
        # b = 1.0 (decimal odds - 1)
        # p = 0.55
        # q = 0.45
        # f = (0.55 * 1.0 - 0.45) / 1.0 = 0.1
        stake_pct = strategy.stake_fraction(bankroll=100.0, market=m)
        assert stake_pct == pytest.approx(0.1)
        
    def test_fractional_kelly(self):
        m = Market(bet_type=BetType.MONEYLINE, odds_decimal=2.0, true_probability=0.55)
        strategy = KellyStrategy(fractional_factor=0.5)
        stake_pct = strategy.stake_fraction(bankroll=100.0, market=m)
        assert stake_pct == pytest.approx(0.05)
        
    def test_negative_edge_kelly(self):
        m = Market(bet_type=BetType.MONEYLINE, odds_decimal=2.0, true_probability=0.45)
        strategy = KellyStrategy(fractional_factor=1.0)
        stake_pct = strategy.stake_fraction(bankroll=100.0, market=m)
        assert stake_pct == 0.0

class TestMonteCarloEngine:
    def test_simulate_outcomes_speed(self):
        engine = MonteCarloEngine(seed=42)
        m = Market(bet_type=BetType.MONEYLINE, odds_decimal=2.0, true_probability=0.55)
        
        start_time = time.time()
        wins, pnl = engine.simulate(m, n_outcomes=100_000)
        end_time = time.time()
        
        assert len(wins) == 100_000
        assert (end_time - start_time) < 5.0
        
        win_rate = np.mean(wins)
        assert win_rate == pytest.approx(0.55, abs=0.01)

class TestMetrics:
    def test_metrics_calculation(self):
        # mock some bet records
        # A win, a loss, a win
        # Start bankroll 100
        # Bet 10 at 2.0 (win) -> +10 -> 110
        # Bet 10 at 2.0 (loss) -> -10 -> 100
        # Bet 10 at 2.0 (win) -> +10 -> 110
        b = Bankroll(initial_bankroll=100.0)
        b.bet(stake=10.0, won=True, payout_multiplier=1.0)
        b.bet(stake=10.0, won=False, payout_multiplier=1.0)
        b.bet(stake=10.0, won=True, payout_multiplier=1.0)
        
        assert b.current_bankroll == 110.0
        
        # Actually need to test MetricsCalculator which takes records
        # Assuming MetricsCalculator exists and works on bankroll history
        # Let's import it and check its API.
