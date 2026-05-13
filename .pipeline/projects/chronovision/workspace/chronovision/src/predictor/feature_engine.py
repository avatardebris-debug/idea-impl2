"""Feature Engineering — transforms raw financial data into model-ready features."""

import logging
from typing import List, Optional, Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngine:
    """Engine for creating features from raw financial data."""

    @staticmethod
    def compute_returns(prices: np.ndarray, periods: List[int] = None) -> np.ndarray:
        """Compute returns for given periods.
        
        Args:
            prices: Array of prices.
            periods: List of periods to compute returns for.
            
        Returns:
            Array of returns.
        """
        if periods is None:
            periods = [1, 5, 10, 20]
        
        returns_list = []
        for period in periods:
            if len(prices) > period:
                returns = np.diff(prices[-(period + 1):]) / prices[-(period + 1):-1]
                returns_list.append(returns)
        
        if not returns_list:
            return np.array([])
        
        return np.column_stack(returns_list)

    @staticmethod
    def compute_moving_averages(prices: np.ndarray, windows: List[int] = None) -> np.ndarray:
        """Compute moving averages for given windows.
        
        Args:
            prices: Array of prices.
            windows: List of window sizes.
            
        Returns:
            Array of moving averages.
        """
        if windows is None:
            windows = [5, 10, 20, 50]
        
        ma_list = []
        for window in windows:
            if len(prices) >= window:
                ma = np.convolve(prices, np.ones(window) / window, mode='valid')
                ma_list.append(ma)
        
        if not ma_list:
            return np.array([])
        
        return np.column_stack(ma_list)

    @staticmethod
    def compute_volatility(prices: np.ndarray, window: int = 20) -> np.ndarray:
        """Compute rolling volatility.
        
        Args:
            prices: Array of prices.
            window: Window size for volatility calculation.
            
        Returns:
            Array of volatility values.
        """
        if len(prices) < window:
            return np.array([])
        
        returns = np.diff(prices) / prices[:-1]
        volatility = pd.Series(returns).rolling(window=window).std().values
        return volatility

    @staticmethod
    def compute_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Compute Relative Strength Index.
        
        Args:
            prices: Array of prices.
            period: RSI period.
            
        Returns:
            Array of RSI values.
        """
        if len(prices) < period + 1:
            return np.array([])
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = pd.Series(gains).rolling(window=period).mean().values
        avg_loss = pd.Series(losses).rolling(window=period).mean().values
        
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def compute_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> np.ndarray:
        """Compute MACD indicator.
        
        Args:
            prices: Array of prices.
            fast: Fast EMA period.
            slow: Slow EMA period.
            signal: Signal line period.
            
        Returns:
            Array of MACD values.
        """
        if len(prices) < slow + signal:
            return np.array([])
        
        exp1 = pd.Series(prices).ewm(span=fast, adjust=False).mean()
        exp2 = pd.Series(prices).ewm(span=slow, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        
        return macd_histogram.values

    @staticmethod
    def compute_volume_features(volumes: np.ndarray, window: int = 20) -> np.ndarray:
        """Compute volume-based features.
        
        Args:
            volumes: Array of volumes.
            window: Window for volume moving average.
            
        Returns:
            Array of volume features.
        """
        if len(volumes) < window:
            return np.array([])
        
        vol_ma = pd.Series(volumes).rolling(window=window).mean().values
        vol_ratio = volumes / (vol_ma + 1e-10)
        vol_change = np.diff(volumes) / (volumes[:-1] + 1e-10)
        
        return np.column_stack([vol_ratio, vol_change])

    @staticmethod
    def compute_bollinger_bands(prices: np.ndarray, window: int = 20, num_std: float = 2.0) -> np.ndarray:
        """Compute Bollinger Bands.
        
        Args:
            prices: Array of prices.
            window: Window for moving average.
            num_std: Number of standard deviations for bands.
            
        Returns:
            Array with middle band, upper band, lower band, and bandwidth.
        """
        if len(prices) < window:
            return np.array([])
        
        ma = pd.Series(prices).rolling(window=window).mean().values
        std = pd.Series(prices).rolling(window=window).std().values
        
        upper_band = ma + num_std * std
        lower_band = ma - num_std * std
        bandwidth = (upper_band - lower_band) / (ma + 1e-10)
        
        return np.column_stack([ma, upper_band, lower_band, bandwidth])

    @staticmethod
    def engineer_features(prices: np.ndarray, volumes: Optional[np.ndarray] = None) -> np.ndarray:
        """Engineer a comprehensive feature set from prices and volumes.
        
        Args:
            prices: Array of prices.
            volumes: Optional array of volumes.
            
        Returns:
            Feature matrix.
        """
        features_list = []
        
        # Returns
        returns = FeatureEngine.compute_returns(prices)
        if len(returns) > 0:
            features_list.append(returns)
        
        # Moving averages
        ma = FeatureEngine.compute_moving_averages(prices)
        if len(ma) > 0:
            features_list.append(ma)
        
        # Volatility
        vol = FeatureEngine.compute_volatility(prices)
        if len(vol) > 0:
            features_list.append(vol.reshape(-1, 1))
        
        # RSI
        rsi = FeatureEngine.compute_rsi(prices)
        if len(rsi) > 0:
            features_list.append(rsi.reshape(-1, 1))
        
        # MACD
        macd = FeatureEngine.compute_macd(prices)
        if len(macd) > 0:
            features_list.append(macd.reshape(-1, 1))
        
        # Bollinger Bands
        bb = FeatureEngine.compute_bollinger_bands(prices)
        if len(bb) > 0:
            features_list.append(bb)
        
        # Volume features
        if volumes is not None and len(volumes) > 0:
            vol_features = FeatureEngine.compute_volume_features(volumes)
            if len(vol_features) > 0:
                features_list.append(vol_features)
        
        if not features_list:
            return np.array([])
        
        # Align lengths
        min_len = min(f.shape[0] for f in features_list)
        aligned_features = [f[-min_len:] for f in features_list]
        
        return np.column_stack(aligned_features)

    @staticmethod
    def get_feature_names() -> List[str]:
        """Get names for engineered features.
        
        Returns:
            List of feature names.
        """
        names = []
        
        # Returns
        for period in [1, 5, 10, 20]:
            names.append(f'return_{period}')
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            names.append(f'ma_{window}')
        
        names.append('volatility_20')
        names.append('rsi_14')
        names.append('macd')
        names.extend(['bb_middle', 'bb_upper', 'bb_lower', 'bb_bandwidth'])
        
        # Volume features
        names.extend(['vol_ratio', 'vol_change'])
        
        return names
