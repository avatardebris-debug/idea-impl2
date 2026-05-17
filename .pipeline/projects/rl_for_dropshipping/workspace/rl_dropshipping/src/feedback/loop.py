"""Feedback loop module — collects outcomes and retrains the RL agent."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FeedbackSample:
    """A single feedback sample for retraining."""
    state: Dict[str, float]
    action: int
    reward: float
    next_state: Dict[str, float]
    done: bool
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "action": self.action,
            "reward": self.reward,
            "next_state": self.next_state,
            "done": self.done,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FeedbackSample:
        return cls(
            state=data["state"],
            action=data["action"],
            reward=data["reward"],
            next_state=data["next_state"],
            done=data["done"],
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )


class FeedbackCollector:
    """Collects feedback samples for retraining.

    Stores samples in memory and supports persistence to disk.
    """

    def __init__(self, max_samples: int = 100000):
        self.max_samples = max_samples
        self._samples: List[FeedbackSample] = []

    def add_sample(
        self,
        state: Dict[str, float],
        action: int,
        reward: float,
        next_state: Dict[str, float],
        done: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeedbackSample:
        """Add a feedback sample."""
        sample = FeedbackSample(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            metadata=metadata or {},
        )
        self._samples.append(sample)

        # Enforce max samples
        if len(self._samples) > self.max_samples:
            self._samples = self._samples[-self.max_samples:]

        logger.debug(
            f"Feedback sample added: reward={reward:.3f}, done={done}"
        )
        return sample

    def get_samples(
        self,
        since: Optional[float] = None,
        min_reward: Optional[float] = None,
        max_reward: Optional[float] = None,
    ) -> List[FeedbackSample]:
        """Get feedback samples, optionally filtered."""
        results = self._samples
        if since is not None:
            results = [s for s in results if s.timestamp >= since]
        if min_reward is not None:
            results = [s for s in results if s.reward >= min_reward]
        if max_reward is not None:
            results = [s for s in results if s.reward <= max_reward]
        return results

    def get_recent_samples(self, n: int = 100) -> List[FeedbackSample]:
        """Get the most recent n samples."""
        return self._samples[-n:]

    def clear(self) -> None:
        """Clear all samples."""
        self._samples.clear()
        logger.debug("Feedback samples cleared")

    @property
    def sample_count(self) -> int:
        """Total number of samples."""
        return len(self._samples)


class FeedbackProcessor:
    """Processes feedback samples for retraining.

    Computes statistics, filters outliers, and prepares data for training.
    """

    def __init__(self):
        self._processed_count = 0

    def compute_statistics(
        self,
        samples: List[FeedbackSample],
    ) -> Dict[str, float]:
        """Compute statistics over a set of samples."""
        if not samples:
            return {
                "mean_reward": 0.0,
                "std_reward": 0.0,
                "min_reward": 0.0,
                "max_reward": 0.0,
                "sample_count": 0,
            }

        rewards = [s.reward for s in samples]
        mean_reward = sum(rewards) / len(rewards)
        variance = sum((r - mean_reward) ** 2 for r in rewards) / len(rewards)
        std_reward = variance ** 0.5

        return {
            "mean_reward": mean_reward,
            "std_reward": std_reward,
            "min_reward": min(rewards),
            "max_reward": max(rewards),
            "sample_count": len(samples),
        }

    def filter_outliers(
        self,
        samples: List[FeedbackSample],
        std_threshold: float = 3.0,
    ) -> List[FeedbackSample]:
        """Filter out outlier samples based on reward."""
        if len(samples) < 2:
            return samples

        stats = self.compute_statistics(samples)
        mean = stats["mean_reward"]
        std = stats["std_reward"]

        if std == 0:
            return samples

        return [
            s for s in samples
            if abs(s.reward - mean) <= std_threshold * std
        ]

    def prepare_training_data(
        self,
        samples: List[FeedbackSample],
        state_dim: int,
        action_dim: int,
    ) -> Tuple[List[List[float]], List[int], List[float]]:
        """Prepare training data from samples.

        Returns:
            Tuple of (states, actions, rewards).
        """
        states = [list(s.state.values()) for s in samples]
        actions = [s.action for s in samples]
        rewards = [s.reward for s in samples]

        # Pad states if necessary
        max_len = max(len(s) for s in states) if states else 0
        padded_states = []
        for s in states:
            if len(s) < max_len:
                s = s + [0.0] * (max_len - len(s))
            padded_states.append(s)

        return padded_states, actions, rewards

    def process_and_train(
        self,
        collector: FeedbackCollector,
        agent: Any,
        n_samples: int = 1000,
    ) -> Dict[str, float]:
        """Process feedback and trigger retraining.

        Args:
            collector: FeedbackCollector instance.
            agent: RL agent with a train() method.
            n_samples: Number of samples to use for training.

        Returns:
            Training statistics.
        """
        samples = collector.get_recent_samples(n_samples * 2)
        samples = self.filter_outliers(samples)

        if len(samples) < 10:
            logger.warning("Not enough samples for training")
            return {"status": "insufficient_data"}

        stats = self.compute_statistics(samples)
        logger.info(
            f"Preparing training data: {len(samples)} samples, "
            f"mean_reward={stats['mean_reward']:.3f}"
        )

        # Trigger retraining (agent-specific)
        if hasattr(agent, "train"):
            agent.train(samples)
            stats["status"] = "trained"
        else:
            stats["status"] = "no_train_method"

        self._processed_count += len(samples)
        return stats

    @property
    def processed_count(self) -> int:
        """Total number of samples processed."""
        return self._processed_count
