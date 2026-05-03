"""Q-Learning agent for the GridWorld environment."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any, Optional

import numpy as np

from gameagent.agent.base import BaseAgent
from gameagent.env.types import Action, Observation


class QLearningAgent(BaseAgent):
    """Tabular Q-Learning agent.

    Uses a Q-table to learn the optimal policy for navigating the grid.
    State representation: (agent_position, goal_position, obstacles)
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        super().__init__()
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table: dict[tuple, dict[Action, float]] = defaultdict(
            lambda: defaultdict(float)
        )

    def _get_state_key(self, observation: Observation) -> tuple:
        """Convert observation to a hashable state key.

        Args:
            observation: The current observation.

        Returns:
            A tuple representing the state.
        """
        return (
            observation.agent_position,
            observation.goal_position,
            tuple(sorted(observation.info.get("obstacles", []))),
        )

    def act(self, observation: Any) -> Action:
        """Select an action using epsilon-greedy policy.

        Args:
            observation: The current observation.

        Returns:
            An action to execute.
        """
        state_key = self._get_state_key(observation)

        if random.random() < self.epsilon:
            return random.choice(list(Action))

        if state_key in self.q_table and self.q_table[state_key]:
            return max(self.q_table[state_key], key=self.q_table[state_key].get)
        else:
            return random.choice(list(Action))

    def update(
        self,
        state_key: tuple,
        action: Action,
        reward: float,
        next_state_key: tuple,
        done: bool,
    ) -> float:
        """Update the Q-value for a state-action pair.

        Args:
            state_key: The current state key.
            action: The action taken.
            reward: The reward received.
            next_state_key: The next state key.
            done: Whether the episode has ended.

        Returns:
            The new Q-value.
        """
        current_q = self.q_table[state_key][action]

        if done:
            target = reward
        else:
            max_next_q = max(self.q_table[next_state_key].values()) if self.q_table[next_state_key] else 0
            target = reward + self.discount_factor * max_next_q

        self.q_table[state_key][action] = current_q + self.learning_rate * (target - current_q)
        return self.q_table[state_key][action]

    def decay_epsilon(self) -> None:
        """Decay the exploration rate."""
        self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

    def reset(self) -> None:
        """Reset the agent's internal state."""
        self.q_table.clear()
        self.epsilon = 1.0
