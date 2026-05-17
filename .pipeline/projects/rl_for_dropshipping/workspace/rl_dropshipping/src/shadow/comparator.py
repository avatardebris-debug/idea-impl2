"""Shadow comparator — computes prediction error metrics."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from rl_dropshipping.src.shadow.predictor import Prediction


class ShadowComparator:
    """Compares shadow predictions against actual outcomes.

    Computes MAE and RMSE on profit/ROI predictions vs. actuals.
    """

    def __init__(self):
        self._comparisons: List[Dict[str, Any]] = []

    def compute_error(
        self,
        predictions: List[Prediction],
        actuals: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Compute MAE and RMSE between predictions and actuals.

        Args:
            predictions: List of shadow predictions.
            actuals: List of actual outcome dicts with keys:
                - "predicted_value": float
                - "actual_value": float

        Returns:
            Dict with "mae" and "rmse" keys.
        """
        if len(predictions) != len(actuals):
            raise ValueError(
                f"Length mismatch: {len(predictions)} predictions vs "
                f"{len(actuals)} actuals"
            )

        errors = []
        for pred, actual in zip(predictions, actuals):
            pred_val = pred.prediction.get("value", 0.0)
            actual_val = actual.get("actual_value", 0.0)
            errors.append(abs(pred_val - actual_val))

        mae = sum(errors) / len(errors) if errors else 0.0
        rmse = math.sqrt(sum(e ** 2 for e in errors) / len(errors)) if errors else 0.0

        result = {"mae": mae, "rmse": rmse}
        self._comparisons.append(result)
        return result

    def get_comparison_history(self) -> List[Dict[str, float]]:
        """Return history of all comparison results."""
        return list(self._comparisons)

    def clear(self) -> None:
        """Clear comparison history."""
        self._comparisons.clear()

    def record_comparison(
        self,
        action_type: str,
        rl_reward: float,
        baseline_reward: float,
    ) -> None:
        """Record a comparison between RL and baseline."""
        self._comparisons.append({
            "action_type": action_type,
            "rl_reward": rl_reward,
            "baseline_reward": baseline_reward,
            "improvement": rl_reward - baseline_reward,
        })

    def get_improvement_rate(self) -> float:
        """Get the rate of improvement over baseline."""
        if not self._comparisons:
            return 0.0

        improvements = [c["improvement"] for c in self._comparisons if "improvement" in c]
        if not improvements:
            return 0.0

        improved_count = sum(1 for i in improvements if i > 0)
        return improved_count / len(improvements)

    def get_metrics(self) -> Dict[str, Any]:
        """Get comparison metrics."""
        if not self._comparisons:
            return {
                "sample_count": 0,
                "improvement_rate": 0.0,
            }

        improvements = [c["improvement"] for c in self._comparisons if "improvement" in c]
        if not improvements:
            return {
                "sample_count": len(self._comparisons),
                "improvement_rate": 0.0,
            }

        return {
            "sample_count": len(self._comparisons),
            "improvement_rate": self.get_improvement_rate(),
            "mean_improvement": sum(improvements) / len(improvements),
            "max_improvement": max(improvements),
            "min_improvement": min(improvements),
        }

    @property
    def sample_count(self) -> int:
        """Total number of comparisons."""
        return len(self._comparisons)
