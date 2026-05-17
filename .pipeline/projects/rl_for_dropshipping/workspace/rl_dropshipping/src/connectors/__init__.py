"""Abstract base connector for platform APIs."""

from __future__ import annotations

import abc
import time
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseConnector(abc.ABC):
    """Abstract base class for platform API connectors.

    All connectors must implement the methods below to support:
    - Product listing CRUD
    - Inventory updates
    - Order retrieval
    - Ad campaign management
    - Budget adjustments
    """

    @abc.abstractmethod
    def get_products(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch product listings from the platform."""
        pass

    @abc.abstractmethod
    def update_inventory(self, product_id: str, quantity: int) -> bool:
        """Update inventory for a product."""
        pass

    @abc.abstractmethod
    def get_orders(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch orders from the platform."""
        pass

    @abc.abstractmethod
    def create_ad_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new ad campaign. Returns campaign ID."""
        pass

    @abc.abstractmethod
    def update_budget(self, campaign_id: str, budget: float) -> bool:
        """Update budget for an ad campaign."""
        pass

    @abc.abstractmethod
    def get_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Fetch analytics for a campaign."""
        pass

    @abc.abstractmethod
    def health_check(self) -> bool:
        """Check if the connector is healthy."""
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """Close the connector and release resources."""
        pass


class PlatformConnector(BaseConnector):
    """Concrete connector that can be swapped for real API calls.

    By default, uses mock data for testing. To use real APIs,
    subclass and override the methods with actual HTTP calls.
    """

    def __init__(self, mock: bool = True):
        self.mock = mock
        self._products = [
            {"id": "p1", "name": "Phone Case", "price": 12.5, "stock": 100},
            {"id": "p2", "name": "LED Lamp", "price": 25.0, "stock": 50},
            {"id": "p3", "name": "Yoga Mat", "price": 18.0, "stock": 75},
        ]
        self._orders: List[Dict[str, Any]] = []
        self._campaigns: Dict[str, Dict[str, Any]] = {}
        self._healthy = True

    def get_products(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch product listings."""
        if not self._healthy:
            raise ConnectionError("Connector is not healthy")
        return list(self._products)

    def update_inventory(self, product_id: str, quantity: int) -> bool:
        """Update inventory for a product."""
        if not self._healthy:
            return False
        for product in self._products:
            if product["id"] == product_id:
                product["stock"] = quantity
                return True
        return False

    def get_orders(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch orders."""
        if not self._healthy:
            raise ConnectionError("Connector is not healthy")
        return list(self._orders)

    def create_ad_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new ad campaign."""
        if not self._healthy:
            raise ConnectionError("Connector is not healthy")
        campaign_id = f"camp_{len(self._campaigns) + 1}"
        self._campaigns[campaign_id] = {
            "id": campaign_id,
            "status": "active",
            "budget": campaign_data.get("budget", 0.0),
            "platform": campaign_data.get("platform", "unknown"),
            "created_at": time.time(),
        }
        return campaign_id

    def update_budget(self, campaign_id: str, budget: float) -> bool:
        """Update budget for an ad campaign."""
        if not self._healthy:
            return False
        if campaign_id in self._campaigns:
            self._campaigns[campaign_id]["budget"] = budget
            return True
        return False

    def get_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Fetch analytics for a campaign."""
        if not self._healthy:
            raise ConnectionError("Connector is not healthy")
        if campaign_id not in self._campaigns:
            return {}
        return {
            "campaign_id": campaign_id,
            "impressions": 1000,
            "clicks": 50,
            "conversions": 5,
            "revenue": 125.0,
            "budget": self._campaigns[campaign_id].get("budget", 0.0),
        }

    def health_check(self) -> bool:
        """Check if the connector is healthy."""
        return self._healthy

    def close(self) -> None:
        """Close the connector."""
        self._healthy = False
        logger.info("PlatformConnector closed")
