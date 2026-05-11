"""Prediction engine for Chronovision2.

Provides the PredictionEngine class that takes real-world observations,
runs multiple world simulations in parallel with different hypotheses,
and produces a composite prediction.
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from chronovision2.core.world_simulator import WorldSimulator


@dataclass
class HypothesisResult:
    """Result from a single hypothesis simulation."""
    hypothesis_id: str
    predicted_state: Dict[str, Any]
    trajectory: List[Dict[str, Any]]
    weight: float
    hypothesis_config: Dict[str, Any]
    simulation_time: float = 0.0


@dataclass
class PredictionResult:
    """Composite prediction result from the prediction engine."""
    prediction: Dict[str, Any]
    hypothesis_results: List[HypothesisResult]
    composite_method: str
    total_time: float
    timestamp: float = field(default_factory=time.time)

    def get_per_hypothesis(self, key: str) -> List[Any]:
        """Get a specific field from all hypothesis predictions."""
        return [hr.predicted_state.get(key) for hr in self.hypothesis_results]

    def get_aggregate(self, key: str) -> Any:
        """Get the aggregate value for a specific field."""
        values = [hr.predicted_state.get(key) for hr in self.hypothesis_results]
        values = [v for v in values if v is not None]
        if not values:
            return None
        return np.mean(values)


class PredictionEngine:
    """Runs multiple world simulations with different hypotheses and produces
    a composite prediction.

    Attributes:
        hypothesis_configs: List of hypothesis configuration dicts.
        composite_method: Method for combining predictions.
        time_horizon: Default simulation horizon.
    """

    def __init__(
        self,
        hypothesis_configs: Optional[List[Dict[str, Any]]] = None,
        composite_method: str = "weighted_average",
        time_horizon: int = 10,
    ) -> None:
        """Initialize the PredictionEngine.

        Args:
            hypothesis_configs: List of hypothesis config dicts. Each should
                contain at minimum a 'hypothesis_id' key.
            composite_method: How to combine predictions. Options:
                - weighted_average: Weighted mean of predictions
                - median: Median of predictions
                - max_likelihood: Most likely prediction
            time_horizon: Default number of steps to simulate.
        """
        self.hypothesis_configs = hypothesis_configs or []
        self.composite_method = composite_method
        self.time_horizon = time_horizon
        self._results: List[PredictionResult] = []

    def add_hypothesis(self, config: Dict[str, Any]) -> None:
        """Add a hypothesis configuration.

        Args:
            config: Hypothesis config dict with at least 'hypothesis_id'.
        """
        if "hypothesis_id" not in config:
            raise ValueError("Hypothesis config must contain 'hypothesis_id'")
        self.hypothesis_configs.append(config)

    def predict(
        self,
        initial_state: Dict[str, Any],
        num_steps: Optional[int] = None,
    ) -> PredictionResult:
        """Run simulations for all hypotheses and produce a composite prediction.

        Args:
            initial_state: The real-world observation to use as initial state.
            num_steps: Number of steps to simulate. Defaults to time_horizon.

        Returns:
            PredictionResult with per-hypothesis and aggregate outputs.
        """
        if num_steps is None:
            num_steps = self.time_horizon

        start_time = time.time()
        hypothesis_results: List[HypothesisResult] = []

        for config in self.hypothesis_configs:
            hyp_id = config.get("hypothesis_id", f"hyp_{len(hypothesis_results)}")
            hyp_start = time.time()

            # Build simulator for this hypothesis
            sim = WorldSimulator(
                initial_state=copy.deepcopy(initial_state),
                hypothesis_id=hyp_id,
                time_horizon=num_steps,
                random_seed=config.get("random_seed"),
                rules=config.get("rules", {}),
            )

            # Run simulation
            trajectory = sim.simulate(num_steps=num_steps)
            predicted_state = trajectory[-1]  # Final state is the prediction

            hyp_time = time.time() - hyp_start
            weight = config.get("weight", 1.0)

            hypothesis_results.append(HypothesisResult(
                hypothesis_id=hyp_id,
                predicted_state=predicted_state,
                trajectory=trajectory,
                weight=weight,
                hypothesis_config=config,
                simulation_time=hyp_time,
            ))

        total_time = time.time() - start_time

        # Compute composite prediction
        prediction = self._compute_composite(hypothesis_results)

        result = PredictionResult(
            prediction=prediction,
            hypothesis_results=hypothesis_results,
            composite_method=self.composite_method,
            total_time=total_time,
        )
        self._results.append(result)
        return result

    def predict_batch(
        self,
        initial_states: List[Dict[str, Any]],
        num_steps: Optional[int] = None,
    ) -> List[PredictionResult]:
        """Run predictions for multiple initial states.

        Args:
            initial_states: List of initial state dicts.
            num_steps: Number of steps to simulate.

        Returns:
            List of PredictionResult objects.
        """
        return [self.predict(state, num_steps) for state in initial_states]

    def _compute_composite(
        self, hypothesis_results: List[HypothesisResult]
    ) -> Dict[str, Any]:
        """Compute the composite prediction from hypothesis results."""
        if not hypothesis_results:
            return {}

        if self.composite_method == "weighted_average":
            return self._weighted_average(hypothesis_results)
        elif self.composite_method == "median":
            return self._median(hypothesis_results)
        elif self.composite_method == "max_likelihood":
            return self._max_likelihood(hypothesis_results)
        else:
            raise ValueError(f"Unknown composite method: {self.composite_method}")

    def _weighted_average(
        self, hypothesis_results: List[HypothesisResult]
    ) -> Dict[str, Any]:
        """Compute weighted average of predictions."""
        total_weight = sum(hr.weight for hr in hypothesis_results)
        if total_weight == 0:
            total_weight = 1.0

        composite: Dict[str, Any] = {}
        for hr in hypothesis_results:
            for key, value in hr.predicted_state.items():
                if isinstance(value, (int, float, np.floating, np.integer)):
                    if key not in composite:
                        composite[key] = 0.0
                    composite[key] += float(value) * hr.weight / total_weight
                else:
                    if key not in composite:
                        composite[key] = value

        return composite

    def _median(
        self, hypothesis_results: List[HypothesisResult]
    ) -> Dict[str, Any]:
        """Compute median of predictions."""
        composite: Dict[str, Any] = {}
        for key in hypothesis_results[0].predicted_state:
            values = [
                hr.predicted_state[key]
                for hr in hypothesis_results
                if hr.predicted_state.get(key) is not None
            ]
            if values:
                composite[key] = float(np.median(values))
        return composite

    def _max_likelihood(
        self, hypothesis_results: List[HypothesisResult]
    ) -> Dict[str, Any]:
        """Return the prediction from the highest-weighted hypothesis."""
        best = max(hypothesis_results, key=lambda hr: hr.weight)
        return copy.deepcopy(best.predicted_state)

    def get_last_result(self) -> Optional[PredictionResult]:
        """Get the most recent prediction result."""
        return self._results[-1] if self._results else None

    def get_all_results(self) -> List[PredictionResult]:
        """Get all prediction results."""
        return list(self._results)
