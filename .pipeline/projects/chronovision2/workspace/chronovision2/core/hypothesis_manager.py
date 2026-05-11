"""Hypothesis manager and RL reward loop for Chronovision2.

Provides the HypothesisManager class that stores, updates, and scores
hypotheses based on surprise scores, and wires the RL reward loop that
adjusts hypothesis weights over time.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from chronovision2.core.surprise_meter import SurpriseMeter


@dataclass
class HypothesisRecord:
    """Internal record for a hypothesis."""
    hypothesis_id: str
    config: Dict[str, Any]
    weight: float
    score: float
    survival_count: int
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_config(self) -> Dict[str, Any]:
        """Export the hypothesis as a config dict."""
        return {
            "hypothesis_id": self.hypothesis_id,
            "weight": self.weight,
            "score": self.score,
            "config": copy.deepcopy(self.config),
        }


class HypothesisManager:
    """Manages a collection of hypotheses, scores them via SurpriseMeter,
    and updates weights using a simple RL-style reward mechanism.

    The reward mechanism works as follows:
    - Lower surprise = higher reward
    - Weights are updated using exponential moving average of rewards
    - Hypotheses with consistently low surprise get higher weights
    - Hypotheses can be pruned if they perform poorly

    Attributes:
        hypotheses: Dict of hypothesis_id -> HypothesisRecord.
        surprise_meter: SurpriseMeter instance for scoring.
        learning_rate: RL learning rate for weight updates.
        min_weight: Minimum weight before pruning.
        reward_decay: Decay factor for reward history.
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        min_weight: float = 0.01,
        reward_decay: float = 0.95,
        surprise_metric: str = "l2",
        normalize_surprise: bool = True,
    ) -> None:
        """Initialize the HypothesisManager.

        Args:
            learning_rate: Step size for weight updates (RL learning rate).
            min_weight: Minimum weight; hypotheses below this are pruned.
            reward_decay: Decay factor for historical rewards.
            surprise_metric: Default metric for SurpriseMeter.
            normalize_surprise: Whether to normalize surprise scores.
        """
        self.hypotheses: Dict[str, HypothesisRecord] = {}
        self.learning_rate = learning_rate
        self.min_weight = min_weight
        self.reward_decay = reward_decay
        self.surprise_meter = SurpriseMeter(
            default_metric=surprise_metric,
            normalize=normalize_surprise,
        )
        self._episode_count: int = 0

    def add_hypothesis(
        self,
        hypothesis_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        initial_weight: float = 1.0,
    ) -> str:
        """Add a new hypothesis.

        Args:
            hypothesis_id: ID for the hypothesis. Auto-generated if None.
            config: Hypothesis configuration dict.
            initial_weight: Starting weight.

        Returns:
            The hypothesis_id.
        """
        if hypothesis_id is None:
            hypothesis_id = f"hyp_{uuid.uuid4().hex[:8]}"

        if hypothesis_id in self.hypotheses:
            raise ValueError(f"Hypothesis '{hypothesis_id}' already exists")

        self.hypotheses[hypothesis_id] = HypothesisRecord(
            hypothesis_id=hypothesis_id,
            config=config or {},
            weight=initial_weight,
            score=0.0,
            survival_count=0,
        )
        return hypothesis_id

    def remove_hypothesis(self, hypothesis_id: str) -> bool:
        """Remove a hypothesis.

        Args:
            hypothesis_id: ID of the hypothesis to remove.

        Returns:
            True if removed, False if not found.
        """
        if hypothesis_id in self.hypotheses:
            del self.hypotheses[hypothesis_id]
            return True
        return False

    def score_hypothesis(
        self,
        hypothesis_id: str,
        predicted_state: Dict[str, Any],
        actual_state: Dict[str, Any],
    ) -> float:
        """Score a hypothesis by comparing its prediction against actual state.

        Args:
            hypothesis_id: ID of the hypothesis to score.
            predicted_state: The predicted state from the hypothesis.
            actual_state: The actual observed state.

        Returns:
            The surprise score (lower is better).
        """
        if hypothesis_id not in self.hypotheses:
            raise ValueError(f"Hypothesis '{hypothesis_id}' not found")

        surprise = self.surprise_meter.compute(predicted_state, actual_state)
        record = self.hypotheses[hypothesis_id]

        # Update score (running average of surprise)
        if record.score == 0.0 and record.survival_count == 0:
            record.score = surprise
        else:
            record.score = (
                (1 - self.reward_decay) * surprise + self.reward_decay * record.score
            )

        record.survival_count += 1
        record.history.append({
            "episode": self._episode_count,
            "surprise": surprise,
            "score": record.score,
        })

        return surprise

    def update_weights(self) -> Dict[str, float]:
        """Update hypothesis weights using RL-style reward mechanism.

        Rewards are computed as inverse of surprise scores (lower surprise = higher reward).
        Weights are updated using exponential moving average of rewards.

        Returns:
            Dict mapping hypothesis_id to updated weight.
        """
        if not self.hypotheses:
            return {}

        # Compute rewards (inverse of surprise, with smoothing)
        rewards: Dict[str, float] = {}
        for hyp_id, record in self.hypotheses.items():
            # Reward = 1 / (1 + score) — sigmoid-like transformation
            reward = 1.0 / (1.0 + record.score)
            rewards[hyp_id] = reward

        # Update weights using exponential moving average of rewards
        for hyp_id, record in self.hypotheses.items():
            reward = rewards[hyp_id]
            # Exponential moving average of reward
            record.weight = (
                (1 - self.learning_rate) * record.weight +
                self.learning_rate * reward
            )
            # Clamp weight
            record.weight = max(self.min_weight, record.weight)

        # Normalize weights to sum to 1
        total_weight = sum(r.weight for r in self.hypotheses.values())
        if total_weight > 0:
            for record in self.hypotheses.values():
                record.weight /= total_weight

        # Prune low-weight hypotheses
        self._prune_low_weight()

        self._episode_count += 1

        return {hid: r.weight for hid, r in self.hypotheses.items()}

    def get_hypothesis_configs(self) -> List[Dict[str, Any]]:
        """Get current hypothesis configs for the next prediction cycle.

        Returns:
            List of hypothesis config dicts with updated weights.
        """
        configs = []
        for record in self.hypotheses.values():
            config = copy.deepcopy(record.config)
            config["hypothesis_id"] = record.hypothesis_id
            config["weight"] = record.weight
            configs.append(config)
        return configs

    def get_best_hypothesis(self) -> Optional[str]:
        """Get the ID of the hypothesis with the lowest score.

        Returns:
            Hypothesis ID or None if no hypotheses.
        """
        if not self.hypotheses:
            return None
        return min(self.hypotheses, key=lambda hid: self.hypotheses[hid].score)

    def get_all_scores(self) -> Dict[str, float]:
        """Get all hypothesis scores.

        Returns:
            Dict mapping hypothesis_id to score.
        """
        return {hid: r.score for hid, r in self.hypotheses.items()}

    def get_all_weights(self) -> Dict[str, float]:
        """Get all hypothesis weights.

        Returns:
            Dict mapping hypothesis_id to weight.
        """
        return {hid: r.weight for hid, r in self.hypotheses.items()}

    def run_reward_cycle(
        self,
        predictions: Dict[str, Dict[str, Any]],
        actual_state: Dict[str, Any],
    ) -> Dict[str, float]:
        """Run a full reward cycle: score all hypotheses and update weights.

        Args:
            predictions: Dict mapping hypothesis_id to predicted state.
            actual_state: The actual observed state.

        Returns:
            Dict mapping hypothesis_id to updated weight.
        """
        # Score each hypothesis
        for hyp_id, pred_state in predictions.items():
            self.score_hypothesis(hyp_id, pred_state, actual_state)

        # Update weights
        return self.update_weights()

    def _prune_low_weight(self) -> None:
        """Remove hypotheses with weights below the minimum threshold."""
        to_remove = [
            hid for hid, r in self.hypotheses.items()
            if r.weight < self.min_weight
        ]
        for hid in to_remove:
            del self.hypotheses[hid]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the hypothesis manager state.

        Returns:
            Summary dict with counts, best hypothesis, and weight distribution.
        """
        if not self.hypotheses:
            return {
                "count": 0,
                "best_hypothesis": None,
                "weights": {},
                "scores": {},
            }

        best = self.get_best_hypothesis()
        return {
            "count": len(self.hypotheses),
            "best_hypothesis": best,
            "weights": {hid: r.weight for hid, r in self.hypotheses.items()},
            "scores": {hid: r.score for hid, r in self.hypotheses.items()},
            "episode_count": self._episode_count,
        }
