"""Product overlap detection — find matching products across stores using fuzzy matching."""

import logging
from typing import List

from rapidfuzz import fuzz, process

from src.models.store_analysis import StoreAnalysis

logger = logging.getLogger(__name__)


class OverlapDetector:
    """Detects overlapping products across multiple competitor stores."""

    def __init__(self, threshold: float = 70.0):
        """
        Args:
            threshold: Minimum fuzzy match score (0–100) to consider two products as overlapping.
        """
        self.threshold = threshold

    def detect_overlaps(self, stores: List[StoreAnalysis]) -> List[dict]:
        """Detect products that appear in multiple stores.

        Args:
            stores: List of StoreAnalysis objects.

        Returns:
            List of overlap dicts with keys: product_name, stores, prices, price_spread.
        """
        if len(stores) < 2:
            return []

        # Build a mapping: product_name -> list of (store_url, price)
        product_map: dict[str, List[tuple[str, float]]] = {}

        for store in stores:
            for product in store.products:
                name = product.get("name", "").strip()
                if not name:
                    continue
                price = product.get("price", 0)
                if name not in product_map:
                    product_map[name] = []
                product_map[name].append((store.stores_url, price))

        overlaps: List[dict] = []

        # Check for exact matches first
        for name, entries in product_map.items():
            if len(entries) >= 2:
                prices = {url: price for url, price in entries}
                price_spread = max(prices.values()) - min(prices.values()) if prices else 0
                overlaps.append({
                    "product_name": name,
                    "stores": [url for url, _ in entries],
                    "prices": prices,
                    "price_spread": round(price_spread, 2),
                    "overlap_score": 100.0,
                })

        # Check for fuzzy matches between different product names
        all_names = list(product_map.keys())
        checked_pairs: set = set()

        for i, name_a in enumerate(all_names):
            for j, name_b in enumerate(all_names):
                if i >= j:
                    continue
                pair_key = (name_a, name_b)
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)

                score = fuzz.token_set_ratio(name_a, name_b)
                if score >= self.threshold:
                    # Merge the two products
                    combined_entries = product_map[name_a] + product_map[name_b]
                    # Use the longer name as canonical
                    canonical_name = name_a if len(name_a) >= len(name_b) else name_b
                    prices = {url: price for url, price in combined_entries}
                    price_spread = max(prices.values()) - min(prices.values()) if prices else 0

                    overlaps.append({
                        "product_name": canonical_name,
                        "stores": list(set(url for url, _ in combined_entries)),
                        "prices": prices,
                        "price_spread": round(price_spread, 2),
                        "overlap_score": round(score, 2),
                    })

        # Sort by number of stores (most overlapping first)
        overlaps.sort(key=lambda x: len(x["stores"]), reverse=True)

        logger.info(f"Detected {len(overlaps)} product overlap(s)")
        return overlaps
