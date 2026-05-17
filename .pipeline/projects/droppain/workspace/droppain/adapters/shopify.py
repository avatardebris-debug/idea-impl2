"""Shopify adapter for fetching and syncing products."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import requests

from droppain.config import Config, get_config
from droppain.exceptions import APIError
from droppain.models import Product, Variant

logger = logging.getLogger(__name__)


class ShopifyAdapter:
    """Adapter for interacting with Shopify Admin API (REST).

    Supports both real API calls and mock/test mode.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        mock_products: Optional[List[Product]] = None,
        use_mock: bool = False,
    ):
        """Initialize the Shopify adapter.

        Args:
            config: Configuration object. If None, loads from env vars.
            mock_products: Pre-defined products for mock mode.
            use_mock: If True, return mock_products instead of calling the API.
        """
        self.config = config or get_config()
        self.mock_products = mock_products or []
        self.use_mock = use_mock
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    @property
    def _admin_base_url(self) -> str:
        """Build the Shopify Admin API base URL."""
        return (
            f"https://{self.config.shopify_api_key}:{self.config.shopify_password}"
            f"@{self.config.shopify_store_name}/admin/api/{self.config.shopify_api_version}"
        )

    def fetch_products(
        self,
        limit: int = 50,
        status: str = "active",
        product_type: Optional[str] = None,
    ) -> List[Product]:
        """Fetch products from Shopify store.

        Args:
            limit: Maximum number of products to fetch.
            status: Filter by product status (active, draft, archived).
            product_type: Optional filter by product type.

        Returns:
            List of Product objects.
        """
        if self.use_mock:
            logger.info("Using mock mode — returning %d mock products", len(self.mock_products))
            return self.mock_products

        url = f"{self._admin_base_url}/products.json"
        params: Dict[str, str] = {
            "limit": str(limit),
            "status": status,
        }
        if product_type:
            params["product_type"] = product_type

        try:
            logger.info("Fetching products from Shopify: %s", url)
            response = self._session.get(url, params=params, timeout=self.config.api_timeout)
            response.raise_for_status()
            data = response.json()
            products = data.get("products", [])
            return self._parse_products(products)
        except requests.exceptions.HTTPError as e:
            raise APIError(
                f"Shopify API HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
                endpoint=url,
            )
        except requests.exceptions.RequestException as e:
            raise APIError(f"Shopify API request failed: {e}")

    def fetch_product(self, product_id: int) -> Optional[Product]:
        """Fetch a single product by ID.

        Args:
            product_id: Shopify product ID.

        Returns:
            Product object or None if not found.
        """
        if self.use_mock:
            for p in self.mock_products:
                if str(p.id) == str(product_id):
                    return p
            return None

        url = f"{self._admin_base_url}/products/{product_id}.json"
        try:
            response = self._session.get(url, timeout=self.config.api_timeout)
            response.raise_for_status()
            data = response.json()
            product_data = data.get("product", {})
            return self._parse_product(product_data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise APIError(
                f"Shopify API HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
                endpoint=url,
            )

    def create_product(self, product_data: Dict) -> Product:
        """Create a new product in Shopify.

        Args:
            product_data: Dictionary with product fields.

        Returns:
            The created Product object.
        """
        if self.use_mock:
            new_id = str(max((int(p.id) for p in self.mock_products), default=0) + 1)
            product = self._parse_product({**product_data, "id": int(new_id)})
            self.mock_products.append(product)
            return product

        url = f"{self._admin_base_url}/products.json"
        try:
            response = self._session.post(url, json={"product": product_data}, timeout=self.config.api_timeout)
            response.raise_for_status()
            data = response.json()
            return self._parse_product(data.get("product", {}))
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to create product: {e}")

    def _parse_products(self, products_data: List[Dict]) -> List[Product]:
        """Parse raw Shopify product data into Product objects."""
        return [self._parse_product(p) for p in products_data]

    def _parse_product(self, data: Dict) -> Product:
        """Parse a single Shopify product dict into a Product."""
        variants = [
            Variant(
                id=str(v.get("id", "")),
                title=v.get("title", "Default Title"),
                price=float(v.get("price", 0)),
                sku=v.get("sku", ""),
                inventory_quantity=v.get("inventory_quantity", 0),
                available=v.get("available", True),
            )
            for v in data.get("variants", [])
        ]
        return Product(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            price=float(data.get("variants", [{}])[0].get("price", 0)) if data.get("variants") else 0.0,
            image_url=data.get("image", {}).get("src", "") if data.get("image") else "",
            description=data.get("body_html", ""),
            tags=data.get("tags", []),
            vendor=data.get("vendor", ""),
            product_type=data.get("product_type", ""),
            variants=variants,
            status=data.get("status", "active"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def set_mock_products(self, products: List[Product]) -> None:
        """Set mock products for testing."""
        self.mock_products = products
        self.use_mock = True

    def disable_mock(self) -> None:
        """Disable mock mode and use real API."""
        self.use_mock = False
