"""Benchmark runner for comparing different RL algorithms."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Callable, Optional

import numpy as np

from gameagent.agent import (
    BaseAgent,
    RandomAgent,
    GreedyAgent,
    QLearningAgent,
    DQNAgent,
    PPOAgent,
)
from gameagent.agent.dqn_agent import DQNConfig
from gameagent.agent.ppo_agent import PPOConfig
from gameagent.env.grid_world import GridWorld
from gameagent.env.multi_goal_world import MultiGoalWorld
from gameagent.env.types import GridConfig


@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking."""
    num_episodes: int = 100
    grid_width: int = 5
    grid_height: int = 5
    goal_position: tuple[int, int] = (4, 4)
    seed: int = 42
    metrics: list[str] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = ["reward", "steps", "success_rate"]


def create_agent(name: str, config: Optional[dict] = None) -> BaseAgent:
    """Create an agent instance by name."""
    config = config or {}

    if name == "RandomAgent":
        return RandomAgent()
    elif name == "GreedyAgent":
        return GreedyAgent()
    elif name == "QLearningAgent":
        return QLearningAgent()
    elif name == "DQNAgent":
        dqn_config = DQNConfig(**config)
        return DQNAgent(config=dqn_config)
    elif name == "PPOAgent":
        ppo_config = PPOConfig(**config)
        return PPOAgent(config=ppo_config)
    else:
        raise ValueError(f"Unknown agent type: {name}")


def benchmark_agent(
    agent: BaseAgent,
    env: GridWorld,
    num_episodes: int,
    metrics: list[str]
) -> dict:
    """Benchmark a single agent on the environment."""
    rewards = []
    steps = []
    successes = 0

    for episode in range(num_episodes):
        observation = env.reset()
        total_reward = 0.0
        step_count = 0

        while not env.is_done():
            action = agent.act(observation)
            observation, reward, done, _ = env.step(action)
            total_reward += reward
            step_count += 1

            if done:
                break

        rewards.append(total_reward)
        steps.append(step_count)

        if total_reward > 0:
            successes += 1

    results = {
        "mean_reward": np.mean(rewards),
        "std_reward": np.std(rewards),
        "mean_steps": np.mean(steps),
        "std_steps": np.std(steps),
        "success_rate": successes / num_episodes,
    }

    return results


def run_benchmark(
    agent_names: list[str],
    benchmark_config: BenchmarkConfig,
    output_dir: str = "output/benchmarks"
) -> dict:
    """Run benchmark for multiple agents."""
    os.makedirs(output_dir, exist_ok=True)

    results = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for agent_name in agent_names:
        print(f"Running benchmark for {agent_name}...")

        agent = create_agent(agent_name)
        env = GridWorld(
            grid_width=benchmark_config.grid_width,
            grid_height=benchmark_config.grid_height,
            goal_position=benchmark_config.goal_position,
            seed=benchmark_config.seed
        )

        agent_results = benchmark_agent(
            agent,
            env,
            benchmark_config.num_episodes,
            benchmark_config.metrics
        )

        results[agent_name] = agent_results

        # Save individual results
        output_file = os.path.join(
            output_dir,
            f"{agent_name}_{timestamp}.json"
        )
        with open(output_file, "w") as f:
            json.dump({
                "agent": agent_name,
                "config": asdict(benchmark_config),
                "results": agent_results,
                "timestamp": timestamp,
            }, f, indent=2)

        print(f"  Mean reward: {agent_results['mean_reward']:.2f}")
        print(f"  Success rate: {agent_results['success_rate']:.2%}")

    # Save combined results
    combined_file = os.path.join(output_dir, f"combined_{timestamp}.json")
    with open(combined_file, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "config": asdict(benchmark_config),
            "results": results,
        }, f, indent=2)

    return results


def main():
    """Main entry point for benchmark runner."""
    parser = argparse.ArgumentParser(description="Run RL agent benchmarks")
    parser.add_argument(
        "--agents",
        type=str,
        nargs="+",
        default=["RandomAgent", "GreedyAgent", "QLearningAgent", "DQNAgent", "PPOAgent"],
        help="Agent types to benchmark"
    )
    parser.add_argument(
        "--num-episodes",
        type=int,
        default=100,
        help="Number of episodes per agent"
    )
    parser.add_argument(
        "--grid-width",
        type=int,
        default=5,
        help="Grid width"
    )
    parser.add_argument(
        "--grid-height",
        type=int,
        default=5,
        help="Grid height"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/benchmarks",
        help="Output directory for results"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()

    benchmark_config = BenchmarkConfig(
        num_episodes=args.num_episodes,
        grid_width=args.grid_width,
        grid_height=args.grid_height,
        seed=args.seed
    )

    results = run_benchmark(
        agent_names=args.agents,
        benchmark_config=benchmark_config,
        output_dir=args.output_dir
    )

    print("\nBenchmark complete!")
    print(f"Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
