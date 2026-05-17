"""Tests for AgentFlow agents."""

import pytest
from agentflow_drophip.agents.fulfillment_agent import FulfillmentAgent
from agentflow_drophip.agents.listing_agent import ListingAgent
from agentflow_drophip.agents.sourcing_agent import SourcingAgent
from agentflow_drophip.models.business_spec import BusinessSpec, FulfillmentType, SupplierType


class TestSourcingAgent:
    def setup_method(self):
        self.agent = SourcingAgent()

    def test_execute_with_spec(self):
        spec = BusinessSpec(niche="electronics")
        result = self.agent.execute(spec=spec, limit=10)

        assert result.is_success
        assert len(result.products) <= 10

    def test_execute_with_niche(self):
        result = self.agent.execute(niche="electronics", limit=10)

        assert result.is_success
        assert len(result.products) <= 10

    def test_execute_with_max_price(self):
        result = self.agent.execute(max_price=20.0, limit=10)

        assert result.is_success
        for product in result.products:
            assert product["price"] <= 20.0

    def test_execute_without_params(self):
        result = self.agent.execute()

        assert result.is_success
        assert len(result.products) > 0

    def test_get_status(self):
        self.agent.execute()
        status = self.agent.get_status()

        assert status["name"] == "sourcing_agent"
        assert status["execution_count"] == 1

    def test_reset(self):
        self.agent.execute()
        self.agent.reset()

        status = self.agent.get_status()
        assert status["execution_count"] == 0


class TestListingAgent:
    def setup_method(self):
        self.agent = ListingAgent()

    def test_execute_with_products(self):
        products = [
            {"id": "prod_1", "name": "Product 1", "price": 10.0},
            {"id": "prod_2", "name": "Product 2", "price": 20.0},
        ]
        result = self.agent.execute(products=products)

        assert result.is_success
        assert len(result.products) == 2

    def test_execute_without_products(self):
        result = self.agent.execute()

        assert result.is_failure
        assert "No products provided" in result.error

    def test_update_listing(self):
        result = self.agent.update_listing("prod_1", {"price": 15.0})

        assert result.is_success
        assert result.products[0]["price"] == 15.0


class TestFulfillmentAgent:
    def setup_method(self):
        self.agent = FulfillmentAgent()

    def test_execute_with_orders(self):
        orders = [
            {"id": "order_1", "product_id": "prod_1"},
            {"id": "order_2", "product_id": "prod_2"},
        ]
        result = self.agent.execute(orders=orders)

        assert result.is_success
        assert result.data["orders_processed"] == 2
        assert result.data["successful"] == 2

    def test_execute_without_orders(self):
        result = self.agent.execute()

        assert result.is_failure
        assert "No orders provided" in result.error

    def test_get_status(self):
        orders = [{"id": "order_1", "product_id": "prod_1"}]
        self.agent.execute(orders=orders)
        status = self.agent.get_status()

        assert status["name"] == "fulfillment_agent"
        assert status["execution_count"] == 1

    def test_reset(self):
        orders = [{"id": "order_1", "product_id": "prod_1"}]
        self.agent.execute(orders=orders)
        self.agent.reset()

        status = self.agent.get_status()
        assert status["execution_count"] == 0
