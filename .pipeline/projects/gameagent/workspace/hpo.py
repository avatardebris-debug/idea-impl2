"""Hyperparameter optimization for RL agents."""

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
    QLearningAgent,
    DQNAgent,
    PPOAgent,
)
from gameagent.agent.dqn_agent import DQNConfig
from gameagent.agent.ppo_agent import PPOConfig
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import GridConfig


@dataclass
class HPOConfig:
    """Configuration for hyperparameter optimization."""
    num_trials: int = 20
    num_episodes_per_trial: int = 50
    grid_width: int = 5
    grid_height: int = 5
    goal_position: tuple[int, int] = (4, 4)
    seed: int = 42
    agent_type: str = "DQNAgent"
    metric: str = "mean_reward"
    output_dir: str = "output/hpo"


# Parameter grids for different agents
PARAM_GRIDS = {
    "QLearningAgent": {
        "learning_rate": [0.01, 0.1, 0.2],
        "gamma": [0.8, 0.9, 0.95, 0.99],
        "epsilon": [0.1, 0.2, 0.3],
    },
    "DQNAgent": {
        "learning_rate": [0.001, 0.0005, 0.0001],
        "gamma": [0.9, 0.95, 0.99],
        "epsilon_start": [0.9, 0.8, 0.7],
        "epsilon_end": [0.01, 0.05, 0.1],
        "hidden_layers": [[32], [64], [64, 32]],
        "batch_size": [32, 64, 128],
    },
    "PPOAgent": {
        "learning_rate": [0.001, 0.0005, 0.0001],
        "gamma": [0.95, 0.99, 0.999],
        "epsilon_clip": [0.1, 0.2, 0.3],
        "hidden_layers": [[32], [64], [64, 32]],
        "batch_size": [32, 64, 128],
        "num_epochs": [5, 10, 20],
    },
}


def create_agent_with_config(
    agent_type: str,
    config: dict
) -> BaseAgent:
    """Create an agent with specific hyperparameters."""
    if agent_type == "QLearningAgent":
        return QLearningAgent(
            learning_rate=config.get("learning_rate", 0.1),
            discount_factor=config.get("gamma", 0.95),
            epsilon=config.get("epsilon", 0.2),
        )
    elif agent_type == "DQNAgent":
        dqn_config = DQNConfig(
            learning_rate=config.get("learning_rate", 0.001),
            gamma=config.get("gamma", 0.95),
            epsilon_start=config.get("epsilon_start", 0.9),
            epsilon_end=config.get("epsilon_end", 0.01),
            hidden_layers=tuple(config.get("hidden_layers", [32])),
            batch_size=config.get("batch_size", 32),
        )
        return DQNAgent(config=dqn_config)
    elif agent_type == "PPOAgent":
        ppo_config = PPOConfig(
            learning_rate=config.get("learning_rate", 0.001),
            gamma=config.get("gamma", 0.99),
            epsilon_clip=config.get("epsilon_clip", 0.2),
            hidden_layers=tuple(config.get("hidden_layers", [64])),
            batch_size=config.get("batch_size", 32),
            num_epochs=config.get("num_epochs", 10),
        )
        return PPOAgent(config=ppo_config)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def evaluate_agent(
    agent: BaseAgent,
    env: GridWorld,
    num_episodes: int,
    metric: str
) -> float:
    """Evaluate an agent and return the specified metric."""
    rewards = []
    steps = []
    successes = 0

    for episode in range(num_episodes):
        observation, _ = env.reset()
        total_reward = 0.0
        step_count = 0
        terminated = False
        truncated = False

        while not terminated and not truncated:
            action = agent.act(observation)
            result = env.step(action)
            observation = result.observation
            reward = result.reward
            terminated = result.terminated
            truncated = result.truncated
            total_reward += reward
            step_count += 1

        rewards.append(total_reward)
        steps.append(step_count)

        if terminated:
            successes += 1

    if metric == "mean_reward":
        return np.mean(rewards)
    elif metric == "success_rate":
        return successes / num_episodes
    elif metric == "mean_steps":
        return np.mean(steps)
    else:
        raise ValueError(f"Unknown metric: {metric}")


def run_hpo(
    hpo_config: HPOConfig,
    param_grid: dict
) -> list[dict]:
    """Run hyperparameter optimization."""
    os.makedirs(hpo_config.output_dir, exist_ok=True)

    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate all parameter combinations
    from itertools import product

    keys = list(param_grid.keys())
    values = [param_grid[key] for key in keys]
    combinations = list(product(*values))

    print(f"Running {len(combinations)} trials...")

    for i, combo in enumerate(combinations):
        config = dict(zip(keys, combo))

        # Create agent with current hyperparameters
        agent = create_agent_with_config(hpo_config.agent_type, config)

        # Create environment
        env = GridWorld(
            GridConfig(
                width=hpo_config.grid_width,
                height=hpo_config.grid_height,
                goal_position=hpo_config.goal_position,
                seed=hpo_config.seed + i,
            )
        )

        # Evaluate agent
        score = evaluate_agent(
            agent,
            env,
            hpo_config.num_episodes_per_trial,
            hpo_config.metric
        )

        result = {
            "trial": i + 1,
            "config": config,
            "score": score,
            "timestamp": timestamp,
        }
        results.append(result)

        print(f"Trial {i + 1}/{len(combinations)}: {config} -> {score:.4f}")

    # Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)

    # Save results
    output_file = os.path.join(
        hpo_config.output_dir,
        f"hpo_{hpo_config.agent_type}_{timestamp}.json"
    )
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "config": asdict(hpo_config),
            "results": results,
            "best": results[0] if results else None,
        }, f, indent=2)

    print(f"\nBest configuration:")
    print(f"  Score: {results[0]['score']:.4f}")
    print(f"  Config: {results[0]['config']}")

    return results


def main():
    """Main entry point for HPO."""
    parser = argparse.ArgumentParser(description="Run hyperparameter optimization")
    parser.add_argument(
        "--agent-type",
        type=str,
        default="DQNAgent",
        help="Agent type to optimize"
    )
    parser.add_argument(
        "--num-trials",
        type=int,
        default=20,
        help="Number of trials"
    )
    parser.add_argument(
        "--num-episodes",
        type=int,
        default=50,
        help="Number of episodes per trial"
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
        "--metric",
        type=str,
        default="mean_reward",
        help="Metric to optimize"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/hpo",
        help="Output directory"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()

    hpo_config = HPOConfig(
        num_trials=args.num_trials,
        num_episodes_per_trial=args.num_episodes,
        grid_width=args.grid_width,
        grid_height=args.grid_height,
        goal_position=(args.grid_height - 1, args.grid_width - 1),
        seed=args.seed,
        agent_type=args.agent_type,
        metric=args.metric,
        output_dir=args.output_dir,
    )

    param_grid = PARAM_GRIDS.get(args.agent_type, {})

    if not param_grid:
        print(f"No parameter grid defined for {args.agent_type}")
        print(f"Available agents: {list(PARAM_GRIDS.keys())}")
        return

    results = run_hpo(hpo_config, param_grid)


if __name__ == "__main__":
    main()
