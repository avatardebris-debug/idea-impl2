"""Greedy agent implementation."""

import random
from typing import Any

from gameagent.agent.base import BaseAgent
from gameagent.env.types import Action, Observation


class GreedyAgent(BaseAgent):
    """Greedy agent that always selects the best known action.

    If no Q-values exist, it uses a greedy heuristic to move toward the goal.
    """

    def __init__(self):
        """Initialize the greedy agent."""
        self._q_table: dict[tuple, dict[Action, float]] = {}

    def act(self, observation: Any) -> Action:
        """Select the best known action.

        Args:
            observation: The current observation.

        Returns:
            The action with the highest Q-value, or a greedy action if no Q-values exist.
        """
        state_key = (
            observation.agent_position,
            observation.goal_position,
            tuple(sorted(observation.info.get("obstacles", []))),
        )

        if state_key in self._q_table and self._q_table[state_key]:
            return max(self._q_table[state_key], key=self._q_table[state_key].get)
        else:
            # Greedy heuristic: move toward the goal
            return self._greedy_action(observation)

    def _greedy_action(self, observation: Observation) -> Action:
        """Select action that moves toward the goal.

        Args:
            observation: The current observation.

        Returns:
            The action that moves the agent closer to the goal.
        """
        agent_pos = observation.agent_position
        goal_pos = observation.goal_position
        obstacles = set(observation.info.get("obstacles", []))

        # Calculate direction to goal
        dx = goal_pos[0] - agent_pos[0]
        dy = goal_pos[1] - agent_pos[1]

        # Prioritize the direction with larger distance
        if abs(dx) >= abs(dy):
            # Move horizontally first
            if dx > 0:
                action = Action.RIGHT
            elif dx < 0:
                action = Action.LEFT
            else:
                # No horizontal distance, move vertically
                if dy > 0:
                    action = Action.UP
                elif dy < 0:
                    action = Action.DOWN
                else:
                    # Already at goal
                    return Action.RIGHT
        else:
            # Move vertically first
            if dy > 0:
                action = Action.UP
            elif dy < 0:
                action = Action.DOWN
            else:
                # No vertical distance, move horizontally
                if dx > 0:
                    action = Action.RIGHT
                elif dx < 0:
                    action = Action.LEFT
                else:
                    # Already at goal
                    return Action.RIGHT

        # Check if the chosen action would hit an obstacle
        next_pos = self._get_next_position(agent_pos, action)
        if next_pos in obstacles:
            # Try alternative direction
            if action == Action.RIGHT:
                action = Action.UP if dy > 0 else Action.DOWN
            elif action == Action.LEFT:
                action = Action.UP if dy > 0 else Action.DOWN
            elif action == Action.DOWN:
                action = Action.RIGHT if dx > 0 else Action.LEFT
            elif action == Action.UP:
                action = Action.RIGHT if dx > 0 else Action.LEFT

        return action

    def _get_next_position(self, position: tuple[int, int], action: Action) -> tuple[int, int]:
        """Get the next position after taking an action.

        Args:
            position: Current position.
            action: Action to take.

        Returns:
            The next position.
        """
        x, y = position
        if action == Action.UP:
            return (x, y + 1)
        elif action == Action.DOWN:
            return (x, y - 1)
        elif action == Action.LEFT:
            return (x - 1, y)
        elif action == Action.RIGHT:
            return (x + 1, y)
        return position

    def update(self, state_key: tuple, action: Action, q_value: float) -> None:
        """Update the Q-value for a state-action pair.

        Args:
            state_key: The state key.
            action: The action.
            q_value: The new Q-value.
        """
        if state_key not in self._q_table:
            self._q_table[state_key] = {}
        self._q_table[state_key][action] = q_value

    def reset(self) -> None:
        """Reset the agent's internal state."""
        self._q_table = {}
