"""Episode runner for simulation."""

from __future__ import annotations

import time
from typing import Any

from gameagent.agent import BaseAgent, GreedyAgent, RandomAgent
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import GridConfig
from gameagent.sim.types import EpisodeResult, SimulationConfig, SimulationResult


class EpisodeRunner:
    """Runner for executing episodes in the GridWorld environment."""

    def __init__(
        self,
        config: SimulationConfig,
        agent: BaseAgent | None = None,
    ):
        """Initialize the EpisodeRunner.

        Args:
            config: Simulation configuration.
            agent: Optional custom agent. Defaults to RandomAgent.
        """
        self.config = config
        self.agent = agent or RandomAgent(seed=config.seed)
        self._env = GridWorld(
            GridConfig(
                width=config.grid_width,
                height=config.grid_height,
                goal_position=config.goal_position,
                seed=config.seed,
                obstacles=config.obstacles,
            )
        )

    def run_episode(self) -> EpisodeResult:
        """Run a single episode.

        Returns:
            EpisodeResult containing episode statistics.
        """
        start_time = time.time()
        self._env.reset()
        self.agent.reset()

        total_reward = 0.0
        num_steps = 0
        terminated = False
        truncated = False

        while not terminated and not truncated:
            observation = self._env._get_observation()
            action = self.agent.act(observation)
            result = self._env.step(action)

            total_reward += result.reward
            num_steps += 1
            terminated = result.terminated
            truncated = result.truncated

        end_time = time.time()

        return EpisodeResult(
            total_reward=total_reward,
            num_steps=num_steps,
            terminated=terminated,
            truncated=truncated,
            start_time=start_time,
            end_time=end_time,
            seed=self.config.seed,
        )

    def run_simulation(self) -> SimulationResult:
        """Run the full simulation.

        Returns:
            SimulationResult containing simulation statistics.
        """
        start_time = time.time()
        episode_results = []

        for _ in range(self.config.num_episodes):
            result = self.run_episode()
            episode_results.append(result)

        end_time = time.time()

        total_rewards = [r.total_reward for r in episode_results]
        total_steps = [r.num_steps for r in episode_results]
        successes = sum(1 for r in episode_results if r.terminated)

        mean_reward = sum(total_rewards) / len(total_rewards)
        mean_steps = sum(total_steps) / len(total_steps)
        std_reward = (sum((r - mean_reward) ** 2 for r in total_rewards) / len(total_rewards)) ** 0.5

        return SimulationResult(
            total_episodes=self.config.num_episodes,
            episode_results=episode_results,
            mean_reward=mean_reward,
            std_reward=std_reward,
            mean_steps=mean_steps,
            success_rate=successes / len(episode_results),
            start_time=start_time,
            end_time=end_time,
        )
