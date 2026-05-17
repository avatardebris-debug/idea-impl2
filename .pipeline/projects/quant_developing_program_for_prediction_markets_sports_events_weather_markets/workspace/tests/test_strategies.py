"""Tests for quant_developing_program.core.strategies."""

import pytest
import numpy as np

from quant_developing_program.core.strategies import (
    RSI,
    MACD,
    BettingStrategy,
    StrategySignal,
)


class TestRSI:
    def test_initialization(self):
        rsi = RSI(period=14)
        assert rsi.period == 14

    def test_calculate(self):
        rsi = RSI(period=14)
        prices = list(range(1, 30))
        result = rsi.calculate(prices)
        assert len(result.values) == len(prices)
        assert all(0 <= v <= 100 for v in result.values if not np.isnan(v))

    def test_overbought(self):
        rsi = RSI(period=14, overbought=70)
        # Strong uptrend
        prices = [100 + i * 10 for i in range(20)]
        result = rsi.calculate(prices)
        assert result.overbought is not None

    def test_oversold(self):
        rsi = RSI(period=14, oversold=30)
        # Strong downtrend
        prices = [100 - i * 10 for i in range(20)]
        result = rsi.calculate(prices)
        assert result.oversold is not None

    def test_insufficient_data(self):
        rsi = RSI(period=14)
        with pytest.raises(ValueError):
            rsi.calculate([1, 2, 3])

    def test_constant_prices(self):
        rsi = RSI(period=14)
        prices = [100] * 20
        result = rsi.calculate(prices)
        assert all(np.isnan(v) or v == 50.0 for v in result.values)


class TestMACD:
    def test_initialization(self):
        macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        assert macd.fast_period == 12
        assert macd.slow_period == 26
        assert macd.signal_period == 9

    def test_calculate(self):
        macd = MACD()
        prices = list(range(1, 50))
        result = macd.calculate(prices)
        assert len(result.macd_line) == len(prices)
        assert len(result.signal_line) == len(prices)
        assert len(result.histogram) == len(prices)

    def test_bullish_crossover(self):
        macd = MACD()
        # Create a price series that should produce a bullish crossover
        prices = [100 + i * 0.1 for i in range(50)]
        result = macd.calculate(prices)
        # Check that we have valid values
        assert any(not np.isnan(v) for v in result.histogram)

    def test_insufficient_data(self):
        macd = MACD()
        with pytest.raises(ValueError):
            macd.calculate([1, 2, 3])

    def test_constant_prices(self):
        macd = MACD()
        prices = [100] * 50
        result = macd.calculate(prices)
        # MACD should be zero for constant prices
        assert all(v == 0.0 for v in result.macd_line if not np.isnan(v))


class TestBettingStrategy:
    def test_initialization(self):
        strategy = BettingStrategy()
        assert strategy.name == "BettingStrategy"

    def test_generate_signal(self):
        strategy = BettingStrategy()
        signal = strategy.generate_signal(
            probability=0.6,
            odds=2.0,
            bankroll=1000,
            timestamp=1.0,
        )
        assert signal is not None
        assert signal.action in ["BET", "NO_BET"]
        assert signal.probability == 0.6
        assert signal.odds == 2.0

    def test_generate_signal_no_bet(self):
        strategy = BettingStrategy()
        signal = strategy.generate_signal(
            probability=0.4,
            odds=2.0,
            bankroll=1000,
            timestamp=1.0,
        )
        assert signal.action == "NO_BET"

    def test_generate_signal_invalid_probability(self):
        strategy = BettingStrategy()
        with pytest.raises(ValueError):
            strategy.generate_signal(
                probability=1.5,
                odds=2.0,
                bankroll=1000,
                timestamp=1.0,
            )

    def test_generate_signal_invalid_odds(self):
        strategy = BettingStrategy()
        with pytest.raises(ValueError):
            strategy.generate_signal(
                probability=0.6,
                odds=0.5,
                bankroll=1000,
                timestamp=1.0,
            )

    def test_generate_signal_zero_bankroll(self):
        strategy = BettingStrategy()
        signal = strategy.generate_signal(
            probability=0.6,
            odds=2.0,
            bankroll=0,
            timestamp=1.0,
        )
        assert signal.action == "NO_BET"

    def test_generate_signal_custom_kelly_fraction(self):
        strategy = BettingStrategy(kelly_fraction=0.5)
        signal = strategy.generate_signal(
            probability=0.6,
            odds=2.0,
            bankroll=1000,
            timestamp=1.0,
        )
        # With half Kelly, bet size should be half of full Kelly
        assert signal.bet_size == pytest.approx(100.0)

    def test_generate_signal_custom_risk_tolerance(self):
        strategy = BettingStrategy(risk_tolerance=0.5)
        signal = strategy.generate_signal(
            probability=0.6,
            odds=2.0,
            bankroll=1000,
            timestamp=1.0,
        )
        # With lower risk tolerance, bet size should be smaller
        assert signal.bet_size < 200.0  # Full Kelly would be 200


class TestStrategySignal:
    def test_initialization(self):
        signal = StrategySignal(
            action="BET",
            probability=0.6,
            odds=2.0,
            bet_size=200.0,
            timestamp=1.0,
        )
        assert signal.action == "BET"
        assert signal.probability == 0.6
        assert signal.odds == 2.0
        assert signal.bet_size == 200.0
        assert signal.timestamp == 1.0

    def test_to_dict(self):
        signal = StrategySignal(
            action="BET",
            probability=0.6,
            odds=2.0,
            bet_size=200.0,
            timestamp=1.0,
        )
        d = signal.to_dict()
        assert d["action"] == "BET"
        assert d["probability"] == 0.6
        assert d["odds"] == 2.0
        assert d["bet_size"] == 200.0
        assert d["timestamp"] == 1.0

    def test_from_dict(self):
        d = {
            "action": "BET",
            "probability": 0.6,
            "odds": 2.0,
            "bet_size": 200.0,
            "timestamp": 1.0,
        }
        signal = StrategySignal.from_dict(d)
        assert signal.action == "BET"
        assert signal.probability == 0.6
        assert signal.odds == 2.0
        assert signal.bet_size == 200.0
        assert signal.timestamp == 1.0

    def test_from_dict_invalid_action(self):
        d = {
            "action": "INVALID",
            "probability": 0.6,
            "odds": 2.0,
            "bet_size": 200.0,
            "timestamp": 1.0,
        }
        with pytest.raises(ValueError):
            StrategySignal.from_dict(d)

    def test_from_dict_missing_key(self):
        d = {
            "action": "BET",
            "probability": 0.6,
            "odds": 2.0,
            "bet_size": 200.0,
        }
        with pytest.raises(KeyError):
            StrategySignal.from_dict(d)
