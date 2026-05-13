"""Edge case and boundary tests for the CostCalculator module.

Tests:
- Very large weights
- Very small weights
- Negative weight handling
- Very large dimensions
- Zero dimensions
- Unknown priority defaults
- Multiple shipments with same origin/destination
- Determinism across multiple calls
- Cost rounding precision
- Shipment with only required fields
- Shipment with all optional fields
- Shipment with whitespace in fields
"""

import pytest
from logistics_csv_optimizer.calculator import (
    CostCalculator,
    BASE_COST_PER_KG,
    VOLUME_COST_PER_M3,
    DISTANCE_COST_PER_1000KM,
    PRIORITY_MULTIPLIERS,
)


# ── Fixtures ──

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


# ── Very large values ──

class TestLargeValues:
    """Tests for handling very large values."""

    def test_very_large_weight(self):
        shipment = _make_shipment(weight=1_000_000.0)
        result = CostCalculator.calculate([shipment])
        expected_base = 1_000_000.0 * BASE_COST_PER_KG
        assert result["per_shipment"][0]["base_cost"] == round(expected_base, 2)

    def test_very_large_dimensions(self):
        shipment = _make_shipment(length=1000, width=1000, height=1000)
        result = CostCalculator.calculate([shipment])
        volume_m3 = (1000 * 1000 * 1000) / 1_000_000  # 1000 m³
        expected_volume = volume_m3 * VOLUME_COST_PER_M3
        assert result["per_shipment"][0]["volume_cost"] == round(expected_volume, 2)

    def test_large_weight_and_dimensions(self):
        shipment = _make_shipment(weight=10000.0, length=200, width=150, height=100)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["cost"] > 0
        assert result["total_cost"] > 0

    def test_very_large_distance(self):
        """Test that large simulated distances produce large costs."""
        shipment = _make_shipment(weight=100.0)
        result = CostCalculator.calculate([shipment])
        distance = result["per_shipment"][0]["distance_km"]
        assert distance >= 50.0
        assert distance <= 5000.0


# ── Very small values ──

class TestSmallValues:
    """Tests for handling very small values."""

    def test_very_small_weight(self):
        shipment = _make_shipment(weight=0.001)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["cost"] > 0

    def test_zero_weight(self):
        shipment = _make_shipment(weight=0.0)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["base_cost"] == 0.0

    def test_zero_dimensions(self):
        shipment = _make_shipment(length=0, width=0, height=0)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["volume_cost"] == 0.0

    def test_all_zero_except_weight(self):
        shipment = _make_shipment(weight=10.0, length=0, width=0, height=0)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["volume_cost"] == 0.0
        assert result["per_shipment"][0]["base_cost"] == 10.0 * BASE_COST_PER_KG


# ── Negative values ──

class TestNegativeValues:
    """Tests for handling negative values."""

    def test_negative_weight(self):
        shipment = _make_shipment(weight=-10.0)
        result = CostCalculator.calculate([shipment])
        # Negative weight should still produce a cost (calculator doesn't validate)
        assert result["per_shipment"][0]["base_cost"] < 0

    def test_negative_dimensions(self):
        shipment = _make_shipment(length=-10, width=-10, height=-10)
        result = CostCalculator.calculate([shipment])
        # Negative dimensions produce negative volume cost
        assert result["per_shipment"][0]["volume_cost"] < 0

    def test_negative_weight_and_dimensions(self):
        shipment = _make_shipment(weight=-10.0, length=-10, width=-10, height=-10)
        result = CostCalculator.calculate([shipment])
        # Both base and volume costs are negative
        assert result["per_shipment"][0]["base_cost"] < 0
        assert result["per_shipment"][0]["volume_cost"] < 0


# ── Unknown priority ──

class TestUnknownPriority:
    """Tests for handling unknown priority values."""

    def test_unknown_priority_defaults_to_standard(self):
        shipment = _make_shipment(priority="unknown")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["priority_multiplier"] == 1.0

    def test_empty_priority_defaults_to_standard(self):
        shipment = _make_shipment(priority="")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["priority_multiplier"] == 1.0

    def test_none_priority_defaults_to_standard(self):
        shipment = _make_shipment(priority=None)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["priority_multiplier"] == 1.0


# ── Multiple shipments ──

class TestMultipleShipments:
    """Tests for handling multiple shipments."""

    def test_multiple_shipments_same_cost(self):
        shipments = [_make_shipment() for _ in range(10)]
        result = CostCalculator.calculate(shipments)
        assert result["total_cost"] == round(result["per_shipment"][0]["cost"] * 10, 2)

    def test_multiple_shipments_different_costs(self):
        shipments = [
            _make_shipment(weight=10.0),
            _make_shipment(weight=20.0),
            _make_shipment(weight=30.0),
        ]
        result = CostCalculator.calculate(shipments)
        costs = [s["cost"] for s in result["per_shipment"]]
        assert costs[0] < costs[1] < costs[2]

    def test_multiple_shipments_total_matches_sum(self):
        shipments = [
            _make_shipment(weight=10.0),
            _make_shipment(weight=20.0),
            _make_shipment(weight=30.0),
        ]
        result = CostCalculator.calculate(shipments)
        total = sum(s["cost"] for s in result["per_shipment"])
        assert result["total_cost"] == round(total, 2)

    def test_multiple_shipments_preserves_order(self):
        shipments = [
            _make_shipment(weight=10.0, origin="A", destination="B"),
            _make_shipment(weight=20.0, origin="C", destination="D"),
            _make_shipment(weight=30.0, origin="E", destination="F"),
        ]
        result = CostCalculator.calculate(shipments)
        origins = [s["origin"] for s in result["per_shipment"]]
        assert origins == ["A", "C", "E"]


# ── Determinism ──

class TestDeterminism:
    """Tests for deterministic output."""

    def test_same_shipment_same_cost(self):
        shipment = _make_shipment(weight=100.0)
        r1 = CostCalculator.calculate([shipment])
        r2 = CostCalculator.calculate([shipment])
        assert r1["per_shipment"][0]["cost"] == r2["per_shipment"][0]["cost"]
        assert r1["total_cost"] == r2["total_cost"]

    def test_multiple_calls_consistent(self):
        shipment = _make_shipment(weight=100.0)
        results = [CostCalculator.calculate([shipment]) for _ in range(100)]
        for r in results[1:]:
            assert r["per_shipment"][0]["cost"] == results[0]["per_shipment"][0]["cost"]
            assert r["total_cost"] == results[0]["total_cost"]

    def test_distance_is_deterministic(self):
        shipment = _make_shipment(weight=100.0)
        r1 = CostCalculator.calculate([shipment])
        r2 = CostCalculator.calculate([shipment])
        assert r1["per_shipment"][0]["distance_km"] == r2["per_shipment"][0]["distance_km"]


# ── Cost rounding ──

class TestCostRounding:
    """Tests for cost rounding precision."""

    def test_cost_rounded_to_two_decimals(self):
        shipment = _make_shipment(weight=100.0)
        result = CostCalculator.calculate([shipment])
        cost = result["per_shipment"][0]["cost"]
        assert cost == round(cost, 2)

    def test_total_cost_rounded_to_two_decimals(self):
        shipments = [_make_shipment(weight=i) for i in range(1, 100)]
        result = CostCalculator.calculate(shipments)
        total = result["total_cost"]
        assert total == round(total, 2)

    def test_distance_rounded_to_two_decimals(self):
        shipment = _make_shipment(weight=100.0)
        result = CostCalculator.calculate([shipment])
        distance = result["per_shipment"][0]["distance_km"]
        assert distance == round(distance, 2)

    def test_distance_factor_rounded_to_four_decimals(self):
        shipment = _make_shipment(weight=100.0)
        result = CostCalculator.calculate([shipment])
        factor = result["per_shipment"][0]["distance_factor"]
        assert factor == round(factor, 4)


# ── Shipment with only required fields ──

class TestRequiredFieldsOnly:
    """Tests for shipments with only required fields."""

    def test_minimal_shipment(self):
        shipment = {"origin": "A", "destination": "B", "weight": 10.0, "priority": "standard"}
        result = CostCalculator.calculate([shipment])
        assert len(result["per_shipment"]) == 1
        assert result["total_cost"] > 0

    def test_minimal_shipment_cost_components(self):
        shipment = {"origin": "A", "destination": "B", "weight": 10.0, "priority": "standard"}
        result = CostCalculator.calculate([shipment])
        entry = result["per_shipment"][0]
        assert "base_cost" in entry
        assert "volume_cost" in entry
        assert "distance_factor" in entry
        assert "priority_multiplier" in entry
        assert "cost" in entry


# ── Shipment with all optional fields ──

class TestAllOptionalFields:
    """Tests for shipments with all optional fields."""

    def test_shipment_with_description(self):
        shipment = _make_shipment(description="Fragile items")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["cost"] > 0

    def test_shipment_with_all_dimensions(self):
        shipment = _make_shipment(length=50, width=40, height=30)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["volume_cost"] > 0

    def test_shipment_with_all_fields(self):
        shipment = _make_shipment(
            description="Test shipment",
            length=50,
            width=40,
            height=30,
        )
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["cost"] > 0
        assert result["total_cost"] > 0


# ── Whitespace handling ──

class TestWhitespaceHandling:
    """Tests for handling whitespace in fields."""

    def test_whitespace_in_origin(self):
        shipment = _make_shipment(origin="  New York  ")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["origin"] == "  New York  "

    def test_whitespace_in_destination(self):
        shipment = _make_shipment(destination="  Chicago  ")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["destination"] == "  Chicago  "

    def test_whitespace_in_weight(self):
        shipment = _make_shipment(weight="  100.0  ")
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["cost"] > 0


# ── Priority multipliers ──

class TestPriorityMultipliers:
    """Tests for priority multiplier values."""

    def test_standard_multiplier(self):
        assert PRIORITY_MULTIPLIERS["standard"] == 1.0

    def test_express_multiplier(self):
        assert PRIORITY_MULTIPLIERS["express"] == 1.5

    def test_overnight_multiplier(self):
        assert PRIORITY_MULTIPLIERS["overnight"] == 2.5

    def test_express_cost_is_1_5x_standard(self):
        shipment_standard = _make_shipment(priority="standard")
        shipment_express = _make_shipment(priority="express")
        r1 = CostCalculator.calculate([shipment_standard])
        r2 = CostCalculator.calculate([shipment_express])
        assert r2["per_shipment"][0]["cost"] == round(r1["per_shipment"][0]["cost"] * 1.5, 2)

    def test_overnight_cost_is_2_5x_standard(self):
        shipment_standard = _make_shipment(priority="standard")
        shipment_overnight = _make_shipment(priority="overnight")
        r1 = CostCalculator.calculate([shipment_standard])
        r2 = CostCalculator.calculate([shipment_overnight])
        assert r2["per_shipment"][0]["cost"] == round(r1["per_shipment"][0]["cost"] * 2.5, 2)

    def test_overnight_cost_is_1_666x_express(self):
        shipment_express = _make_shipment(priority="express")
        shipment_overnight = _make_shipment(priority="overnight")
        r1 = CostCalculator.calculate([shipment_express])
        r2 = CostCalculator.calculate([shipment_overnight])
        expected = round(r1["per_shipment"][0]["cost"] * (2.5 / 1.5), 2)
        assert r2["per_shipment"][0]["cost"] == expected


# ── Distance simulation ──

class TestDistanceSimulation:
    """Tests for distance simulation."""

    def test_distance_between_same_city(self):
        shipment = _make_shipment(origin="New York", destination="New York")
        result = CostCalculator.calculate([shipment])
        distance = result["per_shipment"][0]["distance_km"]
        assert distance >= 50.0
        assert distance <= 5000.0

    def test_distance_is_symmetric(self):
        shipment1 = _make_shipment(origin="A", destination="B")
        shipment2 = _make_shipment(origin="B", destination="A")
        r1 = CostCalculator.calculate([shipment1])
        r2 = CostCalculator.calculate([shipment2])
        assert r1["per_shipment"][0]["distance_km"] == r2["per_shipment"][0]["distance_km"]

    def test_distance_range(self):
        """Distance should be between 50 and 5000 km."""
        for i in range(100):
            shipment = _make_shipment(origin=f"City{i}", destination=f"City{i+1}")
            result = CostCalculator.calculate([shipment])
            distance = result["per_shipment"][0]["distance_km"]
            assert 50.0 <= distance <= 5000.0


# ── Empty input ──

class TestEmptyInput:
    """Tests for empty input handling."""

    def test_empty_shipments_list(self):
        result = CostCalculator.calculate([])
        assert result["per_shipment"] == []
        assert result["total_cost"] == 0.0

    def test_single_zero_cost_shipment(self):
        shipment = _make_shipment(weight=0.0, length=0, width=0, height=0)
        result = CostCalculator.calculate([shipment])
        assert result["total_cost"] == 0.0


# ── Cost formula verification ──

class TestCostFormula:
    """Tests to verify the cost formula is correctly implemented."""

    def test_base_cost_formula(self):
        """base_cost = weight * 2.50"""
        shipment = _make_shipment(weight=100.0)
        result = CostCalculator.calculate([shipment])
        assert result["per_shipment"][0]["base_cost"] == 100.0 * BASE_COST_PER_KG

    def test_volume_cost_formula(self):
        """volume_cost = (l * w * h / 1_000_000) * 500"""
        shipment = _make_shipment(length=100, width=100, height=100)
        result = CostCalculator.calculate([shipment])
        volume_m3 = (100 * 100 * 100) / 1_000_000
        expected = volume_m3 * VOLUME_COST_PER_M3
        assert result["per_shipment"][0]["volume_cost"] == round(expected, 2)

    def test_distance_factor_formula(self):
        """distance_factor = 1.0 + (distance_km / 1000) * 1.0"""
        shipment = _make_shipment(weight=100.0)
        result = CostCalculator.calculate([shipment])
        distance = result["per_shipment"][0]["distance_km"]
        expected_factor = 1.0 + (distance / 1000) * DISTANCE_COST_PER_1000KM
        assert result["per_shipment"][0]["distance_factor"] == round(expected_factor, 4)

    def test_total_cost_formula(self):
        """cost = (base_cost + volume_cost) * distance_factor * priority_multiplier"""
        shipment = _make_shipment(weight=100.0, length=50, width=40, height=30, priority="express")
        result = CostCalculator.calculate([shipment])
        entry = result["per_shipment"][0]
        expected = (entry["base_cost"] + entry["volume_cost"]) * entry["distance_factor"] * entry["priority_multiplier"]
        assert entry["cost"] == round(expected, 2)
