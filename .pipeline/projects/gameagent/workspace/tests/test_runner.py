"""Tests for EpisodeRunner."""

import pytest

from gameagent.agent.base import RandomAgent
from gameagent.agent.greedy_agent import GreedyAgent
from gameagent.env.types import GridConfig
from gameagent.sim.runner import EpisodeRunner
from gameagent.sim.types import SimulationConfig


class TestEpisodeRunner:
    """Tests for the EpisodeRunner class."""

    def test_init(self):
        """Test EpisodeRunner initialization."""
        config = SimulationConfig(num_episodes=10, grid_width=5, grid_height=5)
        runner = EpisodeRunner(config=config)
        assert runner.config == config
        assert isinstance(runner.agent, RandomAgent)

    def test_init_with_custom_agent(self):
        """Test EpisodeRunner with custom agent."""
        config = SimulationConfig(num_episodes=10, grid_width=5, grid_height=5)
        agent = GreedyAgent()
        runner = EpisodeRunner(config=config, agent=agent)
        assert runner.agent == agent

    def test_run_episode(self):
        """Test running a single episode."""
        config = SimulationConfig(
            num_episodes=1, grid_width=5, grid_height=5, goal_position=(1, 1)
        )
        runner = EpisodeRunner(config=config, agent=GreedyAgent())
        result = runner.run_episode()

        assert result.total_reward > 0  # Should reach goal
        assert result.num_steps > 0
        assert result.terminated is True
        assert result.truncated is False

    def test_run_episode_with_obstacles(self):
        """Test episode with obstacles."""
        config = SimulationConfig(
            num_episodes=1,
            grid_width=5,
            grid_height=5,
            goal_position=(4, 4),
            obstacles=[(1, 0), (2, 0), (3, 0)],
        )
        runner = EpisodeRunner(config=config, agent=GreedyAgent())
        result = runner.run_episode()

        assert result.total_reward > 0  # Should still reach goal
        assert result.terminated is True

    def test_run_simulation(self):
        """Test running full simulation."""
        config = SimulationConfig(
            num_episodes=5, grid_width=5, grid_height=5, goal_position=(1, 1)
        )
        runner = EpisodeRunner(config=config, agent=GreedyAgent())
        result = runner.run_simulation()

        assert result.total_episodes == 5
        assert len(result.episode_results) == 5
        assert result.mean_reward > 0
        assert result.success_rate == 1.0  # Greedy agent should always succeed

    def test_run_simulation_with_random_agent(self):
        """Test simulation with random agent."""
        config = SimulationConfig(
            num_episodes=10, grid_width=5, grid_height=5, goal_position=(4, 4)
        )
        runner = EpisodeRunner(config=config, agent=RandomAgent())
        result = runner.run_simulation()

        assert result.total_episodes == 10
        assert result.mean_reward < 0  # Random agent may not reach goal
        assert result.success_rate < 1.0  # Random agent may fail

    def test_simulation_duration(self):
        """Test that simulation has reasonable duration."""
        config = SimulationConfig(num_episodes=10, grid_width=5, grid_height=5)
        runner = EpisodeRunner(config=config, agent=GreedyAgent())
        result = runner.run_simulation()

        assert result.end_time > result.start_time
        duration = result.end_time - result.start_time
        assert duration < 10.0  # Should complete quickly
