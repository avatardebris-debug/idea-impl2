"""Product store integration for droppain.

Handles loading products from Shopify stores.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from droppain.config import Config, get_config
from droppain.models import Product

logger = logging.getLogger(__name__)


@dataclass
class StoreConnection:
    """Represents a connection to a Shopify store."""

    store_name: str
    api_key: str
    password: str
    api_version: str = "2024-01"

    @property
    def base_url(self) -> str:
        """Get the Shopify API base URL."""
        return (
            f"https://{self.api_key}:{self.password}"
            f"@{self.store_name}.myshopify.com/admin/api/{self.api_version}"
        )


class ProductStore:
    """Manages product data from a Shopify store."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the product store.

        Args:
            config: Optional configuration. If not provided, loads from environment.
        """
        self.config = config or get_config()
        self._connection: Optional[StoreConnection] = None

    @property
    def connection(self) -> StoreConnection:
        """Get or create store connection."""
        if self._connection is None:
            if not self.config.shopify_store_name:
                raise ValueError("SHOPIFY_STORE_NAME is required")
            self._connection = StoreConnection(
                store_name=self.config.shopify_store_name,
                api_key=self.config.shopify_api_key,
                password=self.config.shopify_password,
                api_version=self.config.shopify_api_version,
            )
        return self._connection

    def load_products(
        self,
        limit: int = 50,
        status: str = "active",
        product_type: Optional[str] = None,
    ) -> List[Product]:
        """Load products from the Shopify store.

        Args:
            limit: Maximum number of products to load.
            status: Product status filter.
            product_type: Optional product type filter.

        Returns:
            List of Product objects.
        """
        logger.info(
            "Loading products from store: %s (limit=%d, status=%s)",
            self.config.shopify_store_name,
            limit,
            status,
        )

        # In a real implementation, this would call Shopify GraphQL/REST API
        # For now, return empty list
        return []

    def load_product_by_id(self, product_id: str) -> Optional[Product]:
        """Load a single product by ID.

        Args:
            product_id: Shopify product ID.

        Returns:
            Product object or None.
        """
        logger.info("Loading product by ID: %s", product_id)
        # In a real implementation, this would call Shopify API
        return None

    def load_products_from_json(self, file_path: str) -> List[Product]:
        """Load products from a JSON file.

        Args:
            file_path: Path to JSON file containing product data.

        Returns:
            List of Product objects.
        """
        import json

        with open(file_path) as f:
            data = json.load(f)

        products = []
        for item in data:
            from droppain.models import Variant

            variants = []
            for v in item.get("variants", []):
                variants.append(Variant(**v))

            product = Product(
                id=item["id"],
                title=item["title"],
                description=item.get("description", ""),
                price=item["price"],
                image_url=item.get("image_url", ""),
                tags=item.get("tags", []),
                vendor=item.get("vendor", ""),
                product_type=item.get("product_type", ""),
                variants=variants,
                status=item.get("status", "active"),
            )
            products.append(product)

        logger.info("Loaded %d products from %s", len(products), file_path)
        return products

    def save_products_to_json(
        self,
        products: List[Product],
        file_path: str,
    ) -> None:
        """Save products to a JSON file.

        Args:
            products: List of Product objects to save.
            file_path: Path to output JSON file.
        """
        import json

        data = [p.to_dict() for p in products]
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("Saved %d products to %s", len(products), file_path)
