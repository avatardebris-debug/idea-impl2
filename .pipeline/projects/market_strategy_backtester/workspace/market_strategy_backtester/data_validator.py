"""Data validation and quality checks for OHLCV data.

Validates that price data is well-formed and suitable for backtesting.
"""

import pandas as pd
from typing import Dict, List, Tuple


class DataValidator:
    """Validates OHLCV data quality.

    Checks for:
        - Missing values
        - Invalid price relationships (high < low, etc.)
        - Zero or negative prices
        - Duplicate dates
        - Non-monotonic dates
        - Unusual price jumps
    """

    REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]

    def __init__(
        self,
        max_price_jump_pct: float = 0.5,  # 50% max single-day jump
        min_volume: int = 0,
    ):
        self.max_price_jump_pct = max_price_jump_pct
        self.min_volume = min_volume

    def validate(
        self,
        price_data: pd.DataFrame,
    ) -> Dict[str, List[str]]:
        """Validate OHLCV data and return list of warnings/errors.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            Dictionary with 'warnings' and 'errors' lists.
        """
        warnings = []
        errors = []

        # Check required columns
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in price_data.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return {"warnings": warnings, "errors": errors}

        # Check for empty data
        if len(price_data) == 0:
            errors.append("Data is empty")
            return {"warnings": warnings, "errors": errors}

        # Check for missing values
        for col in self.REQUIRED_COLUMNS:
            null_count = price_data[col].isna().sum()
            if null_count > 0:
                warnings.append(f"Column '{col}' has {null_count} missing values")

        # Check date column
        if "date" in price_data.columns:
            if not pd.api.types.is_datetime64_any_dtype(price_data["date"]):
                try:
                    pd.to_datetime(price_data["date"])
                except Exception:
                    errors.append("Date column cannot be parsed as datetime")

            # Check for duplicate dates
            if price_data["date"].duplicated().any():
                dup_count = price_data["date"].duplicated().sum()
                warnings.append(f"Found {dup_count} duplicate dates")

            # Check for non-monotonic dates
            if not price_data["date"].is_monotonic_increasing:
                errors.append("Dates are not in ascending order")

        # Check price relationships
        if "high" in price_data.columns and "low" in price_data.columns:
            invalid_hl = (price_data["high"] < price_data["low"]).sum()
            if invalid_hl > 0:
                errors.append(f"Found {invalid_hl} rows where high < low")

        if "open" in price_data.columns:
            # high >= open and close
            invalid_high_open = (price_data["high"] < price_data["open"]).sum()
            invalid_high_close = (price_data["high"] < price_data["close"]).sum()
            if invalid_high_open > 0 or invalid_high_close > 0:
                errors.append("high must be >= open and close")

            # low <= open and close
            invalid_low_open = (price_data["low"] > price_data["open"]).sum()
            invalid_low_close = (price_data["low"] > price_data["close"]).sum()
            if invalid_low_open > 0 or invalid_low_close > 0:
                errors.append("low must be <= open and close")

        # Check for zero or negative prices
        for col in ["open", "high", "low", "close"]:
            if col in price_data.columns:
                neg_count = (price_data[col] <= 0).sum()
                if neg_count > 0:
                    errors.append(f"Column '{col}' has {neg_count} non-positive values")

        # Check for zero or negative volume
        if "volume" in price_data.columns:
            zero_vol = (price_data["volume"] <= self.min_volume).sum()
            if zero_vol > 0:
                warnings.append(f"Found {zero_vol} rows with volume <= {self.min_volume}")

        # Check for unusual price jumps
        if "close" in price_data.columns:
            returns = price_data["close"].pct_change().dropna()
            large_jumps = (returns.abs() > self.max_price_jump_pct).sum()
            if large_jumps > 0:
                warnings.append(
                    f"Found {large_jumps} rows with price jumps > {self.max_price_jump_pct * 100}%"
                )

        # Check for constant prices
        if "close" in price_data.columns:
            if price_data["close"].nunique() == 1:
                errors.append("Close price is constant (no variation)")

        return {"warnings": warnings, "errors": errors}

    def is_valid(self, price_data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Quick check if data is valid.

        Args:
            price_data: DataFrame with OHLCV columns.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        result = self.validate(price_data)
        if result["errors"]:
            return False, result["errors"]
        return True, []
