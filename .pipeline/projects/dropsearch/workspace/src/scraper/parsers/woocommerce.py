"""WooCommerce-specific product extraction."""

import json
import re
from typing import List

from bs4 import BeautifulSoup

from src.models.product import Product


class WooCommerceParser:
    """Extract products from WooCommerce stores."""

    # WooCommerce-specific markers
    WOOCOMMERCE_MARKERS = [
        r"woocommerce",
        r"wc-.*-",
        r"woocommerce-js",
        r"woocommerce.*css",
        r"wp-.*-woocommerce",
        r"woocommerce.*api",
    ]

    @classmethod
    def is_woocommerce(cls, html: str) -> bool:
        """Detect if HTML is from a WooCommerce store."""
        for marker in cls.WOOCOMMERCE_MARKERS:
            if re.search(marker, html, re.IGNORECASE):
                return True
        return False

    @classmethod
    def extract(cls, html: str, base_url: str) -> List[Product]:
        """Extract products from WooCommerce HTML."""
        soup = BeautifulSoup(html, "html.parser")
        products = []

        # Method 1.5: JSON-LD
        json_ld = cls._extract_json_ld(soup)
        if json_ld:
            products.extend(json_ld)

        # Method 2: WooCommerce JSON API data
        if not products:
            json_data = cls._extract_json_api(html)
            if json_data:
                products.extend(json_data)

        # Method 2: DOM-based extraction
        if not products:
            products.extend(cls._extract_dom(soup, base_url))

        # Method 3: REST API endpoint detection
        if not products:
            products.extend(cls._extract_api_endpoints(html, base_url))

        return products

    @classmethod
    def _extract_json_ld(cls, soup: BeautifulSoup) -> List[Product]:
        products = []
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if "@graph" in data:
                        for item in data["@graph"]:
                            if isinstance(item, dict) and item.get("@type") == "Product":
                                products.append(cls._parse_product(item))
                    elif data.get("@type") == "Product":
                        products.append(cls._parse_product(data))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            products.append(cls._parse_product(item))
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue
        return products

    @classmethod
    def _parse_product(cls, data: dict) -> Product:
        name = data.get("name", "Unknown Product")
        offers = data.get("offers", {})
        if isinstance(offers, list) and len(offers) > 0:
            price_str = offers[0].get("price", "0")
        elif isinstance(offers, dict):
            price_str = offers.get("price", "0")
        else:
            price_str = "0"
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0
        return Product(name=name, price=price, url=data.get("url"), source="woocommerce_json_ld")

    @classmethod
    def _extract_json_api(cls, html: str) -> List[Product]:
        """Extract products from WooCommerce JSON API data embedded in page."""
        products = []

        # Look for wc_product_* scripts
        pattern = r'wc_product_(\d+)\s*=\s*({[^}]+})'
        matches = re.findall(pattern, html)

        for _, json_str in matches:
            try:
                data = json.loads(json_str)
                if "name" in data and "price" in data:
                    products.append(Product(
                        name=data.get("name", "Unknown Product"),
                        price=float(data.get("price", 0)),
                        url=data.get("permalink") or data.get("url"),
                        source="woocommerce_json_api",
                    ))
            except (json.JSONDecodeError, ValueError):
                continue

        return products

    @classmethod
    def _extract_dom(cls, soup: BeautifulSoup, base_url: str) -> List[Product]:
        """Extract products from WooCommerce DOM elements."""
        products = []

        # WooCommerce product classes
        product_selectors = [
            ("li", "product"),
            ("div", "woocommerce-loop-product"),
            ("div", "product"),
            ("article", "product"),
        ]

        for tag, css_class in product_selectors:
            elements = soup.find_all(tag, class_=re.compile(css_class, re.IGNORECASE))
            for element in elements:
                name = cls._extract_name(element)
                price = cls._extract_price(element)

                if name and price > 0:
                    link = element.find("a", href=True)
                    url = link["href"] if link and link["href"].startswith("/") else None
                    if url:
                        url = f"{base_url.rstrip('/')}{url}"

                    products.append(Product(
                        name=name,
                        price=price,
                        url=url,
                        source="woocommerce_dom",
                    ))

        return products

    @classmethod
    def _extract_api_endpoints(cls, html: str, base_url: str) -> List[Product]:
        """Detect WooCommerce REST API endpoints."""
        products = []

        # Look for wp-json/woocommerce/v3/ endpoints
        pattern = r'wp-json/woocommerce/v3/products'
        if re.search(pattern, html):
            # This indicates WooCommerce is present
            # In a real implementation, we'd fetch the API
            pass

        return products

    @classmethod
    def _extract_name(cls, element) -> str:
        """Extract product name from WooCommerce element."""
        # Try WooCommerce-specific selectors
        name = element.find("h2", class_=re.compile("product", re.IGNORECASE))
        if name:
            return name.get_text(strip=True)

        # Try link text
        link = element.find("a", class_=re.compile("product", re.IGNORECASE))
        if link:
            return link.get_text(strip=True)

        # Fallback to any heading
        for tag in ["h2", "h3", "h4"]:
            heading = element.find(tag)
            if heading:
                return heading.get_text(strip=True)

        return ""

    @classmethod
    def _extract_price(cls, element) -> float:
        """Extract product price from WooCommerce element."""
        # Try WooCommerce price classes
        price_classes = ["price", "woocommerce-Price-amount", "amount"]
        for css_class in price_classes:
            price_el = element.find(class_=re.compile(css_class, re.IGNORECASE))
            if price_el:
                price_text = price_el.get_text()
                price = cls._parse_price(price_text)
                if price > 0:
                    return price

        # Try data attributes
        price_data = element.get("data-price")
        if price_data:
            try:
                return float(price_data)
            except ValueError:
                pass

        return 0.0

    @classmethod
    def _parse_price(cls, text: str) -> float:
        """Parse price from text."""
        if not text:
            return 0.0
        cleaned = re.sub(r"[^\d.]", "", text)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
