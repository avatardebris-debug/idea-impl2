"""Tests for the XGBoost predictor."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from chronovision.src.predictor.xgboost_predictor import XGBoostPredictor


class TestXGBoostPredictor:
    """Tests for XGBoostPredictor."""
    
    def test_init(self):
        """Test initialization."""
        predictor = XGBoostPredictor()
        assert predictor.name == "XGBoost"
        assert predictor.n_estimators == 100
        assert predictor.max_depth == 6
        assert predictor.learning_rate == 0.1
        assert predictor.model is None
        assert predictor.is_trained == False
        assert predictor.feature_names == []
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        predictor = XGBoostPredictor(n_estimators=200, max_depth=8, learning_rate=0.05)
        assert predictor.n_estimators == 200
        assert predictor.max_depth == 8
        assert predictor.learning_rate == 0.05
    
    def test_train_import_error(self):
        """Test training with missing xgboost."""
        predictor = XGBoostPredictor()
        
        with patch.dict('sys.modules', {'xgboost': None}):
            # Force ImportError by removing xgboost from modules
            import sys
            xgb_module = sys.modules.pop('xgboost', None)
            try:
                with pytest.raises(ImportError, match="xgboost is required"):
                    predictor.train(np.array([[1, 2]]), np.array([1]))
            finally:
                if xgb_module:
                    sys.modules['xgboost'] = xgb_module
    
    @patch('chronovision.src.predictor.xgboost_predictor.xgb')
    def test_train(self, mock_xgb):
        """Test training."""
        predictor = XGBoostPredictor()
        
        # Mock DMatrix and train
        mock_dtrain = MagicMock()
        mock_model = MagicMock()
        mock_xgb.DMatrix.return_value = mock_dtrain
        mock_xgb.train.return_value = mock_model
        
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([1, 0, 1])
        
        predictor.train(X, y)
        
        assert predictor.is_trained == True
        assert predictor.model == mock_model
        mock_xgb.DMatrix.assert_called_once()
        mock_xgb.train.assert_called_once()
    
    @patch('chronovision.src.predictor.xgboost_predictor.xgb')
    def test_train_with_feature_names(self, mock_xgb):
        """Test training with feature names."""
        predictor = XGBoostPredictor()
        mock_model = MagicMock()
        mock_xgb.train.return_value = mock_model
        
        X = np.array([[1, 2], [3, 4]])
        y = np.array([1, 0])
        feature_names = ["price", "volume"]
        
        predictor.train(X, y, feature_names)
        
        assert predictor.feature_names == feature_names
    
    def test_predict_untrained(self):
        """Test prediction without training."""
        predictor = XGBoostPredictor()
        X = np.array([[1, 2]])
        
        with pytest.raises(ValueError, match="Model not trained"):
            predictor.predict(X)
    
    @patch('chronovision.src.predictor.xgboost_predictor.xgb')
    def test_predict(self, mock_xgb):
        """Test prediction."""
        predictor = XGBoostPredictor()
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.8, 0.3, 0.6])
        predictor.model = mock_model
        predictor.is_trained = True
        
        X = np.array([[1, 2], [3, 4], [5, 6]])
        predictions = predictor.predict(X)
        
        assert len(predictions) == 3
        mock_xgb.DMatrix.assert_called_once()
    
    def test_predict_direction_untrained(self):
        """Test direction prediction without training."""
        predictor = XGBoostPredictor()
        X = np.array([[1, 2]])
        
        with pytest.raises(ValueError, match="Model not trained"):
            predictor.predict_direction(X)
    
    @patch('chronovision.src.predictor.xgboost_predictor.xgb')
    def test_predict_direction(self, mock_xgb):
        """Test direction prediction."""
        predictor = XGBoostPredictor()
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.8, 0.3, 0.6])
        predictor.model = mock_model
        predictor.is_trained = True
        
        X = np.array([[1, 2], [3, 4], [5, 6]])
        directions = predictor.predict_direction(X)
        
        assert len(directions) == 3
        assert set(np.unique(directions)).issubset({0, 1})
        assert directions[0] == 1  # 0.8 > 0.5
        assert directions[1] == 0  # 0.3 < 0.5
        assert directions[2] == 1  # 0.6 > 0.5
    
    def test_get_feature_importance_untrained(self):
        """Test getting feature importance without training."""
        predictor = XGBoostPredictor()
        importance = predictor.get_feature_importance()
        assert importance is None
    
    @patch('chronovision.src.predictor.xgboost_predictor.xgb')
    def test_get_feature_importance(self, mock_xgb):
        """Test getting feature importance."""
        predictor = XGBoostPredictor()
        mock_model = MagicMock()
        mock_model.get_score.return_value = {"f0": 100.0, "f1": 50.0}
        predictor.model = mock_model
        predictor.is_trained = True
        predictor.feature_names = ["price", "volume"]
        
        importance = predictor.get_feature_importance()
        
        assert importance is not None
        assert importance["price"] == 100.0
        assert importance["volume"] == 50.0
    
    @patch('chronovision.src.predictor.xgboost_predictor.xgb')
    def test_get_feature_importance_no_feature_names(self, mock_xgb):
        """Test getting feature importance without feature names."""
        predictor = XGBoostPredictor()
        mock_model = MagicMock()
        mock_model.get_score.return_value = {"f0": 100.0, "f1": 50.0}
        predictor.model = mock_model
        predictor.is_trained = True
        predictor.feature_names = []
        
        importance = predictor.get_feature_importance()
        
        assert importance is not None
        assert "feature_0" in importance
        assert "feature_1" in importance
    
    def test_get_metrics_untrained(self):
        """Test getting metrics without training."""
        predictor = XGBoostPredictor()
        metrics = predictor.get_metrics()
        assert metrics == {}
    
    @patch('chronovision.src.predictor.xgboost_predictor.xgb')
    def test_get_metrics(self, mock_xgb):
        """Test getting metrics."""
        predictor = XGBoostPredictor(n_estimators=200, max_depth=8, learning_rate=0.05)
        mock_model = MagicMock()
        predictor.model = mock_model
        predictor.is_trained = True
        
        metrics = predictor.get_metrics()
        
        assert metrics["n_estimators"] == 200
        assert metrics["max_depth"] == 8
        assert metrics["learning_rate"] == 0.05
    
    def test_predict_with_different_input_shapes(self):
        """Test prediction with different input shapes."""
        predictor = XGBoostPredictor()
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0.8])
        predictor.model = mock_model
        predictor.is_trained = True
        
        # Single sample
        X = np.array([[1, 2]])
        predictions = predictor.predict(X)
        assert len(predictions) == 1
        
        # Multiple samples
        X = np.array([[1, 2], [3, 4], [5, 6]])
        predictions = predictor.predict(X)
        assert len(predictions) == 3
    
    def test_predict_direction_with_edge_cases(self):
        """Test direction prediction with edge cases."""
        predictor = XGBoostPredictor()
        mock_model = MagicMock()
        # Test with values exactly at 0.5
        mock_model.predict.return_value = np.array([0.5, 0.5001, 0.4999])
        predictor.model = mock_model
        predictor.is_trained = True
        
        X = np.array([[1, 2], [3, 4], [5, 6]])
        directions = predictor.predict_direction(X)
        
        assert directions[0] == 0  # 0.5 is not > 0.5
        assert directions[1] == 1  # 0.5001 > 0.5
        assert directions[2] == 0  # 0.4999 < 0.5
