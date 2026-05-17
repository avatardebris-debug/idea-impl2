"""Product extraction from e-commerce HTML."""

import logging
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from src.models.product import Product
from src.scraper.parsers.shopify import ShopifyParser
from src.scraper.parsers.woocommerce import WooCommerceParser
from src.scraper.parsers.generic import GenericParser

logger = logging.getLogger(__name__)


class ProductExtractor:
    """Extracts products from e-commerce HTML using platform-specific parsers."""

    def __init__(self):
        self.parsers = [
            ("shopify", ShopifyParser),
            ("woocommerce", WooCommerceParser),
            ("generic", GenericParser),
        ]

    def extract(self, html: str, url: str) -> List[Product]:
        """Extract products from HTML.

        Args:
            html: Rendered HTML content.
            url: The source URL.

        Returns:
            List of extracted Product objects.
        """
        if not html:
            logger.warning("Empty HTML provided to extractor.")
            return []

        # Detect platform and use appropriate parser
        platform = self._detect_platform(html)
        logger.info(f"Detected platform: {platform}")

        if platform == "shopify":
            products = ShopifyParser.extract(html, url)
        elif platform == "woocommerce":
            products = WooCommerceParser.extract(html, url)
        else:
            products = GenericParser.extract(html, url)

        logger.info(f"Extracted {len(products)} products from {url}")
        return products

    def _detect_platform(self, html: str) -> str:
        """Detect the e-commerce platform from HTML.

        Args:
            html: HTML content to analyze.

        Returns:
            Detected platform name ('shopify', 'woocommerce', or 'generic').
        """
        # Check for Shopify markers
        if ShopifyParser.is_shopify(html):
            return "shopify"

        # Check for WooCommerce markers
        if WooCommerceParser.is_woocommerce(html):
            return "woocommerce"

        # Default to generic
        return "generic"

    def extract_from_url(self, url: str, html: str) -> List[Product]:
        """Extract products from a URL's HTML content.

        Args:
            url: The source URL.
            html: Rendered HTML content.

        Returns:
            List of extracted Product objects.
        """
        return self.extract(html, url)
