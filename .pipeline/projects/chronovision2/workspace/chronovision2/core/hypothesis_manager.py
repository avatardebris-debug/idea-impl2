"""
hypothesis_manager.py
Manages a population of hypotheses, each with a weight, score, and config.

Hypotheses represent candidate strategies (e.g., different learning rates,
prompt templates, or model configurations). The system scores them against
ground truth, then updates weights via a reinforcement-learning loop so that
better hypotheses get more influence over future decisions.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class HypothesisRecord:
    """Internal record for a single hypothesis."""
    hypothesis_id: str
    config: dict[str, Any]
    weight: float = 1.0          # unnormalized weight (will be normalised)
    score: float = 0.0           # cumulative surprise (lower = better)
    survival_count: int = 0      # how many times it survived pruning
    history: list[dict] = field(default_factory=list)  # past scores


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class HypothesisManager:
    """
    Manages a population of hypotheses with RL-style weight updates.

    Parameters
    ----------
    surprise_metric : str
        "l1" or "l2" — how to compute surprise (prediction vs actual).
    learning_rate : float
        Step-size for weight updates (0–1).
    min_weight : float
        Hypotheses with weight below this are pruned.
    reward_decay : float
        Exponential decay for running-average scoring (0–1).
    """

    def __init__(
        self,
        surprise_metric: str = "l2",
        learning_rate: float = 0.1,
        min_weight: float = 0.01,
        reward_decay: float = 0.95,
        **kwargs,
    ):
        self.surprise_metric = surprise_metric
        self.learning_rate = learning_rate
        self.min_weight = min_weight
        self.reward_decay = reward_decay
        self.hypotheses: dict[str, HypothesisRecord] = {}
        self.episode_count: int = 0
        self._episode_count: int = 0  # alias for compat

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def add_hypothesis(
        self,
        hypothesis_id: str | None = None,
        config: dict[str, Any] | None = None,
        initial_weight: float = 1.0,
    ) -> str:
        """
        Register a new hypothesis.

        Returns the hypothesis ID (auto-generated if not provided).
        Raises ValueError if the ID already exists.
        """
        if hypothesis_id is None:
            hypothesis_id = f"hyp_{uuid.uuid4().hex[:8]}"
        if hypothesis_id in self.hypotheses:
            raise ValueError(f"Hypothesis '{hypothesis_id}' already exists")
        self.hypotheses[hypothesis_id] = HypothesisRecord(
            hypothesis_id=hypothesis_id,
            config=config or {},
            weight=initial_weight,
        )
        return hypothesis_id

    def remove_hypothesis(self, hypothesis_id: str) -> bool:
        """Remove a hypothesis. Returns True if it existed."""
        if hypothesis_id in self.hypotheses:
            del self.hypotheses[hypothesis_id]
            return True
        return False

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score_hypothesis(
        self,
        hypothesis_id: str,
        prediction: dict[str, float],
        actual: dict[str, float],
    ) -> float:
        """
        Score a hypothesis by computing surprise between prediction and actual.

        Surprise is the normalised distance (L1 or L2) between the two dicts.
        Lower surprise → better hypothesis.
        Uses exponential moving average with reward_decay.

        Returns the computed surprise value.
        """
        rec = self.hypotheses.get(hypothesis_id)
        if rec is None:
            raise ValueError(f"Hypothesis '{hypothesis_id}' not found")

        # Compute surprise
        surprise = self._compute_surprise(prediction, actual)

        # Running average with decay
        if rec.survival_count == 0:
            rec.score = surprise
        else:
            rec.score = (1 - self.reward_decay) * surprise + self.reward_decay * rec.score

        rec.survival_count += 1
        rec.history.append({
            "episode": self.episode_count,
            "surprise": surprise,
            "score": rec.score,
            "prediction": prediction,
            "actual": actual,
        })
        return surprise

    def _compute_surprise(self, prediction: dict, actual: dict) -> float:
        """Compute normalised surprise between prediction and actual dicts."""
        # Only compare keys present in BOTH dicts
        common_keys = set(prediction.keys()) & set(actual.keys())
        if not common_keys:
            return 0.0

        total = 0.0
        for k in common_keys:
            p = prediction[k]
            a = actual[k]
            diff = p - a
            if self.surprise_metric == "l2":
                total += diff ** 2
            else:  # l1
                total += abs(diff)

        # Normalise by number of fields
        normalised = total / len(common_keys)

        if self.surprise_metric == "l2":
            normalised = math.sqrt(normalised)

        return normalised

    # ------------------------------------------------------------------
    # Weight updates
    # ------------------------------------------------------------------

    def update_weights(self) -> dict[str, float]:
        """
        Update hypothesis weights based on their scores.

        Uses exponential decay: weight *= exp(-lr * surprise).
        Then normalises so weights sum to 1.

        Returns the normalised weights dict.
        """
        if not self.hypotheses:
            return {}

        # Exponential decay based on score
        for rec in self.hypotheses.values():
            rec.weight *= math.exp(-self.learning_rate * rec.score)

        # Normalise
        total = sum(r.weight for r in self.hypotheses.values())
        if total == 0:
            # Fallback: equal weights
            n = len(self.hypotheses)
            for rec in self.hypotheses.values():
                rec.weight = 1.0 / n
        else:
            for rec in self.hypotheses.values():
                rec.weight /= total

        # Prune low-weight hypotheses
        self.prune()

        self.episode_count += 1
        self._episode_count = self.episode_count
        return {hid: rec.weight for hid, rec in self.hypotheses.items()}

    def prune(self, min_weight: float | None = None) -> int:
        """
        Remove hypotheses with weight below min_weight.

        Parameters
        ----------
        min_weight : float, optional
            Threshold for pruning. Defaults to self.min_weight.

        Returns
        -------
        int
            Number of hypotheses pruned.
        """
        if min_weight is None:
            min_weight = self.min_weight
        
        if not self.hypotheses:
            return 0
        
        to_remove = [
            hid for hid, rec in self.hypotheses.items()
            if rec.weight < min_weight
        ]
        for hid in to_remove:
            del self.hypotheses[hid]
        
        return len(to_remove)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_best_hypothesis(self) -> str | None:
        """Return the hypothesis ID with the lowest score (best performer)."""
        if not self.hypotheses:
            return None
        return min(self.hypotheses, key=lambda hid: self.hypotheses[hid].score)

    def get_all_scores(self) -> dict[str, float]:
        """Return {hypothesis_id: score} for all hypotheses."""
        return {hid: rec.score for hid, rec in self.hypotheses.items()}

    def get_all_weights(self) -> dict[str, float]:
        """Return {hypothesis_id: weight} for all hypotheses."""
        return {hid: rec.weight for hid, rec in self.hypotheses.items()}

    def get_hypothesis_configs(self) -> list[dict]:
        """Return list of configs with weights and IDs for external use."""
        result = []
        for hid, rec in self.hypotheses.items():
            entry = dict(rec.config)
            entry["hypothesis_id"] = hid
            entry["weight"] = rec.weight
            entry["score"] = rec.score
            result.append(entry)
        return result

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of the current state."""
        best = self.get_best_hypothesis()
        return {
            "count": len(self.hypotheses),
            "best_hypothesis": best,
            "weights": self.get_all_weights(),
            "scores": self.get_all_scores(),
            "episode_count": self.episode_count,
        }

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def run_reward_cycle(
        self,
        predictions: dict[str, dict[str, float]],
        actual: dict[str, float],
    ) -> dict[str, float]:
        """
        Score all hypotheses against `actual`, then update weights.

        Parameters
        ----------
        predictions : dict
            {hypothesis_id: prediction_dict}
        actual : dict
            Ground truth values
        """
        for hid, pred in predictions.items():
            if hid in self.hypotheses:
                self.score_hypothesis(hid, pred, actual)
        return self.update_weights()
