"""XGBoostPredictor — XGBoost-based predictor for financial forecasting."""

import numpy as np
from typing import Dict, Any, List, Optional

from chronovision.src.predictor.base import BasePredictor


class XGBoostPredictor(BasePredictor):
    """XGBoost-based predictor for financial forecasting."""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6, learning_rate: float = 0.1):
        super().__init__(name="XGBoost")
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model = None
        self.feature_names: List[str] = []
    
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None) -> None:
        """Train the XGBoost model.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            feature_names: Optional list of feature names.
        """
        try:
            import xgboost as xgb
        except ImportError:
            raise ImportError("xgboost is required for XGBoostPredictor. Install with: pip install xgboost")
        
        self.feature_names = feature_names or []
        
        # Convert to DMatrix
        dtrain = xgb.DMatrix(X, label=y)
        
        params = {
            'max_depth': self.max_depth,
            'learning_rate': self.learning_rate,
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
        }
        
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=self.n_estimators,
        )
        self.is_trained = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the trained XGBoost model.
        
        Args:
            X: Feature matrix.
            
        Returns:
            Predicted values.
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")
        
        dtest = xgb.DMatrix(X)
        predictions = self.model.predict(dtest)
        return predictions
    
    def predict_direction(self, X: np.ndarray) -> np.ndarray:
        """Predict price direction.
        
        Args:
            X: Feature matrix.
            
        Returns:
            Direction predictions (1=up, 0=down).
        """
        predictions = self.predict(X)
        return (predictions > 0.5).astype(int)
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance from the XGBoost model.
        
        Returns:
            Dictionary mapping feature names to importance scores.
        """
        if not self.is_trained or self.model is None:
            return None
        
        importance = self.model.get_score(importance_type='gain')
        
        # Convert to dictionary with feature names
        importance_dict = {}
        for i, (feat, imp) in enumerate(importance.items()):
            feat_name = self.feature_names[i] if i < len(self.feature_names) else f"feature_{i}"
            importance_dict[feat_name] = float(imp)
        
        return importance_dict
    
    def get_metrics(self) -> Dict[str, float]:
        """Get model metrics.
        
        Returns:
            Dictionary of model metrics.
        """
        if not self.is_trained or self.model is None:
            return {}
        
        # XGBoost doesn't provide built-in metrics after training
        # Return placeholder metrics
        return {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
        }
