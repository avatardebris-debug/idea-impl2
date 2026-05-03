"""Tests for the GridWorldTrainer module."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from gameagent.agent import GreedyAgent, RandomAgent
from gameagent.agent.q_learning import QLearningAgent
from gameagent.env.grid_world import GridWorld
from gameagent.env.types import GridConfig
from gameagent.trainer import GridWorldTrainer, TrainingConfig, TrainingResult


class TestTrainingConfig:
    """Tests for TrainingConfig dataclass."""

    def test_default_values(self):
        config = TrainingConfig()
        assert config.num_episodes == 1000
        assert config.grid_width == 5
        assert config.grid_height == 5
        assert config.goal_position == (4, 4)
        assert config.learning_rate == 0.2
        assert config.discount_factor == 0.95
        assert config.epsilon_start == 1.0
        assert config.epsilon_decay == 0.995
        assert config.epsilon_min == 0.01
        assert config.seed == 42
        assert config.save_path == "trained_agent.json"
        assert config.render_every == 100


class TestTrainingResult:
    """Tests for TrainingResult dataclass."""

    def test_default_values(self):
        result = TrainingResult()
        assert result.rewards == []
        assert result.steps == []
        assert result.epsilon_history == []
        assert result.final_epsilon == 0.0


class TestGridWorldTrainer:
    """Tests for GridWorldTrainer class."""

    def test_create_agent(self):
        config = TrainingConfig()
        trainer = GridWorldTrainer(config)
        agent = trainer.create_agent()
        assert isinstance(agent, QLearningAgent)
        assert agent.learning_rate == config.learning_rate
        assert agent.discount_factor == config.discount_factor
        assert agent.epsilon == config.epsilon_start

    def test_create_env(self):
        config = TrainingConfig(grid_width=10, grid_height=10, goal_position=(9, 9), seed=123)
        trainer = GridWorldTrainer(config)
        env = trainer.create_env()
        assert isinstance(env, GridWorld)
        assert env.config.width == 10
        assert env.config.height == 10
        assert env.config.goal_position == (9, 9)
        assert env.config.seed == 123

    def test_train_episode(self):
        config = TrainingConfig()
        trainer = GridWorldTrainer(config)
        agent = trainer.create_agent()
        env = trainer.create_env()

        reward, steps = trainer.train_episode(agent, env)
        assert isinstance(reward, float)
        assert isinstance(steps, int)
        assert steps > 0

    def test_evaluate_agent(self):
        config = TrainingConfig()
        trainer = GridWorldTrainer(config)
        env = trainer.create_env()

        # Test with RandomAgent
        random_agent = RandomAgent()
        results = trainer.evaluate_agent(random_agent, env, num_episodes=10)
        assert "mean_reward" in results
        assert "mean_steps" in results
        assert "success_rate" in results
        assert "std_reward" in results
        assert 0.0 <= results["success_rate"] <= 1.0

        # Test with GreedyAgent
        greedy_agent = GreedyAgent()
        results = trainer.evaluate_agent(greedy_agent, env, num_episodes=10)
        assert results["success_rate"] == 1.0  # Greedy should always succeed

    def test_train(self):
        config = TrainingConfig(num_episodes=10, seed=42)
        trainer = GridWorldTrainer(config)
        result = trainer.train()

        assert isinstance(result, TrainingResult)
        assert len(result.rewards) == 10
        assert len(result.steps) == 10
        assert len(result.epsilon_history) == 10
        assert result.final_epsilon > 0

    def test_save_and_load_agent(self):
        config = TrainingConfig(num_episodes=10, seed=42)
        trainer = GridWorldTrainer(config)
        trainer.train()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            saved_path = trainer.save_agent(temp_path)
            assert saved_path == temp_path
            assert os.path.exists(temp_path)

            # Verify JSON structure
            with open(temp_path, "r") as f:
                data = json.load(f)
            assert "q_table" in data
            assert "learning_rate" in data
            assert "discount_factor" in data
            assert "epsilon" in data

            # Load the agent
            loaded_agent = trainer.load_agent(temp_path)
            assert isinstance(loaded_agent, QLearningAgent)
            assert loaded_agent.learning_rate == trainer.agent.learning_rate
            assert loaded_agent.discount_factor == trainer.agent.discount_factor
            assert loaded_agent.epsilon == trainer.agent.epsilon

            # Verify Q-table values match
            for state in trainer.agent.q_table:
                for action in trainer.agent.q_table[state]:
                    assert loaded_agent.q_table[state][action] == pytest.approx(
                        trainer.agent.q_table[state][action]
                    )
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_agent_no_agent_raises(self):
        config = TrainingConfig()
        trainer = GridWorldTrainer(config)
        with pytest.raises(ValueError, match="No agent to save"):
            trainer.save_agent()

    def test_run_benchmark(self):
        config = TrainingConfig(num_episodes=10, seed=42)
        trainer = GridWorldTrainer(config)
        trainer.train()

        results = trainer.run_benchmark()
        assert "RandomAgent" in results
        assert "GreedyAgent" in results
        assert "QLearningAgent" in results

        for agent_name, metrics in results.items():
            assert "mean_reward" in metrics
            assert "mean_steps" in metrics
            assert "success_rate" in metrics
            assert "std_reward" in metrics

    def test_run_benchmark_no_trained_agent(self):
        config = TrainingConfig()
        trainer = GridWorldTrainer(config)
        # Don't train
        results = trainer.run_benchmark()
        assert "RandomAgent" in results
        assert "GreedyAgent" in results
        assert "QLearningAgent" not in results

    def test_training_convergence(self):
        """Test that training converges to optimal solution."""
        config = TrainingConfig(
            num_episodes=500,
            grid_width=5,
            grid_height=5,
            goal_position=(4, 4),
            learning_rate=0.2,
            discount_factor=0.95,
            epsilon_start=1.0,
            epsilon_decay=0.995,
            epsilon_min=0.01,
            seed=42,
        )
        trainer = GridWorldTrainer(config)
        trainer.train()

        # Evaluate the trained agent
        env = trainer.create_env()
        results = trainer.evaluate_agent(trainer.agent, env, num_episodes=100)

        # The agent should achieve near-optimal performance
        assert results["success_rate"] >= 0.95
        assert results["mean_reward"] >= 9.0
        assert results["mean_steps"] <= 10  # Optimal is 8 steps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
