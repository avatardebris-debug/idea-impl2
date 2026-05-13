"""Tests for SalaryCap model."""

import pytest
from ffo.models.salary_cap import SalaryCap, SalaryCapError
from ffo.models.player import Player


@pytest.fixture
def cap():
    return SalaryCap(cap_limit=100000000)


@pytest.fixture
def player_a():
    return Player(name="A", position="FWD", overall_rating=80, age=28,
                  contract_length=3, salary=10000000, value=50000000)


@pytest.fixture
def player_b():
    return Player(name="B", position="MID", overall_rating=75, age=30,
                  contract_length=2, salary=15000000, value=40000000)


class TestSalaryCapCreation:
    """Tests for SalaryCap initialization."""

    def test_create_cap(self, cap):
        assert cap.cap_limit == 100000000
        assert cap.current_usage == 0
        assert cap.remaining == 100000000

    def test_create_cap_zero(self):
        c = SalaryCap(cap_limit=0)
        assert c.cap_limit == 0
        assert c.current_usage == 0

    def test_create_cap_negative(self):
        with pytest.raises(ValueError, match="cap_limit must be non-negative"):
            SalaryCap(cap_limit=-1000)

    def test_repr(self, cap):
        r = repr(cap)
        assert "100000000" in r
        assert "SalaryCap" in r


class TestCanAfford:
    """Tests for the can_afford method."""

    def test_can_afford_exact(self, cap, player_a):
        assert cap.can_afford(player_a) is True

    def test_can_afford_under(self, cap, player_a):
        assert cap.can_afford(player_a) is True

    def test_can_afford_over(self, cap, player_a):
        player_expensive = Player(name="E", position="FWD", overall_rating=90, age=25,
                                  contract_length=5, salary=101000000, value=200000000)
        assert cap.can_afford(player_expensive) is False

    def test_can_afford_zero_salary(self, cap):
        player_zero = Player(name="Z", position="GK", overall_rating=50, age=25,
                             contract_length=1, salary=0, value=10000000)
        assert cap.can_afford(player_zero) is True

    def test_can_afford_zero_cap(self):
        zero_cap = SalaryCap(cap_limit=0)
        player_any = Player(name="A", position="FWD", overall_rating=80, age=28,
                            contract_length=3, salary=10000000, value=50000000)
        assert zero_cap.can_afford(player_any) is False

    def test_can_afford_zero_cap_zero_salary(self):
        zero_cap = SalaryCap(cap_limit=0)
        player_zero = Player(name="Z", position="GK", overall_rating=50, age=25,
                             contract_length=1, salary=0, value=10000000)
        assert zero_cap.can_afford(player_zero) is True


class TestAddPlayer:
    """Tests for the add_player method."""

    def test_add_player_success(self, cap, player_a):
        cap.add_player(player_a)
        assert cap.current_usage == 10000000
        assert cap.remaining == 90000000

    def test_add_player_multiple(self, cap, player_a, player_b):
        cap.add_player(player_a)
        cap.add_player(player_b)
        assert cap.current_usage == 25000000
        assert cap.remaining == 75000000

    def test_add_player_raises_on_over_cap(self, cap, player_a):
        cap.add_player(player_a)
        player_expensive = Player(name="E", position="FWD", overall_rating=90, age=25,
                                  contract_length=5, salary=101000000, value=200000000)
        with pytest.raises(SalaryCapError, match="would exceed"):
            cap.add_player(player_expensive)

    def test_add_player_zero_salary(self, cap):
        player_zero = Player(name="Z", position="GK", overall_rating=50, age=25,
                             contract_length=1, salary=0, value=10000000)
        cap.add_player(player_zero)
        assert cap.current_usage == 0
        assert cap.remaining == 100000000

    def test_add_player_zero_cap(self):
        zero_cap = SalaryCap(cap_limit=0)
        player_any = Player(name="A", position="FWD", overall_rating=80, age=28,
                            contract_length=3, salary=10000000, value=50000000)
        with pytest.raises(SalaryCapError, match="would exceed"):
            zero_cap.add_player(player_any)


class TestRemovePlayer:
    """Tests for the remove_player method."""

    def test_remove_player(self, cap, player_a):
        cap.add_player(player_a)
        cap.remove_player(player_a)
        assert cap.current_usage == 0
        assert cap.remaining == 100000000

    def test_remove_player_not_in_cap(self, cap, player_a):
        with pytest.raises(SalaryCapError, match="not found"):
            cap.remove_player(player_a)

    def test_remove_player_multiple(self, cap, player_a, player_b):
        cap.add_player(player_a)
        cap.add_player(player_b)
        cap.remove_player(player_a)
        assert cap.current_usage == 15000000
        assert cap.remaining == 85000000

    def test_remove_player_zero_salary(self, cap):
        player_zero = Player(name="Z", position="GK", overall_rating=50, age=25,
                             contract_length=1, salary=0, value=10000000)
        cap.add_player(player_zero)
        cap.remove_player(player_zero)
        assert cap.current_usage == 0


class TestReset:
    """Tests for the reset method."""

    def test_reset(self, cap, player_a):
        cap.add_player(player_a)
        cap.reset()
        assert cap.current_usage == 0
        assert cap.remaining == 100000000

    def test_reset_empty(self, cap):
        cap.reset()
        assert cap.current_usage == 0


class TestStr:
    """Tests for string representation."""

    def test_str(self, cap, player_a):
        cap.add_player(player_a)
        s = str(cap)
        assert "100000000" in s
        assert "10000000" in s
        assert "90000000" in s
