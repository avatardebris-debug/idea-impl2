"""SEO optimization utilities for YouTube Studio integration."""

from typing import List, Optional

from dynamic_pricing.models import ProductMetadata


class SEOOptimizer:
    """Optimizes SEO fields for YouTube product metadata.

    Attributes:
        max_title_length: Maximum title length.
        max_description_length: Maximum description length.
        max_tags_count: Maximum number of tags.
    """

    def __init__(
        self,
        max_title_length: int = 60,
        max_description_length: int = 500,
        max_tags_count: int = 15,
    ):
        self.max_title_length = max_title_length
        self.max_description_length = max_description_length
        self.max_tags_count = max_tags_count

    def optimize_title(self, title: str, product_name: str) -> str:
        """Optimize product title for YouTube SEO.

        Args:
            title: Original title.
            product_name: Product name.

        Returns:
            Optimized title string.
        """
        # Ensure title includes product name
        if product_name.lower() not in title.lower():
            title = f"{product_name} - {title}"

        # Truncate if too long
        if len(title) > self.max_title_length:
            title = title[: self.max_title_length - 3] + "..."

        return title

    def optimize_description(
        self,
        description: str,
        product_name: str,
        price: float,
        currency: str,
    ) -> str:
        """Optimize product description for YouTube SEO.

        Args:
            description: Original description.
            product_name: Product name.
            price: Product price.
            currency: Currency code.

        Returns:
            Optimized description string.
        """
        # Add price info if not present
        price_str = f"{price:.2f} {currency}"
        if price_str not in description:
            description = f"Price: {price_str}\n\n{description}"

        # Truncate if too long
        if len(description) > self.max_description_length:
            description = description[: self.max_description_length - 3] + "..."

        return description

    def optimize_tags(self, tags: List[str], product_name: str) -> List[str]:
        """Optimize product tags for YouTube SEO.

        Args:
            tags: Original tags list.
            product_name: Product name.

        Returns:
            Optimized tags list.
        """
        # Add product name as tag if not present
        if product_name.lower() not in [t.lower() for t in tags]:
            tags = [product_name.lower()] + tags

        # Remove duplicates
        tags = list(dict.fromkeys(tags))

        # Truncate if too many
        if len(tags) > self.max_tags_count:
            tags = tags[: self.max_tags_count]

        return tags

    def optimize_metadata(self, metadata: ProductMetadata) -> ProductMetadata:
        """Optimize all SEO fields of a ProductMetadata.

        Args:
            metadata: The ProductMetadata to optimize.

        Returns:
            Optimized ProductMetadata object.
        """
        optimized_title = self.optimize_title(metadata.seo_title, metadata.name)
        optimized_description = self.optimize_description(
            metadata.seo_description,
            metadata.name,
            metadata.effective_price,
            metadata.currency,
        )
        optimized_tags = self.optimize_tags(metadata.seo_tags, metadata.name)

        return ProductMetadata(
            product_id=metadata.product_id,
            name=metadata.name,
            base_price=metadata.base_price,
            effective_price=metadata.effective_price,
            discount_pct=metadata.discount_pct,
            margin_status=metadata.margin_status,
            recommended_price=metadata.recommended_price,
            floor_price=metadata.floor_price,
            ceiling_price=metadata.ceiling_price,
            competitive_position=metadata.competitive_position,
            seo_title=optimized_title,
            seo_description=optimized_description,
            seo_tags=optimized_tags,
            currency=metadata.currency,
            category=metadata.category,
            approval_status=metadata.approval_status,
        )
