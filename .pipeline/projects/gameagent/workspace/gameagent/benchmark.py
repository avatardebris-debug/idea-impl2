"""Benchmarking utilities for the GridWorld agent system."""

from __future__ import annotations

import numpy as np

from gameagent.agent import BaseAgent
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import GridConfig


def benchmark_agent(
    agent: BaseAgent,
    env: GridWorld,
    num_episodes: int = 100
) -> dict:
    """Benchmark a single agent on the environment.

    Args:
        agent: Agent to benchmark.
        env: Environment to benchmark on.
        num_episodes: Number of episodes to run.

    Returns:
        Dictionary with benchmark metrics.
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
        "std_reward": float(np.std(rewards)),
        "mean_steps": float(np.mean(steps_list)),
        "success_rate": successes / num_episodes,
        "total_episodes": num_episodes,
    }


def compare_agents(
    agents: dict[str, BaseAgent],
    env: GridWorld,
    num_episodes: int = 100
) -> dict[str, dict]:
    """Compare multiple agents on the environment.

    Args:
        agents: Dictionary mapping agent names to agent instances.
        env: Environment to benchmark on.
        num_episodes: Number of episodes per agent.

    Returns:
        Dictionary mapping agent names to benchmark results.
    """
    results = {}

    for name, agent in agents.items():
        print(f"\nBenchmarking {name}...")
        results[name] = benchmark_agent(agent, env, num_episodes)
        print(f"  Mean Reward: {results[name]['mean_reward']:.2f}")
        print(f"  Success Rate: {results[name]['success_rate']:.2%}")

    return results


def print_benchmark_summary(results: dict[str, dict]) -> None:
    """Print a formatted benchmark summary.

    Args:
        results: Dictionary mapping agent names to benchmark results.
    """
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    for agent_name, metrics in results.items():
        print(f"\n{agent_name}:")
        print(f"  Mean Reward: {metrics['mean_reward']:.2f} ± {metrics['std_reward']:.2f}")
        print(f"  Mean Steps: {metrics['mean_steps']:.1f}")
        print(f"  Success Rate: {metrics['success_rate']:.2%}")
        print(f"  Episodes: {metrics['total_episodes']}")

    print("\n" + "=" * 60)


def run_comprehensive_benchmark(
    num_episodes: int = 1000,
    grid_width: int = 5,
    grid_height: int = 5,
    goal_position: tuple[int, int] = (4, 4),
    seed: int = 42
) -> dict[str, dict]:
    """Run a comprehensive benchmark comparing different agent types.

    Args:
        num_episodes: Number of episodes per agent.
        grid_width: Grid width.
        grid_height: Grid height.
        goal_position: Goal position.
        seed: Random seed.

    Returns:
        Dictionary mapping agent names to benchmark results.
    """
    from gameagent.agent import RandomAgent, GreedyAgent, QLearningAgent

    config = GridConfig(
        width=grid_width,
        height=grid_height,
        goal_position=goal_position,
        seed=seed
    )
    env = GridWorld(config=config)

    agents = {
        "RandomAgent": RandomAgent(),
        "GreedyAgent": GreedyAgent(),
        "QLearningAgent": QLearningAgent(),
    }

    results = compare_agents(agents, env, num_episodes)
    print_benchmark_summary(results)

    return results
