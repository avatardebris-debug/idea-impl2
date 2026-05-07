"""Tests for the predictor layer."""

import pytest
import numpy as np

from chronovision.src.predictor.base import BasePredictor
from chronovision.src.predictor.lstm_predictor import LSTMPredictor, LSTMModel
from chronovision.src.predictor.ensemble_predictor import EnsemblePredictor


class TestBasePredictor:
    """Tests for BasePredictor."""
    
    def test_init(self):
        """Test initialization."""
        predictor = BasePredictor(name="Test")
        assert predictor.name == "Test"
        assert predictor.is_trained == False
        assert predictor.metrics == {}
    
    def test_predict_not_implemented(self):
        """Test that predict raises NotImplementedError."""
        predictor = BasePredictor(name="Test")
        with pytest.raises(NotImplementedError):
            predictor.predict(np.array([[1, 2, 3]]))
    
    def test_evaluate_not_implemented(self):
        """Test that evaluate raises NotImplementedError."""
        predictor = BasePredictor(name="Test")
        with pytest.raises(NotImplementedError):
            predictor.evaluate(np.array([[1, 2, 3]]), np.array([1]))


class TestLSTMModel:
    """Tests for LSTMModel."""
    
    def test_init(self):
        """Test initialization."""
        model = LSTMModel(input_dim=10, hidden_dim=32, num_layers=2)
        assert model.input_dim == 10
        assert model.hidden_dim == 32
        assert model.num_layers == 2
    
    def test_forward_shape(self):
        """Test forward pass output shape."""
        model = LSTMModel(input_dim=5, hidden_dim=16, num_layers=1)
        
        # Create dummy input
        batch_size = 2
        seq_len = 10
        X = np.random.randn(batch_size, seq_len, model.input_dim)
        
        output = model.forward(X)
        assert output.shape == (batch_size, 1)


class TestLSTMPredictor:
    """Tests for LSTMPredictor."""
    
    def test_init(self):
        """Test initialization."""
        predictor = LSTMPredictor(hidden_dim=64, num_layers=2, epochs=100, lr=0.01)
        assert predictor.hidden_dim == 64
        assert predictor.num_layers == 2
        assert predictor.epochs == 100
        assert predictor.lr == 0.01
        assert predictor.model is None
    
    def test_train_insufficient_data(self):
        """Test training with insufficient data."""
        predictor = LSTMPredictor()
        
        # Create minimal data
        X = np.random.randn(5, 10)
        y = np.random.randn(5, 1)
        
        with pytest.raises(ValueError):
            predictor.train(X, y)
    
    def test_predict_untrained(self):
        """Test prediction without training."""
        predictor = LSTMPredictor()
        X = np.random.randn(10, 5)
        
        with pytest.raises(ValueError):
            predictor.predict(X)
    
    def test_predict_direction(self):
        """Test direction prediction."""
        predictor = LSTMPredictor()
        
        # Create minimal data for training
        X = np.random.randn(20, 5)
        y = np.random.randn(20, 1)
        
        predictor.train(X, y)
        
        # Predict
        X_test = np.random.randn(20, 5)
        directions = predictor.predict_direction(X_test)
        
        assert directions.shape[0] == 10  # lookback = 10
        assert set(np.unique(directions)).issubset({0, 1})


class TestEnsemblePredictor:
    """Tests for EnsemblePredictor."""
    
    def test_init(self):
        """Test initialization."""
        ensemble = EnsemblePredictor()
        assert ensemble.predictors == []
        assert ensemble.weights == []
    
    def test_add_predictor(self):
        """Test adding predictor."""
        ensemble = EnsemblePredictor()
        predictor = LSTMPredictor()
        ensemble.add_predictor(predictor, weight=1.0)
        
        assert len(ensemble.predictors) == 1
        assert ensemble.weights == [1.0]
    
    def test_train(self):
        """Test training ensemble."""
        ensemble = EnsemblePredictor()
        predictor = LSTMPredictor()
        ensemble.add_predictor(predictor, weight=1.0)
        
        X = np.random.randn(20, 5)
        y = np.random.randn(20, 1)
        
        ensemble.train(X, y)
        assert ensemble.is_trained == True
    
    def test_predict_untrained(self):
        """Test prediction without training."""
        ensemble = EnsemblePredictor()
        X = np.random.randn(10, 5)
        
        with pytest.raises(ValueError):
            ensemble.predict(X)
    
    def test_evaluate(self):
        """Test evaluation."""
        ensemble = EnsemblePredictor()
        predictor = LSTMPredictor()
        ensemble.add_predictor(predictor, weight=1.0)
        
        X = np.random.randn(20, 5)
        y = np.random.randn(20, 1)
        
        ensemble.train(X, y)
        metrics = ensemble.evaluate(X, y)
        
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
    
    def test_get_individual_metrics(self):
        """Test getting individual metrics."""
        ensemble = EnsemblePredictor()
        predictor = LSTMPredictor()
        ensemble.add_predictor(predictor, weight=1.0)
        
        X = np.random.randn(20, 5)
        y = np.random.randn(20, 1)
        
        ensemble.train(X, y)
        individual_metrics = ensemble.get_individual_metrics()
        
        assert "LSTM" in individual_metrics
