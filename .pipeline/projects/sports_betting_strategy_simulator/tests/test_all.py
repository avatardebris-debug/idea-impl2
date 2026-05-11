"""Tests for the sports betting strategy simulator."""

import unittest
import numpy as np
from workspace.engine.market import Market, BetType, OddsFormat
from workspace.engine.monte_carlo import MonteCarloEngine
from workspace.strategies.kelly import KellyStrategy, FixedStakeStrategy
from workspace.backtest.bankroll import Bankroll
from workspace.backtest.runner import BacktestRunner
from workspace.backtest.metrics import MetricsCalculator


class TestMarket(unittest.TestCase):
    """Tests for the Market class."""

    def test_decimal_to_american_positive(self):
        """Test decimal odds conversion to positive American odds."""
        market = Market(odds_decimal=2.50)
        self.assertEqual(market.odds_american, 150)

    def test_decimal_to_american_negative(self):
        """Test decimal odds conversion to negative American odds."""
        market = Market(odds_decimal=1.50)
        self.assertEqual(market.odds_american, -200)

    def test_american_to_decimal_positive(self):
        """Test American odds conversion to decimal."""
        market = Market(odds_american=150)
        self.assertAlmostEqual(market.odds_decimal, 2.50, places=2)

    def test_american_to_decimal_negative(self):
        """Test American odds conversion to decimal."""
        market = Market(odds_american=-110)
        self.assertAlmostEqual(market.odds_decimal, 1.909, places=3)

    def test_fractional_to_decimal(self):
        """Test fractional odds conversion to decimal."""
        market = Market(odds_fractional=(3, 2))
        self.assertAlmostEqual(market.odds_decimal, 2.50, places=2)

    def test_implied_probability(self):
        """Test implied probability calculation."""
        market = Market(odds_decimal=2.0)
        self.assertAlmostEqual(market.implied_probability, 0.50, places=2)

    def test_edge_positive(self):
        """Test edge calculation when true probability > implied."""
        market = Market(odds_decimal=2.50, true_probability=0.55)
        self.assertGreater(market.edge, 0)

    def test_edge_negative(self):
        """Test edge calculation when true probability < implied."""
        market = Market(odds_decimal=2.0, true_probability=0.45)
        self.assertLess(market.edge, 0)

    def test_payout_multiplier(self):
        """Test payout multiplier calculation."""
        market = Market(odds_decimal=2.50)
        self.assertAlmostEqual(market.payout_multiplier, 1.50, places=2)


class TestMonteCarloEngine(unittest.TestCase):
    """Tests for the MonteCarloEngine class."""

    def test_simulate_returns_correct_shapes(self):
        """Test that simulate returns arrays of correct shape."""
        market = Market(odds_decimal=2.0, true_probability=0.5)
        engine = MonteCarloEngine(seed=42)
        wins, pnl = engine.simulate(market, n_outcomes=1000)
        self.assertEqual(len(wins), 1000)
        self.assertEqual(len(pnl), 1000)

    def test_simulate_wins_are_boolean(self):
        """Test that wins array contains boolean values."""
        market = Market(odds_decimal=2.0, true_probability=0.5)
        engine = MonteCarloEngine(seed=42)
        wins, _ = engine.simulate(market, n_outcomes=100)
        self.assertTrue(all(isinstance(w, (bool, np.bool_)) for w in wins))

    def test_simulate_pnl_values(self):
        """Test that P&L values are correct for unit stake."""
        market = Market(odds_decimal=2.50, true_probability=0.5)
        engine = MonteCarloEngine(seed=42)
        _, pnl = engine.simulate(market, n_outcomes=100)
        # For decimal odds 2.50, payout_multiplier is 1.50
        # Win: +1.50, Loss: -1.00
        unique_pnl = set(pnl)
        self.assertIn(1.50, unique_pnl)
        self.assertIn(-1.00, unique_pnl)

    def test_simulate_with_custom_stakes(self):
        """Test simulate_with_custom_stakes."""
        market = Market(odds_decimal=2.0, true_probability=0.5)
        engine = MonteCarloEngine(seed=42)
        stakes = np.array([10.0, 20.0, 30.0])
        wins, pnl = engine.simulate_with_custom_stakes(market, stakes)
        self.assertEqual(len(wins), 3)
        self.assertEqual(len(pnl), 3)

    def test_reproducibility(self):
        """Test that simulation is reproducible with same seed."""
        market = Market(odds_decimal=2.0, true_probability=0.5)
        engine1 = MonteCarloEngine(seed=42)
        engine2 = MonteCarloEngine(seed=42)
        wins1, pnl1 = engine1.simulate(market, n_outcomes=100)
        wins2, pnl2 = engine2.simulate(market, n_outcomes=100)
        np.testing.assert_array_equal(wins1, wins2)
        np.testing.assert_array_equal(pnl1, pnl2)


class TestKellyStrategy(unittest.TestCase):
    """Tests for the KellyStrategy class."""

    def test_kelly_positive_edge(self):
        """Test Kelly strategy with positive edge."""
        market = Market(odds_decimal=2.0, true_probability=0.55)
        strategy = KellyStrategy(fractional_factor=1.0)
        fraction = strategy.stake_fraction(1000, market)
        self.assertGreater(fraction, 0)

    def test_kelly_negative_edge(self):
        """Test Kelly strategy with negative edge."""
        market = Market(odds_decimal=2.0, true_probability=0.45)
        strategy = KellyStrategy(fractional_factor=1.0)
        fraction = strategy.stake_fraction(1000, market)
        self.assertEqual(fraction, 0)

    def test_half_kelly(self):
        """Test half-Kelly strategy."""
        market = Market(odds_decimal=2.0, true_probability=0.55)
        full_kelly = KellyStrategy(fractional_factor=1.0)
        half_kelly = KellyStrategy(fractional_factor=0.5)
        full_fraction = full_kelly.stake_fraction(1000, market)
        half_fraction = half_kelly.stake_fraction(1000, market)
        self.assertAlmostEqual(half_fraction, full_fraction / 2, places=6)

    def test_fixed_stake_strategy(self):
        """Test fixed stake strategy."""
        market = Market(odds_decimal=2.0, true_probability=0.55)
        strategy = FixedStakeStrategy(stake_fraction=0.02)
        fraction = strategy.stake_fraction(1000, market)
        self.assertAlmostEqual(fraction, 0.02, places=6)

    def test_fixed_stake_independent_of_bankroll(self):
        """Test that fixed stake is independent of bankroll."""
        market = Market(odds_decimal=2.0, true_probability=0.55)
        strategy = FixedStakeStrategy(stake_fraction=0.02)
        fraction1 = strategy.stake_fraction(1000, market)
        fraction2 = strategy.stake_fraction(5000, market)
        self.assertAlmostEqual(fraction1, fraction2, places=6)


class TestBankroll(unittest.TestCase):
    """Tests for the Bankroll class."""

    def test_initial_bankroll(self):
        """Test initial bankroll setup."""
        bankroll = Bankroll(initial_bankroll=1000)
        self.assertEqual(bankroll.current_bankroll, 1000)
        self.assertEqual(len(bankroll.history), 1)
        self.assertEqual(bankroll.history[0], 1000)

    def test_bet_win(self):
        """Test bankroll update on win."""
        bankroll = Bankroll(initial_bankroll=1000)
        profit = bankroll.bet(stake=100, won=True, payout_multiplier=1.50)
        self.assertEqual(profit, 150)
        self.assertEqual(bankroll.current_bankroll, 1150)
        self.assertEqual(len(bankroll.history), 2)

    def test_bet_loss(self):
        """Test bankroll update on loss."""
        bankroll = Bankroll(initial_bankroll=1000)
        profit = bankroll.bet(stake=100, won=False, payout_multiplier=1.50)
        self.assertEqual(profit, -100)
        self.assertEqual(bankroll.current_bankroll, 900)

    def test_net_profit(self):
        """Test net profit calculation."""
        bankroll = Bankroll(initial_bankroll=1000)
        bankroll.bet(stake=100, won=True, payout_multiplier=1.50)
        bankroll.bet(stake=100, won=False, payout_multiplier=1.50)
        self.assertEqual(bankroll.net_profit, 50)

    def test_total_return(self):
        """Test total return calculation."""
        bankroll = Bankroll(initial_bankroll=1000)
        bankroll.bet(stake=100, won=True, payout_multiplier=1.50)
        self.assertAlmostEqual(bankroll.total_return, 0.15, places=6)

    def test_reset(self):
        """Test bankroll reset."""
        bankroll = Bankroll(initial_bankroll=1000)
        bankroll.bet(stake=100, won=True, payout_multiplier=1.50)
        bankroll.reset()
        self.assertEqual(bankroll.current_bankroll, 1000)
        self.assertEqual(len(bankroll.history), 1)


class TestBacktestRunner(unittest.TestCase):
    """Tests for the BacktestRunner class."""

    def test_run_returns_records(self):
        """Test that run returns BetRecord objects."""
        market = Market(odds_decimal=2.0, true_probability=0.5)
        bankroll = Bankroll(initial_bankroll=1000)
        strategy = FixedStakeStrategy(stake_fraction=0.02)
        runner = BacktestRunner(
            strategy=strategy,
            market=market,
            bankroll=bankroll,
            n_bets=10,
            seed=42,
        )
        records = runner.run()
        self.assertEqual(len(records), 10)
        self.assertTrue(all(hasattr(r, 'bet_index') for r in records))

    def test_final_bankroll(self):
        """Test final bankroll after backtest."""
        market = Market(odds_decimal=2.0, true_probability=0.5)
        bankroll = Bankroll(initial_bankroll=1000)
        strategy = FixedStakeStrategy(stake_fraction=0.02)
        runner = BacktestRunner(
            strategy=strategy,
            market=market,
            bankroll=bankroll,
            n_bets=100,
            seed=42,
        )
        runner.run()
        self.assertGreater(runner.final_bankroll, 0)


class TestMetricsCalculator(unittest.TestCase):
    """Tests for the MetricsCalculator class."""

    def test_compute_metrics(self):
        """Test metrics computation."""
        records = [
            type('BetRecord', (), {
                'bet_index': i,
                'stake': 10.0,
                'won': i % 2 == 0,
                'pnl': 15.0 if i % 2 == 0 else -10.0,
                'bankroll_after': 1000 + (i + 1) * 2.5,
                'market_odds_decimal': 2.0,
                'true_probability': 0.5,
            })()
            for i in range(10)
        ]
        calculator = MetricsCalculator(records, initial_bankroll=1000)
        metrics = calculator.compute()
        self.assertIn('total_return', metrics)
        self.assertIn('roi', metrics)
        self.assertIn('win_rate', metrics)
        self.assertIn('max_drawdown', metrics)
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('final_bankroll', metrics)

    def test_empty_records(self):
        """Test metrics computation with no records."""
        calculator = MetricsCalculator([], initial_bankroll=1000)
        metrics = calculator.compute()
        self.assertEqual(metrics['total_return'], 0.0)
        self.assertEqual(metrics['win_rate'], 0.0)


if __name__ == "__main__":
    unittest.main()
