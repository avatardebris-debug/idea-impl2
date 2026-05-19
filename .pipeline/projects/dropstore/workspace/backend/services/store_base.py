"""Abstract base class for store platform adapters."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class StoreProductInfo(BaseModel):
    """Standardized product info for storefront sync."""
    product_id: str
    title: str
    body_html: str = ""
    image_url: str = ""
    variants: List[Dict[str, Any]] = []
    price: float = 0.0
    compare_at_price: float = 0.0
    inventory_qty: int = 0
    sku: str = ""
    tags: List[str] = []
    category: str = ""
    status: str = "active"


class StoreBase(ABC):
    """Abstract base class for store platform adapters."""

    @property
    @abstractmethod
    def platform_type(self) -> str:
        """Return the platform type identifier (e.g., 'shopify', 'woocommerce')."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable platform name."""
        ...

    @abstractmethod
    async def authenticate(self, api_key: str, api_secret: Optional[str] = None) -> bool:
        """Authenticate with the store platform API. Returns True if credentials are valid."""
        ...

    @abstractmethod
    async def push_product(self, product: StoreProductInfo) -> Dict[str, Any]:
        """Push a single product to the store.

        Returns:
            Dict with platform-specific response data including product_id.
        """
        ...

    @abstractmethod
    async def push_products(self, products: List[StoreProductInfo]) -> Dict[str, Any]:
        """Push multiple products to the store.

        Returns:
            Dict with push results: {'pushed': int, 'failed': int, 'errors': List[str]}
        """
        ...

    @abstractmethod
    async def get_products(self, limit: int = 50, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Fetch products from the store.

        Returns:
            Dict with 'products' list and optional 'next_cursor'.
        """
        ...

    @abstractmethod
    async def get_orders(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch orders from the store.

        Returns:
            List of order dicts.
        """
        ...

    @abstractmethod
    async def update_inventory(self, product_id: str, quantity: int) -> bool:
        """Update inventory for a product.

        Returns:
            True if successful.
        """
        ...

    @abstractmethod
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update the status of an order on the platform.

        Returns:
            True if successful.
        """
        ...

    @abstractmethod
    async def get_analytics(self, period_days: int = 30) -> Dict[str, Any]:
        """Fetch analytics data for the store.

        Returns:
            Dict with metrics data.
        """
        ...

    @abstractmethod
    async def get_templates(self) -> List[Dict[str, Any]]:
        """Get available store templates.

        Returns:
            List of template dicts.
        """
        ...

    @abstractmethod
    async def apply_template(self, template_id: str, config: Dict[str, Any]) -> bool:
        """Apply a template to the store.

        Returns:
            True if successful.
        """
        ...
