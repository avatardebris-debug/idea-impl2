"""Surprise meter for Chronovision2.

Provides the SurpriseMeter class that compares predicted states against
actual observed states and computes a surprise score. Supports L1 and L2
distance metrics.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

import numpy as np


class SurpriseMeter:
    """Measures the 'surprise' (prediction error) between predicted and
    actual states.

    Attributes:
        default_metric: Default distance metric to use.
        normalize: Whether to normalize the score.
    """

    def __init__(
        self,
        default_metric: Literal["l1", "l2"] = "l2",
        normalize: bool = True,
    ) -> None:
        """Initialize the SurpriseMeter.

        Args:
            default_metric: Distance metric. Options: 'l1' (Manhattan), 'l2' (Euclidean).
            normalize: Whether to normalize the score by the number of fields.
        """
        self.default_metric = default_metric
        self.normalize = normalize

    def compute(
        self,
        predicted: Dict[str, Any],
        actual: Dict[str, Any],
        metric: Optional[Literal["l1", "l2"]] = None,
    ) -> float:
        """Compute the surprise score between predicted and actual states.

        Args:
            predicted: Predicted state dict.
            actual: Actual observed state dict.
            metric: Distance metric to use. Defaults to default_metric.

        Returns:
            Numeric surprise score (higher = more surprised).
        """
        metric = metric or self.default_metric

        # Extract numeric values from both states
        pred_values, actual_values = self._extract_numeric_values(predicted, actual)

        if len(pred_values) == 0:
            return 0.0

        if metric == "l1":
            score = self._l1_distance(pred_values, actual_values)
        elif metric == "l2":
            score = self._l2_distance(pred_values, actual_values)
        else:
            raise ValueError(f"Unknown metric: {metric}. Use 'l1' or 'l2'.")

        if self.normalize and len(pred_values) > 0:
            score = score / len(pred_values)

        return float(score)

    def compute_batch(
        self,
        predicted_states: list[Dict[str, Any]],
        actual_states: list[Dict[str, Any]],
        metric: Optional[Literal["l1", "l2"]] = None,
    ) -> list[float]:
        """Compute surprise scores for multiple state pairs.

        Args:
            predicted_states: List of predicted state dicts.
            actual_states: List of actual state dicts.
            metric: Distance metric.

        Returns:
            List of surprise scores.
        """
        if len(predicted_states) != len(actual_states):
            raise ValueError(
                "predicted_states and actual_states must have the same length"
            )
        return [
            self.compute(p, a, metric)
            for p, a in zip(predicted_states, actual_states)
        ]

    def compute_detailed(
        self,
        predicted: Dict[str, Any],
        actual: Dict[str, Any],
        metric: Optional[Literal["l1", "l2"]] = None,
    ) -> Dict[str, Any]:
        """Compute surprise with detailed breakdown.

        Args:
            predicted: Predicted state dict.
            actual: Actual observed state dict.
            metric: Distance metric.

        Returns:
            Dict with 'score', 'metric', 'per_field_errors', and 'num_fields'.
        """
        metric = metric or self.default_metric
        pred_values, actual_values = self._extract_numeric_values(predicted, actual)

        per_field: Dict[str, float] = {}
        for key in predicted:
            if key in actual:
                pv = predicted[key]
                av = actual[key]
                if isinstance(pv, (int, float, np.floating, np.integer)) and \
                   isinstance(av, (int, float, np.floating, np.integer)):
                    per_field[key] = abs(float(pv) - float(av))

        if metric == "l1":
            score = sum(per_field.values())
        else:
            score = float(np.sqrt(sum(v ** 2 for v in per_field.values())))

        if self.normalize and per_field:
            score = score / len(per_field)

        return {
            "score": float(score),
            "metric": metric,
            "per_field_errors": per_field,
            "num_fields": len(per_field),
        }

    def _extract_numeric_values(
        self,
        predicted: Dict[str, Any],
        actual: Dict[str, Any],
    ) -> tuple[np.ndarray, np.ndarray]:
        """Extract aligned numeric values from two state dicts."""
        pred_vals = []
        actual_vals = []

        # Get all keys from both dicts
        all_keys = set(predicted.keys()) | set(actual.keys())

        for key in sorted(all_keys):
            pv = predicted.get(key)
            av = actual.get(key)

            if isinstance(pv, (int, float, np.floating, np.integer)) and \
               isinstance(av, (int, float, np.floating, np.integer)):
                pred_vals.append(float(pv))
                actual_vals.append(float(av))

        return np.array(pred_vals), np.array(actual_vals)

    def _l1_distance(self, pred: np.ndarray, actual: np.ndarray) -> float:
        """Compute L1 (Manhattan) distance."""
        return float(np.sum(np.abs(pred - actual)))

    def _l2_distance(self, pred: np.ndarray, actual: np.ndarray) -> float:
        """Compute L2 (Euclidean) distance."""
        return float(np.sqrt(np.sum((pred - actual) ** 2)))
