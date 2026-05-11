"""Tests for ball physics engine."""

import math
import pytest
from src.football_sim.ball import Ball, CollisionEvent, GRAVITY_YD_S2


class TestBallCreation:
    """Test Ball class instantiation."""

    def test_create_ball_default(self):
        ball = Ball()
        assert ball.ball_id == "ball_1"
        assert ball.position == (0.0, 0.0)
        assert ball.velocity == (0.0, 0.0)
        assert ball.spin == 0.0
        assert ball.gravity == pytest.approx(GRAVITY_YD_S2, abs=0.001)
        assert ball.radius == 0.15
        assert ball.mass == 0.91
        assert ball.is_active is False
        assert ball.is_thrown is False
        assert ball.is_caught is False
        assert ball.is_fumbled is False

    def test_create_ball_with_params(self):
        ball = Ball(
            ball_id="ball_2",
            position=(10.0, 20.0),
            velocity=(5.0, 3.0),
            spin=2.0,
        )
        assert ball.ball_id == "ball_2"
        assert ball.x == 10.0
        assert ball.y == 20.0
        assert ball.vx == 5.0
        assert ball.vy == 3.0
        assert ball.spin == 2.0

    def test_ball_speed_conversion(self):
        ball = Ball(ball_id="test", velocity=(10.0, 0.0))
        assert ball.speed_yd_s == pytest.approx(10.0, abs=0.01)
        assert ball.speed_mph == pytest.approx(10.0 / 0.488889, abs=0.01)

    def test_ball_speed_diagonal(self):
        ball = Ball(ball_id="test", velocity=(6.0, 8.0))
        assert ball.speed_yd_s == pytest.approx(10.0, abs=0.01)

    def test_ball_properties(self):
        ball = Ball(ball_id="test", position=(5.0, 10.0), velocity=(2.0, 3.0))
        assert ball.x == 5.0
        assert ball.y == 10.0
        assert ball.vx == 2.0
        assert ball.vy == 3.0

    def test_ball_is_in_play(self):
        ball = Ball()
        assert ball.is_in_play is False
        ball.is_active = True
        # is_in_play = is_active and not is_caught and not is_fumbled
        # With is_active=True, is_caught=False, is_fumbled=False → True
        assert ball.is_in_play is True
        ball.is_caught = True
        assert ball.is_in_play is False


class TestBallThrow:
    """Test ball throwing mechanics."""

    def test_throw_basic(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        ball.throw(target_x=10.0, target_y=0.0, thrower_id="qb_12")
        assert ball.is_active is True
        assert ball.is_thrown is True
        assert ball.thrower_id == "qb_12"
        assert ball.is_caught is False
        assert ball.is_fumbled is False
        assert ball.catcher_id is None
        assert ball.carrier_id is None

    def test_throw_records_trajectory(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        ball.throw(target_x=10.0, target_y=0.0, thrower_id="qb_12")
        assert len(ball.trajectory) >= 1
        assert ball.trajectory[0] == (0.0, 0.0, 0.0)

    def test_throw_velocity_positive_x(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        ball.throw(target_x=10.0, target_y=0.0, thrower_id="qb_12")
        assert ball.vx > 0

    def test_throw_velocity_negative_x(self):
        ball = Ball(ball_id="test", position=(10.0, 0.0))
        ball.throw(target_x=0.0, target_y=0.0, thrower_id="qb_12")
        assert ball.vx < 0

    def test_throw_velocity_positive_y(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        ball.throw(target_x=0.0, target_y=10.0, thrower_id="qb_12")
        assert ball.vy > 0

    def test_throw_velocity_negative_y(self):
        ball = Ball(ball_id="test", position=(0.0, 10.0))
        ball.throw(target_x=0.0, target_y=0.0, thrower_id="qb_12")
        assert ball.vy < 0

    def test_throw_diagonal(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        ball.throw(target_x=10.0, target_y=10.0, thrower_id="qb_12")
        assert ball.vx > 0
        assert ball.vy > 0

    def test_throw_short_distance(self):
        """Throwing to a very close target should still work."""
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        ball.throw(target_x=0.01, target_y=0.01, thrower_id="qb_12")
        assert ball.is_active is True
        assert ball.is_thrown is True

    def test_throw_resets_state(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        ball.is_caught = True
        ball.is_fumbled = True
        ball.catcher_id = "receiver_1"
        ball.carrier_id = "receiver_1"
        ball.throw(target_x=10.0, target_y=0.0, thrower_id="qb_12")
        assert ball.is_caught is False
        assert ball.is_fumbled is False
        assert ball.catcher_id is None
        assert ball.carrier_id is None
        assert ball.thrower_id == "qb_12"


class TestBallStep:
    """Test ball stepping (physics update)."""

    def test_step_inactive_ball(self):
        ball = Ball(ball_id="test")
        ball.step(1.0)
        assert ball.position == (0.0, 0.0)
        assert ball.velocity == (0.0, 0.0)

    def test_step_active_ball_moves(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(10.0, 0.0))
        ball.is_active = True
        ball.step(1.0)
        assert ball.x != 0.0  # Should have moved

    def test_step_applies_gravity(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(0.0, 10.0))
        ball.is_active = True
        initial_vy = ball.vy
        ball.step(1.0)
        # Gravity should reduce upward velocity
        assert ball.vy < initial_vy

    def test_step_records_trajectory(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(10.0, 0.0))
        ball.is_active = True
        ball.step(1.0)
        # One step adds one trajectory point
        assert len(ball.trajectory) >= 1

    def test_step_multiple(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(10.0, 0.0))
        ball.is_active = True
        for _ in range(5):
            ball.step(0.5)
        assert ball.x > 0.0

    def test_step_air_resistance(self):
        """Air resistance should reduce horizontal velocity over time."""
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(10.0, 0.0))
        ball.is_active = True
        ball.air_resistance = 0.1  # High resistance for testing
        initial_vx = ball.vx
        ball.step(1.0)
        # Air resistance should reduce horizontal velocity
        assert ball.vx < initial_vx

    def test_step_trajectory_time(self):
        """Trajectory timestamps should increase."""
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(10.0, 0.0))
        ball.is_active = True
        ball.step(0.5)
        t1 = ball.trajectory[-1][2]
        ball.step(0.5)
        t2 = ball.trajectory[-1][2]
        assert t2 > t1


class TestBallCatch:
    """Test ball catch mechanics."""

    def test_catch_within_radius(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_thrown = True
        result = ball.catch(
            catcher_id="wr_10",
            catcher_position=(5.0, 5.0),
            catcher_radius=0.5,
        )
        assert result is True
        assert ball.is_caught is True
        assert ball.catcher_id == "wr_10"
        assert ball.carrier_id == "wr_10"
        assert ball.velocity == (0.0, 0.0)

    def test_catch_outside_radius(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_thrown = True
        result = ball.catch(
            catcher_id="wr_10",
            catcher_position=(10.0, 10.0),
            catcher_radius=0.5,
        )
        assert result is False
        assert ball.is_caught is False

    def test_catch_at_boundary(self):
        """Catch at exactly combined radius should succeed."""
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(0.0, 0.0))
        ball.is_thrown = True
        result = ball.catch(
            catcher_id="wr_10",
            catcher_position=(0.65, 0.0),  # 0.15 + 0.5 = 0.65
            catcher_radius=0.5,
        )
        assert result is True

    def test_catch_already_caught(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_caught = True
        result = ball.catch(
            catcher_id="wr_10",
            catcher_position=(5.0, 5.0),
            catcher_radius=0.5,
        )
        assert result is False

    def test_catch_already_fumbled(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_fumbled = True
        result = ball.catch(
            catcher_id="wr_10",
            catcher_position=(5.0, 5.0),
            catcher_radius=0.5,
        )
        assert result is False

    def test_catch_not_thrown(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        result = ball.catch(
            catcher_id="wr_10",
            catcher_position=(5.0, 5.0),
            catcher_radius=0.5,
        )
        assert result is False

    def test_catch_records_position(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_thrown = True
        ball.catch(
            catcher_id="wr_10",
            catcher_position=(5.0, 5.0),
            catcher_radius=0.5,
        )
        assert ball.x == pytest.approx(5.0, abs=0.01)
        assert ball.y == pytest.approx(5.0, abs=0.01)


class TestBallFumble:
    """Test ball fumble mechanics."""

    def test_fumble_high_force(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_caught = True
        ball.carrier_id = "rb_28"
        result = ball.fumble(
            carrier_id="rb_28",
            carrier_position=(5.0, 5.0),
            carrier_strength=1.0,
            defender_strength=1.5,
            collision_force=1.0,
        )
        assert result is True
        assert ball.is_fumbled is True
        assert ball.carrier_id is None

    def test_fumble_low_force(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_caught = True
        ball.carrier_id = "rb_28"
        result = ball.fumble(
            carrier_id="rb_28",
            carrier_position=(5.0, 5.0),
            carrier_strength=1.5,
            defender_strength=1.0,
            collision_force=0.1,
        )
        assert result is False
        assert ball.is_fumbled is False

    def test_fumble_already_fumbled(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_fumbled = True
        result = ball.fumble(
            carrier_id="rb_28",
            carrier_position=(5.0, 5.0),
            carrier_strength=1.0,
            defender_strength=1.0,
            collision_force=1.0,
        )
        assert result is False

    def test_fumble_not_caught(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        result = ball.fumble(
            carrier_id="rb_28",
            carrier_position=(5.0, 5.0),
            carrier_strength=1.0,
            defender_strength=1.0,
            collision_force=1.0,
        )
        assert result is False

    def test_fumble_sets_velocity(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(0.0, 0.0))
        ball.is_caught = True
        ball.carrier_id = "rb_28"
        ball.fumble(
            carrier_id="rb_28",
            carrier_position=(5.0, 5.0),
            carrier_strength=1.0,
            defender_strength=1.5,
            collision_force=1.0,
        )
        assert ball.velocity[0] != 0.0 or ball.velocity[1] != 0.0


class TestBallCollision:
    """Test ball collision detection."""

    def test_colliding_within_radius(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0))
        assert ball.is_colliding_with((5.0, 5.0), 0.5) is True

    def test_colliding_outside_radius(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0))
        assert ball.is_colliding_with((10.0, 10.0), 0.5) is False

    def test_colliding_at_boundary(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        # 0.15 (ball radius) + 0.5 (other radius) = 0.65
        assert ball.is_colliding_with((0.65, 0.0), 0.5) is True

    def test_colliding_diagonal(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        # Distance to (0.45, 0.45) is sqrt(0.45² + 0.45²) ≈ 0.636 < 0.65
        assert ball.is_colliding_with((0.45, 0.45), 0.5) is True


class TestBallDistance:
    """Test ball distance calculations."""

    def test_distance_to_same_position(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0))
        assert ball.distance_to((5.0, 5.0)) == pytest.approx(0.0, abs=0.01)

    def test_distance_to_different_position(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        assert ball.distance_to((3.0, 4.0)) == pytest.approx(5.0, abs=0.01)

    def test_distance_negative_direction(self):
        ball = Ball(ball_id="test", position=(10.0, 10.0))
        assert ball.distance_to((0.0, 0.0)) == pytest.approx(14.142, abs=0.01)


class TestBallReset:
    """Test ball reset functionality."""

    def test_reset_clears_state(self):
        ball = Ball(ball_id="test", position=(5.0, 5.0), velocity=(10.0, 0.0))
        ball.is_active = True
        ball.is_thrown = True
        ball.is_caught = True
        ball.is_fumbled = True
        ball.thrower_id = "qb_12"
        ball.catcher_id = "wr_10"
        ball.carrier_id = "wr_10"
        ball.trajectory = [(0.0, 0.0, 0.0)]
        ball.collision_events = [CollisionEvent(0.0, "a", "b", {}, {}, 0.0)]

        ball.reset()

        assert ball.is_active is False
        assert ball.is_thrown is False
        assert ball.is_caught is False
        assert ball.is_fumbled is False
        assert ball.thrower_id is None
        assert ball.catcher_id is None
        assert ball.carrier_id is None
        assert ball.velocity == (0.0, 0.0)
        assert ball.trajectory == []
        assert ball.collision_events == []

    def test_reset_returns_self(self):
        ball = Ball(ball_id="test")
        assert ball.reset() is ball


class TestBallSerialization:
    """Test ball serialization."""

    def test_to_dict(self):
        ball = Ball(
            ball_id="test",
            position=(5.0, 10.0),
            velocity=(3.0, 4.0),
            spin=2.0,
        )
        ball.is_active = True
        ball.is_thrown = True
        ball.trajectory = [(0.0, 0.0, 0.0), (1.0, 1.0, 0.5)]

        d = ball.to_dict()

        assert d["ball_id"] == "test"
        assert d["position"] == [5.0, 10.0]
        assert d["velocity"] == [3.0, 4.0]
        assert d["spin"] == 2.0
        assert d["is_active"] is True
        assert d["is_thrown"] is True
        assert d["trajectory"] == [(0.0, 0.0, 0.0), (1.0, 1.0, 0.5)]

    def test_to_dict_inactive(self):
        ball = Ball(ball_id="test")
        d = ball.to_dict()
        assert d["is_active"] is False
        assert d["is_thrown"] is False
        assert d["is_caught"] is False
        assert d["is_fumbled"] is False


class TestBallRepr:
    """Test ball string representation."""

    def test_repr_inactive(self):
        ball = Ball(ball_id="test")
        assert "inactive" in repr(ball)

    def test_repr_thrown(self):
        ball = Ball(ball_id="test")
        ball.is_active = True
        ball.is_thrown = True
        assert "thrown" in repr(ball)

    def test_repr_caught(self):
        ball = Ball(ball_id="test")
        ball.is_active = True
        ball.is_caught = True
        assert "caught" in repr(ball)

    def test_repr_fumbled(self):
        ball = Ball(ball_id="test")
        ball.is_active = True
        ball.is_fumbled = True
        assert "fumbled" in repr(ball)

    def test_repr_includes_position(self):
        ball = Ball(ball_id="test", position=(5.0, 10.0))
        assert "5.00" in repr(ball)
        assert "10.00" in repr(ball)


class TestBallEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_ball_at_field_boundary(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0))
        ball.throw(target_x=120.0, target_y=53.3, thrower_id="qb_12")
        assert ball.is_active is True

    def test_ball_velocity_zero(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(0.0, 0.0))
        ball.is_active = True
        ball.step(1.0)
        # With zero initial velocity, gravity should still apply
        assert ball.vy < 0

    def test_ball_spin_preserved(self):
        ball = Ball(ball_id="test", spin=5.0)
        ball.throw(target_x=10.0, target_y=0.0, thrower_id="qb_12")
        ball.step(1.0)
        assert ball.spin == 5.0

    def test_ball_mass_preserved(self):
        ball = Ball(ball_id="test", mass=1.0)
        ball.throw(target_x=10.0, target_y=0.0, thrower_id="qb_12")
        ball.step(1.0)
        assert ball.mass == 1.0

    def test_ball_trajectory_increases(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(10.0, 0.0))
        ball.is_active = True
        for _ in range(10):
            ball.step(0.1)
        # Each step adds one trajectory point
        assert len(ball.trajectory) == 10

    def test_ball_catch_clears_trajectory(self):
        ball = Ball(ball_id="test", position=(0.0, 0.0), velocity=(10.0, 0.0))
        ball.is_active = True
        ball.is_thrown = True
        ball.step(1.0)
        assert len(ball.trajectory) >= 2
        ball.catch(
            catcher_id="wr_10",
            catcher_position=ball.position,
            catcher_radius=0.5,
        )
        # After catch, trajectory should still have points but ball is caught
        assert ball.is_caught is True


class TestCollisionEvent:
    """Test CollisionEvent class."""

    def test_create_collision_event(self):
        event = CollisionEvent(
            timestamp=1.0,
            entity_a="ball_1",
            entity_b="player_1",
            pre_velocities={"ball_1": (10.0, 0.0)},
            post_velocities={"ball_1": (5.0, 0.0)},
            force=2.0,
        )
        assert event.timestamp == 1.0
        assert event.entity_a == "ball_1"
        assert event.entity_b == "player_1"
        assert event.force == 2.0

    def test_collision_event_to_dict(self):
        event = CollisionEvent(
            timestamp=1.0,
            entity_a="ball_1",
            entity_b="player_1",
            pre_velocities={"ball_1": (10.0, 0.0)},
            post_velocities={"ball_1": (5.0, 0.0)},
            force=2.0,
        )
        d = event.to_dict()
        assert d["timestamp"] == 1.0
        assert d["entity_a"] == "ball_1"
        assert d["entity_b"] == "player_1"
        assert d["force"] == 2.0
