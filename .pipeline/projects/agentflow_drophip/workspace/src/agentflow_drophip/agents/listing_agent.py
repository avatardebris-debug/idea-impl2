"""ListingAgent — creates and manages product listings."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agentflow_drophip.agents.base import AgentResult, BaseAgent
from agentflow_drophip.models.business_spec import BusinessSpec, StorefrontType


class ListingAgent(BaseAgent):
    """Agent that creates product listings on storefronts."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        storefront_type: Optional[StorefrontType] = None,
    ):
        """Initialize the listing agent.

        Args:
            config: Configuration dictionary.
            storefront_type: Type of storefront to use.
        """
        super().__init__(name="listing_agent", config=config)
        self.storefront_type = storefront_type or StorefrontType.SHOPIFY

    def execute(
        self,
        spec: Optional[BusinessSpec] = None,
        products: Optional[List[Dict[str, Any]]] = None,
        branding: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Execute listing creation.

        Args:
            spec: Business specification.
            products: List of products to list.
            branding: Branding configuration.
            **kwargs: Additional parameters.

        Returns:
            AgentResult with created listings.
        """
        self.execution_count += 1

        if not products:
            return AgentResult(
                success=False,
                error="No products provided for listing",
                metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
            )

        # Create listings
        listings = []
        for product in products:
            listing = {
                "product_id": product.get("id"),
                "product_name": product.get("name"),
                "storefront": self.storefront_type.value,
                "price": product.get("price", 0.0),
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "url": f"https://{self.storefront_type.value.lower()}.com/product/{product.get('id')}",
            }

            # Apply branding if available
            if branding:
                listing["branding"] = branding
                listing["title"] = f"{branding.get('brand_name', 'Store')} - {product.get('name')}"
            else:
                listing["title"] = product.get("name")

            listings.append(listing)

        result = AgentResult(
            success=True,
            data={
                "storefront_type": self.storefront_type.value,
                "listings_created": len(listings),
            },
            products=listings,
            metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        self.last_result = result
        return result

    def update_listing(self, listing_id: str, updates: Dict[str, Any]) -> AgentResult:
        """Update an existing listing.

        Args:
            listing_id: ID of the listing to update.
            updates: Dictionary of updates to apply.

        Returns:
            AgentResult with updated listing.
        """
        self.execution_count += 1

        # Simulate update
        updated_listing = {
            "id": listing_id,
            **updates,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = AgentResult(
            success=True,
            data={"listing_id": listing_id, "updates_applied": list(updates.keys())},
            products=[updated_listing],
            metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        self.last_result = result
        return result
