"""AliExpress/DSers API adapter."""

import hashlib
import time
import uuid
from typing import List, Optional, Dict, Any
from backend.services.supplier_base import SupplierBase, SupplierProductInfo
from backend.config import settings


class AliExpressSupplier(SupplierBase):
    """Adapter for AliExpress/DSers API."""

    @property
    def supplier_type(self) -> str:
        return "aliexpress"

    @property
    def name(self) -> str:
        return "AliExpress"

    def _generate_signature(self, api_secret: str, params: Dict[str, str]) -> str:
        """Generate a mock signature for API authentication."""
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        raw = f"{api_secret}{sorted_params}{int(time.time())}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def authenticate(self, api_key: str, api_secret: Optional[str] = None) -> bool:
        """Authenticate with AliExpress API. In mock mode, always succeeds."""
        if settings.mock_data:
            return True
        # In production, would make an API call to validate credentials
        if not api_key:
            return False
        return True

    async def fetch_products(
        self,
        category: Optional[str] = None,
        min_margin_pct: float = 0.0,
        max_results: int = 50,
    ) -> List[SupplierProductInfo]:
        """Fetch product listings from AliExpress (mock data)."""
        if settings.mock_data:
            return self._get_mock_products(category, min_margin_pct, max_results)
        # In production, would call AliExpress API
        return []

    def _get_mock_products(self, category: Optional[str], min_margin_pct: float, max_results: int) -> List[SupplierProductInfo]:
        """Return mock product data for development."""
        mock_products = [
            SupplierProductInfo(
                product_id=f"ae_{i}",
                supplier_product_id=f"100500{i:06d}",
                title=f"Wireless Bluetooth Earbuds Pro {i}",
                image_url=f"https://example.com/images/earbuds_{i}.jpg",
                description="High quality wireless earbuds with noise cancellation.",
                category="Electronics" if not category or "Electronics" in category else category,
                variants=[
                    {"name": "Color", "options": ["Black", "White", "Blue"]},
                    {"name": "Size", "options": ["Standard", "Large"]},
                ],
                landed_cost=5.99 + (i * 0.5),
                retail_price=19.99,
                margin_pct=70.0,
                inventory=1000 - (i * 10),
                min_order=1,
                shipping_time_days=15,
            )
            for i in range(1, max_results + 1)
        ]
        if min_margin_pct > 0:
            mock_products = [p for p in mock_products if p.margin_pct >= min_margin_pct]
        return mock_products[:max_results]

    async def get_product_detail(self, product_id: str) -> Optional[SupplierProductInfo]:
        """Get detailed info for a single product."""
        if settings.mock_data:
            return self._get_mock_products(None, 0, 1)[0] if product_id else None
        return None

    async def check_inventory(self, product_ids: List[str]) -> Dict[str, int]:
        """Check inventory levels for given product IDs."""
        if settings.mock_data:
            return {pid: max(0, 100 - int(pid.split("_")[-1]) * 10) for pid in product_ids}
        return {}

    async def get_pricing(self, product_ids: List[str]) -> Dict[str, float]:
        """Get current pricing for given product IDs."""
        if settings.mock_data:
            return {pid: 19.99 for pid in product_ids}
        return {}


class DSersSupplier(SupplierBase):
    """Adapter for DSers API (AliExpress dropshipping platform)."""

    @property
    def supplier_type(self) -> str:
        return "dsers"

    @property
    def name(self) -> str:
        return "DSers"

    async def authenticate(self, api_key: str, api_secret: Optional[str] = None) -> bool:
        if settings.mock_data:
            return True
        return bool(api_key)

    async def fetch_products(
        self,
        category: Optional[str] = None,
        min_margin_pct: float = 0.0,
        max_results: int = 50,
    ) -> List[SupplierProductInfo]:
        if settings.mock_data:
            return self._get_mock_products(category, min_margin_pct, max_results)
        return []

    def _get_mock_products(self, category: Optional[str], min_margin_pct: float, max_results: int) -> List[SupplierProductInfo]:
        mock_products = [
            SupplierProductInfo(
                product_id=f"dsers_{i}",
                supplier_product_id=f"DS{i:06d}",
                title=f"DSers Smart Watch Series {i}",
                image_url=f"https://example.com/images/watch_{i}.jpg",
                description="Smart watch with heart rate monitor and GPS.",
                category="Wearables" if not category or "Wearables" in category else category,
                variants=[
                    {"name": "Color", "options": ["Black", "Silver", "Gold"]},
                ],
                landed_cost=12.50 + (i * 0.3),
                retail_price=39.99,
                margin_pct=68.0,
                inventory=500 - (i * 5),
                min_order=1,
                shipping_time_days=20,
            )
            for i in range(1, max_results + 1)
        ]
        if min_margin_pct > 0:
            mock_products = [p for p in mock_products if p.margin_pct >= min_margin_pct]
        return mock_products[:max_results]

    async def get_product_detail(self, product_id: str) -> Optional[SupplierProductInfo]:
        if settings.mock_data:
            return self._get_mock_products(None, 0, 1)[0] if product_id else None
        return None

    async def check_inventory(self, product_ids: List[str]) -> Dict[str, int]:
        if settings.mock_data:
            return {pid: max(0, 500 - int(pid.split("_")[-1]) * 5) for pid in product_ids}
        return {}

    async def get_pricing(self, product_ids: List[str]) -> Dict[str, float]:
        if settings.mock_data:
            return {pid: 39.99 for pid in product_ids}
        return {}
