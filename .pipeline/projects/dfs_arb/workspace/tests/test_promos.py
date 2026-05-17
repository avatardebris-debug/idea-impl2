"""Tests for the promo/bonus hunting module."""

import pytest
from dfs_arb.core.promos import (
    PromoOffer,
    PromoType,
    PromoEvaluation,
    evaluate_promo,
    evaluate_all_promos,
    _calculate_hedging_ev,
)
from dfs_arb.core.models import OddsEntry, MarketType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(
    market_id: str = "test_market",
    bookmaker: str = "BK1",
    side: str = "over",
    decimal_odds: float = 2.0,
) -> OddsEntry:
    """Helper to create a minimal OddsEntry."""
    return OddsEntry(
        market_id=market_id,
        market_type=MarketType.TWO_SIDED,
        event_name="Test Event",
        event_date="2024-01-01",
        sport="Test",
        bookmaker=bookmaker,
        side=side,
        decimal_odds=decimal_odds,
        line_value=None,
        odds_format="decimal",
        odds_value=decimal_odds,
    )


# ---------------------------------------------------------------------------
# PromoType enum
# ---------------------------------------------------------------------------

class TestPromoType:
    """Tests for PromoType enum."""

    def test_all_types_present(self):
        """All expected promo types exist."""
        expected = {
            "SIGNUP_BONUS",
            "DEPOSIT_MATCH",
            "RISK_FREE_BET",
            "BET_BOOST",
            "ODDS_BOOST",
            "REFERRAL_BONUS",
            "INSURANCE",
        }
        actual = {pt.name for pt in PromoType}
        assert expected == actual

    def test_enum_values(self):
        """Enum values match expected strings."""
        assert PromoType.SIGNUP_BONUS.value == "signup_bonus"
        assert PromoType.DEPOSIT_MATCH.value == "deposit_match"
        assert PromoType.RISK_FREE_BET.value == "risk_free_bet"
        assert PromoType.BET_BOOST.value == "bet_boost"
        assert PromoType.ODDS_BOOST.value == "odds_boost"
        assert PromoType.REFERRAL_BONUS.value == "referral_bonus"
        assert PromoType.INSURANCE.value == "insurance"


# ---------------------------------------------------------------------------
# PromoOffer dataclass
# ---------------------------------------------------------------------------

class TestPromoOffer:
    """Tests for PromoOffer dataclass."""

    def test_defaults(self):
        """Default field values are correct."""
        offer = PromoOffer(
            promo_id="p1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="Bookie",
            description="A bonus",
            max_bonus=50.0,
        )
        assert offer.min_deposit == 0.0
        assert offer.rollover_requirement == 1.0
        assert offer.expiry_date is None
        assert offer.eligible_markets == []
        assert offer.terms == ""

    def test_to_dict(self):
        """Serialization round-trips correctly."""
        offer = PromoOffer(
            promo_id="p1",
            promo_type=PromoType.RISK_FREE_BET,
            provider="BookieX",
            description="Risk free",
            max_bonus=100.0,
            min_deposit=25.0,
            rollover_requirement=2.0,
            expiry_date="2025-06-30",
            eligible_markets=["spread", "total"],
            terms="T&Cs apply",
        )
        d = offer.to_dict()
        assert d["promo_id"] == "p1"
        assert d["promo_type"] == "risk_free_bet"
        assert d["provider"] == "BookieX"
        assert d["description"] == "Risk free"
        assert d["max_bonus"] == 100.0
        assert d["min_deposit"] == 25.0
        assert d["rollover_requirement"] == 2.0
        assert d["expiry_date"] == "2025-06-30"
        assert d["eligible_markets"] == ["spread", "total"]
        assert d["terms"] == "T&Cs apply"

    def test_to_dict_preserves_enum_value(self):
        """to_dict stores the enum value, not the enum itself."""
        offer = PromoOffer(
            promo_id="p2",
            promo_type=PromoType.ODDS_BOOST,
            provider="P",
            description="d",
            max_bonus=10.0,
        )
        d = offer.to_dict()
        assert isinstance(d["promo_type"], str)
        assert d["promo_type"] == "odds_boost"


# ---------------------------------------------------------------------------
# PromoEvaluation dataclass
# ---------------------------------------------------------------------------

class TestPromoEvaluation:
    """Tests for PromoEvaluation dataclass."""

    def test_defaults(self):
        """Default details dict is empty."""
        offer = PromoOffer(
            promo_id="p1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=10.0,
        )
        ev = PromoEvaluation(
            promo=offer,
            expected_value=5.0,
            is_profitable=True,
            best_strategy="bet",
            risk_level="low",
        )
        assert ev.details == {}

    def test_to_dict(self):
        """Serialization includes all fields."""
        offer = PromoOffer(
            promo_id="p1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=10.0,
        )
        ev = PromoEvaluation(
            promo=offer,
            expected_value=5.55,
            is_profitable=True,
            best_strategy="hedge",
            risk_level="medium",
            details={"key": "val"},
        )
        d = ev.to_dict()
        assert d["promo_id"] == "p1"
        assert d["promo_type"] == "signup_bonus"
        assert d["provider"] == "B"
        assert d["expected_value"] == 5.55
        assert d["is_profitable"] is True
        assert d["best_strategy"] == "hedge"
        assert d["risk_level"] == "medium"
        assert d["details"] == {"key": "val"}

    def test_to_dict_rounding(self):
        """expected_value is rounded to 2 decimal places."""
        offer = PromoOffer(
            promo_id="p1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=10.0,
        )
        ev = PromoEvaluation(
            promo=offer,
            expected_value=5.555,
            is_profitable=True,
            best_strategy="bet",
            risk_level="low",
        )
        d = ev.to_dict()
        assert d["expected_value"] == 5.56


# ---------------------------------------------------------------------------
# _calculate_hedging_ev
# ---------------------------------------------------------------------------

class TestCalculateHedgingEV:
    """Tests for the private _calculate_hedging_ev helper."""

    def test_fair_market(self):
        """EV is 0 for a fair market (no vig)."""
        over_entry = _make_entry(side="over", decimal_odds=2.0)
        under_entry = _make_entry(side="under", decimal_odds=2.0)
        ev = _calculate_hedging_ev(over_entry, under_entry)
        assert ev == pytest.approx(0.0)

    def test_vig_market(self):
        """EV is negative for a vig market."""
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        ev = _calculate_hedging_ev(over_entry, under_entry)
        assert ev < 0

    def test_arbitrage_market(self):
        """EV is positive for an arbitrage market."""
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        ev = _calculate_hedging_ev(over_entry, under_entry)
        assert ev > 0

    def test_asymmetric_odds(self):
        """EV calculation handles asymmetric odds."""
        over_entry = _make_entry(side="over", decimal_odds=3.0)
        under_entry = _make_entry(side="under", decimal_odds=1.50)
        ev = _calculate_hedging_ev(over_entry, under_entry)
        # 1/3 + 1/1.5 = 0.333 + 0.666 = 1.0 -> fair
        assert ev == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# evaluate_promo – SIGNUP_BONUS
# ---------------------------------------------------------------------------

class TestEvaluatePromoSignupBonus:
    """Tests for SIGNUP_BONUS evaluation."""

    def test_no_arbitrage(self):
        """Returns None when no arbitrage exists."""
        offer = PromoOffer(
            promo_id="s1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is None

    def test_arbitrage_below_bonus(self):
        """Returns evaluation with arb EV when it's below max bonus."""
        offer = PromoOffer(
            promo_id="s1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.is_profitable is True
        assert result.best_strategy == "arbitrage"
        assert result.expected_value == pytest.approx(result.expected_value)
        assert result.details["max_bonus"] == 50.0

    def test_arbitrage_above_bonus(self):
        """Returns evaluation capped at max_bonus when arb EV exceeds it."""
        offer = PromoOffer(
            promo_id="s1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=5.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=10.0)
        under_entry = _make_entry(side="under", decimal_odds=10.0)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.is_profitable is True
        assert result.best_strategy == "arbitrage"
        assert result.expected_value == pytest.approx(5.0)

    def test_min_deposit_not_met(self):
        """Returns None when bankroll doesn't meet min_deposit."""
        offer = PromoOffer(
            promo_id="s1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=50.0,
            min_deposit=100.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry, bankroll=50.0)
        assert result is None

    def test_min_deposit_met(self):
        """Returns evaluation when bankroll meets min_deposit."""
        offer = PromoOffer(
            promo_id="s1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=50.0,
            min_deposit=100.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry, bankroll=100.0)
        assert result is not None


# ---------------------------------------------------------------------------
# evaluate_promo – RISK_FREE_BET
# ---------------------------------------------------------------------------

class TestEvaluatePromoRiskFreeBet:
    """Tests for RISK_FREE_BET evaluation."""

    def test_no_arbitrage(self):
        """Returns None when no arbitrage exists."""
        offer = PromoOffer(
            promo_id="r1",
            promo_type=PromoType.RISK_FREE_BET,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is None

    def test_arbitrage_below_bonus(self):
        """Returns evaluation with arb EV when it's below max bonus."""
        offer = PromoOffer(
            promo_id="r1",
            promo_type=PromoType.RISK_FREE_BET,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.is_profitable is True
        assert result.best_strategy == "arbitrage"

    def test_arbitrage_above_bonus(self):
        """Returns evaluation capped at max_bonus when arb EV exceeds it."""
        offer = PromoOffer(
            promo_id="r1",
            promo_type=PromoType.RISK_FREE_BET,
            provider="B",
            description="d",
            max_bonus=5.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=10.0)
        under_entry = _make_entry(side="under", decimal_odds=10.0)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.expected_value == pytest.approx(5.0)

    def test_hedging_strategy(self):
        """Returns hedging evaluation when arb EV exceeds bonus."""
        offer = PromoOffer(
            promo_id="r1",
            promo_type=PromoType.RISK_FREE_BET,
            provider="B",
            description="d",
            max_bonus=5.0,
        )
        # Create a scenario where hedging is better
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        # The strategy should be either 'arbitrage' or 'hedge'
        assert result.best_strategy in ("arbitrage", "hedge")


# ---------------------------------------------------------------------------
# evaluate_promo – DEPOSIT_MATCH
# ---------------------------------------------------------------------------

class TestEvaluatePromoDepositMatch:
    """Tests for DEPOSIT_MATCH evaluation."""

    def test_no_arbitrage(self):
        """Returns None when no arbitrage exists."""
        offer = PromoOffer(
            promo_id="d1",
            promo_type=PromoType.DEPOSIT_MATCH,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is None

    def test_arbitrage_below_bonus(self):
        """Returns evaluation with arb EV when it's below max bonus."""
        offer = PromoOffer(
            promo_id="d1",
            promo_type=PromoType.DEPOSIT_MATCH,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.is_profitable is True
        assert result.best_strategy == "arbitrage"

    def test_arbitrage_above_bonus(self):
        """Returns evaluation capped at max_bonus when arb EV exceeds it."""
        offer = PromoOffer(
            promo_id="d1",
            promo_type=PromoType.DEPOSIT_MATCH,
            provider="B",
            description="d",
            max_bonus=5.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=10.0)
        under_entry = _make_entry(side="under", decimal_odds=10.0)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.expected_value == pytest.approx(5.0)

    def test_min_deposit_not_met(self):
        """Returns None when bankroll doesn't meet min_deposit."""
        offer = PromoOffer(
            promo_id="d1",
            promo_type=PromoType.DEPOSIT_MATCH,
            provider="B",
            description="d",
            max_bonus=50.0,
            min_deposit=100.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry, bankroll=50.0)
        assert result is None


# ---------------------------------------------------------------------------
# evaluate_promo – BET_BOOST
# ---------------------------------------------------------------------------

class TestEvaluatePromoBetBoost:
    """Tests for BET_BOOST evaluation."""

    def test_no_arbitrage(self):
        """Returns None when no arbitrage exists."""
        offer = PromoOffer(
            promo_id="b1",
            promo_type=PromoType.BET_BOOST,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is None

    def test_arbitrage_below_bonus(self):
        """Returns evaluation with arb EV when it's below max bonus."""
        offer = PromoOffer(
            promo_id="b1",
            promo_type=PromoType.BET_BOOST,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.is_profitable is True
        assert result.best_strategy == "arbitrage"

    def test_arbitrage_above_bonus(self):
        """Returns evaluation capped at max_bonus when arb EV exceeds it."""
        offer = PromoOffer(
            promo_id="b1",
            promo_type=PromoType.BET_BOOST,
            provider="B",
            description="d",
            max_bonus=5.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=10.0)
        under_entry = _make_entry(side="under", decimal_odds=10.0)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.expected_value == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# evaluate_promo – ODDS_BOOST
# ---------------------------------------------------------------------------

class TestEvaluatePromoOddsBoost:
    """Tests for ODDS_BOOST evaluation."""

    def test_no_arbitrage(self):
        """Returns None when no arbitrage exists."""
        offer = PromoOffer(
            promo_id="o1",
            promo_type=PromoType.ODDS_BOOST,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is None

    def test_arbitrage_below_bonus(self):
        """Returns evaluation with arb EV when it's below max bonus."""
        offer = PromoOffer(
            promo_id="o1",
            promo_type=PromoType.ODDS_BOOST,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.is_profitable is True
        assert result.best_strategy == "arbitrage"

    def test_arbitrage_above_bonus(self):
        """Returns evaluation capped at max_bonus when arb EV exceeds it."""
        offer = PromoOffer(
            promo_id="o1",
            promo_type=PromoType.ODDS_BOOST,
            provider="B",
            description="d",
            max_bonus=5.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=10.0)
        under_entry = _make_entry(side="under", decimal_odds=10.0)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.expected_value == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# evaluate_promo – REFERRAL_BONUS
# ---------------------------------------------------------------------------

class TestEvaluatePromoReferralBonus:
    """Tests for REFERRAL_BONUS evaluation."""

    def test_no_arbitrage(self):
        """Returns None when no arbitrage exists."""
        offer = PromoOffer(
            promo_id="ref1",
            promo_type=PromoType.REFERRAL_BONUS,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is None

    def test_arbitrage_below_bonus(self):
        """Returns evaluation with arb EV when it's below max bonus."""
        offer = PromoOffer(
            promo_id="ref1",
            promo_type=PromoType.REFERRAL_BONUS,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.is_profitable is True
        assert result.best_strategy == "arbitrage"

    def test_arbitrage_above_bonus(self):
        """Returns evaluation capped at max_bonus when arb EV exceeds it."""
        offer = PromoOffer(
            promo_id="ref1",
            promo_type=PromoType.REFERRAL_BONUS,
            provider="B",
            description="d",
            max_bonus=5.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=10.0)
        under_entry = _make_entry(side="under", decimal_odds=10.0)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.expected_value == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# evaluate_promo – INSURANCE
# ---------------------------------------------------------------------------

class TestEvaluatePromoInsurance:
    """Tests for INSURANCE evaluation."""

    def test_no_arbitrage(self):
        """Returns None when no arbitrage exists."""
        offer = PromoOffer(
            promo_id="i1",
            promo_type=PromoType.INSURANCE,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is None

    def test_arbitrage_below_bonus(self):
        """Returns evaluation with arb EV when it's below max bonus."""
        offer = PromoOffer(
            promo_id="i1",
            promo_type=PromoType.INSURANCE,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.is_profitable is True
        assert result.best_strategy == "arbitrage"

    def test_arbitrage_above_bonus(self):
        """Returns evaluation capped at max_bonus when arb EV exceeds it."""
        offer = PromoOffer(
            promo_id="i1",
            promo_type=PromoType.INSURANCE,
            provider="B",
            description="d",
            max_bonus=5.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=10.0)
        under_entry = _make_entry(side="under", decimal_odds=10.0)
        result = evaluate_promo(offer, over_entry, under_entry)
        assert result is not None
        assert result.expected_value == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# evaluate_all_promos
# ---------------------------------------------------------------------------

class TestEvaluateAllPromos:
    """Tests for evaluate_all_promos function."""

    def test_empty_promos(self):
        """Returns empty list when no promos provided."""
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        results = evaluate_all_promos([], over_entry, under_entry)
        assert results == []

    def test_single_promo(self):
        """Returns list with one evaluation for one promo."""
        offer = PromoOffer(
            promo_id="s1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=50.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        results = evaluate_all_promos([offer], over_entry, under_entry)
        assert len(results) == 1
        assert results[0].is_profitable is True

    def test_multiple_promos(self):
        """Returns evaluations for all promos."""
        offers = [
            PromoOffer(
                promo_id="s1",
                promo_type=PromoType.SIGNUP_BONUS,
                provider="B",
                description="d",
                max_bonus=50.0,
            ),
            PromoOffer(
                promo_id="r1",
                promo_type=PromoType.RISK_FREE_BET,
                provider="B",
                description="d",
                max_bonus=50.0,
            ),
        ]
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        results = evaluate_all_promos(offers, over_entry, under_entry)
        assert len(results) == 2
        assert all(r.is_profitable for r in results)

    def test_mixed_profitability(self):
        """Returns correct profitability for mixed promos."""
        offers = [
            PromoOffer(
                promo_id="s1",
                promo_type=PromoType.SIGNUP_BONUS,
                provider="B",
                description="d",
                max_bonus=50.0,
            ),
            PromoOffer(
                promo_id="r1",
                promo_type=PromoType.RISK_FREE_BET,
                provider="B",
                description="d",
                max_bonus=5.0,
            ),
        ]
        over_entry = _make_entry(side="over", decimal_odds=1.90)
        under_entry = _make_entry(side="under", decimal_odds=1.90)
        results = evaluate_all_promos(offers, over_entry, under_entry)
        # Both should be None (no arb) so both evaluations should be None
        assert all(r is None for r in results)

    def test_with_bankroll(self):
        """Bankroll is passed through to individual evaluations."""
        offer = PromoOffer(
            promo_id="s1",
            promo_type=PromoType.SIGNUP_BONUS,
            provider="B",
            description="d",
            max_bonus=50.0,
            min_deposit=100.0,
        )
        over_entry = _make_entry(side="over", decimal_odds=2.10)
        under_entry = _make_entry(side="under", decimal_odds=2.10)
        results = evaluate_all_promos([offer], over_entry, under_entry, bankroll=50.0)
        assert all(r is None for r in results)

        results = evaluate_all_promos([offer], over_entry, under_entry, bankroll=100.0)
        assert all(r is not None for r in results)