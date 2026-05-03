"""Tests for the simulation module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from gameagent.agent import GreedyAgent, RandomAgent
from gameagent.agent.q_learning import QLearningAgent
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import GridConfig
from gameagent.sim.runner import EpisodeRunner
from gameagent.sim.types import EpisodeResult, SimulationConfig, SimulationResult


class TestSimulationConfig:
    """Tests for SimulationConfig dataclass."""

    def test_default_values(self):
        config = SimulationConfig()
        assert config.num_episodes == 100
        assert config.grid_width == 5
        assert config.grid_height == 5
        assert config.goal_position == (4, 4)
        assert config.seed == 42
        assert config.obstacles == []
        assert config.render is False

    def test_custom_values(self):
        config = SimulationConfig(
            num_episodes=50,
            grid_width=10,
            grid_height=10,
            goal_position=(9, 9),
            seed=123,
            obstacles=[(2, 2), (3, 3)],
            render=True,
        )
        assert config.num_episodes == 50
        assert config.grid_width == 10
        assert config.grid_height == 10
        assert config.goal_position == (9, 9)
        assert config.seed == 123
        assert config.obstacles == [(2, 2), (3, 3)]
        assert config.render is True


class TestEpisodeResult:
    """Tests for EpisodeResult dataclass."""

    def test_default_values(self):
        result = EpisodeResult(
            total_reward=0.0,
            num_steps=0,
            terminated=False,
            truncated=False,
            start_time=0.0,
            end_time=0.0,
        )
        assert result.total_reward == 0.0
        assert result.num_steps == 0
        assert result.terminated is False
        assert result.truncated is False
        assert result.seed == 42

    def test_with_seed(self):
        result = EpisodeResult(
            total_reward=10.0,
            num_steps=5,
            terminated=True,
            truncated=False,
            start_time=100.0,
            end_time=100.5,
            seed=123,
        )
        assert result.total_reward == 10.0
        assert result.num_steps == 5
        assert result.terminated is True
        assert result.truncated is False
        assert result.seed == 123


class TestSimulationResult:
    """Tests for SimulationResult dataclass."""

    def test_default_values(self):
        result = SimulationResult(
            total_episodes=10,
            episode_results=[],
            mean_reward=0.0,
            std_reward=0.0,
            mean_steps=0.0,
            success_rate=0.0,
            start_time=0.0,
            end_time=0.0,
        )
        assert result.total_episodes == 10
        assert result.episode_results == []
        assert result.mean_reward == 0.0
        assert result.std_reward == 0.0
        assert result.mean_steps == 0.0
        assert result.success_rate == 0.0

    def test_with_data(self):
        results = [
            EpisodeResult(
                total_reward=10.0,
                num_steps=5,
                terminated=True,
                truncated=False,
                start_time=0.0,
                end_time=1.0,
                seed=42,
            )
        ]
        result = SimulationResult(
            total_episodes=1,
            episode_results=results,
            mean_reward=10.0,
            std_reward=0.0,
            mean_steps=5.0,
            success_rate=1.0,
            start_time=0.0,
            end_time=1.0,
        )
        assert result.total_episodes == 1
        assert len(result.episode_results) == 1
        assert result.mean_reward == 10.0
        assert result.std_reward == 0.0
        assert result.mean_steps == 5.0
        assert result.success_rate == 1.0


class TestEpisodeRunner:
    """Tests for EpisodeRunner class."""

    def test_init_default_agent(self):
        config = SimulationConfig()
        runner = EpisodeRunner(config)
        assert isinstance(runner.agent, RandomAgent)
        assert runner.agent.seed == config.seed

    def test_init_custom_agent(self):
        config = SimulationConfig()
        custom_agent = GreedyAgent()
        runner = EpisodeRunner(config, agent=custom_agent)
        assert runner.agent is custom_agent

    def test_init_env(self):
        config = SimulationConfig(grid_width=10, grid_height=10, seed=123)
        runner = EpisodeRunner(config)
        assert isinstance(runner._env, GridWorld)
        assert runner._env.config.width == 10
        assert runner._env.config.height == 10
        assert runner._env.config.seed == 123

    def test_run_episode_random_agent(self):
        config = SimulationConfig(num_episodes=1, seed=42)
        runner = EpisodeRunner(config)
        result = runner.run_episode()

        assert isinstance(result, EpisodeResult)
        assert isinstance(result.total_reward, float)
        assert isinstance(result.num_steps, int)
        assert isinstance(result.terminated, bool)
        assert isinstance(result.truncated, bool)
        assert result.num_steps > 0
        assert result.seed == 42

    def test_run_episode_greedy_agent(self):
        config = SimulationConfig(num_episodes=1, seed=42)
        runner = EpisodeRunner(config, agent=GreedyAgent())
        result = runner.run_episode()

        assert isinstance(result, EpisodeResult)
        assert result.terminated is True  # Greedy should reach goal
        assert result.num_steps > 0

    def test_run_episode_truncated(self):
        """Test episode that gets truncated due to max steps."""
        config = SimulationConfig(num_episodes=1, seed=42)
        runner = EpisodeRunner(config)

        # Mock the agent's act method to return a specific action
        with patch.object(runner.agent, 'act') as mock_act:
            mock_act.return_value = MagicMock()
            # Mock the environment's step to return truncated
            with patch.object(runner._env, 'step') as mock_step:
                mock_step.return_value = MagicMock(
                    reward=-0.1,
                    terminated=False,
                    truncated=True,
                    observation=MagicMock(),
                )
                result = runner.run_episode()
                assert result.truncated is True

    def test_run_episode_with_obstacles(self):
        """Test episode with obstacles in the grid."""
        config = SimulationConfig(
            num_episodes=1,
            seed=42,
            obstacles=[(0, 1), (1, 0)],
        )
        runner = EpisodeRunner(config)
        result = runner.run_episode()

        assert isinstance(result, EpisodeResult)
        assert result.num_steps > 0

    def test_run_episode_repeated_calls(self):
        """Test that multiple episode runs work correctly."""
        config = SimulationConfig(num_episodes=1, seed=42)
        runner = EpisodeRunner(config)

        result1 = runner.run_episode()
        result2 = runner.run_episode()

        assert isinstance(result1, EpisodeResult)
        assert isinstance(result2, EpisodeResult)
        assert result1.num_steps > 0
        assert result2.num_steps > 0


class TestEpisodeRunnerSimulation:
    """Tests for EpisodeRunner.run_simulation method."""

    def test_run_simulation_basic(self):
        """Test basic simulation execution."""
        config = SimulationConfig(num_episodes=10, seed=42)
        runner = EpisodeRunner(config)
        result = runner.run_simulation()

        assert isinstance(result, SimulationResult)
        assert result.total_episodes == 10
        assert len(result.episode_results) == 10
        assert result.mean_steps > 0
        assert 0.0 <= result.success_rate <= 1.0
        assert result.std_reward >= 0.0

    def test_run_simulation_with_greedy_agent(self):
        """Test simulation with greedy agent."""
        config = SimulationConfig(num_episodes=10, seed=42)
        runner = EpisodeRunner(config, agent=GreedyAgent())
        result = runner.run_simulation()

        assert result.success_rate == 1.0  # Greedy should always succeed
        assert result.mean_steps < 20  # Should be efficient

    def test_run_simulation_with_random_agent(self):
        """Test simulation with random agent."""
        config = SimulationConfig(num_episodes=10, seed=42)
        runner = EpisodeRunner(config, agent=RandomAgent())
        result = runner.run_simulation()

        assert result.success_rate >= 0.0
        assert result.success_rate <= 1.0
        assert result.mean_steps > 0

    def test_run_simulation_with_trained_agent(self):
        """Test simulation with a trained Q-learning agent."""
        config = SimulationConfig(num_episodes=10, seed=42)
        runner = EpisodeRunner(config, agent=QLearningAgent())
        result = runner.run_simulation()

        assert isinstance(result, SimulationResult)
        assert result.total_episodes == 10
        assert len(result.episode_results) == 10

    def test_run_simulation_time_metrics(self):
        """Test that time metrics are correctly calculated."""
        config = SimulationConfig(num_episodes=5, seed=42)
        runner = EpisodeRunner(config)
        result = runner.run_simulation()

        assert result.start_time <= result.end_time
        assert result.end_time - result.start_time >= 0.0

    def test_run_simulation_with_obstacles(self):
        """Test simulation with obstacles."""
        config = SimulationConfig(
            num_episodes=10,
            seed=42,
            obstacles=[(0, 1), (1, 0), (2, 2)],
        )
        runner = EpisodeRunner(config)
        result = runner.run_simulation()

        assert isinstance(result, SimulationResult)
        assert result.total_episodes == 10
        assert result.success_rate >= 0.0
        assert result.success_rate <= 1.0

    def test_run_simulation_repeated_calls(self):
        """Test that multiple simulation runs work correctly."""
        config = SimulationConfig(num_episodes=5, seed=42)
        runner = EpisodeRunner(config)

        result1 = runner.run_simulation()
        result2 = runner.run_simulation()

        assert result1.total_episodes == 5
        assert result2.total_episodes == 5
        assert len(result1.episode_results) == 5
        assert len(result2.episode_results) == 5


class TestSimulationIntegration:
    """Integration tests for simulation module."""

    def test_simulation_with_qlearning_agent(self):
        """Test simulation with Q-learning agent that has learned some policy."""
        config = SimulationConfig(num_episodes=10, seed=42)
        agent = QLearningAgent()

        # Simulate some training by running a few episodes
        runner = EpisodeRunner(config, agent=agent)
        for _ in range(5):
            runner.run_episode()

        # Now run full simulation
        result = runner.run_simulation()

        assert result.total_episodes == 10
        assert len(result.episode_results) == 10
        assert result.success_rate >= 0.0

    def test_simulation_results_consistency(self):
        """Test that simulation results are consistent across runs."""
        config = SimulationConfig(num_episodes=10, seed=42)
        runner = EpisodeRunner(config, agent=GreedyAgent())

        result1 = runner.run_simulation()
        result2 = runner.run_simulation()

        # Greedy agent should have same success rate
        assert result1.success_rate == result2.success_rate == 1.0

    def test_simulation_with_custom_goal(self):
        """Test simulation with custom goal position."""
        config = SimulationConfig(
            num_episodes=10,
            seed=42,
            goal_position=(2, 2),
        )
        runner = EpisodeRunner(config, agent=GreedyAgent())
        result = runner.run_simulation()

        assert result.total_episodes == 10
        assert result.success_rate == 1.0

    def test_simulation_with_large_grid(self):
        """Test simulation with larger grid."""
        config = SimulationConfig(
            num_episodes=10,
            grid_width=10,
            grid_height=10,
            goal_position=(9, 9),
            seed=42,
        )
        runner = EpisodeRunner(config, agent=GreedyAgent())
        result = runner.run_simulation()

        assert result.total_episodes == 10
        assert result.success_rate == 1.0
        assert result.mean_steps > 10  # Larger grid should take more steps


class TestSimulationSerialization:
    """Tests for simulation result serialization."""

    def test_simulation_result_to_dict(self):
        """Test that simulation results can be converted to dictionary."""
        results = [
            EpisodeResult(
                total_reward=10.0,
                num_steps=5,
                terminated=True,
                truncated=False,
                start_time=0.0,
                end_time=1.0,
                seed=42,
            )
        ]
        result = SimulationResult(
            total_episodes=1,
            episode_results=results,
            mean_reward=10.0,
            std_reward=0.0,
            mean_steps=5.0,
            success_rate=1.0,
            start_time=0.0,
            end_time=1.0,
        )

        # Convert to dict manually
        result_dict = {
            "total_episodes": result.total_episodes,
            "mean_reward": result.mean_reward,
            "std_reward": result.std_reward,
            "mean_steps": result.mean_steps,
            "success_rate": result.success_rate,
        }

        assert result_dict["total_episodes"] == 1
        assert result_dict["mean_reward"] == 10.0
        assert result_dict["success_rate"] == 1.0

    def test_simulation_results_json_serialization(self):
        """Test that simulation results can be serialized to JSON."""
        results = [
            EpisodeResult(
                total_reward=10.0,
                num_steps=5,
                terminated=True,
                truncated=False,
                start_time=0.0,
                end_time=1.0,
                seed=42,
            )
        ]
        result = SimulationResult(
            total_episodes=1,
            episode_results=results,
            mean_reward=10.0,
            std_reward=0.0,
            mean_steps=5.0,
            success_rate=1.0,
            start_time=0.0,
            end_time=1.0,
        )

        # Convert to dict for JSON serialization
        result_dict = {
            "total_episodes": result.total_episodes,
            "mean_reward": result.mean_reward,
            "std_reward": result.std_reward,
            "mean_steps": result.mean_steps,
            "success_rate": result.success_rate,
        }

        # Serialize to JSON
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)

        # Deserialize back
        loaded_dict = json.loads(json_str)
        assert loaded_dict["total_episodes"] == 1
        assert loaded_dict["mean_reward"] == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
