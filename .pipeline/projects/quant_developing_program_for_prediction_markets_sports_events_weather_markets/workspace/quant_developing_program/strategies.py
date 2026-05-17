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
            RSIResult with RSI values and thresholds.
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

        # Calculate initial average gain and loss
        avg_gain = sum(gains[: self.period]) / self.period
        avg_loss = sum(losses[: self.period]) / self.period

        rsi_values: list[float] = []

        # First RSI value
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

        # Calculate subsequent RSI values using smoothed averages
        for i in range(self.period, len(changes)):
            avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
            avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period

            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

        # Pad with NaN for initial periods
        full_rsi = [float('nan')] * self.period + rsi_values

        # Check current state
        current_rsi = rsi_values[-1] if rsi_values else float('nan')
        overbought_val = current_rsi if current_rsi > self.overbought else None
        oversold_val = current_rsi if current_rsi < self.oversold else None

        return RSIResult(
            values=full_rsi,
            period=self.period,
            overbought=overbought_val,
            oversold=oversold_val,
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
        if signal_period < 1:
            raise ValueError("signal_period must be at least 1")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def _ema(self, prices: list[float], period: int) -> list[float]:
        """Calculate Exponential Moving Average.

        Args:
            prices: Input price series.
            period: EMA period.

        Returns:
            List of EMA values (same length as input).
        """
        if not prices:
            return []

        multiplier = 2.0 / (period + 1)
        ema_values = [prices[0]]  # First value is the price itself

        for i in range(1, len(prices)):
            ema = (prices[i] - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)

        return ema_values

    def calculate(self, prices: list[float]) -> MACDResult:
        """Calculate MACD from a price series.

        Args:
            prices: List of closing prices.

        Returns:
            MACDResult with MACD line, signal line, and histogram.
        """
        if len(prices) < self.slow_period:
            raise ValueError(
                f"Need at least {self.slow_period} prices, got {len(prices)}"
            )

        # Calculate fast and slow EMAs
        fast_ema = self._ema(prices, self.fast_period)
        slow_ema = self._ema(prices, self.slow_period)

        # MACD line = Fast EMA - Slow EMA
        macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]

        # Signal line = EMA of MACD line
        signal_line = self._ema(macd_line, self.signal_period)

        # Histogram = MACD line - Signal line
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
    """Unified trading signal from a strategy.

    Attributes:
        signal: -1 (sell), 0 (hold), 1 (buy).
        confidence: Confidence in the signal (0 to 1).
        reason: Explanation for the signal.
        kelly_fraction: Kelly criterion fraction (if applicable).
        action: Alias for signal.
        probability: Predicted probability.
        odds: Decimal odds.
        bet_size: Calculated bet size.
        timestamp: Signal timestamp.
    """
    signal: int
    confidence: float
    reason: str
    kelly_fraction: float = 0.0
    action: int = field(init=False)
    probability: float = field(default=0.0)
    odds: float = field(default=0.0)
    bet_size: float = field(default=0.0)
    timestamp: float = field(default=0.0)

    def __post_init__(self):
        """Set action to signal value."""
        self.action = self.signal

    def to_dict(self) -> dict:
        """Convert signal to dictionary."""
        return {
            "signal": self.signal,
            "confidence": self.confidence,
            "reason": self.reason,
            "kelly_fraction": self.kelly_fraction,
            "action": self.action,
            "probability": self.probability,
            "odds": self.odds,
            "bet_size": self.bet_size,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'StrategySignal':
        """Create a StrategySignal from a dictionary."""
        return cls(
            signal=data.get("signal", 0),
            confidence=data.get("confidence", 0.0),
            reason=data.get("reason", ""),
            kelly_fraction=data.get("kelly_fraction", 0.0),
        )


class BettingStrategy:
    """Unified betting strategy combining multiple signals.

    Combines:
        - Hawkes Process intensity (event-driven signals)
        - Kelly criterion (position sizing)
        - Technical analysis (RSI/MACD signals)

    Attributes:
        hawkes_process: Hawkes Process for event intensity.
        rsi: RSI calculator (optional).
        macd: MACD calculator (optional).
        kelly_bankroll: Bankroll for Kelly calculations.
        name: Strategy name.
        kelly_fraction: Base Kelly fraction.
        risk_tolerance: Risk tolerance (0 to 1).
    """

    def __init__(
        self,
        hawkes_process: Optional['HawkesProcess'] = None,
        rsi: Optional[RSI] = None,
        macd: Optional[MACD] = None,
        kelly_bankroll: float = 1000.0,
        name: str = "default",
        kelly_fraction: float = 0.25,
        risk_tolerance: float = 0.5,
    ):
        """Initialize the betting strategy.

        Args:
            hawkes_process: Hawkes Process for event intensity.
            rsi: RSI calculator for technical signals.
            macd: MACD calculator for technical signals.
            kelly_bankroll: Bankroll for Kelly criterion calculations.
            name: Strategy name.
            kelly_fraction: Base Kelly fraction.
            risk_tolerance: Risk tolerance (0 to 1).
        """
        self.hawkes_process = hawkes_process
        self.rsi = rsi
        self.macd = macd
        self.kelly_bankroll = kelly_bankroll
        self.name = name
        self.kelly_fraction = kelly_fraction
        self.risk_tolerance = risk_tolerance

    def generate_signal(
        self,
        current_time: float,
        predicted_prob: float,
        market_prob: float,
        prices: Optional[list[float]] = None,
        probability: Optional[float] = None,
        odds: Optional[float] = None,
        bankroll: Optional[float] = None,
        timestamp: Optional[float] = None,
    ) -> StrategySignal:
        """Generate a unified trading signal.

        Args:
            current_time: Current time for Hawkes intensity calculation.
            predicted_prob: Your predicted probability of the outcome.
            market_prob: Market-implied probability.
            prices: Optional price series for technical analysis.
            probability: Alias for predicted_prob.
            odds: Decimal odds (optional).
            bankroll: Bankroll for Kelly calculations (optional).
            timestamp: Signal timestamp (optional).

        Returns:
            StrategySignal with signal, confidence, reason, and Kelly fraction.
        """
        # Use aliases if provided
        if probability is not None:
            predicted_prob = probability
        if bankroll is not None:
            kelly_bankroll = bankroll
        else:
            kelly_bankroll = self.kelly_bankroll
        if timestamp is not None:
            current_time = timestamp

        signals = []
        reasons = []

        # 1. Hawkes Process signal
        if self.hawkes_process is not None:
            intensity = self.hawkes_process.conditional_intensity(current_time)
            # Normalize intensity to a signal strength (0 to 1)
            intensity_signal = min(1.0, intensity / 10.0)  # Assume max intensity ~10
            if intensity_signal > 0.3:
                signals.append(intensity_signal)
                reasons.append(f"Hawkes intensity: {intensity:.2f}")

        # 2. Technical analysis signals
        if prices is not None and self.rsi is not None:
            rsi_result = self.rsi.calculate(prices)
            current_rsi = rsi_result.values[-1] if not np.isnan(rsi_result.values[-1]) else 50.0

            if current_rsi < self.rsi.oversold:
                signals.append(0.5)
                reasons.append(f"RSI oversold: {current_rsi:.1f}")
            elif current_rsi > self.rsi.overbought:
                signals.append(-0.5)
                reasons.append(f"RSI overbought: {current_rsi:.1f}")

        if prices is not None and self.macd is not None:
            macd_result = self.macd.calculate(prices)
            current_hist = macd_result.histogram[-1] if macd_result.histogram else 0.0

            if current_hist > 0:
                signals.append(0.3)
                reasons.append(f"MACD histogram positive: {current_hist:.4f}")
            elif current_hist < 0:
                signals.append(-0.3)
                reasons.append(f"MACD histogram negative: {current_hist:.4f}")

        # 3. Kelly criterion for position sizing
        kelly_result = None
        if predicted_prob > market_prob:
            from quant_developing_program.core.models import KellyCriterion
            kelly_result = KellyCriterion.calculate_from_probability(
                predicted_prob, market_prob, kelly_bankroll
            )

        # Combine signals
        if not signals:
            # No signals from any source
            if kelly_result and kelly_result["kelly_fraction"] > 0:
                return StrategySignal(
                    signal=1,
                    confidence=kelly_result["kelly_fraction"],
                    reason="Kelly edge only",
                    kelly_fraction=kelly_result["kelly_fraction"],
                )
            return StrategySignal(
                signal=0,
                confidence=0.0,
                reason="No signals generated",
                kelly_fraction=0.0,
            )

        # Weighted average of signals
        avg_signal = sum(signals) / len(signals)

        # Determine final signal
        if avg_signal > 0.1:
            final_signal = 1
        elif avg_signal < -0.1:
            final_signal = -1
        else:
            final_signal = 0

        # Confidence is the average absolute signal strength
        confidence = min(1.0, abs(avg_signal))

        reason = "; ".join(reasons) if reasons else "Combined signals"

        kelly_frac = kelly_result["kelly_fraction"] if kelly_result else 0.0

        return StrategySignal(
            signal=final_signal,
            confidence=confidence,
            reason=reason,
            kelly_fraction=kelly_frac,
        )
