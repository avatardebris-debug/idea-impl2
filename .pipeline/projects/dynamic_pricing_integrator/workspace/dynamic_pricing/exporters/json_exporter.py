"""JSON exporter for ProductMetadata."""

import json
from typing import List

from ..models import ProductMetadata


class JSONExporter:
    """Exports ProductMetadata objects to JSON format.

    Attributes:
        indent: JSON indentation level.
    """

    def __init__(self, indent: int = 2):
        self.indent = indent

    def export(self, metadata: ProductMetadata) -> str:
        """Export a single ProductMetadata to JSON string.

        Args:
            metadata: The ProductMetadata to export.

        Returns:
            JSON string representation.
        """
        data = {
            "product_id": metadata.product_id,
            "name": metadata.name,
            "base_price": metadata.base_price,
            "effective_price": metadata.effective_price,
            "discount_pct": metadata.discount_pct,
            "margin_status": metadata.margin_status.value,
            "recommended_price": metadata.recommended_price,
            "floor_price": metadata.floor_price,
            "ceiling_price": metadata.ceiling_price,
            "competitive_position": metadata.competitive_position,
            "seo_title": metadata.seo_title,
            "seo_description": metadata.seo_description,
            "seo_tags": metadata.seo_tags,
            "currency": metadata.currency,
            "category": metadata.category,
            "approval_status": metadata.approval_status,
        }
        return json.dumps(data, indent=self.indent)

    def export_batch(self, metadatas: List[ProductMetadata]) -> str:
        """Export a list of ProductMetadata objects to a JSON array string.

        Args:
            metadatas: List of ProductMetadata objects.

        Returns:
            JSON array string.
        """
        data = []
        for meta in metadatas:
            data.append({
                "product_id": meta.product_id,
                "name": meta.name,
                "base_price": meta.base_price,
                "effective_price": meta.effective_price,
                "discount_pct": meta.discount_pct,
                "margin_status": meta.margin_status.value,
                "recommended_price": meta.recommended_price,
                "floor_price": meta.floor_price,
                "ceiling_price": meta.ceiling_price,
                "competitive_position": meta.competitive_position,
                "seo_title": meta.seo_title,
                "seo_description": meta.seo_description,
                "seo_tags": meta.seo_tags,
                "currency": meta.currency,
                "category": meta.category,
                "approval_status": meta.approval_status,
            })
        return json.dumps(data, indent=self.indent)
