"""Feature Selector — selects the most relevant features for prediction."""

import logging
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
from sklearn.feature_selection import (
    SelectKBest,
    f_classif,
    mutual_info_classif,
    RFE,
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)


class FeatureSelector:
    """Selects the most relevant features for prediction."""

    @staticmethod
    def select_by_variance(X: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Select features with variance above threshold.
        
        Args:
            X: Feature matrix.
            threshold: Minimum variance threshold.
            
        Returns:
            Boolean mask of selected features.
        """
        variances = np.var(X, axis=0)
        return variances > threshold

    @staticmethod
    def select_by_correlation(X: np.ndarray, y: np.ndarray, k: int = 10) -> np.ndarray:
        """Select features by correlation with target.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            k: Number of top features to select.
            
        Returns:
            Boolean mask of selected features.
        """
        selector = SelectKBest(f_classif, k=k)
        selector.fit(X, y)
        return selector.get_support()

    @staticmethod
    def select_by_mutual_info(X: np.ndarray, y: np.ndarray, k: int = 10) -> np.ndarray:
        """Select features by mutual information with target.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            k: Number of top features to select.
            
        Returns:
            Boolean mask of selected features.
        """
        selector = SelectKBest(mutual_info_classif, k=k)
        selector.fit(X, y)
        return selector.get_support()

    @staticmethod
    def select_by_rfe(X: np.ndarray, y: np.ndarray, n_features_to_select: int = 10) -> np.ndarray:
        """Select features by Recursive Feature Elimination.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            n_features_to_select: Number of features to select.
            
        Returns:
            Boolean mask of selected features.
        """
        estimator = RandomForestClassifier(n_estimators=100, random_state=42)
        selector = RFE(estimator, n_features_to_select=n_features_to_select)
        selector.fit(X, y)
        return selector.support_

    @staticmethod
    def select_by_importance(X: np.ndarray, y: np.ndarray, n_features_to_select: int = 10) -> np.ndarray:
        """Select features by importance from Random Forest.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            n_features_to_select: Number of features to select.
            
        Returns:
            Boolean mask of selected features.
        """
        estimator = RandomForestClassifier(n_estimators=100, random_state=42)
        estimator.fit(X, y)
        importances = estimator.feature_importances_
        indices = np.argsort(importances)[::-1]
        selected_indices = indices[:n_features_to_select]
        
        mask = np.zeros(X.shape[1], dtype=bool)
        mask[selected_indices] = True
        return mask

    @staticmethod
    def select_features(
        X: np.ndarray,
        y: np.ndarray,
        method: str = "mutual_info",
        k: int = 10,
        n_features_to_select: int = 10,
        threshold: float = 0.01,
    ) -> np.ndarray:
        """Select features using the specified method.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            method: Selection method ('variance', 'correlation', 'mutual_info', 'rfe', 'importance').
            k: Number of top features for correlation/mutual info.
            n_features_to_select: Number of features for RFE/importance.
            threshold: Variance threshold.
            
        Returns:
            Boolean mask of selected features.
        """
        if method == "variance":
            return FeatureSelector.select_by_variance(X, threshold)
        elif method == "correlation":
            return FeatureSelector.select_by_correlation(X, y, k)
        elif method == "mutual_info":
            return FeatureSelector.select_by_mutual_info(X, y, k)
        elif method == "rfe":
            return FeatureSelector.select_by_rfe(X, y, n_features_to_select)
        elif method == "importance":
            return FeatureSelector.select_by_importance(X, y, n_features_to_select)
        else:
            raise ValueError(f"Unknown method: {method}")

    @staticmethod
    def evaluate_feature_subset(X: np.ndarray, y: np.ndarray, mask: np.ndarray) -> float:
        """Evaluate the performance of a feature subset.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            mask: Boolean mask of selected features.
            
        Returns:
            Mean cross-validation score.
        """
        X_selected = X[:, mask]
        estimator = RandomForestClassifier(n_estimators=100, random_state=42)
        scores = cross_val_score(estimator, X_selected, y, cv=5, scoring='accuracy')
        return scores.mean()

    @staticmethod
    def get_feature_importance(X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Get feature importance from Random Forest.
        
        Args:
            X: Feature matrix.
            y: Target vector.
            
        Returns:
            Array of feature importances.
        """
        estimator = RandomForestClassifier(n_estimators=100, random_state=42)
        estimator.fit(X, y)
        return estimator.feature_importances_
