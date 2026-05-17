"""Catalog Analyzer — reads and audits product catalog CSV files.

Provides column detection, data quality checks, and metadata field
discovery for product catalogs.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ── Standard product catalog column expectations ──────────────────────

REQUIRED_PRODUCT_COLUMNS: Set[str] = {"product_id", "title", "price"}

OPTIONAL_PRODUCT_COLUMNS: Set[str] = {
    "description",
    "category",
    "brand",
    "sku",
    "image_url",
    "weight",
    "dimensions",
    "color",
    "size",
    "material",
    "keywords",
    "tags",
    "meta_title",
    "meta_description",
    "meta_keywords",
    "url",
    "availability",
    "rating",
    "review_count",
}

# Column aliases: maps common header variations → canonical name
COLUMN_ALIASES: Dict[str, str] = {
    # Product ID
    "product_id": "product_id",
    "productid": "product_id",
    "id": "product_id",
    "sku": "sku",
    "sku_id": "sku",
    "item_id": "product_id",
    # Title
    "title": "title",
    "product_title": "title",
    "productname": "title",
    "product_name": "title",
    "name": "title",
    "item_name": "title",
    "itemname": "title",
    "product name": "title",
    # Price
    "price": "price",
    "unit_price": "price",
    "sale_price": "price",
    "retail_price": "price",
    "cost": "price",
    "amount": "price",
    # Description
    "description": "description",
    "product_description": "description",
    "desc": "description",
    "short_description": "description",
    "long_description": "description",
    "item_description": "description",
    # Category
    "category": "category",
    "product_category": "category",
    "cat": "category",
    "department": "category",
    "subcategory": "category",
    "type": "category",
    # Brand
    "brand": "brand",
    "manufacturer": "brand",
    "maker": "brand",
    "brand_name": "brand",
    # SKU (already mapped above)
    "stock_keeping_unit": "sku",
    # Image
    "image_url": "image_url",
    "image": "image_url",
    "img_url": "image_url",
    "product_image": "image_url",
    "thumbnail": "image_url",
    # Weight
    "weight": "weight",
    "item_weight": "weight",
    "shipping_weight": "weight",
    # Dimensions
    "dimensions": "dimensions",
    "product_dimensions": "dimensions",
    "size": "dimensions",
    # Color
    "color": "color",
    "colour": "color",
    "product_color": "color",
    # Material
    "material": "material",
    "materials": "material",
    "fabric": "material",
    # Keywords / SEO
    "keywords": "keywords",
    "meta_keywords": "meta_keywords",
    "search_keywords": "keywords",
    "tags": "tags",
    "meta_title": "meta_title",
    "meta_description": "meta_description",
    "url": "url",
    "product_url": "url",
    "availability": "availability",
    "stock_status": "availability",
    "rating": "rating",
    "review_count": "review_count",
    "reviews": "review_count",
}


def _normalise_header(header: str) -> str:
    """Lowercase and strip whitespace from a header name."""
    return header.strip().lower()


def _map_header(raw_header: str) -> Optional[str]:
    """Map a raw header to a canonical column name, or None if unknown."""
    key = _normalise_header(raw_header)
    return COLUMN_ALIASES.get(key)


def _parse_numeric(value: str) -> Optional[float]:
    """Try to parse a numeric value from a string."""
    if value is None or value.strip() == "":
        return None
    cleaned = value.strip().replace(",", "").replace("$", "").replace("%", "").replace(" ", "")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_int(value: str) -> Optional[int]:
    """Try to parse an integer value from a string."""
    if value is None or value.strip() == "":
        return None
    cleaned = value.strip().replace(",", "").replace("$", "").replace("%", "").replace(" ", "")
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None


@dataclass
class ColumnInfo:
    """Information about a detected column."""
    canonical_name: str
    raw_headers: List[str] = field(default_factory=list)
    is_required: bool = False
    data_type: str = "string"  # string, numeric, int, boolean


@dataclass
class CatalogAudit:
    """Result of auditing a product catalog."""
    filepath: str
    total_rows: int
    total_columns: int
    detected_columns: List[ColumnInfo]
    missing_required: List[str]
    empty_cells_by_column: Dict[str, int] = field(default_factory=dict)
    numeric_columns: List[str] = field(default_factory=list)
    quality_score: float = 0.0  # 0-100


@dataclass
class CatalogRecord:
    """A single product record with canonical column names."""
    product_id: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    color: Optional[str] = None
    keywords: Optional[str] = None
    tags: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    url: Optional[str] = None
    availability: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    raw: Dict[str, str] = field(default_factory=dict)


class CatalogAnalyzer:
    """Analyzes product catalog CSV files for structure and quality."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._records: List[CatalogRecord] = []
        self._audit: Optional[CatalogAudit] = None
        self._header_map: Dict[str, str] = {}

    # ── Public API ────────────────────────────────────────────────────

    def load(self) -> "CatalogAnalyzer":
        """Load and parse the catalog CSV file."""
        path = Path(self.filepath)
        if not path.exists():
            raise FileNotFoundError(f"Catalog file not found: {self.filepath}")

        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            headers = next(reader)

            # Build header mapping
            self._header_map = {}
            for h in headers:
                canon = _map_header(h)
                if canon:
                    self._header_map[h] = canon

            # Detect columns
            detected_columns: List[ColumnInfo] = []
            for h in headers:
                canon = self._header_map.get(h)
                if canon:
                    is_required = canon in REQUIRED_PRODUCT_COLUMNS
                    detected_columns.append(ColumnInfo(
                        canonical_name=canon,
                        raw_headers=[h],
                        is_required=is_required,
                    ))

            # Parse records
            self._records = []
            for row in reader:
                if not any(cell.strip() for cell in row):
                    continue
                record = CatalogRecord(raw={})
                for raw_col, val in zip(headers, row):
                    canon = self._header_map.get(raw_col)
                    if canon:
                        record.raw[canon] = val
                        self._set_field(record, canon, val)
                    else:
                        record.raw[raw_col] = val
                self._records.append(record)

        self._audit = self._run_audit(headers, detected_columns)
        return self

    def audit(self) -> CatalogAudit:
        """Run a quality audit on the loaded catalog."""
        if not self._audit:
            raise RuntimeError("Call load() before audit()")
        return self._audit

    @property
    def records(self) -> List[CatalogRecord]:
        """Return parsed product records."""
        return self._records

    @property
    def header_map(self) -> Dict[str, str]:
        """Return the raw → canonical header mapping."""
        return self._header_map

    def get_field_values(self, field: str) -> List[str]:
        """Get all values for a canonical field across records."""
        return [r.raw.get(field, "") for r in self._records]

    def get_missing_fields(self) -> List[str]:
        """Return required fields that are missing from the catalog."""
        if not self._audit:
            raise RuntimeError("Call load() before get_missing_fields()")
        return self._audit.missing_required

    def get_detected_columns(self) -> List[str]:
        """Return list of detected canonical column names."""
        if not self._audit:
            raise RuntimeError("Call load() before get_detected_columns()")
        return [c.canonical_name for c in self._audit.detected_columns]

    # ── Internal helpers ──────────────────────────────────────────────

    def _set_field(self, record: CatalogRecord, field: str, value: str) -> None:
        """Set a field on the record, parsing numeric types where appropriate."""
        if field in ("price", "rating", "weight"):
            parsed = _parse_numeric(value)
            if parsed is not None:
                setattr(record, field, parsed)
            else:
                setattr(record, field, value.strip())
        elif field in ("product_id", "title", "description", "category",
                        "brand", "sku", "image_url", "dimensions", "color",
                        "keywords", "tags", "meta_title", "meta_description",
                        "meta_keywords", "url", "availability"):
            setattr(record, field, value.strip() if value else None)
        elif field == "review_count":
            parsed = _parse_int(value)
            setattr(record, field, parsed)
        else:
            setattr(record, field, value.strip() if value else None)

    def _run_audit(self, headers: List[str], detected_columns: List[ColumnInfo]) -> CatalogAudit:
        """Run quality audit on loaded data."""
        # Check missing required columns
        detected_names = {c.canonical_name for c in detected_columns}
        missing_required = [c for c in REQUIRED_PRODUCT_COLUMNS if c not in detected_names]

        # Count empty cells per column
        empty_cells: Dict[str, int] = {}
        numeric_cols: List[str] = []
        for col_info in detected_columns:
            canon = col_info.canonical_name
            empty_count = 0
            is_numeric = False
            for record in self._records:
                val = getattr(record, canon, None)
                if val is None or (isinstance(val, str) and val.strip() == ""):
                    empty_count += 1
                elif isinstance(val, (int, float)):
                    is_numeric = True
            empty_cells[canon] = empty_count
            if is_numeric:
                numeric_cols.append(canon)

        # Calculate quality score (0-100)
        total_cells = len(self._records) * len(detected_columns) if detected_columns else 1
        if total_cells == 0:
            total_cells = 1  # Avoid division by zero for empty catalogs
        total_empty = sum(empty_cells.values())
        completeness = max(0, 100 - (total_empty / total_cells * 100))

        # Penalty for missing required fields
        required_penalty = len(missing_required) * 20
        quality_score = max(0, min(100, completeness - required_penalty))

        return CatalogAudit(
            filepath=self.filepath,
            total_rows=len(self._records),
            total_columns=len(detected_columns),
            detected_columns=detected_columns,
            missing_required=missing_required,
            empty_cells_by_column=empty_cells,
            numeric_columns=numeric_cols,
            quality_score=quality_score,
        )
