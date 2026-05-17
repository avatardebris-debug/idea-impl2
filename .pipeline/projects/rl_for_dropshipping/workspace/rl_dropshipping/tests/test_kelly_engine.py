"""Tests for the Kelly criterion risk engine."""

import pytest
from rl_dropshipping.src.risk.kelly_engine import KellyEngine, MAX_BUDGET_FRACTION, FRACTIONAL_KELLY


class TestKellyEngine:
    """Tests for KellyEngine."""

    def setup_method(self):
        """Create a fresh engine for each test."""
        self.engine = KellyEngine()

    # --- Edge cases ---

    def test_zero_win_rate(self):
        """Engine handles win_rate = 0 correctly."""
        self.engine.update_win_rate(False)
        self.engine.update_win_rate(False)
        self.engine.update_win_rate(False)
        assert self.engine.win_rate == 0.0
        fraction = self.engine.compute_kelly_fraction(odds=2.0)
        assert fraction == 0.0

    def test_one_win_rate(self):
        """Engine handles win_rate = 1 correctly."""
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        assert self.engine.win_rate == 1.0
        # With default confidence=0.5: p=1.0*0.5=0.5, q=0.5, b=1
        # full_kelly = (1*0.5 - 0.5)/1 = 0.0
        fraction = self.engine.compute_kelly_fraction(odds=2.0)
        assert fraction == 0.0

    def test_zero_confidence(self):
        """Engine handles confidence = 0 correctly."""
        self.engine.set_confidence(0.0)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        # p = win_rate * confidence = 1.0 * 0.0 = 0.0
        fraction = self.engine.compute_kelly_fraction(odds=2.0)
        assert fraction == 0.0

    def test_negative_odds(self):
        """Engine handles negative odds correctly."""
        fraction = self.engine.compute_kelly_fraction(odds=-1.0)
        assert fraction == 0.0

    def test_zero_odds(self):
        """Engine handles zero odds correctly."""
        fraction = self.engine.compute_kelly_fraction(odds=0.0)
        assert fraction == 0.0

    # --- 10% cap enforcement ---

    def test_allocation_capped_at_10_percent(self):
        """Allocation never exceeds 10% of total budget."""
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.set_confidence(1.0)
        total_budget = 1000.0
        # With high win rate and confidence, full Kelly could be large
        # but must be capped at 10%
        allocated = self.engine.allocate_budget(total_budget, odds=5.0)
        assert allocated <= 0.10 * total_budget

    def test_allocation_capped_at_10_percent_high_confidence(self):
        """Even with perfect confidence, allocation is capped."""
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.set_confidence(1.0)
        total_budget = 10000.0
        allocated = self.engine.allocate_budget(total_budget, odds=10.0)
        assert allocated <= 0.10 * total_budget

    def test_allocation_zero_for_unfavorable_odds(self):
        """Allocation is zero when odds are unfavorable."""
        self.engine.update_win_rate(False)
        self.engine.update_win_rate(False)
        self.engine.update_win_rate(False)
        self.engine.set_confidence(0.5)
        total_budget = 1000.0
        allocated = self.engine.allocate_budget(total_budget, odds=1.5)
        assert allocated == 0.0

    # --- Fractional Kelly ---

    def test_half_kelly_applied(self):
        """Half-Kelly is applied by default."""
        # Use default win_rate=0.5, confidence=0.5 so p=0.25, q=0.75
        # With odds=5.0: b=4.0, full_kelly = (4.0*0.25 - 0.75)/4.0 = 0.0625
        # half-kelly = 0.03125, which is below the 10% cap
        fraction = self.engine.compute_kelly_fraction(odds=5.0)
        expected_full = (4.0 * 0.25 - 0.75) / 4.0  # 0.0625
        expected_half = expected_full * FRACTIONAL_KELLY  # 0.03125
        assert fraction == expected_half

    def test_custom_fractional_multiplier(self):
        """Custom fractional multiplier works."""
        engine = KellyEngine(fractional_multiplier=0.25)
        # Use default win_rate=0.5, confidence=0.5 so p=0.25, q=0.75
        # With odds=5.0: b=4.0, full_kelly = (4.0*0.25 - 0.75)/4.0 = 0.0625
        # quarter-kelly = 0.015625, which is below the 10% cap
        fraction = engine.compute_kelly_fraction(odds=5.0)
        expected_full = (4.0 * 0.25 - 0.75) / 4.0  # 0.0625
        expected_quarter = expected_full * 0.25  # 0.015625
        assert fraction == expected_quarter

    # --- Win rate updates ---

    def test_win_rate_updates_on_wins(self):
        """Win rate updates correctly on wins."""
        self.engine.update_win_rate(True)
        assert self.engine.win_rate == 1.0
        self.engine.update_win_rate(False)
        assert self.engine.win_rate == 0.5
        self.engine.update_win_rate(True)
        assert self.engine.win_rate == pytest.approx(0.6667, rel=1e-3)

    def test_win_rate_updates_on_losses(self):
        """Win rate updates correctly on losses."""
        self.engine.update_win_rate(False)
        assert self.engine.win_rate == 0.0
        self.engine.update_win_rate(True)
        assert self.engine.win_rate == 0.5

    def test_n_counters_updated(self):
        """Win/loss counters are updated correctly."""
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(False)
        assert self.engine.n_wins == 2
        assert self.engine.n_losses == 1
        assert self.engine.n_total == 3

    # --- Confidence ---

    def test_confidence_clamped_to_1(self):
        """Confidence is clamped to 1.0."""
        self.engine.set_confidence(1.5)
        assert self.engine.confidence == 1.0

    def test_confidence_clamped_to_0(self):
        """Confidence is clamped to 0.0."""
        self.engine.set_confidence(-0.5)
        assert self.engine.confidence == 0.0

    # --- State ---

    def test_get_state(self):
        """Engine state is returned correctly."""
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(False)
        self.engine.set_confidence(0.8)
        state = self.engine.get_state()
        assert state["n_wins"] == 1
        assert state["n_losses"] == 1
        assert state["n_total"] == 2
        assert state["confidence"] == 0.8
        assert state["win_rate"] == 0.5

    def test_repr(self):
        """Engine repr is informative."""
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.set_confidence(0.7)
        repr_str = repr(self.engine)
        assert "KellyEngine" in repr_str
        assert "win_rate=" in repr_str
        assert "confidence=" in repr_str

    # --- Integration: allocate returns valid value ---

    def test_allocate_returns_valid_value(self):
        """Allocate returns a non-negative value within budget."""
        total_budget = 500.0
        allocated = self.engine.allocate_budget(total_budget, odds=2.0)
        assert 0.0 <= allocated <= total_budget

    def test_allocate_with_no_history(self):
        """Engine works with no history (default win_rate=0.5)."""
        total_budget = 1000.0
        allocated = self.engine.allocate_budget(total_budget, odds=2.0)
        # With default win_rate=0.5, confidence=0.5: p=0.25, q=0.75
        # b=1, full_kelly = (1*0.25 - 0.75)/1 = -0.5 -> capped to 0
        assert allocated == 0.0

    def test_allocate_with_positive_edge_case(self):
        """Engine allocates when conditions are favorable."""
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.update_win_rate(True)
        self.engine.set_confidence(1.0)
        total_budget = 1000.0
        allocated = self.engine.allocate_budget(total_budget, odds=3.0)
        assert allocated > 0.0
        assert allocated <= 0.10 * total_budget
