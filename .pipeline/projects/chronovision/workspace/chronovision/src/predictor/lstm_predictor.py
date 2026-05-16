"""LSTMPredictor — LSTM-based predictor for financial time series."""

import numpy as np
from typing import Dict, Any, List, Optional

from chronovision.src.predictor.base import BasePredictor


class LSTMModel:
    """Simple LSTM implementation for demonstration."""
    
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Initialize weights (simplified)
        self.W_xh = np.random.randn(input_dim, hidden_dim) * 0.1
        self.W_hh = np.random.randn(hidden_dim, hidden_dim) * 0.1
        self.W_hy = np.random.randn(hidden_dim, 1) * 0.1
        self.b_h = np.zeros(hidden_dim)
        self.b_y = np.zeros(1)
        
        self.is_trained = False
    
    def forward(self, X: np.ndarray) -> np.ndarray:
        """Forward pass through the LSTM."""
        # X shape: (batch, seq_len, input_dim)
        batch_size, seq_len, _ = X.shape
        
        # Initialize hidden state
        h = np.zeros((batch_size, self.hidden_dim))
        
        # Process each time step
        for t in range(seq_len):
            x_t = X[:, t, :]
            h = np.tanh(x_t @ self.W_xh + h @ self.W_hh + self.b_h)
        
        # Output layer
        y = h @ self.W_hy + self.b_y
        self.h = h
        return y
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 100, lr: float = 0.01) -> List[float]:
        """Train the LSTM model."""
        losses = []
        batch_size = X.shape[0]
        
        for epoch in range(epochs):
            # Forward pass
            y_pred = self.forward(X)
            
            # Compute loss (MSE)
            loss = np.mean((y_pred - y) ** 2)
            losses.append(loss)
            
            if epoch % 20 == 0:
                print(f"Epoch {epoch}, Loss: {loss:.6f}")
            
            # Simplified gradient update
            error = y_pred - y
            dh = error @ self.W_hy.T
            
            # Update weights (simplified)
            self.W_hy -= lr * (self.h.T @ error) / batch_size
            self.b_y -= lr * np.mean(error, axis=0)
            
            # Update hidden weights (simplified)
            for t in range(X.shape[1]):
                x_t = X[:, t, :]
                dh_x = dh * (1 - self.h ** 2)
                self.W_xh -= lr * (x_t.T @ dh_x) / batch_size
                self.W_hh -= lr * (self.h.T @ dh_x) / batch_size
                self.b_h -= lr * np.mean(dh_x, axis=0)
        
        self.is_trained = True
        return losses


class LSTMPredictor(BasePredictor):
    """LSTM-based predictor for financial forecasting."""
    
    def __init__(self, hidden_dim: int = 64, num_layers: int = 2, epochs: int = 100, lr: float = 0.01):
        super().__init__(name="LSTM")
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.epochs = epochs
        self.lr = lr
        self.model: Optional[LSTMModel] = None
        self.feature_names: List[str] = []
    
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None) -> None:
        """Train the LSTM model."""
        self.feature_names = feature_names or []
        
        # Prepare data for LSTM: (batch, seq_len, features)
        # For simplicity, use last lookback steps as sequence
        lookback = min(10, X.shape[0] // 2)
        if lookback < 2:
            lookback = 2
        
        # Create sequences
        sequences = []
        targets = []
        for i in range(len(X) - lookback):
            seq = X[i:i+lookback]
            sequences.append(seq)
            targets.append(y[i+lookback])
        
        if len(sequences) < 10:
            raise ValueError("Not enough data to create sequences")
        
        X_seq = np.array(sequences)
        y_seq = np.array(targets).reshape(-1, 1)
        
        input_dim = X.shape[1]
        self.model = LSTMModel(input_dim, self.hidden_dim, self.num_layers)
        self.model.train(X_seq, y_seq, self.epochs, self.lr)
        self.is_trained = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the trained LSTM model."""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")
        
        lookback = min(10, X.shape[0] // 2)
        if lookback < 2:
            lookback = 2
        
        predictions = []
        for i in range(len(X) - lookback):
            seq = X[i:i+lookback].reshape(1, lookback, X.shape[1])
            pred = self.model.forward(seq)
            predictions.append(pred[0, 0])
        
        return np.array(predictions)
    
    def predict_direction(self, X: np.ndarray) -> np.ndarray:
        """Predict price direction."""
        predictions = self.predict(X)
        return (predictions > 0).astype(int)
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance (simplified)."""
        if not self.is_trained or self.model is None:
            return None
        
        # Use weight magnitudes as proxy for importance
        importance = {}
        for i, name in enumerate(self.feature_names):
            importance[name] = float(np.mean(np.abs(self.model.W_xh[i, :])))
        return importance
