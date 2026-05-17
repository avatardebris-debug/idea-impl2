"""Tests for droppain.product_store module."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from droppain.product_store import ProductStore, StoreConnection
from droppain.models import Product, Variant


class TestStoreConnection:
    """Tests for StoreConnection."""

    def test_base_url(self):
        """Test StoreConnection.base_url property."""
        conn = StoreConnection(
            store_name="mystore",
            api_key="key123",
            password="pass456",
            api_version="2024-01",
        )
        expected = "https://key123:pass456@mystore.myshopify.com/admin/api/2024-01"
        assert conn.base_url == expected


class TestProductStore:
    """Tests for ProductStore."""

    def test_init_with_config(self):
        """Test initialization with config."""
        config = type("Config", (), {
            "shopify_store_name": "mystore",
            "shopify_api_key": "key",
            "shopify_password": "pass",
            "shopify_api_version": "2024-01",
        })()
        store = ProductStore(config=config)
        assert store.config == config

    def test_connection_raises_without_store_name(self):
        """Test that connection raises without store name."""
        config = type("Config", (), {
            "shopify_store_name": "",
            "shopify_api_key": "key",
            "shopify_password": "pass",
            "shopify_api_version": "2024-01",
        })()
        store = ProductStore(config=config)
        with pytest.raises(ValueError):
            _ = store.connection

    def test_load_products_from_json(self):
        """Test loading products from JSON file."""
        products_data = [
            {
                "id": "1",
                "title": "Test Product",
                "description": "A test product",
                "price": 29.99,
                "variants": [{"id": "v1", "title": "Default", "price": 29.99, "sku": "SKU1"}],
                "tags": ["test"],
                "vendor": "Test Vendor",
                "product_type": "Test Type",
                "status": "active",
            }
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(products_data, f)
            temp_path = f.name

        try:
            store = ProductStore()
            products = store.load_products_from_json(temp_path)
            assert len(products) == 1
            assert products[0].title == "Test Product"
            assert products[0].price == 29.99
            assert len(products[0].variants) == 1
        finally:
            os.unlink(temp_path)

    def test_save_products_to_json(self):
        """Test saving products to JSON file."""
        products = [
            Product(
                id="1",
                title="Test Product",
                price=29.99,
                variants=[Variant(id="v1", title="Default", price=29.99, sku="SKU1")],
            )
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            store = ProductStore()
            store.save_products_to_json(products, temp_path)

            # Verify file was created and contains data
            with open(temp_path) as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["title"] == "Test Product"
        finally:
            os.unlink(temp_path)

    def test_load_products_from_shopify(self):
        """Test loading products from Shopify (returns empty for now)."""
        config = type("Config", (), {
            "shopify_store_name": "mystore",
            "shopify_api_key": "key",
            "shopify_password": "pass",
            "shopify_api_version": "2024-01",
        })()
        store = ProductStore(config=config)
        products = store.load_products()
        assert products == []
