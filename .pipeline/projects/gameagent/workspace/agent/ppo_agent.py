"""PPO (Proximal Policy Optimization) agent for the GridWorld environment."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from gameagent.agent.base import BaseAgent
from gameagent.env.types import Action, Observation


@dataclass
class PPOConfig:
    """Configuration for PPO agent."""
    learning_rate: float = 0.001
    discount_factor: float = 0.95
    gamma: float = 0.99
    epsilon_clip: float = 0.2
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 0.5
    num_epochs: int = 10
    batch_size: int = 32
    hidden_layers: tuple = (64, 32)
    seed: Optional[int] = None


class PPONetwork:
    """Simple feedforward neural network for PPO (actor-critic)."""

    def __init__(self, state_dim: int, action_dim: int,
                 hidden_layers: tuple = (64, 32), seed: Optional[int] = None):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_layers = hidden_layers
        self.rng = random.Random(seed)

        self.actor_weights = []
        self.critic_weights = []
        layer_sizes = [state_dim] + list(hidden_layers) + [action_dim]

        # Actor network (policy)
        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            scale = np.sqrt(2.0 / (fan_in + fan_out))
            w = self.rng.gauss(0, scale) * np.ones((fan_in, fan_out))
            b = np.zeros(fan_out)
            self.actor_weights.append((w, b))

        # Critic network (value function)
        critic_layer_sizes = [state_dim] + list(hidden_layers) + [1]
        for i in range(len(critic_layer_sizes) - 1):
            fan_in = critic_layer_sizes[i]
            fan_out = critic_layer_sizes[i + 1]
            scale = np.sqrt(2.0 / (fan_in + fan_out))
            w = self.rng.gauss(0, scale) * np.ones((fan_in, fan_out))
            b = np.zeros(fan_out)
            self.critic_weights.append((w, b))

    def forward_actor(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through actor network."""
        if x.ndim == 1:
            x = x.reshape(1, -1)
            single = True
        else:
            single = False

        for w, b in self.actor_weights[:-1]:
            x = x @ w + b
            x = np.maximum(0, x)

        w, b = self.actor_weights[-1]
        logits = x @ w + b

        if single:
            return logits[0]
        return logits

    def forward_critic(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through critic network."""
        if x.ndim == 1:
            x = x.reshape(1, -1)
            single = True
        else:
            single = False

        for w, b in self.critic_weights[:-1]:
            x = x @ w + b
            x = np.maximum(0, x)

        w, b = self.critic_weights[-1]
        value = x @ w + b

        if single:
            return value[0]
        return value

    def get_action_probs(self, state: np.ndarray) -> np.ndarray:
        """Get action probabilities from actor network."""
        logits = self.forward_actor(state)
        # Softmax for action probabilities
        exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
        return probs

    def get_value(self, state: np.ndarray) -> np.ndarray:
        """Get value estimate from critic network."""
        return self.forward_critic(state)

    def copy_from(self, other: 'PPONetwork') -> None:
        """Copy weights from another network."""
        for (w1, b1), (w2, b2) in zip(self.actor_weights, other.actor_weights):
            w1[:] = w2.copy()
            b1[:] = b2.copy()
        for (w1, b1), (w2, b2) in zip(self.critic_weights, other.critic_weights):
            w1[:] = w2.copy()
            b1[:] = b2.copy()


class PPOAgent(BaseAgent):
    """Proximal Policy Optimization agent."""

    def __init__(self, config: Optional[PPOConfig] = None):
        """Initialize the PPO agent."""
        super().__init__()
        self.config = config or PPOConfig()
        self.rng = random.Random(self.config.seed)

        self.state_dim = 4
        self.action_dim = len(Action)

        self.network = PPONetwork(
            state_dim=self.state_dim,
            action_dim=self.action_dim,
            hidden_layers=self.config.hidden_layers,
            seed=self.config.seed
        )

        self.training_mode = False
        self.total_steps = 0

        # Storage for PPO training
        self.states: list[np.ndarray] = []
        self.actions: list[int] = []
        self.rewards: list[float] = []
        self.dones: list[bool] = []
        self.values: list[float] = []

    def _encode_state(self, observation: Observation) -> np.ndarray:
        """Encode observation as a state vector."""
        state = np.array([
            observation.agent_position[0],
            observation.agent_position[1],
            observation.goal_position[0],
            observation.goal_position[1],
        ], dtype=np.float32)
        return state

    def act(self, observation: Any) -> Action:
        """Select an action using the policy."""
        state = self._encode_state(observation)

        probs = self.network.get_action_probs(state)
        action_idx = self.rng.choices(range(self.action_dim), weights=probs, k=1)[0]
        return Action(action_idx)

    def store_transition(self, state: np.ndarray, action: int, reward: float,
                         value: float, done: bool) -> None:
        """Store a transition for PPO training."""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.dones.append(done)
        self.values.append(value)

    def compute_returns(self, next_value: float) -> np.ndarray:
        """Compute GAE (Generalized Advantage Estimation) returns."""
        returns = []
        gae = 0
        gamma = self.config.gamma
        lam = 0.95

        for t in reversed(range(len(self.rewards))):
            if t == len(self.rewards) - 1:
                next_value = next_value
                delta = self.rewards[t] + gamma * next_value - self.values[t]
            else:
                delta = self.rewards[t] + gamma * self.values[t + 1] - self.values[t]

            gae = delta + gamma * lam * gae
            returns.append(gae + self.values[t])

        returns = np.array(returns[::-1])
        advantages = returns - np.array(self.values)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return returns, advantages

    def train(self, num_epochs: Optional[int] = None) -> dict:
        """Train the PPO agent on stored transitions."""
        if len(self.states) == 0:
            return {"loss": 0.0, "policy_loss": 0.0, "value_loss": 0.0}

        num_epochs = num_epochs or self.config.num_epochs
        batch_size = self.config.batch_size
        gamma = self.config.gamma

        returns, advantages = self.compute_returns(0.0)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        total_policy_loss = 0.0
        total_value_loss = 0.0

        for epoch in range(num_epochs):
            # Shuffle data
            indices = np.random.permutation(len(self.states))

            for start in range(0, len(self.states), batch_size):
                end = start + batch_size
                batch_indices = indices[start:end]

                batch_states = np.array([self.states[i] for i in batch_indices])
                batch_actions = np.array(self.actions[start:end])
                batch_returns = np.array(returns[start:end])
                batch_advantages = np.array(advantages[start:end])
                batch_old_values = np.array(self.values[start:end])

                # Get old action probabilities
                old_probs = self.network.get_action_probs(batch_states)
                old_log_probs = np.log(old_probs[np.arange(len(batch_actions)), batch_actions] + 1e-8)

                # Get new action probabilities
                new_probs = self.network.get_action_probs(batch_states)
                new_log_probs = np.log(new_probs[np.arange(len(batch_actions)), batch_actions] + 1e-8)

                # Ratio for clipping
                ratio = np.exp(new_log_probs - old_log_probs)

                # Surrogate loss with clipping
                surr1 = ratio * batch_advantages
                surr2 = np.clip(ratio, 1 - self.config.epsilon_clip, 1 + self.config.epsilon_clip) * batch_advantages
                policy_loss = -np.mean(np.minimum(surr1, surr2))

                # Value loss
                new_values = self.network.get_value(batch_states)
                value_loss = 0.5 * np.mean((new_values - batch_returns) ** 2)

                # Total loss
                total_loss = policy_loss + \
                             self.config.value_loss_coef * value_loss - \
                             self.config.entropy_coef * np.mean(-new_probs * np.log(new_probs + 1e-8))

                # Simple gradient update (gradient descent)
                for i in range(len(self.network.actor_weights)):
                    w, b = self.network.actor_weights[i]
                    if i == len(self.network.actor_weights) - 1:
                        grad = -policy_loss / len(batch_actions)
                        w[:, batch_actions] += grad * self.config.learning_rate * batch_states
                        b += grad * self.config.learning_rate

                for i in range(len(self.network.critic_weights)):
                    w, b = self.network.critic_weights[i]
                    if i == len(self.network.critic_weights) - 1:
                        grad = -value_loss / len(batch_actions)
                        w += grad * self.config.learning_rate * batch_states.T
                        b += grad * self.config.learning_rate

                total_policy_loss += policy_loss
                total_value_loss += value_loss

        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.dones.clear()
        self.values.clear()

        return {
            "loss": total_policy_loss + total_value_loss,
            "policy_loss": total_policy_loss,
            "value_loss": total_value_loss,
        }

    def update(self, state: np.ndarray, action: int, reward: float,
               next_state: np.ndarray, done: bool) -> float:
        """Update the agent with a single transition."""
        value = self.network.get_value(state)
        self.store_transition(state, action, reward, float(value), done)
        self.total_steps += 1
        return float(value)

    def decay_learning_rate(self, decay_rate: float = 0.99) -> None:
        """Decay the learning rate."""
        self.config.learning_rate *= decay_rate

    def set_training_mode(self, training: bool) -> None:
        """Set the agent's training mode."""
        self.training_mode = training

    def reset(self) -> None:
        """Reset the agent's internal state."""
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.dones.clear()
        self.values.clear()
        self.total_steps = 0
