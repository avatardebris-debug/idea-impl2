"""Unit tests for the CostCalculator module.

Tests cost calculation logic:
- Base cost formula
- Volume cost
- Distance simulation determinism
- Priority multipliers
- Empty shipment list
- Individual shipment cost breakdown accuracy
"""

import pytest
from logistics_csv_optimizer.calculator import (
    CostCalculator,
    BASE_COST_PER_KG,
    VOLUME_COST_PER_M3,
    DISTANCE_COST_PER_1000KM,
    PRIORITY_MULTIPLIERS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

def _make_shipment(**overrides):
    """Helper to create a minimal shipment dict with defaults."""
    base = {
        "origin": "New York",
        "destination": "Chicago",
        "weight": 100.0,
        "priority": "standard",
        "length": 0,
        "width": 0,
        "height": 0,
        "description": "",
    }
    base.update(overrides)
    return base


# ── Empty shipment list ──────────────────────────────────────────────────

class TestEmptyShipmentList:
    """Tests for handling empty shipment lists."""

    def test_calculate_empty_list(self):
        result = CostCalculator.calculate([])
        assert result["per_shipment"] == []
        assert result["total_cost"] == 0.0


# ── Base cost formula ─────────────────────────────────────────────────────

class TestBaseCost:
    """Tests for base cost calculation (weight * BASE_COST_PER_KG)."""

    def test_base_cost_formula(self):
        shipment = _make_shipment(weight=100.0)
        result = CostCalculator.calculate([shipment])
        cost_entry = result["per_shipment"][0]
        expected_base = 100.0 * BASE_COST_PER_KG
        assert cost_entry["base_cost"] == round(expected_base, 2)

    def test_base_cost_zero_weight(self):
        shipment = _make_shipment(weight=0.0)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["base_cost"] == 0.0

    def test_base_cost_large_weight(self):
        shipment = _make_shipment(weight=10000.0)
        result = CostCalculator.calculate([shipment])
        expected_base = 10000.0 * BASE_COST_PER_KG
        assert result["per_shipment"][0]["base_cost"] == round(expected_base, 2)


# ── Volume cost ───────────────────────────────────────────────────────────

class TestVolumeCost:
    """Tests for volume cost calculation."""

    def test_volume_cost_with_dimensions(self):
        shipment = _make_shipment(length=100, width=50, height=40)
        result = CostCalculator.calculate([shipment])
        cost_entry = result["per_shipment"][0]
        volume_m3 = (100 * 50 * 40) / 1_000_000
        expected_volume = volume_m3 * VOLUME_COST_PER_M3
        assert cost_entry["volume_cost"] == round(expected_volume, 2)

    def test_volume_cost_zero_dimensions(self):
        shipment = _make_shipment(length=0, width=0, height=0)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["volume_cost"] == 0.0

    def test_volume_cost_missing_dimensions_defaults_to_zero(self):
        shipment = {"origin": "A", "destination": "B", "weight": 10.0, "priority": "standard"}
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["volume_cost"] == 0.0

    def test_volume_cost_none_dimensions_defaults_to_zero(self):
        shipment = {"origin": "A", "destination": "B", "weight": 10.0, "priority": "standard",
                     "length": None, "width": None, "height": None}
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["volume_cost"] == 0.0


# ── Distance simulation determinism ──────────────────────────────────────

class TestDistanceSimulation:
    """Tests for distance calculation and determinism."""

    def test_same_route_same_distance(self):
        s1 = _make_shipment(origin="New York", destination="Chicago")
        s2 = _make_shipment(origin="New York", destination="Chicago")
        r1 = CostCalculator.calculate([s1])
        r2 = CostCalculator.calculate([s2])
        assert r1["per_shipment"][0]["distance_km"] == r2["per_shipment"][0]["distance_km"]

    def test_reverse_route_same_distance(self):
        s1 = _make_shipment(origin="New York", destination="Chicago")
        s2 = _make_shipment(origin="Chicago", destination="New York")
        r1 = CostCalculator.calculate([s1])
        r2 = CostCalculator.calculate([s2])
        assert r1["per_shipment"][0]["distance_km"] == r2["per_shipment"][0]["distance_km"]

    def test_distance_is_positive(self):
        s = _make_shipment(origin="New York", destination="Chicago")
        r = CostCalculator.calculate([s])
        assert r["per_shipment"][0]["distance_km"] > 0

    def test_distance_factor_formula(self):
        s = _make_shipment(origin="New York", destination="Chicago")
        r = CostCalculator.calculate([s])
        dist = r["per_shipment"][0]["distance_km"]
        expected_factor = 1.0 + (dist / 1000.0) * DISTANCE_COST_PER_1000KM
        assert r["per_shipment"][0]["distance_factor"] == round(expected_factor, 4)


# ── Priority multipliers ──────────────────────────────────────────────────

class TestPriorityMultipliers:
    """Tests for priority multiplier application."""

    def test_standard_multiplier(self):
        shipment = _make_shipment(priority="standard")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["priority_multiplier"] == PRIORITY_MULTIPLIERS["standard"]

    def test_express_multiplier(self):
        shipment = _make_shipment(priority="express")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["priority_multiplier"] == PRIORITY_MULTIPLIERS["express"]

    def test_overnight_multiplier(self):
        shipment = _make_shipment(priority="overnight")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["priority_multiplier"] == PRIORITY_MULTIPLIERS["overnight"]

    def test_cost_applies_multiplier(self):
        """Verify that the final cost includes the priority multiplier."""
        s_standard = _make_shipment(priority="standard", weight=100.0)
        s_express = _make_shipment(priority="express", weight=100.0)
        r_std = CostCalculator.calculate([s_standard])
        r_exp = CostCalculator.calculate([s_express])
        # Express should be more expensive due to multiplier
        assert r_exp["per_shipment"][0]["cost"] > r_std["per_shipment"][0]["cost"]
        ratio = r_exp["per_shipment"][0]["cost"] / r_std["per_shipment"][0]["cost"]
        expected_ratio = PRIORITY_MULTIPLIERS["express"] / PRIORITY_MULTIPLIERS["standard"]
        assert abs(ratio - expected_ratio) < 0.01


# ── Individual shipment cost breakdown accuracy ──────────────────────────

class TestCostBreakdownAccuracy:
    """Tests for individual shipment cost calculation accuracy."""

    def test_cost_formula(self):
        """cost = (base_cost + volume_cost) * distance_factor * priority_multiplier"""
        shipment = _make_shipment(
            origin="New York",
            destination="Chicago",
            weight=100.0,
            priority="express",
            length=100,
            width=50,
            height=40,
        )
        result = CostCalculator.calculate([shipment])
        entry = result["per_shipment"][0]

        base = entry["base_cost"]
        vol = entry["volume_cost"]
        dist_factor = entry["distance_factor"]
        mult = entry["priority_multiplier"]

        expected_cost = (base + vol) * dist_factor * mult
        assert abs(entry["cost"] - round(expected_cost, 2)) < 0.01

    def test_total_cost_is_sum(self):
        shipments = [
            _make_shipment(origin="A", destination="B", weight=100.0, priority="standard"),
            _make_shipment(origin="C", destination="D", weight=200.0, priority="express"),
            _make_shipment(origin="E", destination="F", weight=50.0, priority="overnight"),
        ]
        result = CostCalculator.calculate(shipments)
        total = sum(e["cost"] for e in result["per_shipment"])
        assert abs(result["total_cost"] - round(total, 2)) < 0.01

    def test_cost_is_positive(self):
        shipment = _make_shipment(weight=1.0, priority="standard")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["cost"] > 0

    def test_cost_is_zero_for_zero_weight_zero_volume(self):
        shipment = _make_shipment(weight=0.0, length=0, width=0, height=0)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["cost"] == 0.0


# ── _calculate_single helper ────────────────────────────────────────────

class TestCalculateSingle:
    """Tests for the _calculate_single internal method."""

    def test_returns_dict_with_all_keys(self):
        shipment = _make_shipment()
        result = CostCalculator._calculate_single(shipment)
        expected_keys = {
            "origin", "destination", "weight", "priority",
            "distance_km", "base_cost", "volume_cost",
            "distance_factor", "priority_multiplier", "cost",
        }
        assert set(result.keys()) == expected_keys

    def test_distance_km_is_float(self):
        shipment = _make_shipment()
        result = CostCalculator._calculate_single(shipment)
        assert isinstance(result["distance_km"], float)

    def test_cost_is_float(self):
        shipment = _make_shipment()
        result = CostCalculator._calculate_single(shipment)
        assert isinstance(result["cost"], float)

    def test_none_weight_handled(self):
        shipment = _make_shipment(weight=None)
        result = CostCalculator._calculate_single(shipment)
        assert result["base_cost"] == 0.0

    def test_none_priority_defaults_to_standard(self):
        shipment = _make_shipment(priority=None)
        result = CostCalculator._calculate_single(shipment)
        assert result["priority_multiplier"] == PRIORITY_MULTIPLIERS["standard"]


# ── Multiple shipments ──────────────────────────────────────────────────

class TestMultipleShipments:
    """Tests for calculating costs for multiple shipments."""

    def test_multiple_shipments_returned(self):
        shipments = [
            _make_shipment(origin="A", destination="B", weight=10.0),
            _make_shipment(origin="C", destination="D", weight=20.0),
        ]
        result = CostCalculator.calculate(shipments)
        assert len(result["per_shipment"]) == 2

    def test_total_cost_accurate(self):
        shipments = [
            _make_shipment(origin="A", destination="B", weight=100.0, priority="standard"),
            _make_shipment(origin="C", destination="D", weight=200.0, priority="express"),
        ]
        result = CostCalculator.calculate(shipments)
        expected_total = sum(e["cost"] for e in result["per_shipment"])
        assert abs(result["total_cost"] - round(expected_total, 2)) < 0.01

    def test_each_shipment_has_unique_cost(self):
        shipments = [
            _make_shipment(origin="A", destination="B", weight=100.0),
            _make_shipment(origin="A", destination="B", weight=200.0),
        ]
        result = CostCalculator.calculate(shipments)
        assert result["per_shipment"][0]["cost"] != result["per_shipment"][1]["cost"]
