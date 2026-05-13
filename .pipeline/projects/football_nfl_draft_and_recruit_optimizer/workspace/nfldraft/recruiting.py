"""Recruiting evaluation engine for college football."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from nfldraft.models import Position, RecruitTarget


@dataclass
class RecruitingConfig:
    """Configuration for recruiting evaluation."""
    # Position demand weights (how much each position matters for recruiting)
    position_demand: dict[Position, float] = field(default_factory=lambda: {
        Position.QB: 1.0,
        Position.RB: 0.7,
        Position.WR: 0.9,
        Position.TE: 0.6,
        Position.OL: 0.8,
        Position.DL: 0.85,
        Position.LB: 0.85,
        Position.CB: 0.9,
        Position.S: 0.85,
        Position.K: 0.3,
        Position.P: 0.2,
        Position.EDGE: 0.9,
        Position.ILB: 0.85,
        Position.OLB: 0.9,
        Position.T: 0.85,
        Position.G: 0.75,
        Position.C: 0.75,
        Position.FS: 0.85,
        Position.SS: 0.9,
        Position.UNKNOWN: 0.5,
    })

    # Geographic proximity bonus (closer recruits are easier to win)
    state_bonus: float = 5.0
    region_bonus: float = 2.0

    # Academic eligibility weight
    academics_weight: float = 0.1

    # Coaching relationship weight
    coaching_relationship_weight: float = 3.0

    # Program prestige weight
    program_prestige_weight: float = 2.0

    # NFL projection weight
    nfl_projection_weight: float = 4.0

    # Alternative names for compatibility
    prestige_weight: Optional[float] = None
    location_weight: Optional[float] = None
    development_weight: Optional[float] = None

    def __post_init__(self):
        """Handle alternative parameter names."""
        if self.prestige_weight is not None:
            self.program_prestige_weight = self.prestige_weight
        if self.location_weight is not None:
            self.state_bonus = self.location_weight
        if self.development_weight is not None:
            self.academics_weight = self.development_weight


class RecruitingEngine:
    """Evaluates and ranks recruiting targets for a program."""

    def __init__(
        self,
        school_name: str,
        program_prestige: float = 5.0,  # 1-10 scale
        coaching_staff_strength: float = 5.0,  # 1-10 scale
        config: Optional[RecruitingConfig] = None,
    ):
        self.school_name = school_name
        self.program_prestige = program_prestige
        self.coaching_staff_strength = coaching_staff_strength
        self.config = config or RecruitingConfig()

    def evaluate_recruit(self, recruit: RecruitTarget) -> dict:
        """Evaluate a recruit's fit and likelihood to commit."""
        # 1. Base rating
        base_score = recruit.overall_rating * 0.5

        # 2. Position demand
        pos_demand = self.config.position_demand.get(recruit.position, 0.5)
        position_score = pos_demand * 10

        # 3. Geographic proximity
        geo_score = 0.0
        if recruit.state:
            # Simplified: if state matches school's typical recruiting area
            geo_score = self.config.state_bonus

        # 4. Academic fit
        academics_score = recruit.academics_gpa * self.config.academics_weight * 10

        # 5. Program prestige
        prestige_score = self.program_prestige * self.config.program_prestige_weight

        # 6. Coaching relationship
        coaching_score = self.coaching_staff_strength * self.config.coaching_relationship_weight

        # 7. NFL projection
        nfl_score = 0.0
        if recruit.recruiting_rank and recruit.recruiting_rank <= 50:
            nfl_score = self.config.nfl_projection_weight * 5
        elif recruit.recruiting_rank and recruit.recruiting_rank <= 100:
            nfl_score = self.config.nfl_projection_weight * 3

        # Total likelihood score (0-100)
        total_score = base_score + position_score + geo_score + academics_score + prestige_score + coaching_score + nfl_score
        total_score = min(100.0, max(0.0, total_score))

        # Commitment probability (simplified)
        commitment_prob = min(1.0, total_score / 100.0)

        return {
            "total_score": round(total_score, 2),
            "commitment_probability": round(commitment_prob, 4),
            "breakdown": {
                "base_rating": round(base_score, 2),
                "position_demand": round(position_score, 2),
                "geographic_fit": round(geo_score, 2),
                "academics_fit": round(academics_score, 2),
                "program_prestige": round(prestige_score, 2),
                "coaching_relationship": round(coaching_score, 2),
                "nfl_projection": round(nfl_score, 2),
            },
            "recommendation": self._get_recommendation(total_score, commitment_prob),
        }

    def _get_recommendation(self, score: float, prob: float) -> str:
        """Get a recommendation based on score and probability."""
        if prob >= 0.8:
            return "STRONG TARGET - Focus resources here"
        elif prob >= 0.6:
            return "TARGET - Worth pursuing"
        elif prob >= 0.4:
            return "LONG SHOT - Low priority"
        else:
            return "NOT A TARGET - Skip"

    def rank_recruits(self, recruits: list[RecruitTarget]) -> list[tuple[RecruitTarget, dict]]:
        """Rank recruits by evaluation score."""
        evaluated = [(r, self.evaluate_recruit(r)) for r in recruits]
        evaluated.sort(key=lambda x: x[1]["total_score"], reverse=True)
        return evaluated

    def simulate_recruiting_class(
        self,
        recruits: list[RecruitTarget],
        num_committed: int = 25,
    ) -> list[RecruitTarget]:
        """Simulate which recruits commit to the school."""
        ranked = self.rank_recruits(recruits)
        committed = []
        for recruit, eval_data in ranked:
            if len(committed) >= num_committed:
                break
            if eval_data["commitment_probability"] >= 0.5:
                recruit.commit_to(self.school_name)
                committed.append(recruit)
        return committed


def evaluate_recruit(
    recruit: RecruitTarget,
    school_name: str = "Unknown",
    program_prestige: float = 5.0,
    coaching_staff_strength: float = 5.0,
) -> dict:
    """Convenience function to evaluate a single recruit."""
    engine = RecruitingEngine(
        school_name=school_name,
        program_prestige=program_prestige,
        coaching_staff_strength=coaching_staff_strength,
    )
    return engine.evaluate_recruit(recruit)
