"""World simulation engine for Chronovision2.

Provides the WorldSimulator class that creates and steps forward a simulated
world state given an initial observation and a set of rules/hypotheses.
Stepping is deterministic and reproducible when a random seed is provided.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
from typing import Any, Dict, List, Optional

import numpy as np


class WorldSimulator:
    """Simulates a world state forward in time using rules/hypotheses.

    The simulator maintains an internal state dict and applies transformation
    rules (hypotheses) to step the state forward. Each step produces a new
    state that is a deterministic function of the previous state and the
    active hypothesis configuration.

    Attributes:
        initial_state: The starting state dict.
        current_state: The current simulated state (updated on each step).
        hypothesis_id: Identifier for the hypothesis used.
        time_step: Current simulation time step.
        random_state: Internal numpy RandomState for reproducibility.
    """

    def __init__(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        hypothesis_id: str = "default",
        time_horizon: int = 10,
        random_seed: Optional[int] = None,
        rules: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the WorldSimulator.

        Args:
            initial_state: Starting state dict. If None, starts with empty state.
            hypothesis_id: Identifier for the hypothesis.
            time_horizon: Default number of steps to simulate.
            random_seed: Seed for reproducibility.
            rules: Dict of rule configurations to apply during simulation.
        """
        self.initial_state = copy.deepcopy(initial_state) if initial_state else {}
        self.current_state = copy.deepcopy(self.initial_state)
        self.hypothesis_id = hypothesis_id
        self.time_horizon = time_horizon
        self.time_step = 0
        self.rules = rules or {}
        self._rng = np.random.RandomState(random_seed)
        self._history: List[Dict[str, Any]] = [copy.deepcopy(self.initial_state)]

    @property
    def state(self) -> Dict[str, Any]:
        """Return a deep copy of the current state."""
        return copy.deepcopy(self.current_state)

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Return a deep copy of the simulation history."""
        return [copy.deepcopy(s) for s in self._history]

    def reset(self, initial_state: Optional[Dict[str, Any]] = None) -> "WorldSimulator":
        """Reset the simulator to its initial state.

        Args:
            initial_state: Optional new initial state. If None, uses original.

        Returns:
            self for chaining.
        """
        if initial_state is not None:
            self.initial_state = copy.deepcopy(initial_state)
        self.current_state = copy.deepcopy(self.initial_state)
        self.time_step = 0
        self._history = [copy.deepcopy(self.initial_state)]
        return self

    def step(self, num_steps: int = 1) -> Dict[str, Any]:
        """Step the simulation forward by num_steps.

        Applies transformation rules to the current state to produce
        a forward-predicted state. The transformation is deterministic
        given the same hypothesis configuration and random seed.

        Args:
            num_steps: Number of time steps to advance.

        Returns:
            The state after stepping.
        """
        for _ in range(num_steps):
            self._apply_rules()
            self._apply_hypothesis_effects()
            self.time_step += 1
            self._history.append(copy.deepcopy(self.current_state))
        return self.state

    def simulate(self, num_steps: Optional[int] = None) -> List[Dict[str, Any]]:
        """Run a full simulation for the given number of steps.

        Args:
            num_steps: Number of steps to simulate. Defaults to time_horizon.

        Returns:
            List of states at each time step (including initial state).
        """
        if num_steps is None:
            num_steps = self.time_horizon
        trajectory = [copy.deepcopy(self.initial_state)]
        for _ in range(num_steps):
            self._apply_rules()
            self._apply_hypothesis_effects()
            self.time_step += 1
            trajectory.append(copy.deepcopy(self.current_state))
        return trajectory

    def get_deterministic_hash(self) -> str:
        """Return a hash of the current state for reproducibility checks.

        Returns:
            Hex digest of the current state.
        """
        state_str = json.dumps(self.current_state, sort_keys=True, default=str)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]

    def _apply_rules(self) -> None:
        """Apply configured transformation rules to the current state."""
        for rule_name, rule_config in self.rules.items():
            self.current_state = self._apply_single_rule(rule_name, rule_config)

    def _apply_single_rule(
        self, rule_name: str, rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a single named rule to the current state.

        Supported rule types:
            - linear: state *= coefficient + intercept
            - growth: state *= (1 + growth_rate)
            - noise: add Gaussian noise to numeric fields
            - decay: state *= (1 - decay_rate)
            - clamp: clamp values to [min_val, max_val]
            - custom: call a registered custom function
        """
        state = self.current_state

        # Handle nested state with 'fields' key
        fields = rule_config.get("fields", None)
        if fields is not None:
            # Apply to specific fields
            for field_name, field_config in fields.items():
                if field_name in state:
                    state[field_name] = self._apply_rule_to_value(
                        state[field_name], rule_config
                    )
        else:
            # Apply to all numeric values in state
            new_state = {}
            for key, value in state.items():
                if isinstance(value, (int, float, np.floating, np.integer)):
                    new_state[key] = self._apply_rule_to_value(value, rule_config)
                else:
                    new_state[key] = value
            state = new_state

        return state

    def _apply_rule_to_value(self, value: Any, rule_config: Dict[str, Any]) -> Any:
        """Apply a rule transformation to a single numeric value."""
        rule_type = rule_config.get("type", "linear")
        coefficient = rule_config.get("coefficient", 1.0)
        intercept = rule_config.get("intercept", 0.0)
        growth_rate = rule_config.get("growth_rate", 0.0)
        decay_rate = rule_config.get("decay_rate", 0.0)
        noise_scale = rule_config.get("noise_scale", 0.0)
        min_val = rule_config.get("min_val", None)
        max_val = rule_config.get("max_val", None)

        if not isinstance(value, (int, float, np.floating, np.integer)):
            return value

        val = float(value)

        if rule_type == "linear":
            val = val * coefficient + intercept
        elif rule_type == "growth":
            val = val * (1.0 + growth_rate)
        elif rule_type == "decay":
            val = val * (1.0 - decay_rate)
        elif rule_type == "noise":
            noise = self._rng.normal(0, noise_scale)
            val = val + noise
        elif rule_type == "clamp":
            if min_val is not None:
                val = max(val, float(min_val))
            if max_val is not None:
                val = min(val, float(max_val))
        elif rule_type == "custom":
            custom_fn = rule_config.get("function", None)
            if custom_fn is not None:
                val = custom_fn(val)

        return val

    def _apply_hypothesis_effects(self) -> None:
        """Apply hypothesis-specific effects to the current state.

        Hypothesis effects modify the state based on the hypothesis_id.
        Each hypothesis can define its own transformation logic.
        """
        # Default hypothesis: no additional effects beyond rules
        if self.hypothesis_id == "default":
            return

        # Apply hypothesis-specific modifications
        hypothesis_effects = self.rules.get("hypothesis_effects", {})
        if self.hypothesis_id in hypothesis_effects:
            effect = hypothesis_effects[self.hypothesis_id]
            effect_type = effect.get("type", "none")

            if effect_type == "bias":
                bias = effect.get("bias", 0.0)
                for key, value in self.current_state.items():
                    if isinstance(value, (int, float, np.floating, np.integer)):
                        self.current_state[key] = value + bias
            elif effect_type == "scale":
                scale = effect.get("scale", 1.0)
                for key, value in self.current_state.items():
                    if isinstance(value, (int, float, np.floating, np.integer)):
                        self.current_state[key] = value * scale
            elif effect_type == "drift":
                drift = effect.get("drift", 0.0)
                for key, value in self.current_state.items():
                    if isinstance(value, (int, float, np.floating, np.integer)):
                        self.current_state[key] = value + drift * self.time_step

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the simulator state to a dict."""
        return {
            "initial_state": self.initial_state,
            "current_state": self.current_state,
            "hypothesis_id": self.hypothesis_id,
            "time_step": self.time_step,
            "time_horizon": self.time_horizon,
            "rules": self.rules,
            "deterministic_hash": self.get_deterministic_hash(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldSimulator":
        """Deserialize a WorldSimulator from a dict."""
        sim = cls(
            initial_state=data.get("initial_state"),
            hypothesis_id=data.get("hypothesis_id", "default"),
            time_horizon=data.get("time_horizon", 10),
            rules=data.get("rules"),
        )
        sim.current_state = data.get("current_state", {})
        sim.time_step = data.get("time_step", 0)
        return sim
