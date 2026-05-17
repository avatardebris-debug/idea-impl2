"""Tests for PlannerEngine."""

import pytest
from dropgentic.planner.engine import PlannerEngine, Recommendation, SourcingPlan
from dropgentic.models.product import Product
from dropgentic.models.supplier import Supplier
from dropgentic.models.margin import MarginCalculator


class TestPlannerEngineInit:
    """Test PlannerEngine initialization."""

    def test_default_init(self):
        engine = PlannerEngine()
        assert engine.min_net_margin_pct == 5.0
        assert engine.max_lead_time_days == 30
        assert engine.min_supplier_rating == 0.0
        assert engine.min_gross_margin_pct == 20.0
        assert engine.currency == "USD"
        assert engine.margin_calculator is not None

    def test_custom_init(self):
        engine = PlannerEngine(
            min_net_margin_pct=10.0,
            max_lead_time_days=14,
            min_supplier_rating=4.0,
            min_gross_margin_pct=30.0,
            currency="EUR",
        )
        assert engine.min_net_margin_pct == 10.0
        assert engine.max_lead_time_days == 14
        assert engine.min_supplier_rating == 4.0
        assert engine.min_gross_margin_pct == 30.0
        assert engine.currency == "EUR"


class TestEvaluateProductSupplierPair:
    """Test evaluate_product_supplier_pair method."""

    def test_valid_pair(self):
        engine = PlannerEngine()
        product = Product(product_id="P1", title="Widget", cost_price=10.0, retail_price=50.0)
        supplier = Supplier(supplier_id="S1", name="Test", shipping_cost_per_unit=5.0, lead_time_days=7)
        result = engine.evaluate_product_supplier_pair(product, supplier)
        assert result is not None
        assert result.product_id == "P1"
        assert result.supplier_id == "S1"
        assert result.margin_result is not None

    def test_reject_due_to_low_margin(self):
        engine = PlannerEngine(min_net_margin_pct=50.0)
        product = Product(product_id="P1", title="Widget", cost_price=40.0, retail_price=50.0)
        supplier = Supplier(supplier_id="S1", name="Test", shipping_cost_per_unit=5.0, lead_time_days=7)
        result = engine.evaluate_product_supplier_pair(product, supplier)
        assert result is not None
        assert result.recommended_action == "Reject"

    def test_reject_due_to_lead_time(self):
        engine = PlannerEngine(max_lead_time_days=5)
        product = Product(product_id="P1", title="Widget", cost_price=10.0, retail_price=50.0)
        supplier = Supplier(supplier_id="S1", name="Test", shipping_cost_per_unit=5.0, lead_time_days=10)
        result = engine.evaluate_product_supplier_pair(product, supplier)
        assert result is not None
        assert result.recommended_action == "Reject"

    def test_reject_due_to_low_rating(self):
        engine = PlannerEngine(min_supplier_rating=4.0)
        product = Product(product_id="P1", title="Widget", cost_price=10.0, retail_price=50.0)
        supplier = Supplier(supplier_id="S1", name="Test", rating=3.0, shipping_cost_per_unit=5.0, lead_time_days=7)
        result = engine.evaluate_product_supplier_pair(product, supplier)
        assert result is not None
        assert result.recommended_action == "Reject"

    def test_reject_due_to_low_gross_margin(self):
        engine = PlannerEngine(min_gross_margin_pct=30.0)
        product = Product(product_id="P1", title="Widget", cost_price=40.0, retail_price=50.0)
        supplier = Supplier(supplier_id="S1", name="Test", shipping_cost_per_unit=5.0, lead_time_days=7)
        result = engine.evaluate_product_supplier_pair(product, supplier)
        assert result is not None
        assert result.recommended_action == "Reject"

    def test_list_action(self):
        engine = PlannerEngine()
        product = Product(product_id="P1", title="Widget", cost_price=10.0, retail_price=50.0)
        supplier = Supplier(supplier_id="S1", name="Test", rating=4.5, shipping_cost_per_unit=5.0, lead_time_days=7)
        result = engine.evaluate_product_supplier_pair(product, supplier)
        assert result is not None
        assert result.recommended_action == "List"


class TestGenerateSourcingPlan:
    """Test generate_sourcing_plan method."""

    def test_empty_products(self):
        engine = PlannerEngine()
        plan = engine.generate_sourcing_plan([], [])
        assert plan is not None
        assert plan.product_count == 0
        assert plan.supplier_count == 0
        assert plan.total_cost == 0.0
        assert plan.total_revenue == 0.0
        assert plan.total_profit == 0.0
        assert plan.total_fees == 0.0
        assert plan.avg_net_margin_pct == 0.0
        assert plan.recommendations == []

    def test_single_product_supplier(self):
        engine = PlannerEngine()
        product = Product(product_id="P1", title="Widget", cost_price=10.0, retail_price=50.0)
        supplier = Supplier(supplier_id="S1", name="Test", rating=4.5, shipping_cost_per_unit=5.0, lead_time_days=7)
        plan = engine.generate_sourcing_plan([product], [supplier])
        assert plan is not None
        assert plan.product_count == 1
        assert plan.supplier_count == 1
        assert len(plan.recommendations) == 1
        assert plan.recommendations[0].product_id == "P1"
        assert plan.recommendations[0].supplier_id == "S1"

    def test_multiple_products_suppliers(self):
        engine = PlannerEngine()
        products = [
            Product(product_id="P1", title="Widget1", cost_price=10.0, retail_price=50.0),
            Product(product_id="P2", title="Widget2", cost_price=15.0, retail_price=60.0),
        ]
        suppliers = [
            Supplier(supplier_id="S1", name="Test1", rating=4.5, shipping_cost_per_unit=5.0, lead_time_days=7),
            Supplier(supplier_id="S2", name="Test2", rating=4.0, shipping_cost_per_unit=3.0, lead_time_days=10),
        ]
        plan = engine.generate_sourcing_plan(products, suppliers)
        assert plan is not None
        assert plan.product_count == 2
        assert plan.supplier_count == 2
        assert len(plan.recommendations) == 2

    def test_plan_aggregations(self):
        engine = PlannerEngine()
        product = Product(product_id="P1", title="Widget", cost_price=10.0, retail_price=50.0)
        supplier = Supplier(supplier_id="S1", name="Test", rating=4.5, shipping_cost_per_unit=5.0, lead_time_days=7)
        plan = engine.generate_sourcing_plan([product], [supplier])
        assert plan.total_cost > 0
        assert plan.total_revenue > 0
        assert plan.total_profit > 0
        assert plan.total_fees > 0
        assert plan.avg_net_margin_pct > 0


class TestRecommendation:
    """Test Recommendation model."""

    def test_create_recommendation(self):
        rec = Recommendation(
            product_id="P1",
            supplier_id="S1",
            margin_result=None,
            recommended_action="List",
            priority_score=0.8,
        )
        assert rec.product_id == "P1"
        assert rec.supplier_id == "S1"
        assert rec.recommended_action == "List"
        assert rec.priority_score == 0.8

    def test_to_dict(self):
        rec = Recommendation(product_id="P1", supplier_id="S1", recommended_action="List", priority_score=0.8)
        d = rec.to_dict()
        assert d["product_id"] == "P1"
        assert d["recommended_action"] == "List"

    def test_from_dict(self):
        data = {
            "product_id": "P1",
            "supplier_id": "S1",
            "recommended_action": "List",
            "priority_score": 0.8,
        }
        rec = Recommendation.from_dict(data)
        assert rec.product_id == "P1"
        assert rec.priority_score == 0.8

    def test_repr(self):
        rec = Recommendation(product_id="P1", supplier_id="S1", recommended_action="List", priority_score=0.8)
        r = repr(rec)
        assert "P1" in r
        assert "S1" in r
        assert "List" in r


class TestSourcingPlan:
    """Test SourcingPlan model."""

    def test_create_sourcing_plan(self):
        plan = SourcingPlan(
            product_count=2,
            supplier_count=2,
            total_cost=100.0,
            total_revenue=500.0,
            total_profit=300.0,
            total_fees=100.0,
            avg_net_margin_pct=0.6,
            recommendations=[],
        )
        assert plan.product_count == 2
        assert plan.total_cost == 100.0
        assert plan.total_revenue == 500.0
        assert plan.total_profit == 300.0
        assert plan.avg_net_margin_pct == 0.6

    def test_to_dict(self):
        plan = SourcingPlan(
            product_count=1,
            supplier_count=1,
            total_cost=100.0,
            total_revenue=500.0,
            total_profit=300.0,
            total_fees=100.0,
            avg_net_margin_pct=0.6,
            recommendations=[],
        )
        d = plan.to_dict()
        assert d["product_count"] == 1
        assert d["total_revenue"] == 500.0

    def test_from_dict(self):
        data = {
            "product_count": 1,
            "supplier_count": 1,
            "total_cost": 100.0,
            "total_revenue": 500.0,
            "total_profit": 300.0,
            "total_fees": 100.0,
            "avg_net_margin_pct": 0.6,
            "recommendations": [],
        }
        plan = SourcingPlan.from_dict(data)
        assert plan.product_count == 1
        assert plan.total_profit == 300.0

    def test_repr(self):
        plan = SourcingPlan(
            product_count=1,
            supplier_count=1,
            total_cost=100.0,
            total_revenue=500.0,
            total_profit=300.0,
            total_fees=100.0,
            avg_net_margin_pct=0.6,
            recommendations=[],
        )
        r = repr(plan)
        assert "1" in r
        assert "500.0" in r
