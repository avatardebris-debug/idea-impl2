"""BasePredictor — abstract base class for all predictors."""

import abc
from typing import Dict, Any, List, Optional
import numpy as np


class BasePredictor(abc.ABC):
    """Abstract base class for financial predictors."""
    
    def __init__(self, name: str = "base"):
        self.name = name
        self.is_trained = False
        self.metrics: Dict[str, float] = {}
    
    @abc.abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the predictor on feature matrix X and target y."""
        pass
    
    @abc.abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the trained model."""
        pass
    
    @abc.abstractmethod
    def predict_direction(self, X: np.ndarray) -> np.ndarray:
        """Predict price direction (1=up, 0=down)."""
        pass
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate the predictor on test data."""
        y_pred = self.predict_direction(X)
        
        # Squeeze arrays to handle (N, 1) vs (N,)
        if y.ndim == 2 and y.shape[1] == 1: y = y.flatten()
        if y_pred.ndim == 2 and y_pred.shape[1] == 1: y_pred = y_pred.flatten()
        
        y_aligned = y[-len(y_pred):] if len(y_pred) < len(y) else y
        if len(y_pred) > len(y_aligned): y_pred = y_pred[-len(y_aligned):]
        
        accuracy = float(np.mean(y_pred == y_aligned))
        precision = self._precision(y_aligned, y_pred)
        recall = self._recall(y_aligned, y_pred)
        f1 = self._f1_score(y_aligned, y_pred)
        
        self.metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        }
        return self.metrics
    
    def _precision(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        return tp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    def _recall(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        return tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    def _f1_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        p = self._precision(y_true, y_pred)
        r = self._recall(y_true, y_pred)
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    
    def get_metrics(self) -> Dict[str, float]:
        """Get evaluation metrics."""
        return self.metrics.copy()
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance if available."""
        return None
