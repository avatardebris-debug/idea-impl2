"""Core backtester engine.

Applies a strategy to price data and produces per-trade returns and an equity curve.
"""

import numpy as np
import pandas as pd

from market_strategy_backtester.strategies.base import Strategy


class Backtester:
    """Backtesting engine that applies a strategy to price data.

    Attributes:
        strategy: A Strategy instance with a `generate_signals` method.
        risk_free_rate: Annual risk-free rate for Sharpe calculation (default: 0.02).
    """

    def __init__(
        self,
        strategy: Strategy,
        initial_capital: float = 100000.0,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        risk_free_rate: float = 0.02,
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.risk_free_rate = risk_free_rate

    def run_backtest(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Run the backtest.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            DataFrame with columns ["date", "equity", "position", "cash", "trades"]
        """
        # Generate signals
        signals = self.strategy.generate_signals(price_data)

        # Merge signals with price data
        merged = price_data[["date", "close"]].copy()
        if "date" in signals.columns:
            merged = merged.merge(signals, on="date", how="left")
        else:
            merged["signal"] = signals
            
        if "signal" not in merged.columns:
            merged["signal"] = 0
            
        merged["signal"] = merged["signal"].fillna(0)
        
        # Position is simply the signal shifted by 1 (trade executed at next open/close)
        # For simplicity, we assume trade happens at 'close' of the day after signal, or just use daily return.
        merged["position"] = merged["signal"].shift(1).fillna(0)
        
        # Trades happen when position changes
        merged["trades"] = merged["position"].diff().fillna(0.0)
        
        # Daily return of the asset
        merged["daily_return"] = merged["close"].pct_change().fillna(0.0)
        
        # Trade costs: commission + slippage applied to the absolute value of trades
        merged["trade_costs"] = merged["trades"].abs() * (self.commission_pct + self.slippage_pct)
        
        # Strategy return: return from holding the position minus trading costs
        merged["strategy_return"] = (merged["position"] * merged["daily_return"]) - merged["trade_costs"]
        
        # Equity curve
        merged["equity"] = self.initial_capital * (1 + merged["strategy_return"]).cumprod()
        
        # Cash: approximate for testing (Equity minus the position value roughly)
        # Position = 1 means fully invested, Position = 0 means full cash.
        merged["cash"] = merged["equity"] * (1 - merged["position"])
        
        return merged[["date", "equity", "position", "cash", "trades", "strategy_return"]]
