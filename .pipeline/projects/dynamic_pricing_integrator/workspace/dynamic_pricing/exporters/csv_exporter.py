"""CSV exporter for ProductMetadata."""

import csv
import io
from typing import List

from ..models import ProductMetadata


class CSVExporter:
    """Exports ProductMetadata objects to CSV format.

    Attributes:
        delimiter: CSV column delimiter character.
    """

    def __init__(self, delimiter: str = ","):
        self.delimiter = delimiter

    def export(self, metadata: ProductMetadata) -> str:
        """Export a single ProductMetadata to CSV string.

        Args:
            metadata: The ProductMetadata to export.

        Returns:
            CSV string with header and one data row.
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)
        writer.writerow([
            "product_id",
            "name",
            "base_price",
            "effective_price",
            "discount_pct",
            "margin_status",
            "recommended_price",
            "floor_price",
            "ceiling_price",
            "competitive_position",
            "seo_title",
            "seo_description",
            "seo_tags",
            "currency",
            "category",
            "approval_status",
        ])
        writer.writerow([
            metadata.product_id,
            metadata.name,
            metadata.base_price,
            metadata.effective_price,
            metadata.discount_pct,
            metadata.margin_status.value,
            metadata.recommended_price,
            metadata.floor_price,
            metadata.ceiling_price,
            metadata.competitive_position,
            metadata.seo_title,
            metadata.seo_description,
            "|".join(metadata.seo_tags),
            metadata.currency,
            metadata.category,
            metadata.approval_status,
        ])
        return output.getvalue().strip()

    def export_batch(self, metadatas: List[ProductMetadata]) -> str:
        """Export a list of ProductMetadata objects to a CSV string.

        Args:
            metadatas: List of ProductMetadata objects.

        Returns:
            CSV string with header and data rows.
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter)
        writer.writerow([
            "product_id",
            "name",
            "base_price",
            "effective_price",
            "discount_pct",
            "margin_status",
            "recommended_price",
            "floor_price",
            "ceiling_price",
            "competitive_position",
            "seo_title",
            "seo_description",
            "seo_tags",
            "currency",
            "category",
            "approval_status",
        ])
        for meta in metadatas:
            writer.writerow([
                meta.product_id,
                meta.name,
                meta.base_price,
                meta.effective_price,
                meta.discount_pct,
                meta.margin_status.value,
                meta.recommended_price,
                meta.floor_price,
                meta.ceiling_price,
                meta.competitive_position,
                meta.seo_title,
                meta.seo_description,
                "|".join(meta.seo_tags),
                meta.currency,
                meta.category,
                meta.approval_status,
            ])
        return output.getvalue().strip()
