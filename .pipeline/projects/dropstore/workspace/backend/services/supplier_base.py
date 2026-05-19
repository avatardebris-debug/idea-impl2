"""Abstract base class for supplier API adapters."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class SupplierProductInfo(BaseModel):
    """Standardized product info from any supplier."""
    product_id: str
    supplier_product_id: str
    title: str
    image_url: str = ""
    description: str = ""
    category: str = ""
    variants: List[Dict[str, Any]] = []
    landed_cost: float = 0.0
    retail_price: float = 0.0
    margin_pct: float = 0.0
    inventory: int = 0
    min_order: int = 1
    shipping_time_days: int = 0


class SupplierBase(ABC):
    """Abstract base class for supplier API adapters."""

    @property
    @abstractmethod
    def supplier_type(self) -> str:
        """Return the supplier type identifier (e.g., 'aliexpress', 'cjdropshipping')."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable supplier name."""
        ...

    @abstractmethod
    async def authenticate(self, api_key: str, api_secret: Optional[str] = None) -> bool:
        """Authenticate with the supplier API. Returns True if credentials are valid."""
        ...

    @abstractmethod
    async def fetch_products(
        self,
        category: Optional[str] = None,
        min_margin_pct: float = 0.0,
        max_results: int = 50,
    ) -> List[SupplierProductInfo]:
        """Fetch product listings from the supplier.

        Args:
            category: Optional category filter.
            min_margin_pct: Minimum margin percentage filter.
            max_results: Maximum number of products to return.

        Returns:
            List of standardized product info objects.
        """
        ...

    @abstractmethod
    async def get_product_detail(self, product_id: str) -> Optional[SupplierProductInfo]:
        """Get detailed info for a single product.

        Args:
            product_id: The supplier's product ID.

        Returns:
            Product detail or None if not found.
        """
        ...

    @abstractmethod
    async def check_inventory(self, product_ids: List[str]) -> Dict[str, int]:
        """Check inventory levels for given product IDs.

        Args:
            product_ids: List of supplier product IDs.

        Returns:
            Dict mapping product_id to inventory count.
        """
        ...

    @abstractmethod
    async def get_pricing(self, product_ids: List[str]) -> Dict[str, float]:
        """Get current pricing for given product IDs.

        Args:
            product_ids: List of supplier product IDs.

        Returns:
            Dict mapping product_id to current price.
        """
        ...
