"""Training script for the dropshipping RL environment."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Dict, List, Tuple

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

from rl_dropshipping.src.config.settings import load_settings


class PolicyNetwork(nn.Module):
    """Simple policy network for dropshipping."""

    def __init__(self, n_actions: int, hidden_dim: int = 128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(17, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class DropshippingTrainer:
    """Trainer for the dropshipping environment using PPO."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load environment
        self.env = gym.make(
            "Dropshipping-v0",
            config=config,
        )

        # Policy network
        self.policy = PolicyNetwork(
            n_actions=self.env.action_space.n,
            hidden_dim=128,
        ).to(self.device)

        # Optimizer
        self.optimizer = optim.Adam(self.policy.parameters(), lr=config["training"]["learning_rate"])

        # Training parameters
        self.n_episodes = config["training"]["n_episodes"]
        self.discount_factor = config["training"]["discount_factor"]
        self.epsilon_start = config["training"]["epsilon_start"]
        self.epsilon_end = config["training"]["epsilon_end"]
        self.epsilon_decay = config["training"]["epsilon_decay"]

        # Logging
        self.episode_rewards: List[float] = []
        self.episode_costs: List[float] = []
        self.episode_revenues: List[float] = []

    def select_action(self, observation: np.ndarray, training: bool = True) -> Tuple[int, torch.Tensor]:
        """Select an action using epsilon-greedy policy."""
        if training and np.random.rand() < self._get_epsilon():
            action = self.env.action_space.sample()
            return action, torch.tensor(0.0)

        obs_tensor = torch.FloatTensor(observation).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.policy(obs_tensor)
            probs = torch.softmax(logits, dim=-1)
            dist = Categorical(probs)
            action = dist.sample()
            return action.item(), dist.log_prob(action)

    def _get_epsilon(self) -> float:
        """Get current epsilon value."""
        return max(
            self.epsilon_end,
            self.epsilon_start * (self.epsilon_decay ** len(self.episode_rewards)),
        )

    def train_step(self, observation: np.ndarray, action: int, reward: float,
                   next_observation: np.ndarray, done: bool, log_prob: torch.Tensor) -> float:
        """Perform one training step."""
        # Compute advantage (simplified)
        with torch.no_grad():
            next_logits = self.policy(torch.FloatTensor(next_observation).unsqueeze(0).to(self.device))
            next_probs = torch.softmax(next_logits, dim=-1)
            next_dist = Categorical(next_probs)
            next_log_prob = next_dist.log_prob(torch.tensor([action]).to(self.device))
            advantage = reward + self.discount_factor * (-next_log_prob) * (1 - done)

        # Compute loss
        ratio = torch.exp(log_prob - next_log_prob)
        loss = -ratio * advantage
        loss = loss.mean()

        # Update policy
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def train(self) -> Dict[str, Any]:
        """Train the agent for n_episodes."""
        print(f"Starting training for {self.n_episodes} episodes...")
        start_time = time.time()

        for episode in range(self.n_episodes):
            observation, info = self.env.reset()
            episode_reward = 0.0
            episode_cost = 0.0
            episode_revenue = 0.0
            losses = []

            for step in range(self.env.episode_length):
                action, log_prob = self.select_action(observation, training=True)
                next_observation, reward, terminated, truncated, info = self.env.step(action)

                episode_reward += reward
                episode_cost += info.get("step_cost", 0.0)
                episode_revenue += info.get("step_revenue", 0.0)

                loss = self.train_step(
                    observation, action, reward, next_observation, terminated or truncated, log_prob
                )
                losses.append(loss)

                observation = next_observation
                if terminated or truncated:
                    break

            self.episode_rewards.append(episode_reward)
            self.episode_costs.append(episode_cost)
            self.episode_revenues.append(episode_revenue)

            # Logging
            if (episode + 1) % self.config["logging"]["log_interval"] == 0:
                avg_reward = np.mean(self.episode_rewards[-100:])
                avg_cost = np.mean(self.episode_costs[-100:])
                avg_revenue = np.mean(self.episode_revenues[-100:])
                avg_loss = np.mean(losses)

                print(f"Episode {episode + 1}/{self.n_episodes}")
                print(f"  Avg Reward (100): {avg_reward:.4f}")
                print(f"  Avg Cost: {avg_cost:.4f}")
                print(f"  Avg Revenue: {avg_revenue:.4f}")
                print(f"  Avg Loss: {avg_loss:.4f}")
                print(f"  Epsilon: {self._get_epsilon():.4f}")
                print()

        elapsed = time.time() - start_time
        print(f"Training completed in {elapsed:.2f} seconds")

        # Save results
        results = {
            "episode_rewards": self.episode_rewards,
            "episode_costs": self.episode_costs,
            "episode_revenues": self.episode_revenues,
            "final_epsilon": self._get_epsilon(),
            "training_time": elapsed,
        }

        return results

    def save_model(self, path: str):
        """Save the trained model."""
        torch.save({
            "policy_state_dict": self.policy.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
        }, path)
        print(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load a trained model."""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy.load_state_dict(checkpoint["policy_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        print(f"Model loaded from {path}")


def main():
    """Main training function."""
    config = load_settings()
    trainer = DropshippingTrainer(config)
    results = trainer.train()

    # Save results
    results_path = pathlib.Path("./results/training_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {results_path}")

    # Save model
    trainer.save_model("./results/model.pth")


if __name__ == "__main__":
    main()
