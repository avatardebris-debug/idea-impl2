"""Tests for MultiGoalGridWorld environment."""

import pytest

from gameagent.env.multi_goal_grid_world import MultiGoalConfig, MultiGoalGridWorld
from gameagent.env.types import Action


class TestMultiGoalConfig:
    """Tests for MultiGoalConfig validation."""

    def test_initialization_with_goals(self):
        """Test that MultiGoalConfig initializes correctly with goals."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[],
        )

        assert config.width == 5
        assert config.height == 5
        assert len(config.goals) == 2
        assert config.goals[0] == ((1, 1), 1.0)
        assert config.goals[1] == ((4, 4), 2.0)

    def test_no_goals_raises_error(self):
        """Test that empty goals list raises error."""
        with pytest.raises(ValueError, match="At least one goal must be specified"):
            MultiGoalConfig(width=5, height=5, goals=[], seed=42, obstacles=[])

    def test_goal_out_of_bounds_raises_error(self):
        """Test that goal out of bounds raises error."""
        with pytest.raises(ValueError, match="out of bounds"):
            MultiGoalConfig(
                width=5, height=5, goals=[((10, 10), 1.0)], seed=42, obstacles=[]
            )

    def test_obstacle_overlaps_goal_raises_error(self):
        """Test that obstacle overlapping goal raises error."""
        with pytest.raises(ValueError, match="overlaps with goal"):
            MultiGoalConfig(
                width=5,
                height=5,
                goals=[((4, 4), 1.0)],
                seed=42,
                obstacles=[(4, 4)],
            )

    def test_duplicate_goal_positions_raises_error(self):
        """Test that duplicate goal positions raises error."""
        with pytest.raises(ValueError, match="Duplicate goal positions"):
            MultiGoalConfig(
                width=5,
                height=5,
                goals=[((1, 1), 1.0), ((1, 1), 2.0)],
                seed=42,
                obstacles=[],
            )


class TestMultiGoalGridWorld:
    """Tests for MultiGoalGridWorld environment."""

    def test_initialization(self):
        """Test that MultiGoalGridWorld initializes correctly."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[],
        )
        env = MultiGoalGridWorld(config)

        assert env.config.width == 5
        assert env.config.height == 5
        assert len(env.config.goals) == 2
        assert env.agent_position == (0, 0)
        assert env.step_count == 0
        assert len(env.completed_goals) == 0

    def test_reset(self):
        """Test that reset returns initial state."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[],
        )
        env = MultiGoalGridWorld(config)
        env.reset()

        assert env.agent_position == (0, 0)
        assert env.step_count == 0
        assert len(env.completed_goals) == 0

    def test_higher_priority_goal_selected(self):
        """Test that higher priority goal is selected as target."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[],
        )
        env = MultiGoalGridWorld(config)
        obs, _ = env.reset()

        # Higher priority goal (4,4) should be the target
        assert obs.goal_position == (4, 4)

    def test_goal_reached_with_priority_reward(self):
        """Test that reaching a goal gives priority-based reward."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[],
        )
        env = MultiGoalGridWorld(config)
        env.reset()

        # Move to lower priority goal (1,1)
        env.step(Action.RIGHT)
        env.step(Action.UP)

        result = env.step(Action.INTERACT)
        assert result.reward == 10.0  # 1.0 * 10.0
        assert result.terminated is True
        assert (1, 1) in env.completed_goals

    def test_higher_priority_goal_gives_higher_reward(self):
        """Test that higher priority goals give higher rewards."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[],
        )
        env = MultiGoalGridWorld(config)
        env.reset()

        # Move to higher priority goal (4,4)
        for _ in range(4):
            env.step(Action.RIGHT)
        for _ in range(4):
            env.step(Action.UP)

        result = env.step(Action.INTERACT)
        assert result.reward == 20.0  # 2.0 * 10.0
        assert result.terminated is True
        assert (4, 4) in env.completed_goals

    def test_multiple_goals_completion(self):
        """Test completing multiple goals in sequence."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[],
        )
        env = MultiGoalGridWorld(config)
        env.reset()

        # Complete first goal
        env.step(Action.RIGHT)
        env.step(Action.UP)
        result = env.step(Action.INTERACT)
        assert result.reward == 10.0
        assert len(env.completed_goals) == 1

        # After completing first goal, should target second goal
        obs, _ = env.reset()
        assert obs.goal_position == (4, 4)

    def test_all_goals_completed(self):
        """Test behavior when all goals are completed."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[],
        )
        env = MultiGoalGridWorld(config)
        env.reset()

        # Complete both goals
        env.step(Action.RIGHT)
        env.step(Action.UP)
        env.step(Action.INTERACT)

        env.step(Action.RIGHT)
        for _ in range(3):
            env.step(Action.RIGHT)
        for _ in range(4):
            env.step(Action.UP)
        env.step(Action.INTERACT)

        # All goals completed
        assert len(env.completed_goals) == 2

    def test_obstacle_collision(self):
        """Test obstacle collision in multi-goal environment."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((4, 4), 2.0)],
            seed=42,
            obstacles=[(1, 0)],
        )
        env = MultiGoalGridWorld(config)
        env.reset()

        result = env.step(Action.RIGHT)
        assert result.reward == -5.0
        assert result.terminated is False
        assert result.observation.agent_position == (0, 0)

    def test_truncation(self):
        """Test episode truncation after max steps."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((4, 4), 2.0)],
            seed=42,
            obstacles=[],
            max_steps=10,
        )
        env = MultiGoalGridWorld(config)
        env.reset()

        # Run 10 steps without reaching goal
        for _ in range(10):
            result = env.step(Action.RIGHT)
            if result.terminated:
                break

        assert result.truncated is True

    def test_render(self):
        """Test grid rendering."""
        config = MultiGoalConfig(
            width=5,
            height=5,
            goals=[((1, 1), 1.0), ((4, 4), 2.0)],
            seed=42,
            obstacles=[(2, 2)],
        )
        env = MultiGoalGridWorld(config)
        env.reset()

        # Move agent and complete a goal
        env.step(Action.RIGHT)
        env.step(Action.UP)
        env.step(Action.INTERACT)

        rendered = env.render()
        assert "A" in rendered
        assert "C" in rendered  # Completed goal
        assert "G" in rendered  # Active goal
        assert "X" in rendered  # Obstacle
