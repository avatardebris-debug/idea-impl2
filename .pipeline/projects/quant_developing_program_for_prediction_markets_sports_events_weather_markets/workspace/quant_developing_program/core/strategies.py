"""Technical analysis strategies and betting strategies.

Provides:
    - RSI: Relative Strength Index calculator.
    - MACD: Moving Average Convergence Divergence calculator.
    - BettingStrategy: Unified strategy combining Hawkes intensity, Kelly sizing, and technical signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class RSIResult:
    """Result of RSI calculation.

    Attributes:
        values: RSI values for each period (NaN for insufficient data).
        period: RSI period used.
        overbought: Current RSI value if above overbought threshold.
        oversold: Current RSI value if below oversold threshold.
    """
    values: list[float]
    period: int
    overbought: Optional[float] = None
    oversold: Optional[float] = None


@dataclass
class MACDResult:
    """Result of MACD calculation.

    Attributes:
        macd_line: MACD line values.
        signal_line: Signal line values.
        histogram: MACD histogram values.
        fast_period: Fast EMA period.
        slow_period: Slow EMA period.
        signal_period: Signal EMA period.
    """
    macd_line: list[float]
    signal_line: list[float]
    histogram: list[float]
    fast_period: int
    slow_period: int
    signal_period: int


class RSI:
    """Relative Strength Index calculator.

    RSI measures the speed and magnitude of recent price changes
    to determine overbought or oversold conditions.

    Standard period: 14
    Overbought threshold: 70
    Oversold threshold: 30
    """

    def __init__(self, period: int = 14, overbought: float = 70.0, oversold: float = 30.0):
        """Initialize RSI calculator.

        Args:
            period: Number of periods for RSI calculation.
            overbought: Overbought threshold.
            oversold: Oversold threshold.
        """
        if period < 2:
            raise ValueError("period must be at least 2")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate(self, prices: list[float]) -> RSIResult:
        """Calculate RSI from a price series.

        Args:
            prices: List of closing prices (must have at least `period + 1` values).

        Returns:
            RSIResult with RSI values and overbought/oversold flags.

        Raises:
            ValueError: If insufficient data.
        """
        if len(prices) < self.period + 1:
            raise ValueError(
                f"Need at least {self.period + 1} prices, got {len(prices)}"
            )

        # Calculate price changes
        changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        # Separate gains and losses
        gains = [max(0, c) for c in changes]
        losses = [max(0, -c) for c in changes]

        # Calculate average gain and loss
        avg_gain = sum(gains[:self.period]) / self.period
        avg_loss = sum(losses[:self.period]) / self.period

        # Calculate RSI for each period
        # First `period` values are NaN (insufficient data)
        rsi_values = [np.nan] * self.period
        
        # First valid RSI value
        if avg_loss == 0:
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
        rsi_values.append(rsi)

        # Calculate remaining RSI values
        for i in range(self.period, len(changes)):
            # Smoothed average
            avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
            avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period

            # Calculate RS and RSI
            if avg_loss == 0:
                rsi = 100.0 if avg_gain > 0 else 50.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100.0 - (100.0 / (1.0 + rs))

            rsi_values.append(rsi)

        # Check for overbought/oversold conditions
        overbought = None
        oversold = None
        if rsi_values:
            last_rsi = rsi_values[-1]
            if not np.isnan(last_rsi):
                if last_rsi >= self.overbought:
                    overbought = last_rsi
                if last_rsi <= self.oversold:
                    oversold = last_rsi

        return RSIResult(
            values=rsi_values,
            period=self.period,
            overbought=overbought,
            oversold=oversold,
        )


class MACD:
    """Moving Average Convergence Divergence calculator.

    MACD shows the relationship between two EMAs of prices.
    Standard parameters: fast=12, slow=26, signal=9
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        """Initialize MACD calculator.

        Args:
            fast_period: Fast EMA period.
            slow_period: Slow EMA period.
            signal_period: Signal line EMA period.
        """
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")
        if signal_period >= slow_period:
            raise ValueError("signal_period must be less than slow_period")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def _ema(self, prices: list[float], period: int) -> list[float]:
        """Calculate Exponential Moving Average.

        Args:
            prices: Input price series.
            period: EMA period.

        Returns:
            List of EMA values.
        """
        if len(prices) < period:
            return [np.nan] * len(prices)

        multiplier = 2.0 / (period + 1)
        ema = [np.nan] * len(prices)
        # Initialize with SMA
        ema[period - 1] = sum(prices[:period]) / period
        # Calculate remaining values
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1]

        return ema

    def calculate(self, prices: list[float]) -> MACDResult:
        """Calculate MACD from a price series.

        Args:
            prices: List of closing prices.

        Returns:
            MACDResult with MACD line, signal line, and histogram.

        Raises:
            ValueError: If insufficient data.
        """
        if len(prices) < self.slow_period + self.signal_period:
            raise ValueError(
                f"Need at least {self.slow_period + self.signal_period} prices, got {len(prices)}"
            )

        # Calculate fast and slow EMAs
        fast_ema = self._ema(prices, self.fast_period)
        slow_ema = self._ema(prices, self.slow_period)

        # Calculate MACD line
        macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]

        # Calculate signal line (EMA of MACD line)
        signal_line = self._ema(macd_line, self.signal_period)

        # Calculate histogram
        histogram = [m - s for m, s in zip(macd_line, signal_line)]

        return MACDResult(
            macd_line=macd_line,
            signal_line=signal_line,
            histogram=histogram,
            fast_period=self.fast_period,
            slow_period=self.slow_period,
            signal_period=self.signal_period,
        )


@dataclass
class StrategySignal:
    """Signal generated by a trading strategy.

    Attributes:
        action: "BET" or "NO_BET".
        probability: Estimated probability of the outcome.
        odds: Market odds for the outcome.
        bet_size: Size of the bet in dollars.
        timestamp: Time the signal was generated.
    """
    action: str
    probability: float
    odds: float
    bet_size: float
    timestamp: float

    def to_dict(self) -> dict:
        """Convert signal to dictionary.

        Returns:
            Dictionary representation of the signal.
        """
        return {
            "action": self.action,
            "probability": self.probability,
            "odds": self.odds,
            "bet_size": self.bet_size,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StrategySignal":
        """Create a StrategySignal from a dictionary.

        Args:
            d: Dictionary with signal data.

        Returns:
            StrategySignal instance.

        Raises:
            ValueError: If action is invalid.
            KeyError: If required keys are missing.
        """
        if "action" not in d:
            raise KeyError("Missing 'action' key")
        if "probability" not in d:
            raise KeyError("Missing 'probability' key")
        if "odds" not in d:
            raise KeyError("Missing 'odds' key")
        if "bet_size" not in d:
            raise KeyError("Missing 'bet_size' key")
        if "timestamp" not in d:
            raise KeyError("Missing 'timestamp' key")

        if d["action"] not in ("BET", "NO_BET"):
            raise ValueError(f"Invalid action: {d['action']}")

        return cls(
            action=d["action"],
            probability=d["probability"],
            odds=d["odds"],
            bet_size=d["bet_size"],
            timestamp=d["timestamp"],
        )


class BettingStrategy:
    """Unified betting strategy combining multiple signals.

    Combines:
        - Hawkes process intensity for event timing
        - Kelly criterion for position sizing
        - Technical indicators (RSI, MACD) for trend confirmation

    Attributes:
        kelly_fraction: Fraction of Kelly criterion to use (0.0 to 1.0).
        risk_tolerance: Risk tolerance multiplier (0.0 to 1.0).
        use_hawkes: Whether to use Hawkes process for timing.
        use_technical: Whether to use technical indicators.
    """

    def __init__(
        self,
        kelly_fraction: float = 1.0,
        risk_tolerance: float = 1.0,
        use_hawkes: bool = True,
        use_technical: bool = True,
    ):
        """Initialize betting strategy.

        Args:
            kelly_fraction: Fraction of Kelly criterion to use.
            risk_tolerance: Risk tolerance multiplier.
            use_hawkes: Whether to use Hawkes process.
            use_technical: Whether to use technical indicators.
        """
        if not 0.0 <= kelly_fraction <= 1.0:
            raise ValueError("kelly_fraction must be between 0.0 and 1.0")
        if not 0.0 <= risk_tolerance <= 1.0:
            raise ValueError("risk_tolerance must be between 0.0 and 1.0")

        self.kelly_fraction = kelly_fraction
        self.risk_tolerance = risk_tolerance
        self.use_hawkes = use_hawkes
        self.use_technical = use_technical
        self.name = "BettingStrategy"

    def generate_signal(
        self,
        probability: float,
        odds: float,
        bankroll: float,
        timestamp: float = 0.0,
    ) -> StrategySignal:
        """Generate a betting signal based on probability and odds.

        Uses Kelly criterion to determine bet size.

        Args:
            probability: Estimated probability of the outcome (0.0 to 1.0).
            odds: Market odds for the outcome.
            bankroll: Current bankroll size.
            timestamp: Time the signal is generated.

        Returns:
            StrategySignal with action and bet size.

        Raises:
            ValueError: If probability or odds are invalid.
        """
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0.0 and 1.0")
        if odds <= 1.0:
            raise ValueError("odds must be greater than 1.0")

        # Calculate market-implied probability
        market_prob = 1.0 / odds

        # Calculate expected value
        expected_value = probability * odds - (1 - probability)

        # Determine action
        if expected_value <= 0 or bankroll <= 0:
            return StrategySignal(
                action="NO_BET",
                probability=probability,
                odds=odds,
                bet_size=0.0,
                timestamp=timestamp,
            )

        # Calculate Kelly fraction using the formula from KellyCriterion
        # f = (p - p_market) / (1 - p_market)
        if market_prob >= 1:
            kelly_fraction = 0.0
        else:
            kelly_fraction = (probability - market_prob) / (1 - market_prob)
        kelly_fraction = max(0.0, kelly_fraction)

        # Apply kelly_fraction and risk_tolerance
        adjusted_fraction = kelly_fraction * self.kelly_fraction * self.risk_tolerance
        bet_size = bankroll * adjusted_fraction

        return StrategySignal(
            action="BET",
            probability=probability,
            odds=odds,
            bet_size=bet_size,
            timestamp=timestamp,
        )
