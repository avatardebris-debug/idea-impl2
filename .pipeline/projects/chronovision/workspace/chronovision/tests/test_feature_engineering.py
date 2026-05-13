"""Tests for FeatureEngine."""

import pytest
import numpy as np
from chronovision.src.predictor.feature_engine import FeatureEngine


class TestFeatureEngine:
    """Tests for the FeatureEngine class."""

    def test_compute_returns(self):
        """Test compute_returns method."""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])
        returns = FeatureEngine.compute_returns(prices)
        
        # Should return 2D array with 4 columns (periods 1, 5, 10, 20)
        assert returns.shape[1] == 4
        # First column should be 1-period returns
        assert returns[0, 0] == pytest.approx((102 - 100) / 100)
    
    def test_compute_returns_custom_periods(self):
        """Test compute_returns with custom periods."""
        prices = np.array([100, 102, 104, 106, 108])
        returns = FeatureEngine.compute_returns(prices, periods=[1, 2])
        
        assert returns.shape[1] == 2
        assert returns[0, 0] == pytest.approx((102 - 100) / 100)
        assert returns[0, 1] == pytest.approx((104 - 100) / 100)
    
    def test_compute_returns_insufficient_data(self):
        """Test compute_returns with insufficient data."""
        prices = np.array([100, 101])
        returns = FeatureEngine.compute_returns(prices)
        
        # Should return empty array since no period can be computed
        assert len(returns) == 0
    
    def test_compute_moving_averages(self):
        """Test compute_moving_averages method."""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])
        ma = FeatureEngine.compute_moving_averages(prices)
        
        # Should return 2D array with 4 columns (windows 5, 10, 20, 50)
        assert ma.shape[1] == 4
        # First column should be 5-period MA
        assert ma[0, 0] == pytest.approx(np.mean(prices[:5]))
    
    def test_compute_moving_averages_custom_windows(self):
        """Test compute_moving_averages with custom windows."""
        prices = np.array([100, 102, 104, 106, 108])
        ma = FeatureEngine.compute_moving_averages(prices, windows=[2, 3])
        
        assert ma.shape[1] == 2
        assert ma[0, 0] == pytest.approx(np.mean(prices[:2]))
        assert ma[0, 1] == pytest.approx(np.mean(prices[:3]))
    
    def test_compute_moving_averages_insufficient_data(self):
        """Test compute_moving_averages with insufficient data."""
        prices = np.array([100, 101])
        ma = FeatureEngine.compute_moving_averages(prices)
        
        # Should return empty array since no window can be computed
        assert len(ma) == 0
    
    def test_compute_volatility(self):
        """Test compute_volatility method."""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                           110, 112, 111, 113, 115, 114, 116, 118, 117, 119])
        vol = FeatureEngine.compute_volatility(prices, window=5)
        
        assert len(vol) == len(prices) - 1  # Returns have one less element
        assert vol[0] > 0  # Volatility should be positive
    
    def test_compute_volatility_insufficient_data(self):
        """Test compute_volatility with insufficient data."""
        prices = np.array([100, 101])
        vol = FeatureEngine.compute_volatility(prices, window=5)
        
        assert len(vol) == 0
    
    def test_compute_rsi(self):
        """Test compute_rsi method."""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                           110, 112, 111, 113, 115, 114, 116, 118, 117, 119])
        rsi = FeatureEngine.compute_rsi(prices, period=14)
        
        assert len(rsi) == len(prices) - 14
        assert np.all((rsi >= 0) & (rsi <= 100))
    
    def test_compute_rsi_insufficient_data(self):
        """Test compute_rsi with insufficient data."""
        prices = np.array([100, 101])
        rsi = FeatureEngine.compute_rsi(prices, period=14)
        
        assert len(rsi) == 0
    
    def test_compute_macd(self):
        """Test compute_macd method."""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                           110, 112, 111, 113, 115, 114, 116, 118, 117, 119,
                           120, 122, 121, 123, 125, 124, 126, 128, 127, 129])
        macd = FeatureEngine.compute_macd(prices)
        
        assert len(macd) > 0
        assert isinstance(macd, np.ndarray)
    
    def test_compute_macd_insufficient_data(self):
        """Test compute_macd with insufficient data."""
        prices = np.array([100, 101])
        macd = FeatureEngine.compute_macd(prices)
        
        assert len(macd) == 0
    
    def test_compute_volume_features(self):
        """Test compute_volume_features method."""
        volumes = np.array([1000, 1200, 1100, 1300, 1500, 1400, 1600, 1800, 1700, 1900,
                            2000, 2200, 2100, 2300, 2500, 2400, 2600, 2800, 2700, 2900])
        vol_features = FeatureEngine.compute_volume_features(volumes, window=5)
        
        assert vol_features.shape[1] == 2  # vol_ratio and vol_change
        assert len(vol_features) == len(volumes) - 5
    
    def test_compute_volume_features_insufficient_data(self):
        """Test compute_volume_features with insufficient data."""
        volumes = np.array([1000, 1200])
        vol_features = FeatureEngine.compute_volume_features(volumes, window=5)
        
        assert len(vol_features) == 0
    
    def test_compute_bollinger_bands(self):
        """Test compute_bollinger_bands method."""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                           110, 112, 111, 113, 115, 114, 116, 118, 117, 119])
        bb = FeatureEngine.compute_bollinger_bands(prices, window=5)
        
        assert bb.shape[1] == 4  # middle, upper, lower, bandwidth
        assert len(bb) == len(prices) - 5
        # Upper band should be >= middle band
        assert np.all(bb[:, 1] >= bb[:, 0])
        # Lower band should be <= middle band
        assert np.all(bb[:, 2] <= bb[:, 0])
    
    def test_compute_bollinger_bands_insufficient_data(self):
        """Test compute_bollinger_bands with insufficient data."""
        prices = np.array([100, 101])
        bb = FeatureEngine.compute_bollinger_bands(prices, window=5)
        
        assert len(bb) == 0
    
    def test_engineer_features(self):
        """Test engineer_features method."""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                           110, 112, 111, 113, 115, 114, 116, 118, 117, 119])
        volumes = np.array([1000, 1200, 1100, 1300, 1500, 1400, 1600, 1800, 1700, 1900,
                            2000, 2200, 2100, 2300, 2500, 2400, 2600, 2800, 2700, 2900])
        features = FeatureEngine.engineer_features(prices, volumes)
        
        assert features.shape[1] > 0
        assert features.shape[0] == len(prices) - 20  # Limited by longest feature computation
        assert isinstance(features, np.ndarray)
    
    def test_engineer_features_no_volumes(self):
        """Test engineer_features without volumes."""
        prices = np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                           110, 112, 111, 113, 115, 114, 116, 118, 117, 119])
        features = FeatureEngine.engineer_features(prices)
        
        assert features.shape[1] > 0
        assert isinstance(features, np.ndarray)
    
    def test_engineer_features_insufficient_data(self):
        """Test engineer_features with insufficient data."""
        prices = np.array([100, 101])
        features = FeatureEngine.engineer_features(prices)
        
        assert len(features) == 0
    
    def test_get_feature_names(self):
        """Test get_feature_names method."""
        names = FeatureEngine.get_feature_names()
        
        assert len(names) == 18  # 4 returns + 4 MAs + 1 vol + 1 RSI + 1 MACD + 4 BB + 2 vol features
        assert 'return_1' in names
        assert 'ma_5' in names
        assert 'volatility_20' in names
        assert 'rsi_14' in names
        assert 'macd' in names
        assert 'bb_middle' in names
        assert 'vol_ratio' in names
