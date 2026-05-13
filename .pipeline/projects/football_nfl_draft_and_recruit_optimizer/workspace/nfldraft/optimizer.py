"""Draft optimization engine for NFL teams."""

from __future__ import annotations

import random
from typing import Optional

from nfldraft.models import DraftPick, DraftResult, Player, Position, Team
from nfldraft.scoring import PlayerScorer, ScoringConfig


class DraftOptimizer:
    """Optimizes draft picks for a team based on needs, value, and salary cap."""

    def __init__(
        self,
        team: Team,
        available_picks: list[DraftPick],
        available_players: list[Player],
        scoring_config: Optional[ScoringConfig] = None,
        strategy: str = "best_available",
    ):
        """
        Args:
            team: The team doing the drafting.
            available_picks: List of picks this team has.
            available_players: Pool of available players to draft.
            scoring_config: Scoring configuration.
            strategy: "best_available" (BPA), "best_for_need", or "value_at_need".
        """
        self.team = team
        self.available_picks = list(available_picks)
        self.available_players = list(available_players)
        self.scorer = PlayerScorer(scoring_config)
        valid_strategies = {"best_available", "best_for_need", "value_at_need"}
        if strategy not in valid_strategies:
            raise ValueError(
                f"Invalid strategy '{strategy}'. Must be one of: {', '.join(sorted(valid_strategies))}"
            )
        self.strategy = strategy
        self.result = DraftResult(team=team)

    def draft(self, num_picks: Optional[int] = None) -> DraftResult:
        """Run the draft optimization."""
        picks_to_use = self.available_picks[:num_picks] if num_picks else self.available_picks
        remaining_players = list(self.available_players)

        for pick in picks_to_use:
            if pick.pick_status != "available":
                continue

            best_player = self._select_best_player(pick, remaining_players)
            if best_player:
                pick.select(best_player)
                self.result.add_pick(pick)
                remaining_players.remove(best_player)

        return self.result

    def _select_best_player(
        self, pick: DraftPick, candidates: list[Player]
    ) -> Optional[Player]:
        """Select the best player for this pick based on strategy."""
        if not candidates:
            return None

        scored = self.scorer.rank_players(candidates)

        if self.strategy == "best_available":
            return scored[0][0]

        elif self.strategy == "best_for_need":
            # Prioritize players at positions the team needs
            team_needs = self.team.needs
            best_need = None
            best_score = -1
            for player, score_data in scored:
                need_score = 0
                for pos_list in team_needs.values():
                    if player.position in pos_list:
                        need_score += 10
                total = score_data["total_score"] + need_score
                if total > best_score:
                    best_score = total
                    best_need = player
            return best_need

        elif self.strategy == "value_at_need":
            # Blend value and need
            team_needs = self.team.needs
            best_blend = None
            best_blend_score = -1
            for player, score_data in scored:
                need_score = 0
                for pos_list in team_needs.values():
                    if player.position in pos_list:
                        need_score += 5
                # Blend: 70% value, 30% need
                total = score_data["total_score"] * 0.7 + need_score * 0.3
                if total > best_blend_score:
                    best_blend_score = total
                    best_blend = player
            return best_blend

        else:
            return scored[0][0]

    def simulate_draft(
        self,
        num_rounds: int = 7,
        seed: Optional[int] = None,
    ) -> DraftResult:
        """Simulate a full draft with some randomness."""
        if seed is not None:
            random.seed(seed)

        picks_to_use = list(self.available_picks)
        remaining_players = list(self.available_players)

        for pick in picks_to_use:
            if pick.pick_status != "available":
                continue

            # Add some randomness to player selection
            if len(remaining_players) > 3:
                top_k = random.randint(1, 3)
                scored = self.scorer.rank_players(remaining_players)
                candidates = [p for p, _ in scored[:top_k]]
                best_player = random.choice(candidates)
            else:
                best_player = self._select_best_player(pick, remaining_players)

            if best_player:
                pick.select(best_player)
                self.result.add_pick(pick)
                remaining_players.remove(best_player)

        return self.result


def optimize_draft(
    team: Team,
    available_picks: list[DraftPick],
    available_players: list[Player],
    strategy: str = "best_available",
    scoring_config: Optional[ScoringConfig] = None,
) -> DraftResult:
    """Convenience function to run draft optimization."""
    optimizer = DraftOptimizer(
        team=team,
        available_picks=available_picks,
        available_players=available_players,
        scoring_config=scoring_config,
        strategy=strategy,
    )
    return optimizer.draft()
