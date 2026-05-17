"""Shared test fixtures for AgentFlow tests."""

import pytest


@pytest.fixture
def sample_spec():
    """Sample BusinessSpec for testing."""
    from agentflow_drophip.models.business_spec import (
        BusinessSpec,
        FulfillmentType,
        PricingStrategy,
        StorefrontType,
        SupplierType,
    )

    return BusinessSpec(
        niche="electronics",
        supplier_type=SupplierType.ALIEXPRESS,
        storefront_type=StorefrontType.SHOPIFY,
        fulfillment_type=FulfillmentType.AUTO,
        pricing_strategy=PricingStrategy.MARKUP,
        max_product_cost=50.0,
        auto_reorder_threshold=10,
    )


@pytest.fixture
def sample_products():
    """Sample products for testing."""
    return [
        {"id": "prod_1", "name": "Product 1", "price": 10.0, "rating": 4.5, "stock": 100},
        {"id": "prod_2", "name": "Product 2", "price": 20.0, "rating": 4.0, "stock": 50},
        {"id": "prod_3", "name": "Product 3", "price": 30.0, "rating": 3.5, "stock": 0},
    ]


@pytest.fixture
def sample_orders():
    """Sample orders for testing."""
    return [
        {"id": "order_1", "product_id": "prod_1", "quantity": 1},
        {"id": "order_2", "product_id": "prod_2", "quantity": 2},
    ]


@pytest.fixture
def sample_config():
    """Sample config for testing."""
    return {
        "openai_api_key": "test_key",
        "max_retries": 3,
        "timeout_seconds": 300,
        "log_level": "DEBUG",
    }
