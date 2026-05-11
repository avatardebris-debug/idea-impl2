"""Tests for formation definitions."""

import pytest
from src.football_sim.formation import (
    create_formation,
    create_offensive_player,
    create_defensive_player,
    get_available_formations,
    create_formation_from_dict,
)
from src.football_sim.entities import Formation


class TestFormationCreation:
    """Test formation creation functions."""

    def test_create_i_formation(self):
        f = create_formation("i_formation", 20.0)
        assert f.name == "i_formation"
        assert f.line_of_scrimmage_x == 20.0
        assert f.total_players == 22
        assert f.is_complete is True
        assert len(f.offensive_players) == 11
        assert len(f.defensive_players) == 11

    def test_offensive_players_have_correct_team(self):
        f = create_formation("i_formation", 20.0)
        for p in f.offensive_players:
            assert p.team == "offense"

    def test_defensive_players_have_correct_team(self):
        f = create_formation("i_formation", 20.0)
        for p in f.defensive_players:
            assert p.team == "defense"

    def test_offensive_players_start_behind_los(self):
        f = create_formation("i_formation", 20.0)
        for p in f.offensive_players:
            assert p.x <= 20.0 + 5.0  # Max offset is 5 yards

    def test_defensive_players_start_at_or_ahead_of_los(self):
        f = create_formation("i_formation", 20.0)
        for p in f.defensive_players:
            assert p.x >= 20.0 - 5.0  # Min offset is -5 yards

    def test_players_have_speed(self):
        f = create_formation("i_formation", 20.0)
        for p in f.offensive_players + f.defensive_players:
            assert p.max_speed_yd_s > 0
            assert p.acceleration_rate > 0

    def test_players_have_agility(self):
        f = create_formation("i_formation", 20.0)
        for p in f.offensive_players + f.defensive_players:
            assert 0.0 < p.agility <= 1.0

    def test_players_have_strength(self):
        f = create_formation("i_formation", 20.0)
        for p in f.offensive_players + f.defensive_players:
            assert p.strength > 0

    def test_different_los_positions(self):
        f1 = create_formation("i_formation", 10.0)
        f2 = create_formation("i_formation", 30.0)
        # Players should be at different x positions
        assert f1.offensive_players[0].x != f2.offensive_players[0].x

    def test_offensive_player_offsets(self):
        f = create_formation("i_formation", 20.0)
        # QB should be furthest back (largest y offset)
        qb = next(p for p in f.offensive_players if p.name == "QB")
        assert qb.y > 26.665  # Above center line

    def test_defensive_linemen_close_to_los(self):
        f = create_formation("i_formation", 20.0)
        # DEs should be close to LOS
        de1 = next(p for p in f.defensive_players if p.name == "DE1")
        assert abs(de1.x - 20.0) <= 5.0

    def test_wide_receivers_far_out(self):
        f = create_formation("i_formation", 20.0)
        wr1 = next(p for p in f.offensive_players if p.name == "WR1")
        wr2 = next(p for p in f.offensive_players if p.name == "WR2")
        # WRs should be far from center (large y offset)
        assert abs(wr1.y - 26.665) > 10.0
        assert abs(wr2.y - 26.665) > 10.0

    def test_all_jersey_numbers_set(self):
        f = create_formation("i_formation", 20.0)
        for p in f.offensive_players + f.defensive_players:
            assert p.jersey_number > 0

    def test_all_player_ids_unique(self):
        f = create_formation("i_formation", 20.0)
        ids = [p.player_id for p in f.offensive_players + f.defensive_players]
        assert len(ids) == len(set(ids))


class TestFormationHelpers:
    """Test formation helper functions."""

    def test_get_available_formations(self):
        forms = get_available_formations()
        assert "i_formation" in forms

    def test_create_formation_from_dict(self):
        f = create_formation_from_dict({
            "formation_name": "i_formation",
            "line_of_scrimmage_x": 25.0,
        })
        assert f.name == "i_formation"
        assert f.line_of_scrimmage_x == 25.0
        assert f.is_complete is True

    def test_create_formation_from_dict_defaults(self):
        f = create_formation_from_dict({})
        assert f.name == "i_formation"
        assert f.line_of_scrimmage_x == 20.0

    def test_create_offensive_player(self):
        p = create_offensive_player(
            name="QB",
            jersey=12,
            max_speed_mph=10.0,
            agility=0.7,
            strength=0.9,
            offset_x=0.0,
            offset_y=7.0,
            line_of_scrimmage_x=20.0,
        )
        assert p.x == pytest.approx(20.0, abs=0.01)
        assert p.y == pytest.approx(33.665, abs=0.01)
        assert p.max_speed_yd_s == pytest.approx(10.0 * 0.488889, abs=0.001)
        assert p.team == "offense"

    def test_create_defensive_player(self):
        p = create_defensive_player(
            name="DE",
            jersey=97,
            max_speed_mph=8.0,
            agility=0.8,
            strength=1.5,
            offset_x=-3.5,
            offset_y=0.0,
            line_of_scrimmage_x=20.0,
        )
        assert p.x == pytest.approx(16.5, abs=0.01)
        assert p.y == pytest.approx(26.665, abs=0.01)
        assert p.team == "defense"
