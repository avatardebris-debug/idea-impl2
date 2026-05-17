"""Catalog Exporter — exports enriched product catalog data to CSV.

Takes optimized catalog records and writes them to CSV files with
all metadata fields included.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ecommercecatalog_optimizer.catalog_analyzer import CatalogRecord
from ecommercecatalog_optimizer.metadata_optimizer import MetadataOptimizationResult


# ── Output column order ─────────────────────────────────────────────

OUTPUT_COLUMNS: List[str] = [
    "product_id",
    "title",
    "price",
    "description",
    "category",
    "brand",
    "sku",
    "image_url",
    "weight",
    "dimensions",
    "color",
    "keywords",
    "tags",
    "meta_title",
    "meta_description",
    "meta_keywords",
    "url",
    "availability",
    "rating",
    "review_count",
]


@dataclass
class ExportResult:
    """Result of an export operation."""
    output_path: str
    records_exported: int
    format: str


class CatalogExporter:
    """Exports catalog records to CSV files.

    Supports exporting raw records and records enriched with
    optimized metadata.
    """

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(
        self,
        records: List[CatalogRecord],
        output_filename: str = "catalog_export.csv",
        include_metadata: bool = False,
        metadata_results: Optional[List[MetadataOptimizationResult]] = None,
    ) -> ExportResult:
        """Export catalog records to a CSV file.

        Args:
            records: List of catalog records to export.
            output_filename: Name of the output CSV file.
            include_metadata: If True, include optimized metadata columns.
            metadata_results: List of optimization results (required if
                              include_metadata=True).

        Returns:
            ExportResult with details of the export.

        Raises:
            ValueError: If include_metadata is True but metadata_results
                        is None or has a different length than records.
        """
        if include_metadata:
            if metadata_results is None:
                raise ValueError(
                    "metadata_results is required when include_metadata=True"
                )
            if len(metadata_results) != len(records):
                raise ValueError(
                    f"metadata_results length ({len(metadata_results)}) "
                    f"does not match records length ({len(records)})"
                )

        output_path = self.output_dir / output_filename

        # Determine columns
        if include_metadata:
            columns = OUTPUT_COLUMNS + [
                "optimized_meta_title",
                "optimized_meta_description",
                "optimized_meta_keywords",
                "metadata_changes",
            ]
        else:
            columns = OUTPUT_COLUMNS

        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(columns)

            for i, record in enumerate(records):
                # Always use base columns for the record data
                row = self._record_to_row(record, OUTPUT_COLUMNS)

                if include_metadata and metadata_results:
                    meta = metadata_results[i]
                    row.extend([
                        meta.optimized_meta_title or "",
                        meta.optimized_meta_description or "",
                        meta.optimized_meta_keywords or "",
                        "; ".join(meta.changes_made) if meta.changes_made else "",
                    ])

                writer.writerow(row)

        return ExportResult(
            output_path=str(output_path),
            records_exported=len(records),
            format="csv",
        )

    def export_enriched(
        self,
        records: List[CatalogRecord],
        metadata_results: List[MetadataOptimizationResult],
        output_filename: str = "catalog_enriched.csv",
    ) -> ExportResult:
        """Convenience method to export records with optimized metadata.

        Args:
            records: List of catalog records.
            metadata_results: List of optimization results.
            output_filename: Name of the output CSV file.

        Returns:
            ExportResult with details of the export.
        """
        return self.export_csv(
            records=records,
            output_filename=output_filename,
            include_metadata=True,
            metadata_results=metadata_results,
        )

    def _record_to_row(self, record: CatalogRecord, columns: List[str]) -> List[str]:
        """Convert a catalog record to a CSV row (list of strings)."""
        row: List[str] = []
        for col in columns:
            val = getattr(record, col, None)
            if val is None:
                row.append("")
            elif isinstance(val, float):
                # Format floats: remove trailing zeros
                if val == int(val):
                    row.append(str(int(val)))
                else:
                    row.append(f"{val:.2f}")
            else:
                row.append(str(val))
        return row
