"""Training and evaluation utilities for the GridWorld environment."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from gameagent.agent import BaseAgent, GreedyAgent, RandomAgent
from gameagent.agent.q_learning import QLearningAgent
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import Action, GridConfig


@dataclass
class TrainingConfig:
    """Configuration for training."""
    num_episodes: int = 1000
    grid_width: int = 5
    grid_height: int = 5
    goal_position: tuple[int, int] = (4, 4)
    learning_rate: float = 0.2
    discount_factor: float = 0.95
    epsilon_start: float = 1.0
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    seed: int = 42
    save_path: str = "trained_agent.json"
    render_every: int = 100  # Render every N episodes


@dataclass
class TrainingResult:
    """Results from training."""
    rewards: list[float] = field(default_factory=list)
    steps: list[int] = field(default_factory=list)
    epsilon_history: list[float] = field(default_factory=list)
    final_epsilon: float = 0.0


class GridWorldTrainer:
    """Trains and evaluates agents on the GridWorld environment."""

    def __init__(self, training_config: TrainingConfig):
        self.config = training_config
        self.agent: Optional[QLearningAgent] = None
        self.result: Optional[TrainingResult] = None

    def create_agent(self) -> QLearningAgent:
        """Create a new Q-learning agent."""
        return QLearningAgent(
            learning_rate=self.config.learning_rate,
            discount_factor=self.config.discount_factor,
            epsilon=self.config.epsilon_start,
            epsilon_decay=self.config.epsilon_decay,
            epsilon_min=self.config.epsilon_min,
        )

    def create_env(self) -> GridWorld:
        """Create a new GridWorld environment."""
        config = GridConfig(
            width=self.config.grid_width,
            height=self.config.grid_height,
            goal_position=self.config.goal_position,
            seed=self.config.seed,
        )
        return GridWorld(config=config)

    def train_episode(self, agent: QLearningAgent, env: GridWorld) -> tuple[float, int]:
        """Run one training episode.

        Returns:
            Total reward and number of steps taken.
        """
        obs, _ = env.reset()
        agent.set_training_mode(True)
        total_reward = 0.0
        steps = 0

        while True:
            state_key = agent._get_state_key(obs)
            action = agent.act(obs)
            result = env.step(action)
            next_state_key = agent._get_state_key(result.observation)
            agent.update(state_key, action, result.reward, next_state_key, result.terminated)
            total_reward += result.reward
            steps += 1

            if result.terminated or result.truncated:
                break
            obs = result.observation

        return total_reward, steps

    def evaluate_agent(self, agent: BaseAgent, env: GridWorld, num_episodes: int = 100) -> dict[str, float]:
        """Evaluate an agent over multiple episodes.

        Returns:
            Dictionary with mean_reward, mean_steps, success_rate.
        """
        rewards = []
        steps_list = []
        successes = 0

        for _ in range(num_episodes):
            obs, _ = env.reset()
            agent.set_training_mode(False)
            total_reward = 0.0
            steps = 0

            while True:
                action = agent.act(obs)
                result = env.step(action)
                total_reward += result.reward
                steps += 1

                if result.terminated or result.truncated:
                    break
                obs = result.observation

            rewards.append(total_reward)
            steps_list.append(steps)
            if result.terminated:
                successes += 1

        return {
            "mean_reward": float(np.mean(rewards)),
            "mean_steps": float(np.mean(steps_list)),
            "success_rate": successes / num_episodes,
            "std_reward": float(np.std(rewards)),
        }

    def train(self) -> TrainingResult:
        """Run the full training loop.

        Returns:
            TrainingResult with training history.
        """
        self.agent = self.create_agent()
        self.result = TrainingResult()
        env = self.create_env()

        print(f"Starting training: {self.config.num_episodes} episodes")
        print(f"Grid: {self.config.grid_width}x{self.config.grid_height}, Goal: {self.config.goal_position}")
        print("-" * 50)

        for episode in range(self.config.num_episodes):
            reward, steps = self.train_episode(self.agent, env)
            self.result.rewards.append(reward)
            self.result.steps.append(steps)
            self.result.epsilon_history.append(self.agent.epsilon)

            # Decay epsilon
            self.agent.decay_epsilon()

            # Print progress
            if (episode + 1) % 100 == 0:
                recent_rewards = self.result.rewards[-100:]
                recent_steps = self.result.steps[-100:]
                print(
                    f"Episode {episode + 1}/{self.config.num_episodes} | "
                    f"Reward: {np.mean(recent_rewards):.2f} | "
                    f"Steps: {np.mean(recent_steps):.1f} | "
                    f"Epsilon: {self.agent.epsilon:.3f}"
                )

            # Render occasionally
            if (episode + 1) % self.config.render_every == 0:
                print(f"\n--- Episode {episode + 1} ---")
                print(env.render())

        self.result.final_epsilon = self.agent.epsilon
        print("-" * 50)
        print(f"Training complete! Final epsilon: {self.result.final_epsilon:.3f}")

        return self.result

    def save_agent(self, path: Optional[str] = None) -> str:
        """Save the trained agent's Q-table to a JSON file."""
        if self.agent is None:
            raise ValueError("No agent to save. Run train() first.")

        save_path = path or self.config.save_path
        q_data = {}
        for state, actions in self.agent.q_table.items():
            q_data[str(state)] = {str(action): value for action, value in actions.items()}

        with open(save_path, "w") as f:
            json.dump({
                "q_table": q_data,
                "learning_rate": self.agent.learning_rate,
                "discount_factor": self.agent.discount_factor,
                "epsilon": self.agent.epsilon,
            }, f, indent=2)

        print(f"Agent saved to {save_path}")
        return save_path

    def load_agent(self, path: str) -> QLearningAgent:
        """Load a trained agent from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        agent = QLearningAgent(
            learning_rate=data["learning_rate"],
            discount_factor=data["discount_factor"],
            epsilon=data["epsilon"],
        )

        for state_str, actions in data["q_table"].items():
            state = eval(state_str)
            for action_str, value in actions.items():
                action = Action(int(action_str))
                agent.q_table[state][action] = value

        print(f"Agent loaded from {path}")
        return agent

    def run_benchmark(self) -> dict[str, dict[str, float]]:
        """Run a benchmark comparing different agents.

        Returns:
            Dictionary mapping agent names to their evaluation results.
        """
        env = self.create_env()
        results = {}

        # Random Agent
        print("\n--- Benchmarking Random Agent ---")
        random_agent = RandomAgent()
        results["RandomAgent"] = self.evaluate_agent(random_agent, env)
        print(f"  Mean Reward: {results['RandomAgent']['mean_reward']:.2f}")
        print(f"  Success Rate: {results['RandomAgent']['success_rate']:.2%}")

        # Greedy Agent
        print("\n--- Benchmarking Greedy Agent ---")
        greedy_agent = GreedyAgent()
        results["GreedyAgent"] = self.evaluate_agent(greedy_agent, env)
        print(f"  Mean Reward: {results['GreedyAgent']['mean_reward']:.2f}")
        print(f"  Success Rate: {results['GreedyAgent']['success_rate']:.2%}")

        # Trained Q-Learning Agent
        if self.agent is not None:
            print("\n--- Benchmarking Trained Q-Learning Agent ---")
            results["QLearningAgent"] = self.evaluate_agent(self.agent, env)
            print(f"  Mean Reward: {results['QLearningAgent']['mean_reward']:.2f}")
            print(f"  Success Rate: {results['QLearningAgent']['success_rate']:.2%}")
        else:
            print("\n--- No trained agent to benchmark ---")

        return results


def main():
    """Main training script."""
    # Training configuration
    training_config = TrainingConfig(
        num_episodes=1000,
        grid_width=5,
        grid_height=5,
        goal_position=(4, 4),
        learning_rate=0.2,
        discount_factor=0.95,
        epsilon_start=1.0,
        epsilon_decay=0.995,
        epsilon_min=0.01,
        seed=42,
        save_path="trained_agent.json",
        render_every=200,
    )

    # Create trainer and run training
    trainer = GridWorldTrainer(training_config)
    result = trainer.train()

    # Save the trained agent
    trainer.save_agent()

    # Run benchmark
    benchmark_results = trainer.run_benchmark()

    # Print summary
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    for agent_name, metrics in benchmark_results.items():
        print(f"\n{agent_name}:")
        print(f"  Mean Reward: {metrics['mean_reward']:.2f} ± {metrics['std_reward']:.2f}")
        print(f"  Mean Steps: {metrics['mean_steps']:.1f}")
        print(f"  Success Rate: {metrics['success_rate']:.2%}")


if __name__ == "__main__":
    main()
