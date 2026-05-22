"""EnsemblePredictor — combines multiple predictors for robust forecasting."""

import numpy as np
from typing import Dict, Any, List, Optional

from chronovision.src.predictor.base import BasePredictor
from chronovision.src.predictor.lstm_predictor import LSTMPredictor


class EnsemblePredictor(BasePredictor):
    """Combines multiple predictors for robust forecasting."""
    
    def __init__(self, predictors: Optional[List[BasePredictor]] = None):
        super().__init__(name="Ensemble")
        self.predictors: List[BasePredictor] = predictors or []
        self.weights: List[float] = []
    
    def add_predictor(self, predictor: BasePredictor, weight: float = 1.0) -> None:
        """Add a predictor to the ensemble."""
        self.predictors.append(predictor)
        self.weights.append(weight)
    
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None) -> None:
        """Train all predictors in the ensemble."""
        for predictor in self.predictors:
            predictor.train(X, y, feature_names)
        self.is_trained = True
        
        # Normalize weights
        total_weight = sum(self.weights)
        if total_weight > 0:
            self.weights = [w / total_weight for w in self.weights]
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the ensemble."""
        if not self.is_trained:
            raise ValueError("Ensemble not trained")
        
        predictions = []
        for predictor in self.predictors:
            predictions.append(predictor.predict(X))
            
        if not predictions:
            return np.array([])
            
        # Find minimum length
        min_len = min(len(p) for p in predictions)
        
        # Align and weight
        aligned = [p[-min_len:] * w for p, w in zip(predictions, self.weights)]
        return np.sum(aligned, axis=0)
    
    def predict_direction(self, X: np.ndarray) -> np.ndarray:
        """Predict price direction using ensemble."""
        predictions = self.predict(X)
        return (predictions > 0).astype(int)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate the ensemble."""
        for predictor in self.predictors:
            try:
                predictor.evaluate(X, y)
            except Exception:
                pass
        y_pred = self.predict_direction(X)
        y_aligned = y[-len(y_pred):] if len(y_pred) < len(y) else y
        if len(y_pred) > len(y): y_pred = y_pred[-len(y):]
        accuracy = np.mean(y_pred == y_aligned)
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
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get weighted feature importance from all predictors."""
        importance = {}
        for predictor, weight in zip(self.predictors, self.weights):
            pred_importance = predictor.get_feature_importance()
            if pred_importance:
                for feature, imp in pred_importance.items():
                    importance[feature] = importance.get(feature, 0) + imp * weight
        return importance
    
    def get_individual_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get metrics for each individual predictor."""
        metrics = {}
        for predictor in self.predictors:
            metrics[predictor.name] = predictor.get_metrics()
        return metrics
