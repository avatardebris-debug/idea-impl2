"""Shadow store — persistent storage for shadow mode data."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from rl_dropshipping.src.shadow.predictor import Prediction


class ShadowStore:
    """Persists shadow predictions and comparison results to disk.

    Uses JSON files for simplicity. Supports loading and saving.
    """

    def __init__(self, base_dir: str = "data/shadow"):
        self.base_dir = base_dir
        self._predictions_file = os.path.join(base_dir, "predictions.json")
        self._comparisons_file = os.path.join(base_dir, "comparisons.json")
        self._data_file = os.path.join(base_dir, "data.json")
        self._sample_count = 0
        os.makedirs(base_dir, exist_ok=True)

    def save_predictions(self, predictions: List[Prediction]) -> None:
        """Save predictions to JSON file."""
        data = [p.to_dict() for p in predictions]
        with open(self._predictions_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_predictions(self) -> List[Prediction]:
        """Load predictions from JSON file."""
        if not os.path.exists(self._predictions_file):
            return []
        with open(self._predictions_file, "r") as f:
            data = json.load(f)
        return [
            Prediction(
                timestamp=p["timestamp"],
                action_type=p["action_type"],
                prediction=p["prediction"],
                confidence=p["confidence"],
                channel=p.get("channel", ""),
            )
            for p in data
        ]

    def save_comparisons(self, comparisons: List[Dict[str, float]]) -> None:
        """Save comparison results to JSON file."""
        with open(self._comparisons_file, "w") as f:
            json.dump(comparisons, f, indent=2)

    def load_comparisons(self) -> List[Dict[str, float]]:
        """Load comparison results from JSON file."""
        if not os.path.exists(self._comparisons_file):
            return []
        with open(self._comparisons_file, "r") as f:
            return json.load(f)

    def save(self, data: Dict[str, Any]) -> None:
        """Save arbitrary data to the data file."""
        self._sample_count += 1
        with open(self._data_file, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> Dict[str, Any]:
        """Load data from the data file."""
        if not os.path.exists(self._data_file):
            return {}
        with open(self._data_file, "r") as f:
            return json.load(f)

    @property
    def sample_count(self) -> int:
        """Total number of samples stored."""
        return self._sample_count
