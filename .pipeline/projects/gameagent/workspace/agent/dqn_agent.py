"""DQN (Deep Q-Network) agent for the GridWorld environment."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from gameagent.agent.base import BaseAgent
from gameagent.env.types import Action, Observation


@dataclass
class DQNConfig:
    """Configuration for DQN agent."""
    learning_rate: float = 0.001
    discount_factor: float = 0.95
    epsilon_start: float = 1.0
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    batch_size: int = 32
    replay_buffer_size: int = 10000
    target_update_frequency: int = 100
    hidden_layers: tuple = (64, 32)
    seed: Optional[int] = None


class ReplayBuffer:
    """Experience replay buffer for DQN training."""

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state: np.ndarray, action: int, reward: float,
             next_state: np.ndarray, done: bool) -> None:
        """Store a transition in the buffer."""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> list[tuple]:
        """Sample a random batch of transitions."""
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self) -> int:
        """Return the number of transitions in the buffer."""
        return len(self.buffer)


class DQNNetwork:
    """Simple feedforward neural network for DQN."""

    def __init__(self, state_dim: int, action_dim: int,
                 hidden_layers: tuple = (64, 32), seed: Optional[int] = None):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_layers = hidden_layers
        self.rng = random.Random(seed)

        self.weights = []
        layer_sizes = [state_dim] + list(hidden_layers) + [action_dim]

        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            scale = np.sqrt(2.0 / (fan_in + fan_out))
            w = self.rng.gauss(0, scale) * np.ones((fan_in, fan_out))
            b = np.zeros(fan_out)
            self.weights.append((w, b))

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through the network."""
        if x.ndim == 1:
            x = x.reshape(1, -1)
            single = True
        else:
            single = False

        for w, b in self.weights[:-1]:
            x = x @ w + b
            x = np.maximum(0, x)

        w, b = self.weights[-1]
        x = x @ w + b

        if single:
            return x[0]
        return x

    def get_q_values(self, state: np.ndarray) -> np.ndarray:
        """Get Q-values for a state."""
        return self.forward(state)

    def copy_from(self, other: 'DQNNetwork') -> None:
        """Copy weights from another network."""
        for (w1, b1), (w2, b2) in zip(self.weights, other.weights):
            w1[:] = w2.copy()
            b1[:] = b2.copy()


class DQNAgent(BaseAgent):
    """Deep Q-Network agent with experience replay and target network."""

    def __init__(self, config: Optional[DQNConfig] = None):
        """Initialize the DQN agent."""
        super().__init__()
        self.config = config or DQNConfig()
        self.rng = random.Random(self.config.seed)

        self.state_dim = 4
        self.action_dim = len(Action)

        self.network = DQNNetwork(
            state_dim=self.state_dim,
            action_dim=self.action_dim,
            hidden_layers=self.config.hidden_layers,
            seed=self.config.seed
        )
        self.target_network = DQNNetwork(
            state_dim=self.state_dim,
            action_dim=self.action_dim,
            hidden_layers=self.config.hidden_layers,
            seed=self.config.seed
        )
        self.target_network.copy_from(self.network)

        self.replay_buffer = ReplayBuffer(capacity=self.config.replay_buffer_size)
        self.epsilon = self.config.epsilon_start
        self.training_mode = False
        self.total_steps = 0

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
        """Select an action using epsilon-greedy policy."""
        state = self._encode_state(observation)

        if self.training_mode and self.rng.random() < self.epsilon:
            return self.rng.choice(list(Action))

        q_values = self.network.get_q_values(state)
        action_idx = int(np.argmax(q_values))
        return Action(action_idx)

    def update(self, state: np.ndarray, action: int, reward: float,
               next_state: np.ndarray, done: bool) -> float:
        """Update the network using a single transition."""
        q_values = self.network.get_q_values(state)
        current_q = q_values[action]

        if done:
            target = reward
        else:
            next_q_values = self.target_network.get_q_values(next_state)
            max_next_q = np.max(next_q_values) if np.any(np.isfinite(next_q_values)) else 0
            target = reward + self.config.discount_factor * max_next_q

        learning_rate = self.config.learning_rate
        for i in range(len(self.network.weights)):
            w, b = self.network.weights[i]
            if i == len(self.network.weights) - 1:
                grad = learning_rate * (target - current_q)
                w[:, action] += grad * state
                b[action] += grad

        self.replay_buffer.push(state, action, reward, next_state, done)

        self.total_steps += 1
        if self.total_steps % self.config.target_update_frequency == 0:
            self.target_network.copy_from(self.network)

        return current_q

    def train_batch(self) -> float:
        """Train on a random batch from the replay buffer."""
        if len(self.replay_buffer) < self.config.batch_size:
            return 0.0

        batch = self.replay_buffer.sample(self.config.batch_size)
        states, actions, rewards, next_states, dones = [], [], [], [], []

        for state, action, reward, next_state, done in batch:
            states.append(state)
            actions.append(action)
            rewards.append(reward)
            next_states.append(next_state)
            dones.append(done)

        states = np.array(states, dtype=np.float32)
        actions = np.array(actions)
        rewards = np.array(rewards)
        next_states = np.array(next_states, dtype=np.float32)
        dones = np.array(dones)

        next_q_values = self.target_network.get_q_values(next_states)
        max_next_q = np.max(next_q_values, axis=1)
        targets = rewards + self.config.discount_factor * max_next_q * (1 - dones)

        current_q_values = self.network.get_q_values(states)
        current_q = current_q_values[np.arange(len(actions)), actions]

        loss = np.mean((current_q - targets) ** 2)

        for i in range(len(self.network.weights)):
            w, b = self.network.weights[i]
            if i == len(self.network.weights) - 1:
                grad = -2 * (targets - current_q) / len(actions)
                for j in range(len(actions)):
                    w[:, actions[j]] += grad[j] * self.config.learning_rate * states[j]
                b += grad * self.config.learning_rate

        self.total_steps += 1
        if self.total_steps % self.config.target_update_frequency == 0:
            self.target_network.copy_from(self.network)

        return float(loss)

    def decay_epsilon(self) -> None:
        """Decay the exploration rate."""
        self.epsilon = max(self.epsilon * self.config.epsilon_decay, self.config.epsilon_min)

    def set_training_mode(self, training: bool) -> None:
        """Set the agent's training mode."""
        self.training_mode = training

    def reset(self) -> None:
        """Reset the agent's internal state."""
        self.replay_buffer = ReplayBuffer(capacity=self.config.replay_buffer_size)
        self.epsilon = self.config.epsilon_start
        self.total_steps = 0
        self.target_network.copy_from(self.network)
