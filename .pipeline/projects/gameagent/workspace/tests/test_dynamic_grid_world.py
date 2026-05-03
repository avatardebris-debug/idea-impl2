"""Tests for DynamicGridWorld environment."""

import pytest

from gameagent.env.dynamic_grid_world import (
    DynamicGridConfig,
    DynamicGridWorld,
    ObstacleMovementPattern,
)
from gameagent.env.types import Action


class TestDynamicGridConfig:
    """Tests for DynamicGridConfig validation."""

    def test_initialization(self):
        """Test that DynamicGridConfig initializes correctly."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
        )

        assert config.width == 5
        assert config.height == 5
        assert config.goal_position == (4, 4)
        assert config.movement_interval == 5

    def test_goal_out_of_bounds_raises_error(self):
        """Test that goal out of bounds raises error."""
        with pytest.raises(ValueError, match="out of bounds"):
            DynamicGridConfig(
                width=5, height=5, goal_position=(10, 10), seed=42, initial_obstacles=[]
            )

    def test_obstacle_overlaps_goal_raises_error(self):
        """Test that obstacle overlapping goal raises error."""
        with pytest.raises(ValueError, match="overlaps with goal"):
            DynamicGridConfig(
                width=5,
                height=5,
                goal_position=(4, 4),
                seed=42,
                initial_obstacles=[(4, 4)],
            )

    def test_obstacle_out_of_bounds_raises_error(self):
        """Test that obstacle out of bounds raises error."""
        with pytest.raises(ValueError, match="out of bounds"):
            DynamicGridConfig(
                width=5,
                height=5,
                goal_position=(4, 4),
                seed=42,
                initial_obstacles=[(10, 10)],
            )


class TestDynamicGridWorld:
    """Tests for DynamicGridWorld environment."""

    def test_initialization(self):
        """Test that DynamicGridWorld initializes correctly."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
        )
        env = DynamicGridWorld(config)

        assert env.config.width == 5
        assert env.config.height == 5
        assert env.agent_position == (0, 0)
        assert env.step_count == 0
        assert len(env.obstacles) == 0

    def test_reset(self):
        """Test that reset returns initial state."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
        )
        env = DynamicGridWorld(config)
        env.reset()

        assert env.agent_position == (0, 0)
        assert env.step_count == 0
        assert len(env.obstacles) == 0

    def test_move_up(self):
        """Test UP action."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
        )
        env = DynamicGridWorld(config)
        env.reset()

        result = env.step(Action.UP)
        assert result.observation.agent_position == (0, 1)
        assert result.reward == -0.1

    def test_move_down(self):
        """Test DOWN action."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
        )
        env = DynamicGridWorld(config)
        env.reset()

        result = env.step(Action.DOWN)
        assert result.observation.agent_position == (0, 0)  # Can't go below 0
        assert result.reward == -0.1

    def test_move_left(self):
        """Test LEFT action."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
        )
        env = DynamicGridWorld(config)
        env.reset()

        result = env.step(Action.LEFT)
        assert result.observation.agent_position == (0, 0)  # Can't go left of 0
        assert result.reward == -0.1

    def test_move_right(self):
        """Test RIGHT action."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
        )
        env = DynamicGridWorld(config)
        env.reset()

        result = env.step(Action.RIGHT)
        assert result.observation.agent_position == (1, 0)
        assert result.reward == -0.1

    def test_obstacle_collision(self):
        """Test obstacle collision."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[(1, 0)],
        )
        env = DynamicGridWorld(config)
        env.reset()

        result = env.step(Action.RIGHT)
        assert result.reward == -5.0
        assert result.observation.agent_position == (0, 0)  # Stay in place

    def test_goal_reached(self):
        """Test reaching the goal."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
        )
        env = DynamicGridWorld(config)
        env.reset()

        # Move to goal
        for _ in range(4):
            env.step(Action.RIGHT)
        for _ in range(4):
            env.step(Action.UP)

        result = env.step(Action.INTERACT)
        assert result.reward == 10.0
        assert result.terminated is True

    def test_obstacle_movement_horizontal(self):
        """Test horizontal obstacle movement."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[(0, 0)],
            obstacle_movement_patterns={(0, 0): ObstacleMovementPattern.HORIZONTAL},
            movement_interval=5,
        )
        env = DynamicGridWorld(config)
        env.reset()

        # After 5 steps, obstacle should move
        for _ in range(5):
            env.step(Action.RIGHT)

        # Obstacle should have moved from (0,0) to (1,0)
        assert (1, 0) in env.obstacles
        assert (0, 0) not in env.obstacles

    def test_obstacle_movement_vertical(self):
        """Test vertical obstacle movement."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[(0, 0)],
            obstacle_movement_patterns={(0, 0): ObstacleMovementPattern.VERTICAL},
            movement_interval=5,
        )
        env = DynamicGridWorld(config)
        env.reset()

        # After 5 steps, obstacle should move
        for _ in range(5):
            env.step(Action.RIGHT)

        # Obstacle should have moved from (0,0) to (0,1)
        assert (0, 1) in env.obstacles
        assert (0, 0) not in env.obstacles

    def test_obstacle_movement_random(self):
        """Test random obstacle movement."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[(0, 0)],
            obstacle_movement_patterns={(0, 0): ObstacleMovementPattern.RANDOM},
            movement_interval=5,
        )
        env = DynamicGridWorld(config)
        env.reset()

        # After 5 steps, obstacle should move
        for _ in range(5):
            env.step(Action.RIGHT)

        # Obstacle should have moved to a new position
        assert len(env.obstacles) == 1
        assert (0, 0) not in env.obstacles

    def test_truncation(self):
        """Test episode truncation after max steps."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[],
            max_steps=10,
        )
        env = DynamicGridWorld(config)
        env.reset()

        # Run 10 steps without reaching goal
        for _ in range(10):
            result = env.step(Action.RIGHT)
            if result.terminated:
                break

        assert result.truncated is True

    def test_render(self):
        """Test grid rendering."""
        config = DynamicGridConfig(
            width=5,
            height=5,
            goal_position=(4, 4),
            seed=42,
            initial_obstacles=[(2, 2)],
        )
        env = DynamicGridWorld(config)
        env.reset()

        rendered = env.render()
        assert "A" in rendered
        assert "G" in rendered
        assert "X" in rendered
