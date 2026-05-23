"""Monte Carlo learning module for blackjack.

This module provides Monte Carlo control algorithms for learning optimal
blackjack strategy through simulation and reinforcement learning.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Tuple
import random
import json
import os
from ..simulators.blackjack import (
    BlackjackGame,
    BlackjackResult,
    BlackjackResultData,
    Card,
    Deck,
    GameStatus,
    Hand,
    SimulatorStats,
)


class Action(Enum):
    """Enumeration of possible actions in blackjack."""
    HIT = auto()
    STAND = auto()
    DOUBLE = auto()
    SURRENDER = auto()
    SPLIT = auto()


@dataclass
class State:
    """State representation for blackjack."""
    player_total: int
    player_hand_type: str
    dealer_upcard: int
    can_double: bool
    can_split: bool
    can_surrender: bool

    def __hash__(self) -> int:
        """Generate hash for state."""
        return hash((
            self.player_total,
            self.player_hand_type,
            self.dealer_upcard,
            self.can_double,
            self.can_split,
            self.can_surrender,
        ))

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, State):
            return False
        return (
            self.player_total == other.player_total and
            self.player_hand_type == other.player_hand_type and
            self.dealer_upcard == other.dealer_upcard and
            self.can_double == other.can_double and
            self.can_split == other.can_split and
            self.can_surrender == other.can_surrender
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "player_total": self.player_total,
            "player_hand_type": self.player_hand_type,
            "dealer_upcard": self.dealer_upcard,
            "can_double": self.can_double,
            "can_split": self.can_split,
            "can_surrender": self.can_surrender,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "State":
        """Create from dictionary."""
        return cls(
            player_total=data["player_total"],
            player_hand_type=data["player_hand_type"],
            dealer_upcard=data["dealer_upcard"],
            can_double=data["can_double"],
            can_split=data["can_split"],
            can_surrender=data["can_surrender"],
        )


@dataclass
class Episode:
    """Represents a complete episode of blackjack."""
    states: List[State] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    rewards: List[float] = field(default_factory=list)
    total_reward: float = 0.0

    def append(self, state: State, action: Action, reward: float) -> None:
        """Append a state-action-reward tuple to the episode.

        Args:
            state: The state
            action: The action taken
            reward: The reward received
        """
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.total_reward += reward

    @property
    def state_action_pairs(self) -> List[Tuple[State, Action, float]]:
        """Get list of (state, action, reward) tuples.

        Returns:
            List of state-action-reward tuples
        """
        return list(zip(self.states, self.actions, self.rewards))

    def clear(self) -> None:
        """Clear all data from the episode."""
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.total_reward = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "states": [state.to_dict() for state in self.states],
            "actions": [action.name.lower() for action in self.actions],
            "rewards": self.rewards,
            "total_reward": self.total_reward,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Episode":
        """Create from dictionary."""
        episode = cls()
        for i, state_data in enumerate(data["states"]):
            state = State.from_dict(state_data)
            action = Action(data["actions"][i])
            reward = data["rewards"][i]
            episode.append(state, action, reward)
        episode.total_reward = data["total_reward"]
        return episode


class StateValueEstimator:
    """State-action value estimator for Monte Carlo learning."""

    def __init__(self):
        """Initialize estimator."""
        self.N: Dict[State, Dict[Action, int]] = {}
        self.Q: Dict[State, Dict[Action, float]] = {}

    def update(self, state: State, action: Action, reward: float) -> None:
        """Update state-action value estimate.

        Args:
            state: The state
            action: The action taken
            reward: The reward received
        """
        if state not in self.N:
            self.N[state] = {}
            self.Q[state] = {}

        if action not in self.N[state]:
            self.N[state][action] = 0
            self.Q[state][action] = 0.0

        self.N[state][action] += 1
        n = self.N[state][action]
        self.Q[state][action] += (reward - self.Q[state][action]) / n

    def get_action_value(self, state: State, action: Action) -> float:
        """Get action value for state-action pair.

        Args:
            state: The state
            action: The action

        Returns:
            Action value estimate
        """
        if state in self.Q and action in self.Q[state]:
            return self.Q[state][action]
        return 0.0

    def get_best_action(
        self,
        state: State,
        available_actions: List[Action],
    ) -> Action:
        """Get best action for state.

        Args:
            state: The state
            available_actions: List of available actions

        Returns:
            Best action
        """
        best_action = available_actions[0]
        best_value = self.get_action_value(state, best_action)

        for action in available_actions[1:]:
            value = self.get_action_value(state, action)
            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    def get_stats(self) -> dict:
        """Get estimator statistics.

        Returns:
            Dictionary of statistics
        """
        total_states = len(self.N)
        total_state_action_pairs = sum(len(actions) for actions in self.N.values())

        return {
            "total_states": total_states,
            "total_state_action_pairs": total_state_action_pairs,
        }


class EpsilonGreedyPolicy:
    """Epsilon-greedy policy for action selection."""

    def __init__(
        self,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        """Initialize policy.

        Args:
            epsilon: Initial exploration rate
            epsilon_decay: Decay rate for epsilon
            epsilon_min: Minimum epsilon value
        """
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = epsilon_min

    def get_action(
        self,
        available_actions: List[Action],
        best_action: Action,
        state: State,
    ) -> Action:
        """Select action using epsilon-greedy policy.

        Args:
            available_actions: List of available actions
            best_action: Best action according to current policy
            state: Current state

        Returns:
            Selected action
        """
        import random
        if random.random() < self.epsilon:
            return random.choice(available_actions)
        return best_action

    def decay(self) -> None:
        """Decay epsilon."""
        self.epsilon = max(self.epsilon * self.epsilon_decay, self.min_epsilon)

    def set_epsilon(self, epsilon: float) -> None:
        """Set epsilon value.

        Args:
            epsilon: New epsilon value
        """
        self.epsilon = max(epsilon, self.epsilon_min)


class MonteCarloTrainer:
    """Monte Carlo trainer for blackjack strategy."""

    def __init__(
        self,
        seed: Optional[int] = None,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        """Initialize trainer.

        Args:
            seed: Random seed for reproducibility
            epsilon: Initial exploration rate
            epsilon_decay: Decay rate for epsilon
            epsilon_min: Minimum epsilon value
        """
        self._rng = random.Random(seed)
        self.estimator = StateValueEstimator()
        self.policy = EpsilonGreedyPolicy(
            epsilon=epsilon,
            epsilon_decay=epsilon_decay,
            epsilon_min=epsilon_min,
        )
        self._total_episodes: int = 0
        self._game: Optional[BlackjackGame] = None
        # Initialize game instance for tests
        self._game = BlackjackGame(
            num_decks=6,
            dealer_stands_soft_17=True,
        )

    @property
    def game(self) -> Optional[BlackjackGame]:
        """Get current game instance."""
        return self._game

    @property
    def epsilon(self) -> float:
        """Get current epsilon value."""
        return self.policy.epsilon

    @property
    def total_episodes(self) -> int:
        """Get total episodes trained."""
        return self._total_episodes

    @total_episodes.setter
    def total_episodes(self, value: int) -> None:
        """Set total episodes."""
        self._total_episodes = value

    def get_available_actions(self, state: State) -> List[Action]:
        """Get available actions for state.

        Args:
            state: Current state

        Returns:
            List of available actions
        """
        actions = [Action.HIT, Action.STAND]

        if state.can_double:
            actions.append(Action.DOUBLE)

        if state.can_surrender:
            actions.append(Action.SURRENDER)

        if state.can_split:
            actions.append(Action.SPLIT)

        return actions

    def get_best_action(self, state: State) -> Action:
        """Get best action for state.

        Args:
            state: Current state

        Returns:
            Best action
        """
        available_actions = self.get_available_actions(state)
        return self.estimator.get_best_action(state, available_actions)

    def get_policy(self, state: State) -> Action:
        """Get policy action for state.

        Args:
            state: Current state

        Returns:
            Selected action
        """
        available_actions = self.get_available_actions(state)
        best_action = self.estimator.get_best_action(state, available_actions)
        return self.policy.get_action(available_actions, best_action, state)

    def train_episode(self) -> Tuple[Episode, float]:
        """Train on a single episode.

        Returns:
            Tuple of (episode, total reward)
        """
        self._game = BlackjackGame(
            num_decks=6,
            dealer_stands_soft_17=True,
        )

        episode = Episode()
        total_reward = 0.0

        # Deal initial cards
        initial_result = self._game.deal_initial_cards()
        total_reward += initial_result.net_result

        if initial_result.outcome != BlackjackResult.PUSH:
            return episode, total_reward

        # Create initial state
        player_hand = self._game.player_hand
        dealer_upcard = self._game.dealer_upcard

        state = State(
            player_total=player_hand.total,
            player_hand_type="soft" if player_hand.is_soft else "hard",
            dealer_upcard=dealer_upcard,
            can_double=player_hand.can_double,
            can_split=player_hand.can_split,
            can_surrender=True,
        )

        # Play episode
        while self._game.status == GameStatus.PLAYER_TURN:
            available_actions = self.get_available_actions(state)
            best_action = self.estimator.get_best_action(state, available_actions)
            action = self.policy.get_action(available_actions, best_action, state)

            # Execute action
            if action == Action.HIT:
                self._game.player_hit()
            elif action == Action.STAND:
                self._game.player_stand()
            elif action == Action.DOUBLE:
                self._game.player_double()
            elif action == Action.SURRENDER:
                self._game.player_surrender()
            else:
                raise ValueError(f"Unknown action: {action}")

            # Get result from game
            result = self._game.get_result()
            if result:
                total_reward += result.net_result

            # Record state-action-reward
            episode.append(state, action, result.net_result)

            # Check if episode ended
            if self._game.status in [
                GameStatus.WIN,
                GameStatus.LOSS,
                GameStatus.PUSH,
                GameStatus.BUST,
                GameStatus.BLACKJACK,
                GameStatus.FOLD,
            ]:
                break

            # Update state
            player_hand = self._game.player_hand
            dealer_upcard = self._game.dealer_upcard

            state = State(
                player_total=player_hand.total,
                player_hand_type="soft" if player_hand.is_soft else "hard",
                dealer_upcard=dealer_upcard,
                can_double=player_hand.can_split,
                can_split=player_hand.can_split,
                can_surrender=False,
            )

        # Update estimator with episode returns
        self._update_estimator(episode, total_reward)

        return episode, total_reward

    def _update_estimator(self, episode: Episode, total_reward: float) -> None:
        """Update estimator with episode returns.

        Args:
            episode: Episode to process
            total_reward: Total reward from episode
        """
        seen_states: Dict[State, float] = {}

        for state, action, reward in episode.state_action_pairs:
            if state not in seen_states:
                seen_states[state] = 0.0
            seen_states[state] += reward

        for state, action, reward in episode.state_action_pairs:
            if state in seen_states:
                self.estimator.update(state, action, seen_states[state])

    def train(
        self,
        num_episodes: int,
        verbose: bool = True,
    ) -> dict:
        """Train for specified number of episodes.

        Args:
            num_episodes: Number of episodes to train
            verbose: Whether to print progress

        Returns:
            Dictionary of training statistics
        """
        initial_epsilon = self.epsilon
        total_reward = 0.0

        for i in range(num_episodes):
            episode, reward = self.train_episode()
            self.total_episodes += 1
            total_reward += reward

            if verbose and (i + 1) % 100 == 0:
                print(f"Episode {i + 1}/{num_episodes}, "
                      f"Reward: {reward:.2f}, "
                      f"Epsilon: {self.epsilon:.4f}")

            self.policy.decay()

        stats = self.estimator.get_stats()
        stats["total_episodes"] = self.total_episodes
        stats["initial_epsilon"] = initial_epsilon
        stats["final_epsilon"] = self.epsilon
        stats["states_learned"] = stats["total_states"]
        stats["avg_reward"] = total_reward / num_episodes

        return stats

    def evaluate(self, num_episodes: int = 100) -> dict:
        """Evaluate current policy.

        Args:
            num_episodes: Number of episodes to evaluate

        Returns:
            Dictionary of evaluation statistics
        """
        total_reward = 0.0
        wins = 0
        losses = 0
        pushes = 0

        for _ in range(num_episodes):
            episode, reward = self.train_episode()
            total_reward += reward

            # Count outcomes
            if reward > 0:
                wins += 1
            elif reward < 0:
                losses += 1
            else:
                pushes += 1

        return {
            "total_episodes": num_episodes,
            "total_reward": total_reward,
            "avg_reward": total_reward / num_episodes,
            "win_rate": wins / num_episodes,
            "loss_rate": losses / num_episodes,
            "push_rate": pushes / num_episodes,
        }

    def get_action_values(self, state: State) -> Dict[Action, float]:
        """Get action values for state.

        Args:
            state: State to get values for

        Returns:
            Dictionary of action values
        """
        available_actions = self.get_available_actions(state)
        return {
            action: self.estimator.get_action_value(state, action)
            for action in available_actions
        }

    def get_stats(self) -> dict:
        """Get trainer statistics.

        Returns:
            Dictionary of statistics
        """
        estimator_stats = self.estimator.get_stats()
        return {
            **estimator_stats,
            "total_episodes": self.total_episodes,
            "current_epsilon": self.epsilon,
            "avg_reward": 0.0,
        }

    def save(self, filepath: str) -> None:
        """Save trainer to file.

        Args:
            filepath: Path to save file
        """
        data = {
            "total_episodes": self.total_episodes,
            "epsilon": self.epsilon,
            "epsilon_decay": self.policy.epsilon_decay,
            "epsilon_min": self.policy.epsilon_min,
            "policy": {
                "epsilon": self.epsilon,
                "epsilon_decay": self.policy.epsilon_decay,
                "epsilon_min": self.policy.min_epsilon,
            },
            "estimator": {
                "N": {
                    state.to_dict(): {
                        action.value: count
                        for action, count in actions.items()
                    }
                    for state, actions in self.estimator.N.items()
                },
                "Q": {
                    state.to_dict(): {
                        action.value: value
                        for action, value in actions.items()
                    }
                    for state, actions in self.estimator.Q.items()
                },
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "MonteCarloTrainer":
        """Load trainer from file.

        Args:
            filepath: Path to load file

        Returns:
            Loaded MonteCarloTrainer
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        trainer = cls(
            epsilon=data["epsilon"],
            epsilon_decay=data["epsilon_decay"],
            epsilon_min=data["epsilon_min"],
        )
        trainer.total_episodes = data["total_episodes"]

        # Load estimator
        for state_dict, actions in data["estimator"]["N"].items():
            state = State.from_dict(state_dict)
            trainer.estimator.N[state] = {}
            trainer.estimator.Q[state] = {}

            for action_value, count in actions.items():
                action = Action(action_value)
                trainer.estimator.N[state][action] = count
                trainer.estimator.Q[state][action] = data["estimator"]["Q"][state_dict][action_value]

        return trainer
