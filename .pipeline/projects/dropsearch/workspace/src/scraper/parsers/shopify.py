"""Shopify-specific product extraction."""

import json
import re
from typing import List

from bs4 import BeautifulSoup

from src.models.product import Product


class ShopifyParser:
    """Extract products from Shopify stores."""

    # Shopify-specific markers
    SHOPIFY_MARKERS = [
        r"cdn\.shopify\.com",
        r"shopify\.com",
        r"shopify.*theme",
        r"assets\.cdn-shopify",
        r"shopify.*checkout",
        r"data-shopify",
        r"shopify.*buy-button",
    ]

    @classmethod
    def is_shopify(cls, html: str) -> bool:
        """Detect if HTML is from a Shopify store."""
        for marker in cls.SHOPIFY_MARKERS:
            if re.search(marker, html, re.IGNORECASE):
                return True
        return False

    @classmethod
    def extract(cls, html: str, base_url: str) -> List[Product]:
        """Extract products from Shopify HTML."""
        soup = BeautifulSoup(html, "html.parser")
        products = []

        # Method 1: JSON-LD product data
        json_ld = cls._extract_json_ld(soup)
        if json_ld:
            products.extend(json_ld)

        # Method 2: Shopify product JSON templates
        if not products:
            products.extend(cls._extract_json_templates(html, base_url))

        # Method 3: DOM-based extraction
        if not products:
            products.extend(cls._extract_dom(soup, base_url))

        return products

    @classmethod
    def _extract_json_ld(cls, soup: BeautifulSoup) -> List[Product]:
        """Extract products from JSON-LD structured data."""
        products = []
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get("@type") == "Product":
                        products.append(cls._parse_product(data))
                    elif data.get("@type") == "ItemList":
                        for item in data.get("itemListElement", []):
                            if isinstance(item, dict):
                                product_data = item.get("item", {})
                                if product_data:
                                    products.append(cls._parse_product(product_data))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            products.append(cls._parse_product(item))
            except (json.JSONDecodeError, AttributeError):
                continue

        return products

    @classmethod
    def _extract_json_templates(cls, html: str, base_url: str) -> List[Product]:
        """Extract products from Shopify's JSON template files."""
        products = []
        pattern = r'"url":\s*"(\/products\/[^"]+)"'
        matches = re.findall(pattern, html)

        for url_path in matches:
            product_url = f"{base_url.rstrip('/')}{url_path}"
            # Extract price from adjacent JSON
            price_match = re.search(
                rf'"url":\s*"{re.escape(url_path)}".*?"price":\s*(\d+)',
                html,
                re.DOTALL,
            )
            price = float(price_match.group(1)) / 100 if price_match else 0.0

            # Extract name
            name_match = re.search(
                rf'"url":\s*"{re.escape(url_path)}".*?"title":\s*"([^"]+)"',
                html,
                re.DOTALL,
            )
            name = name_match.group(1) if name_match else "Unknown Product"

            products.append(Product(
                name=name,
                price=price,
                url=product_url,
                source="shopify_json_template",
            ))

        return products

    @classmethod
    def _extract_dom(cls, soup: BeautifulSoup, base_url: str) -> List[Product]:
        """Extract products from DOM elements."""
        products = []

        # Shopify product cards
        product_cards = soup.find_all(
            ["div", "a"],
            class_=re.compile(r"product|card|item", re.IGNORECASE),
        )

        for card in product_cards:
            name = cls._extract_text(card, ["h2", "h3", "h4", "a", "span"], ["product-name", "title"])
            price_text = cls._extract_text(card, ["span", "div"], ["price", "money"])
            price = cls._parse_price(price_text)

            if name and price > 0:
                link = card.find("a", href=True)
                url = link["href"] if link and link["href"].startswith("/") else None
                if url:
                    url = f"{base_url.rstrip('/')}{url}"

                products.append(Product(
                    name=name,
                    price=price,
                    url=url,
                    source="shopify_dom",
                ))

        return products

    @classmethod
    def _parse_product(cls, data: dict) -> Product:
        """Parse a single product from JSON-LD data."""
        name = data.get("name", data.get("title", "Unknown Product"))
        price_str = data.get("offers", {}).get("price", "0")
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0

        url = data.get("url")
        if url and not url.startswith("http"):
            url = f"https://example.com{url}"

        return Product(
            name=name,
            price=price,
            url=url,
            source="shopify_json_ld",
        )

    @classmethod
    def _extract_text(cls, element, tags: List[str], classes: List[str]) -> str:
        """Extract text from element matching tags and classes."""
        for tag in tags:
            for cls in classes:
                found = element.find(tag, class_=re.compile(cls, re.IGNORECASE))
                if found and found.get_text(strip=True):
                    return found.get_text(strip=True)
        return ""

    @classmethod
    def _parse_price(cls, text: str) -> float:
        """Parse price from text."""
        if not text:
            return 0.0
        # Remove currency symbols and commas
        cleaned = re.sub(r"[^\d.]", "", text)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
