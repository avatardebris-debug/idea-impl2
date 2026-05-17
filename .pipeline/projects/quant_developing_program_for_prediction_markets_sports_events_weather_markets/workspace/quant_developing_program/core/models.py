"""Core mathematical models for prediction markets.

Provides:
    - BayesUpdater: Bayesian inference for hypothesis updating.
    - KellyCriterion: Kelly criterion for optimal bet sizing.
    - KLDivergence: Kullback-Leibler divergence calculations.
    - HawkesProcess: Hawkes process for event intensity modeling.
    - HawkesEvent: Event dataclass for Hawkes process.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional


class BayesUpdater:
    """Bayesian inference engine for hypothesis updating.

    Maintains a set of hypotheses with prior probabilities and updates
    them based on observed evidence using Bayes' theorem.

    Attributes:
        hypotheses: List of hypothesis names.
        prior: Current prior probabilities for each hypothesis.
    """

    def __init__(self, hypotheses: List[str], prior: List[float]):
        """Initialize the Bayesian updater.

        Args:
            hypotheses: List of hypothesis names.
            prior: Prior probabilities for each hypothesis.

        Raises:
            ValueError: If priors don't sum to 1 or have wrong length.
        """
        if len(hypotheses) != len(prior):
            raise ValueError("hypotheses and prior must have the same length")
        if abs(sum(prior) - 1.0) > 1e-10:
            raise ValueError("prior probabilities must sum to 1")
        if any(p < 0 for p in prior):
            raise ValueError("prior probabilities must be non-negative")

        self.hypotheses = list(hypotheses)
        self.prior = list(prior)

    def update(self, likelihood: List[float]) -> List[float]:
        """Update posterior probabilities given new evidence.

        Args:
            likelihood: Likelihood of evidence under each hypothesis.

        Returns:
            Updated posterior probabilities.

        Raises:
            ValueError: If likelihood length doesn't match hypotheses.
        """
        if len(likelihood) != len(self.hypotheses):
            raise ValueError(
                f"likelihood must have length {len(self.hypotheses)}, "
                f"got {len(likelihood)}"
            )

        # Calculate unnormalized posterior
        posterior = [p * l for p, l in zip(self.prior, likelihood)]

        # Normalize
        total = sum(posterior)
        if total == 0:
            # All likelihoods are zero - return uniform
            n = len(self.hypotheses)
            return [1.0 / n] * n

        posterior = [p / total for p in posterior]
        self.prior = posterior
        return posterior

    def predict(self, likelihood: List[float]) -> float:
        """Predict the probability of evidence using current posterior.

        Args:
            likelihood: Likelihood of evidence under each hypothesis.

        Returns:
            Predicted probability of the evidence.
        """
        return sum(p * l for p, l in zip(self.prior, likelihood))


class KellyCriterion:
    """Kelly criterion for optimal bet sizing.

    Attributes:
        kelly_fraction: Optimal fraction of bankroll to bet.
        bet_size: Dollar amount to bet.
        expected_value: Expected value of the bet.
        recommendation: "BET" or "NO_BET".
    """

    def __init__(
        self,
        kelly_fraction: float,
        bet_size: float,
        expected_value: float,
        recommendation: str,
    ):
        self.kelly_fraction = kelly_fraction
        self.bet_size = bet_size
        self.expected_value = expected_value
        self.recommendation = recommendation

    def __getitem__(self, key: str):
        """Allow dict-like access for backward compatibility."""
        return getattr(self, key)

    @classmethod
    def calculate_from_probability(
        cls,
        probability: float,
        market_prob: float,
        bankroll: float,
    ) -> "KellyCriterion":
        """Calculate Kelly criterion from probability and market odds.

        Args:
            probability: Your estimated probability of winning.
            market_prob: Market-implied probability (1/decimal_odds).
            bankroll: Total bankroll.

        Returns:
            KellyCriterion result.

        Raises:
            ValueError: If probability is invalid.
        """
        if probability < 0 or probability > 1:
            raise ValueError("probability must be between 0 and 1")

        # Kelly fraction: f = (bp - q) / b
        # where b = (1-p_market)/p_market, p = your_prob, q = 1-p
        # Simplified: f = (p - p_market) / (1 - p_market)
        if market_prob >= 1:
            raise ValueError("market_prob must be less than 1")

        decimal_odds = 1.0 / market_prob
        b = decimal_odds - 1  # net odds
        p = probability
        q = 1 - p

        if b <= 0:
            return cls(kelly_fraction=0.0, bet_size=0.0, expected_value=0.0, recommendation="NO_BET")

        kelly_fraction = (b * p - q) / b

        if kelly_fraction <= 0:
            return cls(kelly_fraction=0.0, bet_size=0.0, expected_value=0.0, recommendation="NO_BET")

        bet_size = kelly_fraction * bankroll
        expected_value = (p * (bet_size * b)) - (q * bet_size)

        return cls(
            kelly_fraction=kelly_fraction,
            bet_size=bet_size,
            expected_value=expected_value,
            recommendation="BET",
        )

    @classmethod
    def calculate_from_odds(
        cls,
        probability: float,
        decimal_odds: float,
        bankroll: float,
    ) -> "KellyCriterion":
        """Calculate Kelly criterion from probability and decimal odds.

        Args:
            probability: Your estimated probability of winning.
            decimal_odds: Decimal odds offered by the market.
            bankroll: Total bankroll.

        Returns:
            KellyCriterion result.

        Raises:
            ValueError: If probability or odds are invalid.
        """
        if probability < 0 or probability > 1:
            raise ValueError("probability must be between 0 and 1")
        if decimal_odds <= 1:
            raise ValueError("decimal_odds must be greater than 1")

        market_prob = 1.0 / decimal_odds
        return cls.calculate_from_probability(probability, market_prob, bankroll)


class KLDivergence:
    """Kullback-Leibler divergence calculations.

    Measures the difference between two probability distributions.
    """

    @staticmethod
    def calculate(p: List[float], q: List[float]) -> float:
        """Calculate KL divergence D(p || q).

        Args:
            p: First probability distribution.
            q: Second probability distribution.

        Returns:
            KL divergence value.

        Raises:
            ValueError: If distributions have different lengths or invalid values.
        """
        if len(p) != len(q):
            raise ValueError("distributions must have the same length")

        for pi, qi in zip(p, q):
            if pi < 0 or qi < 0:
                raise ValueError("probabilities must be non-negative")
            if qi == 0 and pi > 0:
                raise ValueError("q must not be zero where p is non-zero")

        return sum(pi * math.log(pi / qi) for pi, qi in zip(p, q) if pi > 0)

    @staticmethod
    def relative_entropy(p: List[float], q: List[float]) -> float:
        """Alias for KL divergence.

        Args:
            p: First probability distribution.
            q: Second probability distribution.

        Returns:
            KL divergence value.
        """
        return KLDivergence.calculate(p, q)


@dataclass
class HawkesEvent:
    """Event in a Hawkes process.

    Attributes:
        time: Time of the event.
        category: Category of the event.
    """
    time: float
    category: int


class HawkesProcess:
    """Hawkes process for modeling self-exciting events.

    Attributes:
        baseline_rate: Base event rate.
        n_categories: Number of event categories.
        events: List of observed events.
    """

    def __init__(self, baseline_rate: float, n_categories: int):
        """Initialize the Hawkes process.

        Args:
            baseline_rate: Base event rate.
            n_categories: Number of event categories.

        Raises:
            ValueError: If parameters are invalid.
        """
        if baseline_rate <= 0:
            raise ValueError("baseline_rate must be positive")
        if n_categories <= 0:
            raise ValueError("n_categories must be positive")

        self.baseline_rate = baseline_rate
        self.n_categories = n_categories
        self.events: List[HawkesEvent] = []

    def add_event(self, event: HawkesEvent) -> None:
        """Add an event to the process.

        Args:
            event: The event to add.
        """
        self.events.append(event)

    def conditional_intensity(self, t: float) -> float:
        """Calculate the conditional intensity at time t.

        Args:
            t: Time to calculate intensity at.

        Returns:
            Conditional intensity.
        """
        intensity = self.baseline_rate
        for event in self.events:
            if event.time < t:
                # Self-excitation: exponential decay
                intensity += math.exp(-(t - event.time))
        return intensity

    def simulate_events(self, duration: float, seed: Optional[int] = None) -> List[HawkesEvent]:
        """Simulate events over a time period.

        Args:
            duration: Time period to simulate.
            seed: Random seed for reproducibility.

        Returns:
            List of simulated events.
        """
        if seed is not None:
            random.seed(seed)

        events = []
        t = 0.0

        while t < duration:
            # Calculate current intensity
            intensity = self.baseline_rate
            for event in events:
                if event.time < t:
                    intensity += math.exp(-(t - event.time))

            # Generate next event time
            dt = -math.log(random.random()) / intensity
            t += dt

            if t < duration:
                category = random.randint(0, self.n_categories - 1)
                events.append(HawkesEvent(time=t, category=category))

        return events
