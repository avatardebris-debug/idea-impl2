"""YouTube Studio — product metadata generation with pricing integration."""

from typing import Dict, List, Optional

from dynamic_pricing.config import PricingConfig
from dynamic_pricing.integrator import PricingIntegrator
from dynamic_pricing.models import Product, ProductMetadata, PriceSnapshot
from .seo_optimizer import SEOOptimizer


class YouTubeStudio:
    """Generates YouTube Studio product metadata with pricing integration.

    Attributes:
        integrator: PricingIntegrator instance for pricing data.
        channel_id: YouTube channel identifier.
        config: Pricing configuration.
        seo_optimizer: Optional SEOOptimizer for SEO field optimization.
    """

    def __init__(
        self,
        channel_id: str,
        integrator: Optional[PricingIntegrator] = None,
        config: Optional[PricingConfig] = None,
        seo_optimizer: Optional[SEOOptimizer] = None,
    ):
        self.channel_id = channel_id
        self.integrator = integrator or PricingIntegrator(config=config)
        self.config = self.integrator.config
        self.seo_optimizer = seo_optimizer

    def generate_product_metadata(
        self,
        product: Product,
        video_id: str,
        snapshots: Optional[List[PriceSnapshot]] = None,
    ) -> ProductMetadata:
        """Generate YouTube Studio product metadata with pricing data.

        Args:
            product: The product to generate metadata for.
            video_id: YouTube video ID for the product.
            snapshots: Optional pre-fetched price snapshots.

        Returns:
            ProductMetadata with YouTube-specific SEO fields.
        """
        if snapshots is None:
            snapshots = self.integrator.poll_prices(product.id)

        # Build SEO metadata with YouTube-specific fields
        seo_metadata = {
            "name": product.name,
            "base_price": product.base_price,
            "currency": product.currency,
            "category": product.category,
            "seo_title": f"{product.name} - Best Price | {video_id}",
            "seo_description": f"Shop {product.name} in this video. Best price guaranteed. {product.category} category.",
            "seo_tags": [product.category.lower(), "youtube", "shop", video_id],
        }

        metadata = self.integrator.merge_with_seo(seo_metadata, product.id, snapshots)

        # Apply SEO optimization if an SEOOptimizer is configured
        if self.seo_optimizer is not None:
            metadata = self.seo_optimizer.optimize_metadata(metadata)

        return metadata

    def generate_batch_metadata(
        self,
        products: List[Product],
        video_id: str,
    ) -> List[ProductMetadata]:
        """Generate YouTube Studio product metadata for multiple products.

        Args:
            products: List of Product objects.
            video_id: YouTube video ID for the products.

        Returns:
            List of ProductMetadata objects.
        """
        return [self.generate_product_metadata(p, video_id) for p in products]

    def get_channel_insights(self, video_id: str) -> Dict[str, float]:
        """Get channel-level pricing insights.

        Args:
            video_id: YouTube video ID.

        Returns:
            Dictionary with channel pricing metrics.
        """
        # In a real implementation, this would aggregate data from YouTube API
        # For now, return placeholder metrics
        return {
            "video_id": video_id,
            "channel_id": self.channel_id,
            "avg_discount": 0.0,
            "avg_margin": self.config.target_margin,
            "total_products": 0,
        }
