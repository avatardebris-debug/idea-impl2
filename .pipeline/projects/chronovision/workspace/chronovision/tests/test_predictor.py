"""Tests for Predictors."""

import pytest
import numpy as np
from chronovision.src.predictor.base import BasePredictor
from chronovision.src.predictor.lstm_predictor import LSTMPredictor
from chronovision.src.predictor.ensemble_predictor import EnsemblePredictor
from chronovision.src.predictor.xgboost_predictor import XGBoostPredictor


class TestBasePredictor:
    """Tests for the BasePredictor class."""

    def test_base_predictor_is_abstract(self):
        """Test that BasePredictor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BasePredictor()

    def test_base_predictor_has_required_methods(self):
        """Test that BasePredictor has all required abstract methods."""
        assert hasattr(BasePredictor, 'train')
        assert hasattr(BasePredictor, 'predict')
        assert hasattr(BasePredictor, 'predict_direction')
        assert hasattr(BasePredictor, 'evaluate')
        assert hasattr(BasePredictor, 'get_metrics')
        assert hasattr(BasePredictor, 'get_feature_importance')


class TestLSTMPredictor:
    """Tests for the LSTMPredictor class."""

    def test_lstm_predictor_initialization(self):
        """Test LSTMPredictor initialization."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=10, lr=0.01)
        
        assert predictor.name == "LSTM"
        assert predictor.hidden_dim == 16
        assert predictor.num_layers == 2
        assert predictor.epochs == 10
        assert predictor.lr == 0.01
        assert predictor.is_trained == False
        assert predictor.model is None
    
    def test_lstm_predictor_train(self):
        """Test LSTMPredictor training."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        assert predictor.is_trained == True
        assert predictor.model is not None
    
    def test_lstm_predictor_predict(self):
        """Test LSTMPredictor prediction."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        # Predict on new data
        X_test = np.random.randn(20, 5)
        predictions = predictor.predict(X_test)
        
        assert predictions.shape[0] == X_test.shape[0] - 10  # lookback
        assert isinstance(predictions, np.ndarray)
    
    def test_lstm_predictor_predict_direction(self):
        """Test LSTMPredictor direction prediction."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        # Predict direction on new data
        X_test = np.random.randn(20, 5)
        directions = predictor.predict_direction(X_test)
        
        assert directions.shape[0] == X_test.shape[0] - 10
        assert np.all((directions == 0) | (directions == 1))
    
    def test_lstm_predictor_evaluate(self):
        """Test LSTMPredictor evaluation."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        # Evaluate on test data
        X_test = np.random.randn(20, 5)
        y_test = np.random.randint(0, 2, (20, 1))
        
        metrics = predictor.evaluate(X_test, y_test)
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert isinstance(metrics['accuracy'], float)
    
    def test_lstm_predictor_get_feature_importance(self):
        """Test LSTMPredictor feature importance."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        importance = predictor.get_feature_importance()
        
        assert importance is not None
        assert len(importance) == 5
        assert 'feature_0' in importance
        assert 'feature_4' in importance
    
    def test_lstm_predictor_predict_before_train(self):
        """Test that prediction before training raises error."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        
        X_test = np.random.randn(20, 5)
        
        with pytest.raises(ValueError):
            predictor.predict(X_test)
    
    def test_lstm_predictor_predict_direction_before_train(self):
        """Test that direction prediction before training raises error."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        
        X_test = np.random.randn(20, 5)
        
        with pytest.raises(ValueError):
            predictor.predict_direction(X_test)
    
    def test_lstm_predictor_get_feature_importance_before_train(self):
        """Test that feature importance before training returns None."""
        predictor = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        
        importance = predictor.get_feature_importance()
        
        assert importance is None


class TestEnsemblePredictor:
    """Tests for the EnsemblePredictor class."""

    def test_ensemble_predictor_initialization(self):
        """Test EnsemblePredictor initialization."""
        ensemble = EnsemblePredictor()
        
        assert ensemble.name == "Ensemble"
        assert ensemble.is_trained == False
        assert ensemble.predictors == []
        assert ensemble.weights == []
    
    def test_ensemble_predictor_add_predictor(self):
        """Test adding predictors to ensemble."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        xgb = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        ensemble.add_predictor(lstm, weight=1.0)
        ensemble.add_predictor(xgb, weight=2.0)
        
        assert len(ensemble.predictors) == 2
        assert len(ensemble.weights) == 2
        assert ensemble.weights == [1.0, 2.0]
    
    def test_ensemble_predictor_train(self):
        """Test training ensemble."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        xgb = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        ensemble.add_predictor(lstm, weight=1.0)
        ensemble.add_predictor(xgb, weight=2.0)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        ensemble.train(X, y, feature_names)
        
        assert ensemble.is_trained == True
        # Weights should be normalized
        assert abs(sum(ensemble.weights) - 1.0) < 1e-6
    
    def test_ensemble_predictor_predict(self):
        """Test ensemble prediction."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        xgb = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        ensemble.add_predictor(lstm, weight=1.0)
        ensemble.add_predictor(xgb, weight=2.0)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        ensemble.train(X, y, feature_names)
        
        # Predict on new data
        X_test = np.random.randn(20, 5)
        predictions = ensemble.predict(X_test)
        
        assert predictions.shape[0] == X_test.shape[0] - 10  # lookback
        assert isinstance(predictions, np.ndarray)
    
    def test_ensemble_predictor_predict_direction(self):
        """Test ensemble direction prediction."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        xgb = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        ensemble.add_predictor(lstm, weight=1.0)
        ensemble.add_predictor(xgb, weight=2.0)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        ensemble.train(X, y, feature_names)
        
        # Predict direction on new data
        X_test = np.random.randn(20, 5)
        directions = ensemble.predict_direction(X_test)
        
        assert directions.shape[0] == X_test.shape[0] - 10
        assert np.all((directions == 0) | (directions == 1))
    
    def test_ensemble_predictor_evaluate(self):
        """Test ensemble evaluation."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        xgb = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        ensemble.add_predictor(lstm, weight=1.0)
        ensemble.add_predictor(xgb, weight=2.0)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        ensemble.train(X, y, feature_names)
        
        # Evaluate on test data
        X_test = np.random.randn(20, 5)
        y_test = np.random.randint(0, 2, (20, 1))
        
        metrics = ensemble.evaluate(X_test, y_test)
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert isinstance(metrics['accuracy'], float)
    
    def test_ensemble_predictor_get_individual_metrics(self):
        """Test getting individual metrics from ensemble."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        xgb = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        ensemble.add_predictor(lstm, weight=1.0)
        ensemble.add_predictor(xgb, weight=2.0)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        ensemble.train(X, y, feature_names)
        
        # Evaluate individual predictors
        X_test = np.random.randn(20, 5)
        y_test = np.random.randint(0, 2, (20, 1))
        
        ensemble.evaluate(X_test, y_test)
        
        individual_metrics = ensemble.get_individual_metrics()
        
        assert 'LSTM' in individual_metrics
        assert 'XGBoost' in individual_metrics
        assert 'accuracy' in individual_metrics['LSTM']
        assert 'accuracy' in individual_metrics['XGBoost']
    
    def test_ensemble_predictor_get_feature_importance(self):
        """Test getting feature importance from ensemble."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        xgb = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        ensemble.add_predictor(lstm, weight=1.0)
        ensemble.add_predictor(xgb, weight=2.0)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100, 1))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        ensemble.train(X, y, feature_names)
        
        importance = ensemble.get_feature_importance()
        
        assert importance is not None
        assert len(importance) == 5
        assert 'feature_0' in importance
        assert 'feature_4' in importance
    
    def test_ensemble_predictor_predict_before_train(self):
        """Test that prediction before training raises error."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        ensemble.add_predictor(lstm, weight=1.0)
        
        X_test = np.random.randn(20, 5)
        
        with pytest.raises(ValueError):
            ensemble.predict(X_test)
    
    def test_ensemble_predictor_predict_direction_before_train(self):
        """Test that direction prediction before training raises error."""
        ensemble = EnsemblePredictor()
        
        lstm = LSTMPredictor(hidden_dim=16, num_layers=2, epochs=5, lr=0.01)
        ensemble.add_predictor(lstm, weight=1.0)
        
        X_test = np.random.randn(20, 5)
        
        with pytest.raises(ValueError):
            ensemble.predict_direction(X_test)


class TestXGBoostPredictor:
    """Tests for the XGBoostPredictor class."""

    def test_xgboost_predictor_initialization(self):
        """Test XGBoostPredictor initialization."""
        predictor = XGBoostPredictor(n_estimators=100, learning_rate=0.1)
        
        assert predictor.name == "XGBoost"
        assert predictor.n_estimators == 100
        assert predictor.learning_rate == 0.1
        assert predictor.is_trained == False
        assert predictor.model is None
    
    def test_xgboost_predictor_train(self):
        """Test XGBoostPredictor training."""
        predictor = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100,))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        assert predictor.is_trained == True
        assert predictor.model is not None
    
    def test_xgboost_predictor_predict(self):
        """Test XGBoostPredictor prediction."""
        predictor = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100,))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        # Predict on new data
        X_test = np.random.randn(20, 5)
        predictions = predictor.predict(X_test)
        
        assert predictions.shape[0] == X_test.shape[0]
        assert isinstance(predictions, np.ndarray)
    
    def test_xgboost_predictor_predict_direction(self):
        """Test XGBoostPredictor direction prediction."""
        predictor = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100,))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        # Predict direction on new data
        X_test = np.random.randn(20, 5)
        directions = predictor.predict_direction(X_test)
        
        assert directions.shape[0] == X_test.shape[0]
        assert np.all((directions == 0) | (directions == 1))
    
    def test_xgboost_predictor_evaluate(self):
        """Test XGBoostPredictor evaluation."""
        predictor = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100,))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        # Evaluate on test data
        X_test = np.random.randn(20, 5)
        y_test = np.random.randint(0, 2, (20,))
        
        metrics = predictor.evaluate(X_test, y_test)
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert isinstance(metrics['accuracy'], float)
    
    def test_xgboost_predictor_get_feature_importance(self):
        """Test XGBoostPredictor feature importance."""
        predictor = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        # Create synthetic data
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, (100,))
        feature_names = [f'feature_{i}' for i in range(5)]
        
        predictor.train(X, y, feature_names)
        
        importance = predictor.get_feature_importance()
        
        assert importance is not None
        assert len(importance) == 5
        assert 'feature_0' in importance
        assert 'feature_4' in importance
    
    def test_xgboost_predictor_predict_before_train(self):
        """Test that prediction before training raises error."""
        predictor = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        X_test = np.random.randn(20, 5)
        
        with pytest.raises(ValueError):
            predictor.predict(X_test)
    
    def test_xgboost_predictor_predict_direction_before_train(self):
        """Test that direction prediction before training raises error."""
        predictor = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        X_test = np.random.randn(20, 5)
        
        with pytest.raises(ValueError):
            predictor.predict_direction(X_test)
    
    def test_xgboost_predictor_get_feature_importance_before_train(self):
        """Test that feature importance before training returns None."""
        predictor = XGBoostPredictor(n_estimators=10, learning_rate=0.1)
        
        importance = predictor.get_feature_importance()
        
        assert importance is None
