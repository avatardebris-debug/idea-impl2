"""CJDropshipping API adapter."""

import hashlib
import time
from typing import List, Optional, Dict, Any
from backend.services.supplier_base import SupplierBase, SupplierProductInfo
from backend.config import settings


class CJDropshippingSupplier(SupplierBase):
    """Adapter for CJDropshipping API."""

    @property
    def supplier_type(self) -> str:
        return "cjdropshipping"

    @property
    def name(self) -> str:
        return "CJDropshipping"

    def _generate_signature(self, api_secret: str, params: Dict[str, str]) -> str:
        """Generate a mock signature for API authentication."""
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        raw = f"{api_secret}{sorted_params}{int(time.time())}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def authenticate(self, api_key: str, api_secret: Optional[str] = None) -> bool:
        """Authenticate with CJDropshipping API. In mock mode, always succeeds."""
        if settings.mock_data:
            return True
        if not api_key:
            return False
        return True

    async def fetch_products(
        self,
        category: Optional[str] = None,
        min_margin_pct: float = 0.0,
        max_results: int = 50,
    ) -> List[SupplierProductInfo]:
        """Fetch product listings from CJDropshipping (mock data)."""
        if settings.mock_data:
            return self._get_mock_products(category, min_margin_pct, max_results)
        return []

    def _get_mock_products(self, category: Optional[str], min_margin_pct: float, max_results: int) -> List[SupplierProductInfo]:
        """Return mock product data for development."""
        mock_products = [
            SupplierProductInfo(
                product_id=f"cj_{i}",
                supplier_product_id=f"CJ{i:06d}",
                title=f"CJ Premium Yoga Mat Non-Slip {i}",
                image_url=f"https://example.com/images/yoga_{i}.jpg",
                description="Premium quality yoga mat with alignment lines.",
                category="Sports" if not category or "Sports" in category else category,
                variants=[
                    {"name": "Color", "options": ["Purple", "Green", "Pink"]},
                    {"name": "Thickness", "options": ["6mm", "8mm", "10mm"]},
                ],
                landed_cost=8.50 + (i * 0.2),
                retail_price=24.99,
                margin_pct=66.0,
                inventory=800 - (i * 8),
                min_order=1,
                shipping_time_days=12,
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
            return {pid: max(0, 800 - int(pid.split("_")[-1]) * 8) for pid in product_ids}
        return {}

    async def get_pricing(self, product_ids: List[str]) -> Dict[str, float]:
        """Get current pricing for given product IDs."""
        if settings.mock_data:
            return {pid: 24.99 for pid in product_ids}
        return {}
