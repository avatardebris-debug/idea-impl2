"""Tests for quant_developing_program.core.models."""

import math
import pytest
import numpy as np

from quant_developing_program.core.models import (
    BayesUpdater,
    KellyCriterion,
    KLDivergence,
    HawkesProcess,
    HawkesEvent,
)


class TestBayesUpdater:
    def test_initialization(self):
        updater = BayesUpdater(["A", "B", "C"], [0.5, 0.3, 0.2])
        assert updater.hypotheses == ["A", "B", "C"]
        assert updater.prior == pytest.approx([0.5, 0.3, 0.2])

    def test_update_with_evidence(self):
        updater = BayesUpdater(["A", "B"], [0.5, 0.5])
        # Likelihood: P(E|A) = 0.8, P(E|B) = 0.2
        likelihood = [0.8, 0.2]
        posterior = updater.update(likelihood)
        # P(A|E) = 0.8 * 0.5 / (0.8 * 0.5 + 0.2 * 0.5) = 0.4 / 0.5 = 0.8
        assert posterior[0] == pytest.approx(0.8)
        assert posterior[1] == pytest.approx(0.2)

    def test_update_normalization(self):
        updater = BayesUpdater(["A", "B"], [0.5, 0.5])
        likelihood = [0.3, 0.7]
        posterior = updater.update(likelihood)
        assert sum(posterior) == pytest.approx(1.0)

    def test_update_invalid_likelihood_length(self):
        updater = BayesUpdater(["A", "B"], [0.5, 0.5])
        with pytest.raises(ValueError):
            updater.update([0.5])

    def test_update_zero_likelihood(self):
        updater = BayesUpdater(["A", "B"], [0.5, 0.5])
        likelihood = [0.0, 1.0]
        posterior = updater.update(likelihood)
        assert posterior[0] == pytest.approx(0.0)
        assert posterior[1] == pytest.approx(1.0)

    def test_predict(self):
        updater = BayesUpdater(["A", "B"], [0.5, 0.5])
        likelihood = [0.8, 0.2]
        updater.update(likelihood)
        # Predict next event probability
        pred = updater.predict([0.9, 0.1])
        assert 0 <= pred <= 1

    def test_predict_with_single_hypothesis(self):
        updater = BayesUpdater(["A"], [1.0])
        pred = updater.predict([0.5])
        assert pred == pytest.approx(0.5)


class TestKellyCriterion:
    def test_calculate_from_probability(self):
        result = KellyCriterion.calculate_from_probability(0.6, 0.5, 1000)
        assert result["kelly_fraction"] == pytest.approx(0.2)
        assert result["bet_size"] == pytest.approx(200.0)
        assert result["expected_value"] == pytest.approx(160.0)
        assert result["recommendation"] == "BET"

    def test_calculate_from_odds(self):
        result = KellyCriterion.calculate_from_odds(0.6, 2.0, 1000)
        assert result["kelly_fraction"] == pytest.approx(0.2)

    def test_negative_edge(self):
        result = KellyCriterion.calculate_from_probability(0.4, 0.5, 1000)
        assert result["recommendation"] == "NO_BET"
        assert result["kelly_fraction"] == pytest.approx(0.0)

    def test_zero_edge(self):
        result = KellyCriterion.calculate_from_probability(0.5, 0.5, 1000)
        assert result["recommendation"] == "NO_BET"
        assert result["kelly_fraction"] == pytest.approx(0.0)

    def test_invalid_probability(self):
        with pytest.raises(ValueError):
            KellyCriterion.calculate_from_probability(1.5, 0.5, 1000)

    def test_invalid_odds(self):
        with pytest.raises(ValueError):
            KellyCriterion.calculate_from_odds(0.6, 0.5, 1000)


class TestKLDivergence:
    def test_zero_divergence(self):
        p = [0.5, 0.5]
        q = [0.5, 0.5]
        result = KLDivergence.calculate(p, q)
        assert result == pytest.approx(0.0)

    def test_asymmetric(self):
        p = [0.9, 0.1]
        q = [0.1, 0.9]
        kl_pq = KLDivergence.calculate(p, q)
        kl_qp = KLDivergence.calculate(q, p)
        assert kl_pq > 0
        assert kl_qp > 0
        assert kl_pq != kl_qp  # KL divergence is asymmetric

    def test_invalid_length(self):
        with pytest.raises(ValueError):
            KLDivergence.calculate([0.5], [0.5, 0.5])

    def test_invalid_probability(self):
        with pytest.raises(ValueError):
            KLDivergence.calculate([1.5, -0.5], [0.5, 0.5])

    def test_zero_in_q(self):
        p = [0.5, 0.5]
        q = [0.5, 0.0]
        with pytest.raises(ValueError):
            KLDivergence.calculate(p, q)

    def test_relative_entropy(self):
        p = [0.8, 0.2]
        q = [0.6, 0.4]
        result = KLDivergence.relative_entropy(p, q)
        assert result > 0


class TestHawkesProcess:
    def test_initialization(self):
        process = HawkesProcess(baseline_rate=1.0, n_categories=1)
        assert process.baseline_rate == 1.0
        assert process.n_categories == 1

    def test_simulate_events(self):
        process = HawkesProcess(baseline_rate=1.0, n_categories=1)
        events = process.simulate_events(10.0, seed=42)
        assert len(events) > 0
        assert all(isinstance(e, HawkesEvent) for e in events)
        assert all(0 <= e.time <= 10.0 for e in events)

    def test_conditional_intensity(self):
        process = HawkesProcess(baseline_rate=1.0, n_categories=1)
        # Before any events, intensity should be baseline
        intensity = process.conditional_intensity(0.0)
        assert intensity == pytest.approx(1.0)

    def test_intensity_after_event(self):
        process = HawkesProcess(baseline_rate=1.0, n_categories=1)
        process.add_event(HawkesEvent(time=1.0, category=0))
        intensity = process.conditional_intensity(1.5)
        assert intensity > 1.0  # Should be higher due to self-excitation

    def test_simulate_with_seed(self):
        process1 = HawkesProcess(baseline_rate=1.0, n_categories=1)
        process2 = HawkesProcess(baseline_rate=1.0, n_categories=1)
        events1 = process1.simulate_events(10.0, seed=42)
        events2 = process2.simulate_events(10.0, seed=42)
        assert len(events1) == len(events2)
        assert all(e1.time == e2.time for e1, e2 in zip(events1, events2))

    def test_invalid_baseline_rate(self):
        with pytest.raises(ValueError):
            HawkesProcess(baseline_rate=-1.0, n_categories=1)

    def test_invalid_n_categories(self):
        with pytest.raises(ValueError):
            HawkesProcess(baseline_rate=1.0, n_categories=0)
