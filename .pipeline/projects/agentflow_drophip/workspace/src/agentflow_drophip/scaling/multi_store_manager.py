"""MultiStoreManager — manages multiple storefronts across niches and platforms."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from agentflow_drophip.models.business_spec import StorefrontType


class StoreStatus(str, Enum):
    """Status of a managed store."""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


@dataclass
class StoreConfig:
    """Configuration for a single storefront."""
    name: str
    niche: str
    storefront_type: StorefrontType
    region: str = "US"
    markup_multiplier: float = 2.5
    branding: Dict[str, str] = field(default_factory=dict)
    products: List[Dict[str, Any]] = field(default_factory=list)
    status: StoreStatus = StoreStatus.PENDING
    store_id: str = ""

    def __post_init__(self):
        if not self.store_id:
            self.store_id = f"store_{uuid.uuid4().hex[:8]}"


class MultiStoreManager:
    """Manages creation, configuration, and lifecycle of multiple storefronts."""

    def __init__(self):
        self.stores: Dict[str, StoreConfig] = {}
        self._store_order: List[str] = []

    def create_store(self, config: StoreConfig) -> StoreConfig:
        """Create a new store with the given configuration."""
        self.stores[config.store_id] = config
        self._store_order.append(config.store_id)
        return config

    def get_store(self, store_id: str) -> Optional[StoreConfig]:
        """Get a store by its ID."""
        return self.stores.get(store_id)

    def list_stores(self, status: Optional[StoreStatus] = None) -> List[StoreConfig]:
        """List all stores, optionally filtered by status."""
        if status is None:
            return [self.stores[sid] for sid in self._store_order if sid in self.stores]
        return [
            self.stores[sid] for sid in self._store_order
            if sid in self.stores and self.stores[sid].status == status
        ]

    def activate_store(self, store_id: str) -> bool:
        """Activate a store."""
        store = self.stores.get(store_id)
        if store:
            store.status = StoreStatus.ACTIVE
            return True
        return False

    def pause_store(self, store_id: str) -> bool:
        """Pause a store."""
        store = self.stores.get(store_id)
        if store:
            store.status = StoreStatus.PAUSED
            return True
        return False

    def remove_store(self, store_id: str) -> bool:
        """Remove a store."""
        if store_id in self.stores:
            del self.stores[store_id]
            self._store_order.remove(store_id)
            return True
        return False

    def add_products(self, store_id: str, products: List[Dict[str, Any]]) -> bool:
        """Add products to a store."""
        store = self.stores.get(store_id)
        if store:
            store.products.extend(products)
            return True
        return False

    def get_active_stores(self) -> List[StoreConfig]:
        """Get all active stores."""
        return [s for s in self.stores.values() if s.status == StoreStatus.ACTIVE]

    def get_store_count(self, status: Optional[StoreStatus] = None) -> int:
        """Count stores, optionally filtered by status."""
        if status is None:
            return len(self.stores)
        return sum(1 for s in self.stores.values() if s.status == status)

    def generate_store_configs(
        self,
        base_niche: str,
        regions: List[str],
        storefront_types: List[StorefrontType],
        count_per_combo: int = 1,
    ) -> List[StoreConfig]:
        """Generate multiple store configs from a base niche across regions and platforms."""
        configs: List[StoreConfig] = []
        for niche in [base_niche]:
            for region in regions:
                for storefront_type in storefront_types:
                    for i in range(count_per_combo):
                        name = f"{niche}-{region}-{storefront_type.value}"
                        if count_per_combo > 1:
                            name += f"-{i+1}"
                        config = StoreConfig(
                            name=name,
                            niche=niche,
                            storefront_type=storefront_type,
                            region=region,
                            branding={
                                "store_name": f"{niche.title()} Hub",
                                "tagline": f"Premium {niche} products",
                            },
                        )
                        configs.append(config)
                        self.create_store(config)
        return configs
