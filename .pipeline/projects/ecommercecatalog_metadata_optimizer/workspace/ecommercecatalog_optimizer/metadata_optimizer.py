"""Metadata Optimizer — generates and optimizes SEO metadata for product records.

Takes parsed catalog records and produces enriched metadata fields
(meta_title, meta_description, meta_keywords) based on available
product information.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ecommercecatalog_optimizer.catalog_analyzer import CatalogRecord


# ── SEO metadata templates ─────────────────────────────────────────────

# Maximum lengths for SEO best practices
MAX_META_TITLE_LENGTH = 60
MAX_META_DESCRIPTION_LENGTH = 160
MAX_META_KEYWORDS_LENGTH = 200

# Words to exclude from generated keywords
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can",
    "this", "that", "these", "those", "it", "its", "not", "no",
    "as", "if", "so", "than", "too", "very", "just", "about",
    "also", "from", "into", "over", "after",
}


@dataclass
class MetadataOptimizationResult:
    """Result of optimizing metadata for a single product record."""
    product_id: Optional[str]
    original_meta_title: Optional[str]
    optimized_meta_title: Optional[str]
    original_meta_description: Optional[str]
    optimized_meta_description: Optional[str]
    original_meta_keywords: Optional[str]
    optimized_meta_keywords: Optional[str]
    changes_made: List[str] = field(default_factory=list)


class MetadataOptimizer:
    """Optimizes SEO metadata for product catalog records.

    Generates meta_title, meta_description, and meta_keywords for
    products that are missing or have suboptimal metadata.
    """

    def __init__(
        self,
        brand_prefix: bool = True,
        category_suffix: bool = True,
        max_title_length: int = MAX_META_TITLE_LENGTH,
        max_description_length: int = MAX_META_DESCRIPTION_LENGTH,
        max_keywords_length: int = MAX_META_KEYWORDS_LENGTH,
    ):
        self.brand_prefix = brand_prefix
        self.category_suffix = category_suffix
        self.max_title_length = max_title_length
        self.max_description_length = max_description_length
        self.max_keywords_length = max_keywords_length

    def optimize_record(self, record: CatalogRecord) -> MetadataOptimizationResult:
        """Optimize metadata for a single product record.

        Args:
            record: A parsed catalog record.

        Returns:
            MetadataOptimizationResult with original and optimized values.
        """
        original_meta_title = record.meta_title
        original_meta_description = record.meta_description
        original_meta_keywords = record.meta_keywords

        optimized_title = self._generate_meta_title(record)
        optimized_description = self._generate_meta_description(record)
        optimized_keywords = self._generate_meta_keywords(record)

        changes_made: List[str] = []
        if original_meta_title is None or not original_meta_title.strip():
            changes_made.append("meta_title: generated")
        elif optimized_title != original_meta_title:
            changes_made.append("meta_title: optimized")

        if original_meta_description is None or not original_meta_description.strip():
            changes_made.append("meta_description: generated")
        elif optimized_description != original_meta_description:
            changes_made.append("meta_description: optimized")

        if original_meta_keywords is None or not original_meta_keywords.strip():
            changes_made.append("meta_keywords: generated")
        elif optimized_keywords != original_meta_keywords:
            changes_made.append("meta_keywords: optimized")

        return MetadataOptimizationResult(
            product_id=record.product_id,
            original_meta_title=original_meta_title,
            optimized_meta_title=optimized_title,
            original_meta_description=original_meta_description,
            optimized_meta_description=optimized_description,
            original_meta_keywords=original_meta_keywords,
            optimized_meta_keywords=optimized_keywords,
            changes_made=changes_made,
        )

    def optimize_records(
        self, records: List[CatalogRecord]
    ) -> List[MetadataOptimizationResult]:
        """Optimize metadata for a list of product records.

        Args:
            records: List of parsed catalog records.

        Returns:
            List of MetadataOptimizationResult, one per record.
        """
        return [self.optimize_record(r) for r in records]

    def _generate_meta_title(self, record: CatalogRecord) -> Optional[str]:
        """Generate an optimized meta title for a product.

        Format: [Brand] [Title] [Category]
        """
        parts: List[str] = []

        if self.brand_prefix and record.brand:
            parts.append(record.brand.strip())

        if record.title:
            parts.append(record.title.strip())

        if self.category_suffix and record.category:
            parts.append(record.category.strip())

        if not parts:
            return None

        title = " ".join(parts)
        # Truncate to max length, word-safe
        return self._truncate_word_safe(title, self.max_title_length)

    def _generate_meta_description(self, record: CatalogRecord) -> Optional[str]:
        """Generate an optimized meta description for a product.

        Uses the product description if available, otherwise builds
        a description from available fields.
        """
        if record.description and record.description.strip():
            desc = record.description.strip()
        else:
            desc = self._build_description_from_fields(record)

        if not desc:
            return None

        return self._truncate_word_safe(desc, self.max_description_length)

    def _generate_meta_keywords(self, record: CatalogRecord) -> Optional[str]:
        """Generate optimized meta keywords for a product.

        Collects keywords from title, category, brand, color, and
        existing keywords, removing stop words and duplicates.
        """
        keyword_parts: List[str] = []

        # Extract words from title
        if record.title:
            keyword_parts.extend(self._extract_keywords(record.title))

        # Add category
        if record.category:
            keyword_parts.extend(self._extract_keywords(record.category))

        # Add brand
        if record.brand:
            keyword_parts.extend(self._extract_keywords(record.brand))

        # Add color
        if record.color:
            keyword_parts.extend(self._extract_keywords(record.color))

        # Add existing keywords
        if record.keywords:
            existing = [k.strip().lower() for k in record.keywords.split(",")]
            keyword_parts.extend(existing)

        # Remove duplicates and stop words
        seen_keywords_set: set[str] = set()
        unique_keywords: List[str] = []
        for kw in keyword_parts:
            kw_lower = kw.lower()
            if kw_lower not in STOP_WORDS and kw_lower not in seen_keywords_set and len(kw_lower) > 1:
                seen_keywords_set.add(kw_lower)
                unique_keywords.append(kw)

        if not unique_keywords:
            return None

        # Join and truncate to max length
        keywords_str = ", ".join(unique_keywords)
        return self._truncate_word_safe(keywords_str, self.max_keywords_length)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful words from text, removing stop words."""
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [w for w in words if w not in STOP_WORDS and len(w) > 1]

    def _build_description_from_fields(self, record: CatalogRecord) -> Optional[str]:
        """Build a description from available product fields."""
        parts: List[str] = []

        if record.title:
            parts.append(record.title.strip())

        if record.brand:
            parts.append(f"by {record.brand.strip()}")

        if record.category:
            parts.append(f"Category: {record.category.strip()}")

        if record.color:
            parts.append(f"Color: {record.color.strip()}")

        if record.weight:
            parts.append(f"Weight: {record.weight} kg")

        if record.dimensions:
            parts.append(f"Dimensions: {record.dimensions.strip()}")

        if not parts:
            return None

        return ". ".join(parts) + "."

    @staticmethod
    def _truncate_word_safe(text: str, max_length: int) -> str:
        """Truncate text to max_length, breaking at the last word boundary."""
        if len(text) <= max_length:
            return text
        # Reserve space for the ellipsis suffix
        ellipsis = "..."
        available = max_length - len(ellipsis)
        truncated = text[:available]
        # Break at last space
        last_space = truncated.rfind(" ")
        if last_space > available // 2:
            return truncated[:last_space].strip() + ellipsis
        return truncated.strip() + ellipsis
