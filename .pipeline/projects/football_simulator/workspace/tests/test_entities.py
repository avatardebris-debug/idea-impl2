"""Tests for Player entity physics engine."""

import math
import pytest
from src.football_sim.entities import Player, Formation


class TestPlayerCreation:
    """Test Player class instantiation."""

    def test_create_player_default(self):
        player = Player(player_id="test_1")
        assert player.player_id == "test_1"
        assert player.position == (0.0, 0.0)
        assert player.velocity == (0.0, 0.0)
        assert player.speed_yd_s == 0.0
        assert player.speed_mph == pytest.approx(0.0, abs=0.01)
        assert player.team == "offense"
        assert player.radius == 0.5

    def test_create_player_with_mph(self):
        player = Player.from_mph("qb_12", 10.0)
        assert player.max_speed_yd_s == pytest.approx(10.0 * 0.488889, abs=0.001)
        # speed_mph is current speed (0 since not moving), not max speed
        assert player.speed_mph == pytest.approx(0.0, abs=0.01)

    def test_player_speed_conversion(self):
        """Test mph to yd/s conversion."""
        player = Player.from_mph("test", 10.0)
        # 10 mph = 4.88889 yd/s
        assert player.max_speed_yd_s == pytest.approx(4.88889, abs=0.001)

    def test_player_properties(self):
        player = Player(player_id="test", position=(5.0, 10.0), velocity=(2.0, 3.0))
        assert player.x == 5.0
        assert player.y == 10.0
        assert player.vx == 2.0
        assert player.vy == 3.0
        assert player.speed_yd_s == pytest.approx(math.sqrt(13.0), abs=0.01)


class TestPlayerMovement:
    """Test Player movement and physics."""

    def test_step_forward(self):
        player = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(10.0, 0.0),  # 10 yd/s along x
        )
        player.step(1.0)  # 1 second
        assert player.x == pytest.approx(10.0, abs=0.01)
        assert player.y == pytest.approx(0.0, abs=0.01)

    def test_step_diagonal(self):
        player = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(6.0, 8.0),  # 10 yd/s diagonal
        )
        player.step(1.0)
        assert player.x == pytest.approx(6.0, abs=0.01)
        assert player.y == pytest.approx(8.0, abs=0.01)

    def test_step_multiple(self):
        player = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(10.0, 0.0),
        )
        for _ in range(5):
            player.step(0.5)
        assert player.x == pytest.approx(25.0, abs=0.01)

    def test_stop(self):
        player = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(10.0, 0.0),
        )
        player.stop()
        assert player.vx == 0.0
        assert player.vy == 0.0
        assert player.speed_yd_s == 0.0

    def test_set_position(self):
        player = Player(player_id="test")
        player.set_position(15.0, 20.0)
        assert player.x == 15.0
        assert player.y == 20.0

    def test_set_velocity(self):
        player = Player(player_id="test")
        player.set_velocity(5.0, 5.0)
        assert player.vx == 5.0
        assert player.vy == 5.0
        assert player.speed_yd_s == pytest.approx(math.sqrt(50.0), abs=0.01)


class TestPlayerAcceleration:
    """Test Player acceleration toward targets."""

    def test_accelerate_toward_simple(self):
        player = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(0.0, 0.0),
            max_speed_yd_s=10.0,
            acceleration_rate=5.0,
            agility=1.0,
        )
        player.accelerate_toward(10.0, 0.0, 1.0)
        # After 1s at 5 yd/s², speed should be 5 yd/s
        assert player.speed_yd_s == pytest.approx(5.0, abs=0.1)
        assert player.vx == pytest.approx(5.0, abs=0.1)
        assert player.vy == pytest.approx(0.0, abs=0.1)

    def test_accelerate_capped_at_max_speed(self):
        player = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(0.0, 0.0),
            max_speed_yd_s=5.0,
            acceleration_rate=10.0,
            agility=1.0,
        )
        player.accelerate_toward(100.0, 0.0, 1.0)
        # Should be capped at max speed
        assert player.speed_yd_s == pytest.approx(5.0, abs=0.1)

    def test_accelerate_diagonal(self):
        player = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(0.0, 0.0),
            max_speed_yd_s=10.0,
            acceleration_rate=5.0,
            agility=1.0,
        )
        player.accelerate_toward(10.0, 10.0, 1.0)
        # Speed should be 5 yd/s in diagonal direction
        assert player.speed_yd_s == pytest.approx(5.0, abs=0.1)
        # Direction should be 45 degrees
        expected_vx = 5.0 / math.sqrt(2)
        expected_vy = 5.0 / math.sqrt(2)
        assert player.vx == pytest.approx(expected_vx, abs=0.1)
        assert player.vy == pytest.approx(expected_vy, abs=0.1)

    def test_agility_reduces_turning(self):
        """Lower agility should reduce effective acceleration when turning."""
        player_high = Player(
            player_id="high_agi",
            position=(0.0, 0.0),
            velocity=(10.0, 0.0),  # Already moving along +x
            max_speed_yd_s=20.0,
            acceleration_rate=10.0,
            agility=1.0,
        )
        player_low = Player(
            player_id="low_agi",
            position=(0.0, 0.0),
            velocity=(10.0, 0.0),  # Already moving along +x
            max_speed_yd_s=20.0,
            acceleration_rate=10.0,
            agility=0.3,
        )

        # Both accelerate toward a target 90 degrees from current heading
        # Use dt=0.5 so desired_speed = min(20, 5) = 5, which is less than current speed
        # This means the cap doesn't interfere with the comparison
        player_high.accelerate_toward(0.0, 10.0, 0.5)
        player_low.accelerate_toward(0.0, 10.0, 0.5)

        # High agility player should have higher speed after turn
        assert player_high.speed_yd_s > player_low.speed_yd_s

    def test_deterministic_acceleration(self):
        """Same inputs should produce same outputs."""
        p1 = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(0.0, 0.0),
            max_speed_yd_s=10.0,
            acceleration_rate=5.0,
            agility=0.8,
        )
        p2 = Player(
            player_id="test",
            position=(0.0, 0.0),
            velocity=(0.0, 0.0),
            max_speed_yd_s=10.0,
            acceleration_rate=5.0,
            agility=0.8,
        )
        p1.accelerate_toward(10.0, 5.0, 1.0)
        p2.accelerate_toward(10.0, 5.0, 1.0)
        assert p1.speed_yd_s == pytest.approx(p2.speed_yd_s, abs=0.001)
        assert p1.vx == pytest.approx(p2.vx, abs=0.001)
        assert p1.vy == pytest.approx(p2.vy, abs=0.001)


class TestPlayerCollision:
    """Test Player collision detection."""

    def test_colliding_adjacent(self):
        p1 = Player(player_id="p1", position=(0.0, 0.0), radius=0.5)
        p2 = Player(player_id="p2", position=(0.9, 0.0), radius=0.5)
        assert p1.is_colliding_with(p2) is True

    def test_not_colliding_far(self):
        p1 = Player(player_id="p1", position=(0.0, 0.0), radius=0.5)
        p2 = Player(player_id="p2", position=(2.0, 0.0), radius=0.5)
        assert p1.is_colliding_with(p2) is False

    def test_colliding_at_boundary(self):
        """Players touching at exactly combined radius should collide."""
        p1 = Player(player_id="p1", position=(0.0, 0.0), radius=0.5)
        p2 = Player(player_id="p2", position=(1.0, 0.0), radius=0.5)
        assert p1.is_colliding_with(p2) is True

    def test_distance_to(self):
        p1 = Player(player_id="p1", position=(0.0, 0.0))
        p2 = Player(player_id="p2", position=(3.0, 4.0))
        assert p1.distance_to(p2) == pytest.approx(5.0, abs=0.01)


class TestPlayerSerialization:
    """Test Player serialization."""

    def test_to_dict(self):
        player = Player(
            player_id="test",
            position=(5.0, 10.0),
            velocity=(2.0, 3.0),
            max_speed_yd_s=10.0,
            name="Test Player",
            team="defense",
            jersey_number=12,
        )
        d = player.to_dict()
        assert d["player_id"] == "test"
        assert d["position"] == [5.0, 10.0]
        assert d["velocity"] == [2.0, 3.0]
        assert d["name"] == "Test Player"
        assert d["team"] == "defense"
        assert d["jersey_number"] == 12

    def test_repr(self):
        player = Player(player_id="test", position=(5.0, 10.0), velocity=(2.0, 3.0))
        r = repr(player)
        assert "test" in r
        assert "5.0" in r


class TestFormation:
    """Test Formation class."""

    def test_create_empty_formation(self):
        f = Formation(name="test")
        assert f.name == "test"
        assert f.total_players == 0
        assert f.is_complete is False

    def test_add_players(self):
        f = Formation(name="test")
        for i in range(11):
            f.add_offensive_player(Player(player_id=f"off_{i}"))
        for i in range(11):
            f.add_defensive_player(Player(player_id=f"def_{i}"))
        assert f.total_players == 22
        assert f.is_complete is True

    def test_get_players_by_team(self):
        f = Formation(name="test")
        f.add_offensive_player(Player(player_id="off_1"))
        f.add_defensive_player(Player(player_id="def_1"))
        assert len(f.get_players_by_team("offense")) == 1
        assert len(f.get_players_by_team("defense")) == 1

    def test_step_all(self):
        f = Formation(name="test")
        p1 = Player(player_id="p1", position=(0.0, 0.0), velocity=(10.0, 0.0))
        p2 = Player(player_id="p2", position=(0.0, 0.0), velocity=(0.0, 10.0))
        f.add_offensive_player(p1)
        f.add_defensive_player(p2)
        f.step_all(1.0)
        assert p1.x == pytest.approx(10.0, abs=0.01)
        assert p2.y == pytest.approx(10.0, abs=0.01)

    def test_to_dict(self):
        f = Formation(name="test")
        f.add_offensive_player(Player(player_id="off_1"))
        f.add_defensive_player(Player(player_id="def_1"))
        d = f.to_dict()
        assert d["name"] == "test"
        assert len(d["offensive_players"]) == 1
        assert len(d["defensive_players"]) == 1

    def test_repr(self):
        f = Formation(name="test", line_of_scrimmage_x=20.0)
        r = repr(f)
        assert "test" in r
        assert "20.0" in r

