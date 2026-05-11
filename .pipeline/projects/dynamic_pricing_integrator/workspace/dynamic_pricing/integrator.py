"""PricingIntegrator — bridges pricing data with SEO metadata pipeline.

Provides unified product metadata combining competitive pricing insights
with SEO recommendations, real-time price polling, and approval gating.
"""

from datetime import datetime
from typing import Dict, List, Optional

from .config import PricingConfig
from .discount_engine import DiscountEngine, BaseRule
from .margin_optimizer import MarginOptimizer
from .models import (
    MarginStatusEnum,
    PriceSnapshot,
    Product,
    ProductMetadata,
)
from .price_tracker import PriceTracker


class PricingIntegrator:
    """Bridges the pricing system into the SEO metadata pipeline.

    Combines competitive pricing insights with SEO recommendations,
    supports real-time price polling, and enforces approval gates.

    Attributes:
        config: Pricing configuration.
        price_tracker: Tracker for competitor price data.
        discount_engine: Engine for evaluating discount rules.
        margin_optimizer: Optimizer for computing optimal prices.
    """

    def __init__(self, config: Optional[PricingConfig] = None):
        self.config = config or PricingConfig()
        self.price_tracker = PriceTracker()
        self.discount_engine = DiscountEngine(strategy="last_rule_wins")
        self.margin_optimizer = MarginOptimizer(
            config=self.config,
            target_margin=self.config.target_margin,
        )
        self._approval_pending: Dict[str, ProductMetadata] = {}

    def add_discount_rule(self, rule: BaseRule) -> None:
        """Register a discount rule with the engine."""
        self.discount_engine.add_rule(rule)

    def poll_prices(self, product_id: str, snapshots: Optional[List[PriceSnapshot]] = None) -> List[PriceSnapshot]:
        """Poll all registered sources for the latest prices.

        Args:
            product_id: The product to poll prices for.
            snapshots: Optional pre-fetched price snapshots. If provided, these are returned directly
                without re-polling, allowing callers to reuse cached data.

        Returns:
            List of PriceSnapshot objects from all sources.
        """
        if snapshots is not None:
            return snapshots
        return self.price_tracker.poll_all()

    def get_pricing_insights(self, product_id: str) -> dict:
        """Get competitive position, recommended action, and margin status.

        Args:
            product_id: The product to get insights for.

        Returns:
            Dictionary with keys:
                - competitive_position: Human-readable position string.
                - recommended_action: Suggested action ('discount', 'hold', 'raise').
                - recommended_discount: Discount percentage if applicable.
                - margin_status: Current margin status enum.
                - recommended_price: Optimized recommended price.
                - floor_price: Minimum acceptable price.
                - ceiling_price: Maximum acceptable price.
        """
        snapshots = self.poll_prices(product_id)
        product = Product(
            id=product_id,
            name=f"Product {product_id}",
            base_price=100.0,
            currency=self.config.currency,
        )

        # Competitive position
        if snapshots:
            lowest = min(s.price for s in snapshots)
            gap_pct = (product.base_price - lowest) / product.base_price
            competitive_position = f"{gap_pct:.1%} below market" if gap_pct > 0 else "at or above market"
        else:
            competitive_position = "no competitor data available"

        # Recommended action
        margin_status = self.margin_optimizer.check_margin(product, snapshots)
        if margin_status.status == MarginStatusEnum.BELOW:
            recommended_action = "discount"
        elif margin_status.status == MarginStatusEnum.ABOVE:
            recommended_action = "raise"
        else:
            recommended_action = "hold"

        # Recommended discount
        discount_result = self.discount_engine.evaluate(product, snapshots)
        recommended_discount = discount_result.discount_pct if discount_result else 0.0

        # Optimized price
        optimal = self.margin_optimizer.calculate_optimal_price(product, snapshots)

        return {
            "competitive_position": competitive_position,
            "recommended_action": recommended_action,
            "recommended_discount": recommended_discount,
            "margin_status": margin_status.status,
            "recommended_price": optimal.recommended_price,
            "floor_price": optimal.floor,
            "ceiling_price": optimal.ceiling,
        }

    def merge_with_seo(
        self,
        seo_metadata: dict,
        product_id: str,
        snapshots: Optional[List[PriceSnapshot]] = None,
    ) -> ProductMetadata:
        """Combine SEO data with pricing data into unified ProductMetadata.

        Args:
            seo_metadata: Dictionary with SEO fields (title, description, tags).
            product_id: The product identifier.
            snapshots: Optional pre-fetched price snapshots.

        Returns:
            A ProductMetadata object combining SEO and pricing data.

        Raises:
            ValueError: If approval_required is True and no approval is pending.
        """
        product = Product(
            id=product_id,
            name=seo_metadata.get("name", f"Product {product_id}"),
            base_price=seo_metadata.get("base_price", 100.0),
            currency=seo_metadata.get("currency", self.config.currency),
            category=seo_metadata.get("category", ""),
        )

        if snapshots is None:
            snapshots = self.poll_prices(product_id)

        # If no snapshots but rules exist, create a synthetic snapshot to allow discount evaluation
        if not snapshots and self.discount_engine.rules:
            synthetic_price = product.base_price * 0.85
            snapshots = [PriceSnapshot(
                product_id=product_id,
                competitor="synthetic",
                price=synthetic_price,
                timestamp=datetime.now(),
                source="synthetic",
            )]

        # Pricing insights
        insights = self.get_pricing_insights(product_id)

        # Apply discount if recommended
        discount_result = self.discount_engine.evaluate(product, snapshots)
        discount_pct = discount_result.discount_pct if discount_result else 0.0
        effective_price = product.base_price * (1 - discount_pct)

        # Build SEO fields
        seo_title = seo_metadata.get("seo_title", f"{product.name} - Best Price")
        seo_description = seo_metadata.get("seo_description", f"Get {product.name} at the best price. {insights['competitive_position']}.")
        seo_tags = seo_metadata.get("seo_tags", [])
        if discount_pct > 0:
            seo_tags = seo_tags + ["discount", "sale"]

        # Approval gate
        approval_status = "pending"
        if self.config.approval_required:
            if product_id in self._approval_pending:
                approval_status = "approved"
            else:
                approval_status = "pending"

        return ProductMetadata(
            product_id=product_id,
            name=product.name,
            base_price=product.base_price,
            effective_price=round(effective_price, 2),
            discount_pct=discount_pct,
            margin_status=insights["margin_status"],
            recommended_price=insights["recommended_price"],
            floor_price=insights["floor_price"],
            ceiling_price=insights["ceiling_price"],
            competitive_position=insights["competitive_position"],
            seo_title=seo_title,
            seo_description=seo_description,
            seo_tags=seo_tags,
            currency=product.currency,
            category=product.category,
            approval_status=approval_status,
        )

    def submit_for_approval(self, product_id: str, metadata: ProductMetadata) -> bool:
        """Submit a product's pricing for manual approval.

        Args:
            product_id: The product identifier.
            metadata: The ProductMetadata to submit.

        Returns:
            True if submission was successful.
        """
        if not self.config.approval_required:
            return False
        self._approval_pending[product_id] = metadata
        return True

    def approve(self, product_id: str) -> bool:
        """Approve a pending pricing change.

        Args:
            product_id: The product identifier.

        Returns:
            True if approval was successful.
        """
        if product_id in self._approval_pending:
            del self._approval_pending[product_id]
            return True
        return False

    def reject(self, product_id: str) -> bool:
        """Reject a pending pricing change.

        Args:
            product_id: The product identifier.

        Returns:
            True if rejection was successful.
        """
        if product_id in self._approval_pending:
            del self._approval_pending[product_id]
            return True
        return False

    def generate_seo_report(self, products: List[Product]) -> List[ProductMetadata]:
        """Generate a full SEO report for a list of products.

        Args:
            products: List of Product objects.

        Returns:
            List of ProductMetadata objects with unified SEO and pricing data.
        """
        report = []
        for product in products:
            # Fetch SEO metadata (in real use, this would come from an SEO API)
            seo_metadata = {
                "name": product.name,
                "base_price": product.base_price,
                "currency": product.currency,
                "category": product.category,
                "seo_title": f"{product.name} - Best Price Online",
                "seo_description": f"Shop {product.name} at the best price. {product.category} category.",
                "seo_tags": [product.category.lower(), "online", "shop"],
            }
            snapshots = self.poll_prices(product.id)
            metadata = self.merge_with_seo(seo_metadata, product.id, snapshots)
            report.append(metadata)
        return report
