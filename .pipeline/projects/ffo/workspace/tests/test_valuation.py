"""Tests for valuation scoring."""

import pytest
from ffo.models.player import Player
from ffo.valuation import value_player, rank_by_efficiency


class TestValuePlayer:
    """Tests for the value_player function."""

    def test_basic_value(self):
        p = Player(name="Test", position="FWD", overall_rating=80, age=28,
                   contract_length=3, salary=10000000, value=50000000)
        score = value_player(p, age_weight=0.3, contract_weight=0.2)
        assert score > 0

    def test_age_weight_zero(self):
        p = Player(name="Test", position="FWD", overall_rating=80, age=28,
                   contract_length=3, salary=10000000, value=50000000)
        score_no_age = value_player(p, age_weight=0.0, contract_weight=0.2)
        score_with_age = value_player(p, age_weight=0.3, contract_weight=0.2)
        assert score_with_age != score_no_age

    def test_contract_weight_zero(self):
        p = Player(name="Test", position="FWD", overall_rating=80, age=28,
                   contract_length=3, salary=10000000, value=50000000)
        score_no_contract = value_player(p, age_weight=0.3, contract_weight=0.0)
        score_with_contract = value_player(p, age_weight=0.3, contract_weight=0.2)
        assert score_with_contract != score_no_contract

    def test_both_weights_zero(self):
        p = Player(name="Test", position="FWD", overall_rating=80, age=28,
                   contract_length=3, salary=10000000, value=50000000)
        score = value_player(p, age_weight=0.0, contract_weight=0.0)
        # When both weights are 0, age_factor and contract_factor are 1.0,
        # so score = overall_rating / salary (the base score)
        assert score == p.overall_rating / p.salary

    def test_high_rating_better(self):
        p1 = Player(name="A", position="FWD", overall_rating=90, age=28,
                    contract_length=3, salary=10000000, value=50000000)
        p2 = Player(name="B", position="FWD", overall_rating=70, age=28,
                    contract_length=3, salary=10000000, value=50000000)
        assert value_player(p1) > value_player(p2)

    def test_younger_better_with_age_weight(self):
        p_young = Player(name="Young", position="FWD", overall_rating=80, age=22,
                         contract_length=5, salary=10000000, value=50000000)
        p_old = Player(name="Old", position="FWD", overall_rating=80, age=35,
                       contract_length=2, salary=10000000, value=50000000)
        score_young = value_player(p_young, age_weight=0.3, contract_weight=0.2)
        score_old = value_player(p_old, age_weight=0.3, contract_weight=0.2)
        assert score_young > score_old

    def test_longer_contract_better_with_contract_weight(self):
        p_long = Player(name="Long", position="FWD", overall_rating=80, age=28,
                        contract_length=5, salary=10000000, value=50000000)
        p_short = Player(name="Short", position="FWD", overall_rating=80, age=28,
                         contract_length=1, salary=10000000, value=50000000)
        score_long = value_player(p_long, age_weight=0.0, contract_weight=0.3)
        score_short = value_player(p_short, age_weight=0.0, contract_weight=0.3)
        assert score_long > score_short

    def test_zero_salary(self):
        p = Player(name="Free", position="FWD", overall_rating=80, age=28,
                   contract_length=3, salary=0, value=50000000)
        score = value_player(p, age_weight=0.3, contract_weight=0.2)
        assert score == float("inf")

    def test_negative_rating(self):
        p = Player(name="Neg", position="FWD", overall_rating=-10, age=28,
                   contract_length=3, salary=10000000, value=50000000)
        score = value_player(p, age_weight=0.3, contract_weight=0.2)
        assert score > 0  # Should still produce a positive score

    def test_edge_case_age_16(self):
        p = Player(name="Youngest", position="FWD", overall_rating=80, age=16,
                   contract_length=3, salary=10000000, value=50000000)
        score = value_player(p, age_weight=0.3, contract_weight=0.2)
        assert score > 0

    def test_edge_case_age_50(self):
        p = Player(name="Oldest", position="FWD", overall_rating=80, age=50,
                   contract_length=3, salary=10000000, value=50000000)
        score = value_player(p, age_weight=0.3, contract_weight=0.2)
        assert score > 0


class TestRankByEfficiency:
    """Tests for the rank_by_efficiency function."""

    def test_basic_ranking(self):
        players = [
            Player(name="A", position="FWD", overall_rating=80, age=28,
                   contract_length=3, salary=10000000, value=50000000),
            Player(name="B", position="MID", overall_rating=85, age=25,
                   contract_length=4, salary=12000000, value=60000000),
            Player(name="C", position="DEF", overall_rating=75, age=30,
                   contract_length=2, salary=8000000, value=40000000),
        ]
        ranked = rank_by_efficiency(players, age_weight=0.3, contract_weight=0.2)
        assert len(ranked) == 3
        # C should be ranked first (lowest salary with decent rating gives highest score)
        assert ranked[0].name == "C"

    def test_empty_list(self):
        ranked = rank_by_efficiency([], age_weight=0.3, contract_weight=0.2)
        assert ranked == []

    def test_single_player(self):
        p = Player(name="Solo", position="FWD", overall_rating=80, age=28,
                   contract_length=3, salary=10000000, value=50000000)
        ranked = rank_by_efficiency([p], age_weight=0.3, contract_weight=0.2)
        assert len(ranked) == 1
        assert ranked[0].name == "Solo"

    def test_default_weights(self):
        p1 = Player(name="A", position="FWD", overall_rating=80, age=28,
                    contract_length=3, salary=10000000, value=50000000)
        p2 = Player(name="B", position="FWD", overall_rating=80, age=28,
                    contract_length=3, salary=10000000, value=50000000)
        ranked = rank_by_efficiency([p1, p2])
        assert len(ranked) == 2

    def test_ranking_order(self):
        """Verify ranking is in descending order of score."""
        players = [
            Player(name="Low", position="FWD", overall_rating=60, age=35,
                   contract_length=1, salary=10000000, value=30000000),
            Player(name="High", position="FWD", overall_rating=90, age=24,
                   contract_length=5, salary=10000000, value=70000000),
        ]
        ranked = rank_by_efficiency(players, age_weight=0.3, contract_weight=0.2)
        assert ranked[0].name == "High"
        assert ranked[1].name == "Low"
