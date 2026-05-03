"""Tests for MultiAgentGridWorld environment."""

import pytest

from gameagent.env.multi_agent_grid_world import (
    GameMode,
    MultiAgentConfig,
    MultiAgentGridWorld,
)
from gameagent.env.types import Action


class TestMultiAgentConfig:
    """Tests for MultiAgentConfig validation."""

    def test_initialization(self):
        """Test that MultiAgentConfig initializes correctly."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )

        assert config.width == 5
        assert config.height == 5
        assert config.num_agents == 2
        assert config.game_mode == GameMode.COOPERATIVE

    def test_invalid_num_agents_raises_error(self):
        """Test that less than 2 agents raises error."""
        with pytest.raises(ValueError, match="At least 2 agents required"):
            MultiAgentConfig(
                width=5,
                height=5,
                num_agents=1,
                goal_position=(4, 4),
                seed=42,
                obstacles=[],
            )

    def test_goal_out_of_bounds_raises_error(self):
        """Test that goal out of bounds raises error."""
        with pytest.raises(ValueError, match="out of bounds"):
            MultiAgentConfig(
                width=5,
                height=5,
                num_agents=2,
                goal_position=(10, 10),
                seed=42,
                obstacles=[],
            )

    def test_obstacle_overlaps_goal_raises_error(self):
        """Test that obstacle overlapping goal raises error."""
        with pytest.raises(ValueError, match="overlaps with goal"):
            MultiAgentConfig(
                width=5,
                height=5,
                num_agents=2,
                goal_position=(4, 4),
                seed=42,
                obstacles=[(4, 4)],
            )

    def test_duplicate_obstacles_raises_error(self):
        """Test that duplicate obstacles raises error."""
        with pytest.raises(ValueError, match="Duplicate obstacle positions"):
            MultiAgentConfig(
                width=5,
                height=5,
                num_agents=2,
                goal_position=(4, 4),
                seed=42,
                obstacles=[(1, 1), (1, 1)],
            )


class TestMultiAgentGridWorld:
    """Tests for MultiAgentGridWorld environment."""

    def test_initialization(self):
        """Test that MultiAgentGridWorld initializes correctly."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)

        assert env.config.width == 5
        assert env.config.height == 5
        assert env.config.num_agents == 2
        assert len(env.agent_positions) == 2
        assert env.step_count == 0

    def test_reset(self):
        """Test that reset returns initial state."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        obs_list, info = env.reset()

        assert len(obs_list) == 2
        assert env.agent_positions[0] != env.agent_positions[1]

    def test_move_up(self):
        """Test UP action for agent 0."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        results, _ = env.step([Action.UP, Action.RIGHT])
        assert results[0].observation.agent_position == (0, 1)
        assert results[0].reward == -0.1

    def test_move_down(self):
        """Test DOWN action for agent 0."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        results, _ = env.step([Action.DOWN, Action.RIGHT])
        assert results[0].observation.agent_position == (0, 0)  # Can't go below 0
        assert results[0].reward == -0.1

    def test_move_left(self):
        """Test LEFT action for agent 0."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        results, _ = env.step([Action.LEFT, Action.RIGHT])
        assert results[0].observation.agent_position == (0, 0)  # Can't go left of 0
        assert results[0].reward == -0.1

    def test_move_right(self):
        """Test RIGHT action for agent 0."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        results, _ = env.step([Action.RIGHT, Action.RIGHT])
        assert results[0].observation.agent_position == (1, 0)
        assert results[0].reward == -0.1

    def test_obstacle_collision(self):
        """Test obstacle collision."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[(1, 0)],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        results, _ = env.step([Action.RIGHT, Action.RIGHT])
        assert results[0].reward == -5.0
        assert results[0].observation.agent_position == (0, 0)  # Stay in place

    def test_agent_collision(self):
        """Test agent-agent collision."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        # Agent 0 starts at (0,0), Agent 1 starts at (0,1)
        # Move agent 0 UP to (0,1) where agent 1 is
        # Agent 1 stays at (0,1) with INTERACT
        # This causes a collision at (0,1)
        results, _ = env.step([Action.UP, Action.INTERACT])
        assert results[0].observation.agent_position == (0, 1)
        assert results[1].observation.agent_position == (0, 1)
        # Both should get collision penalty
        assert results[0].reward == -2.0
        assert results[1].reward == -2.0

    def test_goal_reached(self):
        """Test reaching the goal."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        # Move agent 0 to goal
        for _ in range(4):
            results, _ = env.step([Action.RIGHT, Action.RIGHT])
        for _ in range(4):
            results, _ = env.step([Action.UP, Action.UP])

        results, _ = env.step([Action.INTERACT, Action.INTERACT])
        assert results[0].reward == 10.0
        assert results[0].terminated is True

    def test_invalid_num_actions_raises_error(self):
        """Test that wrong number of actions raises error."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        with pytest.raises(ValueError, match="Number of actions"):
            env.step([Action.RIGHT])  # Only 1 action for 2 agents

    def test_truncation(self):
        """Test episode truncation after max steps."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[],
            game_mode=GameMode.COOPERATIVE,
            max_steps=10,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        # Run 10 steps without reaching goal
        for _ in range(10):
            results, _ = env.step([Action.RIGHT, Action.RIGHT])
            if results[0].terminated:
                break

        assert results[0].truncated is True

    def test_render(self):
        """Test grid rendering."""
        config = MultiAgentConfig(
            width=5,
            height=5,
            num_agents=2,
            goal_position=(4, 4),
            seed=42,
            obstacles=[(2, 2)],
            game_mode=GameMode.COOPERATIVE,
        )
        env = MultiAgentGridWorld(config)
        env.reset()

        rendered = env.render()
        assert "A" in rendered or "0" in rendered or "1" in rendered
        assert "G" in rendered
        assert "X" in rendered
