"""Base agent classes and implementations."""

from abc import ABC, abstractmethod
from typing import Any, Optional
import random

from gameagent.env.types import Action


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def act(self, observation: Any) -> Action:
        """Select an action based on the current observation.

        Args:
            observation: The current observation from the environment.

        Returns:
            An action to execute.
        """
        pass

    def reset(self) -> None:
        """Reset the agent's internal state."""
        pass

    def set_training_mode(self, training: bool) -> None:
        """Set the agent's training mode.

        Args:
            training: True for training mode, False for evaluation mode.
        """
        pass


class RandomAgent(BaseAgent):
    """Random agent that selects actions uniformly at random."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the random agent.

        Args:
            seed: Optional random seed for reproducibility.
        """
        self.seed = seed
        self._rng = random.Random(seed)

    def act(self, observation: Any) -> Action:
        """Select a random action.

        Args:
            observation: The current observation (unused).

        Returns:
            A randomly selected action.
        """
        return self._rng.choice(list(Action))

    def reset(self) -> None:
        """Reset the agent's internal state."""
        if self.seed is not None:
            self._rng = random.Random(self.seed)
