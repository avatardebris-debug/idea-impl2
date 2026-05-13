"""Tests for WorldSimulator."""

import copy
import pytest
import numpy as np

from chronovision2.core.world_simulator import WorldSimulator


class TestWorldSimulatorInit:
    """Tests for WorldSimulator initialization."""

    def test_default_init(self):
        """Default initialization should produce empty state."""
        sim = WorldSimulator()
        assert sim.initial_state == {}
        assert sim.current_state == {}
        assert sim.hypothesis_id == "default"
        assert sim.time_horizon == 10
        assert sim.time_step == 0
        assert len(sim.history) == 1

    def test_init_with_state(self):
        """Initialization with initial state should copy it."""
        initial = {"x": 1, "y": 2}
        sim = WorldSimulator(initial_state=initial)
        assert sim.initial_state == {"x": 1, "y": 2}
        assert sim.current_state == {"x": 1, "y": 2}
        # Verify deep copy
        initial["x"] = 999
        assert sim.initial_state["x"] == 1

    def test_init_with_seed(self):
        """Initialization with seed should produce reproducible results."""
        sim1 = WorldSimulator(
            initial_state={"x": 10},
            random_seed=42,
            rules={"growth": {"type": "growth", "growth_rate": 0.1}}
        )
        sim2 = WorldSimulator(
            initial_state={"x": 10},
            random_seed=42,
            rules={"growth": {"type": "growth", "growth_rate": 0.1}}
        )
        # Both should produce same results
        assert sim1.get_deterministic_hash() == sim2.get_deterministic_hash()

    def test_init_with_rules(self):
        """Initialization with rules should store them."""
        rules = {"test_rule": {"type": "linear", "coefficient": 2.0}}
        sim = WorldSimulator(initial_state={"x": 5}, rules=rules)
        assert sim.rules == rules


class TestWorldSimulatorStep:
    """Tests for WorldSimulator stepping."""

    def test_step_single(self):
        """Single step should advance time and update state."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            rules={"growth": {"type": "growth", "growth_rate": 0.1}}
        )
        new_state = sim.step(num_steps=1)
        assert sim.time_step == 1
        assert new_state["x"] == pytest.approx(11.0)
        assert len(sim.history) == 2

    def test_step_multiple(self):
        """Multiple steps should advance time correctly."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            rules={"growth": {"type": "growth", "growth_rate": 0.1}}
        )
        new_state = sim.step(num_steps=3)
        assert sim.time_step == 3
        # 10 * 1.1^3 = 13.31
        assert new_state["x"] == pytest.approx(13.31)
        assert len(sim.history) == 4

    def test_step_no_rules(self):
        """Stepping with no rules should keep state unchanged."""
        sim = WorldSimulator(initial_state={"x": 5})
        new_state = sim.step(num_steps=1)
        assert new_state["x"] == 5
        assert sim.time_step == 1

    def test_step_with_linear_rule(self):
        """Linear rule should apply coefficient and intercept."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            rules={"linear": {"type": "linear", "coefficient": 2.0, "intercept": 3}}
        )
        new_state = sim.step(num_steps=1)
        assert new_state["x"] == pytest.approx(23.0)  # 10*2 + 3

    def test_step_with_decay_rule(self):
        """Decay rule should reduce values."""
        sim = WorldSimulator(
            initial_state={"x": 100},
            rules={"decay": {"type": "decay", "decay_rate": 0.1}}
        )
        new_state = sim.step(num_steps=1)
        assert new_state["x"] == pytest.approx(90.0)

    def test_step_with_clamp_rule(self):
        """Clamp rule should limit values."""
        sim = WorldSimulator(
            initial_state={"x": 150},
            rules={"clamp": {"type": "clamp", "min_val": 0, "max_val": 100}}
        )
        new_state = sim.step(num_steps=1)
        assert new_state["x"] == pytest.approx(100.0)

    def test_step_with_noise_rule(self):
        """Noise rule should add random noise."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            random_seed=42,
            rules={"noise": {"type": "noise", "noise_scale": 1.0}}
        )
        new_state = sim.step(num_steps=1)
        # With seed 42, the noise should be deterministic
        assert new_state["x"] != 10.0  # Noise was added
        assert isinstance(new_state["x"], float)


class TestWorldSimulatorSimulate:
    """Tests for WorldSimulator simulation."""

    def test_simulate_default_horizon(self):
        """Simulate with default horizon should run time_horizon steps."""
        sim = WorldSimulator(
            initial_state={"x": 1},
            time_horizon=5,
            rules={"growth": {"type": "growth", "growth_rate": 0.0}}
        )
        trajectory = sim.simulate()
        assert len(trajectory) == 6  # initial + 5 steps
        assert sim.time_step == 5

    def test_simulate_custom_steps(self):
        """Simulate with custom steps should run that many steps."""
        sim = WorldSimulator(
            initial_state={"x": 1},
            time_horizon=10,
            rules={"growth": {"type": "growth", "growth_rate": 0.0}}
        )
        trajectory = sim.simulate(num_steps=3)
        assert len(trajectory) == 4  # initial + 3 steps
        assert sim.time_step == 3

    def test_simulate_trajectory_contains_initial(self):
        """Trajectory should start with initial state."""
        initial = {"x": 42, "y": 99}
        sim = WorldSimulator(initial_state=initial)
        trajectory = sim.simulate(num_steps=1)
        assert trajectory[0] == initial


class TestWorldSimulatorReset:
    """Tests for WorldSimulator reset."""

    def test_reset_to_initial(self):
        """Reset should restore initial state."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            rules={"growth": {"type": "growth", "growth_rate": 0.1}}
        )
        sim.step(num_steps=5)
        assert sim.time_step == 5
        sim.reset()
        assert sim.time_step == 0
        assert sim.current_state == {"x": 10}

    def test_reset_with_new_state(self):
        """Reset with new state should use it."""
        sim = WorldSimulator(initial_state={"x": 10})
        sim.reset(initial_state={"x": 20})
        assert sim.initial_state == {"x": 20}
        assert sim.current_state == {"x": 20}

    def test_reset_returns_self(self):
        """Reset should return self for chaining."""
        sim = WorldSimulator()
        assert sim.reset() is sim


class TestWorldSimulatorProperties:
    """Tests for WorldSimulator properties."""

    def test_state_property(self):
        """State property should return deep copy."""
        sim = WorldSimulator(initial_state={"x": 10})
        state1 = sim.state
        state1["x"] = 999
        assert sim.state["x"] == 10  # Original unchanged

    def test_history_property(self):
        """History property should return deep copy."""
        sim = WorldSimulator(initial_state={"x": 10})
        sim.step(num_steps=1)
        hist1 = sim.history
        hist1[0]["x"] = 999
        assert sim.history[0]["x"] == 10  # Original unchanged

    def test_deterministic_hash(self):
        """Hash should be consistent for same state."""
        sim = WorldSimulator(initial_state={"x": 10})
        hash1 = sim.get_deterministic_hash()
        hash2 = sim.get_deterministic_hash()
        assert hash1 == hash2
        assert len(hash1) == 16  # First 16 chars of SHA256


class TestWorldSimulatorSerialization:
    """Tests for WorldSimulator serialization."""

    def test_to_dict(self):
        """to_dict should serialize all attributes."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            hypothesis_id="test",
            time_horizon=5,
            rules={"growth": {"type": "growth", "growth_rate": 0.1}}
        )
        sim.step(num_steps=2)
        data = sim.to_dict()
        assert data["initial_state"] == {"x": 10}
        assert data["hypothesis_id"] == "test"
        assert data["time_horizon"] == 5
        assert data["time_step"] == 2

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            hypothesis_id="test",
            time_horizon=5,
            rules={"growth": {"type": "growth", "growth_rate": 0.1}}
        )
        sim.step(num_steps=2)
        data = sim.to_dict()
        sim2 = WorldSimulator.from_dict(data)
        assert sim2.initial_state == {"x": 10}
        assert sim2.hypothesis_id == "test"
        assert sim2.time_horizon == 5
        assert sim2.time_step == 2


class TestWorldSimulatorHypothesisEffects:
    """Tests for hypothesis-specific effects."""

    def test_default_hypothesis_no_effect(self):
        """Default hypothesis should have no additional effects."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            hypothesis_id="default",
            rules={"growth": {"type": "growth", "growth_rate": 0.1}}
        )
        new_state = sim.step(num_steps=1)
        assert new_state["x"] == pytest.approx(11.0)

    def test_bias_effect(self):
        """Bias effect should add constant to all numeric fields."""
        sim = WorldSimulator(
            initial_state={"x": 10, "y": 20},
            hypothesis_id="biased",
            rules={
                "hypothesis_effects": {
                    "biased": {"type": "bias", "bias": 5.0}
                }
            }
        )
        new_state = sim.step(num_steps=1)
        assert new_state["x"] == pytest.approx(15.0)
        assert new_state["y"] == pytest.approx(25.0)

    def test_scale_effect(self):
        """Scale effect should multiply all numeric fields."""
        sim = WorldSimulator(
            initial_state={"x": 10, "y": 20},
            hypothesis_id="scaled",
            rules={
                "hypothesis_effects": {
                    "scaled": {"type": "scale", "scale": 2.0}
                }
            }
        )
        new_state = sim.step(num_steps=1)
        assert new_state["x"] == pytest.approx(20.0)
        assert new_state["y"] == pytest.approx(40.0)

    def test_drift_effect(self):
        """Drift effect should add time-dependent value."""
        sim = WorldSimulator(
            initial_state={"x": 10},
            hypothesis_id="drifting",
            rules={
                "hypothesis_effects": {
                    "drifting": {"type": "drift", "drift": 1.0}
                }
            }
        )
        sim.step(num_steps=1)
        new_state = sim.step(num_steps=1)
        # After 2 steps: step 1 adds 1.0*1=1.0, step 2 adds 1.0*2=2.0, total=3.0
        assert new_state["x"] == pytest.approx(13.0)


class TestWorldSimulatorEdgeCases:
    """Tests for edge cases."""

    def test_step_zero(self):
        """Stepping zero times should not change state."""
        sim = WorldSimulator(initial_state={"x": 10})
        new_state = sim.step(num_steps=0)
        assert new_state["x"] == 10
        assert sim.time_step == 0

    def test_empty_state(self):
        """Empty state should be handled gracefully."""
        sim = WorldSimulator()
        new_state = sim.step(num_steps=1)
        assert new_state == {}

    def test_non_numeric_fields(self):
        """Non-numeric fields should be preserved."""
        sim = WorldSimulator(
            initial_state={"x": 10, "name": "test", "active": True}
        )
        new_state = sim.step(num_steps=1)
        assert new_state["name"] == "test"
        assert new_state["active"] is True

    def test_rules_with_fields(self):
        """Rules with specific fields should only affect those fields."""
        sim = WorldSimulator(
            initial_state={"x": 10, "y": 20},
            rules={
                "linear": {
                    "type": "linear",
                    "coefficient": 2.0,
                    "fields": {"x": {}}
                }
            }
        )
        new_state = sim.step(num_steps=1)
        assert new_state["x"] == pytest.approx(20.0)
        assert new_state["y"] == 20  # Unchanged
