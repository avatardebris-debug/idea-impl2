"""CSV data loader for OHLCV price data."""

import pandas as pd
from pathlib import Path


REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
MIN_TRADING_DAYS = 252  # ~1 year of trading days


def load_ohlcv_data(filepath: str) -> pd.DataFrame:
    """Load OHLCV data from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        DataFrame with columns [date, open, high, low, close, volume],
        sorted by date, with date as index.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing or data is insufficient.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(path, parse_dates=["date"])

    # Validate required columns
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Ensure correct column order
    df = df[REQUIRED_COLUMNS]

    # Validate data types
    for col in ["open", "high", "low", "close", "volume"]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col])

    # Drop rows with missing values
    df.dropna(inplace=True)

    # Validate minimum trading days
    if len(df) < MIN_TRADING_DAYS:
        raise ValueError(
            f"Insufficient data: {len(df)} trading days < {MIN_TRADING_DAYS} "
            f"required (need at least {MIN_TRADING_DAYS / 252:.0f} years)"
        )

    # Sort by date
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df
