"""Generate synthetic OHLCV sample data for testing."""

import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_ohlcv(
    filepath: str,
    n_days: int = 600,
    start_price: float = 100.0,
    volatility: float = 0.02,
    drift: float = 0.0003,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing.

    Uses geometric Brownian motion for price generation.

    Args:
        filepath: Output CSV path.
        n_days: Number of trading days to generate.
        start_price: Starting price.
        volatility: Daily volatility (standard deviation of returns).
        drift: Daily drift (expected return).
        seed: Random seed.

    Returns:
        DataFrame with OHLCV columns.
    """
    rng = np.random.default_rng(seed)

    # Generate log returns
    log_returns = rng.normal(loc=drift, scale=volatility, size=n_days)
    prices = start_price * np.exp(np.cumsum(log_returns))

    # Generate OHLCV from close prices
    dates = pd.date_range(start="2020-01-02", periods=n_days, freq="B")  # business days

    # Add intraday variation
    df = pd.DataFrame({
        "date": dates,
        "close": prices,
        "open": prices * (1 + rng.uniform(-0.005, 0.005, n_days)),
        "high": prices * (1 + abs(rng.normal(0, 0.01, n_days))),
        "low": prices * (1 - abs(rng.normal(0, 0.01, n_days))),
        "volume": rng.integers(1_000_000, 10_000_000, n_days),
    })

    # Ensure high >= open, close and low <= open, close
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)

    df.to_csv(filepath, index=False)
    return df


if __name__ == "__main__":
    base = Path(__file__).parent.parent.parent
    filepath = base / "examples" / "sample_data" / "sample_ohlcv.csv"
    df = generate_sample_ohlcv(str(filepath), n_days=600)
    print(f"Generated {len(df)} trading days to {filepath}")
    print(df.head())
