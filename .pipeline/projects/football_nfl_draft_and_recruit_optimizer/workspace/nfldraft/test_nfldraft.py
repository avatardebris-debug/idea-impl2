"""Tests for nfldraft core package."""

import pytest
from nfldraft.models import (
    Player,
    Team,
    DraftPick,
    RecruitTarget,
    DraftResult,
    Position,
    DraftRound,
    RecruitStatus,
)
from nfldraft.scoring import PlayerScorer, ScoringConfig, score_player, rank_players
from nfldraft.optimizer import DraftOptimizer, optimize_draft
from nfldraft.recruiting import RecruitingEngine, RecruitingConfig, evaluate_recruit


# ==================== Models Tests ====================

class TestPlayer:
    def test_create_player(self):
        p = Player(name="Test Player", position=Position.QB, overall_rating=85)
        assert p.name == "Test Player"
        assert p.position == Position.QB
        assert p.overall_rating == 85

    def test_player_value_score(self):
        p = Player(name="Valued", position=Position.QB, overall_rating=80, salary=5.0, contract_length=4)
        score = p.value_score
        assert score > 0

    def test_player_value_score_zero_salary(self):
        p = Player(name="Free", position=Position.QB, overall_rating=80, salary=0)
        assert p.value_score == float("inf")

    def test_player_to_dict(self):
        p = Player(name="Dict Test", position=Position.WR, overall_rating=75)
        d = p.to_dict()
        assert d["name"] == "Dict Test"
        assert d["position"] == "WR"

    def test_player_from_dict(self):
        data = {"name": "From Dict", "position": "RB", "overall_rating": 70}
        p = Player.from_dict(data)
        assert p.name == "From Dict"
        assert p.position == Position.RB
        assert p.overall_rating == 70

    def test_position_enum(self):
        assert Position.QB.value == "QB"
        assert Position.WR.value == "WR"
        assert Position.UNKNOWN.value == "UNKNOWN"

    def test_player_default_values(self):
        p = Player(name="Default", position=Position.QB)
        assert p.age is None
        assert p.salary is None
        assert p.contract_length is None
        assert p.stats == {}
        assert p.strengths == []
        assert p.weaknesses == []

    def test_player_invalid_position(self):
        with pytest.raises(ValueError):
            Player(name="Invalid", position="INVALID")

    def test_player_negative_rating(self):
        with pytest.raises(ValueError):
            Player(name="Bad Rating", position=Position.QB, overall_rating=-1)

    def test_player_rating_too_high(self):
        with pytest.raises(ValueError):
            Player(name="Too High", position=Position.QB, overall_rating=101)


class TestTeam:
    def test_create_team(self):
        t = Team(name="Test Team", city="Test City", conference="AFC", division="North")
        assert t.name == "Test Team"
        assert t.remaining_cap == 250.0

    def test_add_player(self):
        t = Team(name="Test Team", city="Test City", conference="AFC", division="North")
        p = Player(name="New Player", position=Position.QB, salary=2.0)
        t.add_player(p)
        assert len(t.roster) == 1
        assert t.current_payroll == 2.0

    def test_add_player_exceeds_cap(self):
        t = Team(name="Test Team", city="Test City", conference="AFC", division="North", salary_cap=10.0)
        p = Player(name="Expensive", position=Position.QB, salary=15.0)
        with pytest.raises(ValueError, match="exceed salary cap"):
            t.add_player(p)

    def test_can_afford(self):
        t = Team(name="Test Team", city="Test City", conference="AFC", division="North", salary_cap=10.0)
        p = Player(name="Cheap", position=Position.QB, salary=2.0)
        assert t.can_afford(p) is True
        p2 = Player(name="Expensive", position=Position.QB, salary=15.0)
        assert t.can_afford(p2) is False

    def test_remove_player(self):
        t = Team(name="Test Team", city="Test City", conference="AFC", division="North")
        p = Player(name="Remove Me", position=Position.QB, salary=2.0)
        t.add_player(p)
        t.remove_player(p)
        assert len(t.roster) == 0
        assert t.current_payroll == 0.0

    def test_to_dict(self):
        t = Team(name="Test Team", city="Test City", conference="AFC", division="North")
        d = t.to_dict()
        assert d["name"] == "Test Team"
        assert d["remaining_cap"] == 250.0

    def test_from_dict(self):
        data = {"name": "From Dict Team", "city": "City", "conference": "NFC", "division": "East"}
        t = Team.from_dict(data)
        assert t.name == "From Dict Team"
        assert t.conference == "NFC"

    def test_team_empty_roster_payroll(self):
        t = Team(name="Empty", city="City", conference="AFC", division="North")
        assert t.current_payroll == 0.0
        assert t.remaining_cap == 250.0

    def test_team_multiple_players(self):
        t = Team(name="Multi", city="City", conference="AFC", division="North", salary_cap=100.0)
        for i in range(5):
            p = Player(name=f"Player{i}", position=Position.QB, salary=10.0)
            t.add_player(p)
        assert len(t.roster) == 5
        assert t.current_payroll == 50.0
        assert t.remaining_cap == 50.0


class TestDraftPick:
    def test_create_pick(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        p = DraftPick(round_num=1, overall_pick=1, team=t)
        assert p.pick_status == "available"

    def test_select_player(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        pick = DraftPick(round_num=1, overall_pick=1, team=t)
        player = Player(name="Drafted", position=Position.QB)
        pick.select(player)
        assert pick.pick_status == "selected"
        assert pick.player == player
        assert player in t.roster

    def test_double_select(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        pick = DraftPick(round_num=1, overall_pick=1, team=t)
        player1 = Player(name="First", position=Position.QB)
        pick.select(player1)
        player2 = Player(name="Second", position=Position.QB)
        with pytest.raises(ValueError):
            pick.select(player2)

    def test_to_dict(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        pick = DraftPick(round_num=1, overall_pick=1, team=t)
        d = pick.to_dict()
        assert d["round"] == 1
        assert d["overall_pick"] == 1
        assert d["status"] == "available"

    def test_pick_unavailable_select(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        pick = DraftPick(round_num=1, overall_pick=1, team=t)
        player = Player(name="First", position=Position.QB)
        pick.select(player)
        player2 = Player(name="Second", position=Position.QB)
        with pytest.raises(ValueError, match="already been used"):
            pick.select(player2)


class TestRecruitTarget:
    def test_create_recruit(self):
        r = RecruitTarget(name="Recruit", position=Position.QB)
        assert r.name == "Recruit"
        assert r.commitment_status == RecruitStatus.UNCOMMITTED

    def test_commit_to(self):
        r = RecruitTarget(name="Committed", position=Position.QB)
        r.commit_to("University X")
        assert r.committed_to == "University X"
        assert r.commitment_status == RecruitStatus.COMMITTED

    def test_to_dict(self):
        r = RecruitTarget(name="Dict Recruit", position=Position.WR)
        d = r.to_dict()
        assert d["name"] == "Dict Recruit"
        assert d["commitment_status"] == "uncommitted"

    def test_from_dict(self):
        data = {"name": "From Recruit", "position": "RB", "commitment_status": "committed"}
        r = RecruitTarget.from_dict(data)
        assert r.name == "From Recruit"
        assert r.commitment_status == RecruitStatus.COMMITTED

    def test_recruit_default_values(self):
        r = RecruitTarget(name="Default", position=Position.QB)
        assert r.committed_to is None
        assert r.commitment_status == RecruitStatus.UNCOMMITTED


class TestDraftResult:
    def test_add_pick(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        result = DraftResult(team=t)
        pick = DraftPick(round_num=1, overall_pick=1, team=t)
        player = Player(name="Picked", position=Position.QB, salary=1.0)
        pick.select(player)
        result.add_pick(pick)
        assert result.total_players == 1
        assert result.total_spent == 1.0

    def test_to_dict(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        result = DraftResult(team=t)
        d = result.to_dict()
        assert d["team"] == "Test"
        assert d["total_picks"] == 0

    def test_draft_result_multiple_picks(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        result = DraftResult(team=t)
        for i in range(3):
            pick = DraftPick(round_num=1, overall_pick=i+1, team=t)
            player = Player(name=f"P{i}", position=Position.QB, salary=1.0)
            pick.select(player)
            result.add_pick(pick)
        assert result.total_players == 3
        assert result.total_spent == 3.0


# ==================== Scoring Tests ====================

class TestPlayerScorer:
    def test_score_player(self):
        p = Player(name="Scored", position=Position.QB, overall_rating=80, age=25, salary=2.0, contract_length=4)
        scorer = PlayerScorer()
        score = scorer.score_player(p)
        assert "total_score" in score
        assert score["total_score"] > 0

    def test_rank_players(self):
        p1 = Player(name="Better", position=Position.QB, overall_rating=90)
        p2 = Player(name="Worse", position=Position.QB, overall_rating=70)
        scorer = PlayerScorer()
        ranked = scorer.rank_players([p1, p2])
        assert ranked[0][0].name == "Better"

    def test_age_factor(self):
        # Younger players should score higher on age
        p_young = Player(name="Young", position=Position.QB, overall_rating=80, age=24)
        p_old = Player(name="Old", position=Position.QB, overall_rating=80, age=32)
        scorer = PlayerScorer()
        s_young = scorer.score_player(p_young)
        s_old = scorer.score_player(p_old)
        # Age score should favor younger
        assert s_young["age_score"] >= s_old["age_score"]

    def test_value_score(self):
        p_expensive = Player(name="Expensive", position=Position.QB, overall_rating=80, salary=10.0)
        p_cheap = Player(name="Cheap", position=Position.QB, overall_rating=80, salary=1.0)
        scorer = PlayerScorer()
        s_exp = scorer.score_player(p_expensive)
        s_cheap = scorer.score_player(p_cheap)
        # Cheaper player should have better value score
        assert s_cheap["value_score"] > s_exp["value_score"]

    def test_custom_config(self):
        config = ScoringConfig(
            age_peak=27,
            age_boost_per_year_below_peak=2.0,
            age_penalty_per_year_above_peak=1.5,
            contract_length_weight=0.5,
            stats_weights={"passing_yards": 0.1, "rushing_yards": 0.1},
            strength_weight=5.0,
            weakness_weight=-3.0,
        )
        scorer = PlayerScorer(config)
        p = Player(name="Custom", position=Position.QB, overall_rating=80, age=25, salary=2.0)
        score = scorer.score_player(p)
        assert "total_score" in score

    def test_score_player_no_age(self):
        p = Player(name="No Age", position=Position.QB, overall_rating=80)
        scorer = PlayerScorer()
        score = scorer.score_player(p)
        assert "age_score" in score

    def test_score_player_no_salary(self):
        p = Player(name="No Salary", position=Position.QB, overall_rating=80)
        scorer = PlayerScorer()
        score = scorer.score_player(p)
        assert "value_score" in score

    def test_score_player_with_stats(self):
        p = Player(
            name="Stats",
            position=Position.QB,
            overall_rating=80,
            stats={"passing_yards": 4000, "rushing_yards": 500, "touchdowns": 30}
        )
        scorer = PlayerScorer()
        score = scorer.score_player(p)
        assert "stats_score" in score

    def test_score_player_with_strengths_weaknesses(self):
        p = Player(
            name="Strengths",
            position=Position.QB,
            overall_rating=80,
            strengths=["arm_strength", "accuracy"],
            weaknesses=["mobility"]
        )
        scorer = PlayerScorer()
        score = scorer.score_player(p)
        assert "adjustment" in score

    def test_rank_players_empty(self):
        scorer = PlayerScorer()
        ranked = scorer.rank_players([])
        assert ranked == []

    def test_rank_players_single(self):
        p1 = Player(name="Only", position=Position.QB, overall_rating=80)
        scorer = PlayerScorer()
        ranked = scorer.rank_players([p1])
        assert len(ranked) == 1
        assert ranked[0][0].name == "Only"


class TestScorePlayer:
    def test_convenience_function(self):
        p = Player(name="Conv", position=Position.WR, overall_rating=75)
        score = score_player(p)
        assert "total_score" in score


class TestRankPlayers:
    def test_convenience_function(self):
        p1 = Player(name="A", position=Position.QB, overall_rating=90)
        p2 = Player(name="B", position=Position.QB, overall_rating=80)
        ranked = rank_players([p1, p2])
        assert ranked[0][0].name == "A"


# ==================== Optimizer Tests ====================

class TestDraftOptimizer:
    def test_best_available_strategy(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        p1 = Player(name="Best", position=Position.QB, overall_rating=95)
        p2 = Player(name="Good", position=Position.QB, overall_rating=85)
        available = [p1, p2]
        optimizer = DraftOptimizer(t, picks, available, strategy="best_available")
        result = optimizer.draft()
        assert result.total_players == 1
        assert result.top_picks[0].name == "Best"

    def test_best_for_need_strategy(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        t.needs = {"high": [Position.QB]}
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        p_qb = Player(name="QB", position=Position.QB, overall_rating=80)
        p_wr = Player(name="WR", position=Position.WR, overall_rating=90)
        available = [p_qb, p_wr]
        optimizer = DraftOptimizer(t, picks, available, strategy="best_for_need")
        result = optimizer.draft()
        # QB should be picked due to need
        assert result.top_picks[0].name == "QB"

    def test_value_at_need_strategy(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        t.needs = {"high": [Position.QB]}
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        p_qb = Player(name="QB", position=Position.QB, overall_rating=85)
        p_wr = Player(name="WR", position=Position.WR, overall_rating=90)
        available = [p_qb, p_wr]
        optimizer = DraftOptimizer(t, picks, available, strategy="value_at_need")
        result = optimizer.draft()
        assert result.total_players == 1

    def test_simulate_draft(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        picks = [DraftPick(round_num=1, overall_pick=i, team=t) for i in range(1, 4)]
        players = [Player(name=f"P{i}", position=Position.QB, overall_rating=80) for i in range(1, 4)]
        optimizer = DraftOptimizer(t, picks, players, strategy="best_available")
        result = optimizer.simulate_draft(num_rounds=1, seed=42)
        assert result.total_players >= 1

    def test_no_available_players(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        optimizer = DraftOptimizer(t, picks, [], strategy="best_available")
        result = optimizer.draft()
        assert result.total_players == 0

    def test_multiple_picks(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        picks = [DraftPick(round_num=1, overall_pick=i, team=t) for i in range(1, 4)]
        players = [Player(name=f"P{i}", position=Position.QB, overall_rating=80+i) for i in range(1, 4)]
        optimizer = DraftOptimizer(t, picks, players, strategy="best_available")
        result = optimizer.draft()
        assert result.total_players == 3

    def test_salary_cap_constraint(self):
        t = Team(name="Cap Team", city="City", conference="AFC", division="North", salary_cap=5.0)
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        p_expensive = Player(name="Expensive", position=Position.QB, overall_rating=95, salary=10.0)
        p_cheap = Player(name="Cheap", position=Position.QB, overall_rating=80, salary=1.0)
        available = [p_expensive, p_cheap]
        optimizer = DraftOptimizer(t, picks, available, strategy="best_available")
        result = optimizer.draft()
        # Should pick the cheap player since expensive exceeds cap
        assert result.total_players == 1
        assert result.top_picks[0].name == "Cheap"

    def test_invalid_strategy(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        with pytest.raises(ValueError):
            DraftOptimizer(t, picks, [], strategy="invalid_strategy")


class TestOptimizeDraft:
    def test_convenience_function(self):
        t = Team(name="Test", city="City", conference="AFC", division="North")
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        p = Player(name="Optimized", position=Position.QB, overall_rating=90)
        result = optimize_draft(t, picks, [p])
        assert result.total_players == 1


# ==================== Recruiting Tests ====================

class TestRecruitingEngine:
    def test_evaluate_recruit(self):
        r = RecruitTarget(name="Target", position=Position.QB, overall_rating=85)
        engine = RecruitingEngine("Test School", program_prestige=7.0)
        eval_data = engine.evaluate_recruit(r)
        assert "total_score" in eval_data
        assert "commitment_probability" in eval_data

    def test_rank_recruits(self):
        r1 = RecruitTarget(name="Better", position=Position.QB, overall_rating=90)
        r2 = RecruitTarget(name="Worse", position=Position.QB, overall_rating=70)
        engine = RecruitingEngine("Test School")
        ranked = engine.rank_recruits([r1, r2])
        assert ranked[0][0].name == "Better"

    def test_simulate_recruiting_class(self):
        r1 = RecruitTarget(name="Commit", position=Position.QB, overall_rating=90)
        r2 = RecruitTarget(name="No Commit", position=Position.QB, overall_rating=50)
        engine = RecruitingEngine("Test School", program_prestige=9.0)
        committed = engine.simulate_recruiting_class([r1, r2], num_committed=2)
        assert len(committed) >= 1
        assert committed[0].committed_to == "Test School"

    def test_recruiting_engine_default_config(self):
        engine = RecruitingEngine("Default School")
        assert engine.program_prestige == 5.0

    def test_recruiting_engine_custom_config(self):
        config = RecruitingConfig(
            prestige_weight=0.4,
            location_weight=0.3,
            development_weight=0.3,
        )
        engine = RecruitingEngine("Custom School", program_prestige=8.0, config=config)
        assert engine.config.prestige_weight == 0.4

    def test_rank_recruits_empty(self):
        engine = RecruitingEngine("Test School")
        ranked = engine.rank_recruits([])
        assert ranked == []

    def test_rank_recruits_single(self):
        r1 = RecruitTarget(name="Only", position=Position.QB, overall_rating=80)
        engine = RecruitingEngine("Test School")
        ranked = engine.rank_recruits([r1])
        assert len(ranked) == 1
        assert ranked[0][0].name == "Only"


class TestEvaluateRecruit:
    def test_convenience_function(self):
        r = RecruitTarget(name="Conv Recruit", position=Position.WR, overall_rating=80)
        eval_data = evaluate_recruit(r, "Test School")
        assert "total_score" in eval_data


# ==================== Integration Tests ====================

class TestIntegration:
    def test_full_draft_flow(self):
        """Test a complete draft optimization flow."""
        t = Team(name="Draft Team", city="City", conference="AFC", division="North")
        picks = [DraftPick(round_num=1, overall_pick=i, team=t) for i in range(1, 4)]
        players = [
            Player(name=f"Player{i}", position=Position.QB, overall_rating=80 + i, salary=1.0 + i * 0.5)
            for i in range(1, 4)
        ]
        optimizer = DraftOptimizer(t, picks, players, strategy="best_available")
        result = optimizer.draft()
        assert result.total_players == 3
        assert result.total_spent > 0

    def test_full_recruiting_flow(self):
        """Test a complete recruiting evaluation flow."""
        recruits = [
            RecruitTarget(name=f"Recruit{i}", position=Position.QB, overall_rating=80 + i)
            for i in range(1, 4)
        ]
        engine = RecruitingEngine("Recruit School", program_prestige=8.0)
        ranked = engine.rank_recruits(recruits)
        assert len(ranked) == 3
        assert ranked[0][0].name == "Recruit3"  # Highest rating

    def test_team_salary_cap_management(self):
        """Test that team manages salary cap correctly through draft."""
        t = Team(name="Cap Team", city="City", conference="AFC", division="North", salary_cap=10.0)
        picks = [DraftPick(round_num=1, overall_pick=i, team=t) for i in range(1, 4)]
        players = [
            Player(name=f"Player{i}", position=Position.QB, overall_rating=80, salary=3.0)
            for i in range(1, 4)
        ]
        # Only 3 players can be added (3 * 3 = 9 <= 10)
        optimizer = DraftOptimizer(t, picks, players, strategy="best_available")
        result = optimizer.draft()
        assert t.current_payroll <= t.salary_cap

    def test_draft_and_recruit_integration(self):
        """Test that draft and recruiting can work together."""
        # Create a team
        t = Team(name="Integration Team", city="City", conference="AFC", division="North")
        
        # Draft a player
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        p = Player(name="Drafted", position=Position.QB, overall_rating=85)
        optimizer = DraftOptimizer(t, picks, [p], strategy="best_available")
        draft_result = optimizer.draft()
        assert draft_result.total_players == 1
        
        # Recruit a player
        recruit = RecruitTarget(name="Recruit", position=Position.WR, overall_rating=80)
        engine = RecruitingEngine("Test School", program_prestige=7.0)
        eval_data = engine.evaluate_recruit(recruit)
        assert "total_score" in eval_data

    def test_scoring_and_optimization_integration(self):
        """Test that scoring and optimization work together."""
        t = Team(name="Test", city="City", conference="AFC", division="North")
        picks = [DraftPick(round_num=1, overall_pick=1, team=t)]
        
        # Create players with different scores
        p1 = Player(name="High Score", position=Position.QB, overall_rating=90, age=24, salary=2.0)
        p2 = Player(name="Low Score", position=Position.QB, overall_rating=70, age=32, salary=10.0)
        
        # Score them
        scorer = PlayerScorer()
        s1 = scorer.score_player(p1)
        s2 = scorer.score_player(p2)
        
        # High score player should rank higher
        assert s1["total_score"] > s2["total_score"]
        
        # Optimize draft should pick the higher scored player
        optimizer = DraftOptimizer(t, picks, [p1, p2], strategy="best_available")
        result = optimizer.draft()
        assert result.top_picks[0].name == "High Score"
