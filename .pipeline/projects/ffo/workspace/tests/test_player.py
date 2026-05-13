"""Tests for Player and FreeAgent data models."""

import pytest
from ffo.models.player import Player, FreeAgent


class TestPlayer:
    """Tests for the Player dataclass."""

    def test_create_player(self, sample_player):
        assert sample_player.name == "Test Player"
        assert sample_player.position == "FWD"
        assert sample_player.overall_rating == 80.0
        assert sample_player.age == 28
        assert sample_player.contract_length == 3
        assert sample_player.salary == 10000000
        assert sample_player.value == 50000000

    def test_value_per_salary(self, sample_player):
        assert sample_player.value_per_salary == pytest.approx(5.0)

    def test_value_per_salary_zero_salary(self):
        p = Player(name="Z", position="GK", overall_rating=50, age=25,
                   contract_length=1, salary=0, value=10000000)
        assert p.value_per_salary == float("inf")

    def test_value_per_salary_negative_salary(self):
        p = Player(name="Z", position="GK", overall_rating=50, age=25,
                   contract_length=1, salary=-1000, value=10000000)
        assert p.value_per_salary == float("inf")

    def test_value_per_dollar_alias(self, sample_player):
        assert sample_player.value_per_dollar == sample_player.value_per_salary

    def test_to_dict(self, sample_player):
        d = sample_player.to_dict()
        assert d["name"] == "Test Player"
        assert d["salary"] == 10000000
        assert isinstance(d, dict)

    def test_from_dict(self):
        data = {"name": "FromDict", "position": "DEF", "overall_rating": 75.0,
                "age": 30, "contract_length": 2, "salary": 7000000, "value": 35000000}
        p = Player.from_dict(data)
        assert p.name == "FromDict"
        assert p.salary == 7000000

    def test_repr(self, sample_player):
        r = repr(sample_player)
        assert "Test Player" in r
        assert "Player(" in r

    def test_repr_empty_name(self):
        p = Player(name="", position="GK", overall_rating=50, age=25,
                   contract_length=1, salary=5000000, value=10000000)
        r = repr(p)
        assert "Player(" in r

    def test_comparison(self):
        p1 = Player(name="A", position="GK", overall_rating=50, age=25,
                    contract_length=1, salary=5000000, value=10000000)  # 2.0
        p2 = Player(name="B", position="GK", overall_rating=50, age=25,
                    contract_length=1, salary=10000000, value=10000000)  # 1.0
        assert p1 < p2  # p1 has higher value_per_salary
        assert (p1 > p2) is False
        assert (p1 >= p2) is False
        assert (p1 <= p2) is True

    def test_equality(self):
        p1 = Player(name="A", position="GK", overall_rating=50, age=25,
                    contract_length=1, salary=5000000, value=10000000)
        p2 = Player(name="A", position="DEF", overall_rating=60, age=30,
                    contract_length=2, salary=5000000, value=20000000)
        assert p1 == p2  # equality is by name and salary

    def test_equality_different_name(self):
        p1 = Player(name="A", position="GK", overall_rating=50, age=25,
                    contract_length=1, salary=5000000, value=10000000)
        p2 = Player(name="B", position="GK", overall_rating=50, age=25,
                    contract_length=1, salary=5000000, value=10000000)
        assert p1 != p2

    def test_equality_different_salary(self):
        p1 = Player(name="A", position="GK", overall_rating=50, age=25,
                    contract_length=1, salary=5000000, value=10000000)
        p2 = Player(name="A", position="GK", overall_rating=50, age=25,
                    contract_length=1, salary=6000000, value=10000000)
        assert p1 != p2

    def test_equality_non_player(self):
        p = Player(name="A", position="GK", overall_rating=50, age=25,
                   contract_length=1, salary=5000000, value=10000000)
        assert p != "A"
        assert p != 5


class TestFreeAgent:
    """Tests for the FreeAgent dataclass."""

    def test_create_free_agent(self, sample_free_agent):
        assert sample_free_agent.name == "Test Agent"
        assert sample_free_agent.available is True
        assert sample_free_agent.agent_name == "SuperAgent"
        assert sample_free_agent.preferred_positions == ["MID", "FWD"]

    def test_free_agent_defaults(self):
        fa = FreeAgent(name="Default", position="FWD", overall_rating=80, age=25,
                       contract_length=3, salary=10000000, value=50000000)
        assert fa.available is True
        assert fa.agent_name is None
        assert fa.preferred_positions == []

    def test_free_agent_to_dict(self, sample_free_agent):
        d = sample_free_agent.to_dict()
        assert d["name"] == "Test Agent"
        assert d["available"] is True
        assert d["preferred_positions"] == ["MID", "FWD"]

    def test_free_agent_from_dict(self):
        data = {"name": "FA", "position": "DEF", "overall_rating": 75, "age": 28,
                "contract_length": 2, "salary": 8000000, "value": 40000000,
                "available": True, "agent_name": "AgentX", "preferred_positions": ["DEF"]}
        fa = FreeAgent.from_dict(data)
        assert fa.name == "FA"
        assert fa.agent_name == "AgentX"

    def test_free_agent_repr(self, sample_free_agent):
        r = repr(sample_free_agent)
        assert "Test Agent" in r
        assert "FreeAgent(" in r

    def test_free_agent_inherits_player(self):
        fa = FreeAgent(name="FA", position="FWD", overall_rating=80, age=25,
                       contract_length=3, salary=10000000, value=50000000)
        assert fa.value_per_salary == 5.0
        assert isinstance(fa, Player)

    def test_free_agent_available_false(self):
        fa = FreeAgent(name="Unavailable", position="FWD", overall_rating=80, age=25,
                       contract_length=3, salary=10000000, value=50000000, available=False)
        assert fa.available is False
