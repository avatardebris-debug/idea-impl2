"""Tests for field geometry module."""

import pytest
import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from football_sim.config import Config
from football_sim.field import Field, YardLine, HashMark, Endzone


class TestConfig:
    """Tests for the Config class."""

    def test_nfl_config(self):
        config = Config(field_type="nfl")
        assert config.field_type == "nfl"
        assert config.field_length_yards == 120
        assert config.field_width_yards == 53.33
        assert config.endzone_depth_yards == 10
        assert config.field_of_play_yards == 100

    def test_college_config(self):
        config = Config(field_type="college")
        assert config.field_type == "college"
        assert config.field_length_yards == 120
        assert config.field_width_yards == 53.33
        assert config.endzone_depth_yards == 10
        assert config.field_of_play_yards == 100

    def test_high_school_config(self):
        config = Config(field_type="high_school")
        assert config.field_type == "high_school"
        assert config.field_length_yards == 110
        assert config.field_width_yards == 48.0
        assert config.endzone_depth_yards == 5
        assert config.field_of_play_yards == 100

    def test_to_dict(self):
        config = Config(field_type="nfl")
        d = config.to_dict()
        assert d["field_type"] == "nfl"
        assert d["field_length_yards"] == 120

    def test_from_dict(self):
        config = Config.from_dict({"field_type": "college", "field_length_yards": 120})
        assert config.field_type == "college"
        assert config.field_length_yards == 120

    def test_get_available_types(self):
        types = Config.get_available_types()
        assert "nfl" in types
        assert "college" in types
        assert "high_school" in types


class TestField:
    """Tests for the Field class."""

    def test_nfl_field_length(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.length_yards == 120

    def test_college_field_length(self):
        config = Config(field_type="college")
        field = Field(config)
        assert field.length_yards == 120

    def test_high_school_field_length(self):
        config = Config(field_type="high_school")
        field = Field(config)
        assert field.length_yards == 110

    def test_field_width_nfl(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.width_yards == 53.33

    def test_field_width_high_school(self):
        config = Config(field_type="high_school")
        field = Field(config)
        assert field.width_yards == 48.0

    def test_endzone_depth_nfl(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.endzone_depth_yards == 10

    def test_endzone_depth_high_school(self):
        config = Config(field_type="high_school")
        field = Field(config)
        assert field.endzone_depth_yards == 5

    def test_field_of_play_yards(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.field_of_play_yards == 100

    def test_yard_lines_count(self):
        config = Config(field_type="nfl")
        field = Field(config)
        # 0 through 100 = 101 yard lines
        assert len(field.yard_lines) == 101

    def test_yard_line_positions(self):
        config = Config(field_type="nfl")
        field = Field(config)
        # Yard line 0 should be at x=0
        assert field.yard_lines[0].yard == 0
        assert field.yard_lines[0].x == 0.0
        # Yard line 50 should be at x=50
        assert field.yard_lines[50].yard == 50
        assert field.yard_lines[50].x == 50.0
        # Yard line 100 should be at x=100
        assert field.yard_lines[100].yard == 100
        assert field.yard_lines[100].x == 100.0

    def test_endzones(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert len(field.endzones) == 2
        # Home endzone: 0 to 10
        assert field.home_endzone.start == 0.0
        assert field.home_endzone.end == 10.0
        assert field.home_endzone.team == "home"
        # Away endzone: 110 to 120
        assert field.away_endzone.start == 110.0
        assert field.away_endzone.end == 120.0
        assert field.away_endzone.team == "away"

    def test_is_in_field_of_play(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.is_in_field_of_play(0.0) is True
        assert field.is_in_field_of_play(50.0) is True
        assert field.is_in_field_of_play(100.0) is True
        assert field.is_in_field_of_play(10.0) is True
        assert field.is_in_field_of_play(105.0) is False
        assert field.is_in_field_of_play(-1.0) is False

    def test_is_in_endzone(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.is_in_endzone(5.0) == "home"
        assert field.is_in_endzone(115.0) == "away"
        assert field.is_in_endzone(50.0) is None
        assert field.is_in_endzone(0.0) == "home"
        assert field.is_in_endzone(120.0) == "away"

    def test_is_in_bounds(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.is_in_bounds(50.0, 26.665) is True
        assert field.is_in_bounds(0.0, 0.0) is True
        assert field.is_in_bounds(120.0, 53.33) is True
        assert field.is_in_bounds(-1.0, 0.0) is False
        assert field.is_in_bounds(0.0, -1.0) is False
        assert field.is_in_bounds(121.0, 0.0) is False

    def test_yards_to_line(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.yards_to_line(0.0) == 0
        assert field.yards_to_line(25.0) == 25
        assert field.yards_to_line(50.0) == 50
        assert field.yards_to_line(100.0) == 100
        assert field.yards_to_line(105.0) == 100
        assert field.yards_to_line(-5.0) == 0

    def test_get_field_position_string(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert field.get_field_position_string(0.0) == "Own Goal Line"
        assert field.get_field_position_string(100.0) == "Opp Goal Line"
        assert field.get_field_position_string(25.0) == "Own 25"
        assert field.get_field_position_string(75.0) == "Opp 25"
        assert field.get_field_position_string(50.0) == "Own 50"

    def test_hash_marks_exist(self):
        config = Config(field_type="nfl")
        field = Field(config)
        assert len(field.hash_marks) > 0
        # Check hash marks at yard 10
        hm_at_10 = field.get_hash_marks_at_yard(10)
        assert len(hm_at_10) == 2  # left and right hash marks

    def test_default_field_is_nfl(self):
        field = Field()
        assert field.length_yards == 120
        assert field.config.field_type == "nfl"

    def test_hs_field_dimensions(self):
        config = Config(field_type="high_school")
        field = Field(config)
        assert field.length_yards == 110
        assert field.endzone_depth_yards == 5
        # Away endzone: 105 to 110
        assert field.away_endzone.start == 105.0
        assert field.away_endzone.end == 110.0

    def test_hs_yard_lines(self):
        config = Config(field_type="high_school")
        field = Field(config)
        assert len(field.yard_lines) == 101  # 0 through 100

    def test_hs_field_of_play(self):
        config = Config(field_type="high_school")
        field = Field(config)
        assert field.field_of_play_yards == 100
        assert field.is_in_field_of_play(100.0) is True
        assert field.is_in_field_of_play(105.0) is False
