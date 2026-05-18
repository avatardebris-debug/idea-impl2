"""Generic e-commerce product extraction."""

import re
from typing import List

from bs4 import BeautifulSoup

from src.models.product import Product


class GenericParser:
    """Extract products from generic e-commerce stores."""

    # Common e-commerce patterns
    PRODUCT_SELECTORS = [
        ("div", re.compile(r"product|item|card", re.IGNORECASE)),
        ("article", re.compile(r"product|item", re.IGNORECASE)),
        ("li", re.compile(r"product|item", re.IGNORECASE)),
    ]

    PRICE_SELECTORS = [
        re.compile(r"price|cost|amount|money", re.IGNORECASE),
        re.compile(r"\$|€|£|¥", re.IGNORECASE),
    ]

    NAME_SELECTORS = [
        re.compile(r"name|title|heading", re.IGNORECASE),
        re.compile(r"product|item", re.IGNORECASE),
    ]

    @classmethod
    def extract(cls, html: str, base_url: str) -> List[Product]:
        """Extract products from generic HTML."""
        soup = BeautifulSoup(html, "html.parser")
        products = []

        # Extract from common product containers
        for tag, pattern in cls.PRODUCT_SELECTORS:
            elements = soup.find_all(tag, class_=pattern)
            for element in elements:
                product = cls._extract_single_product(element, base_url)
                if product:
                    products.append(product)

        # Extract from links that look like products
        products.extend(cls._extract_from_links(soup, base_url))

        # Deduplicate by name
        return cls._deduplicate(products)

    @classmethod
    def _extract_single_product(cls, element, base_url: str) -> Product:
        """Extract a single product from a DOM element."""
        name = cls._extract_name(element)
        price = cls._extract_price(element)

        if not name or price <= 0:
            return None

        # Extract URL
        link = element.find("a", href=True)
        url = None
        if link:
            href = link["href"]
            if href.startswith("/"):
                url = f"{base_url.rstrip('/')}{href}"
            elif href.startswith("http"):
                url = href

        return Product(
            name=name,
            price=price,
            url=url,
            source="generic_dom",
        )

    @classmethod
    def _extract_from_links(cls, soup: BeautifulSoup, base_url: str) -> List[Product]:
        """Extract products from links that look like product pages."""
        products = []

        # Look for links with price in text
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            price = cls._parse_price(text)

            if price > 0 and link["href"].startswith("/"):
                url = f"{base_url.rstrip('/')}{link['href']}"
                name = text.split("$")[0].strip() if "$" in text else text

                if name and len(name) > 2:
                    products.append(Product(
                        name=name,
                        price=price,
                        url=url,
                        source="generic_link",
                    ))

        return products

    @classmethod
    def _extract_name(cls, element) -> str:
        """Extract product name from element."""
        # Try common name patterns
        for pattern in cls.NAME_SELECTORS:
            # Check class names
            classes = element.get("class", [])
            for css_class in classes:
                if re.search(pattern, css_class):
                    text = element.get_text(strip=True)
                    if text and len(text) > 2:
                        return text

            # Check child elements
            for tag in ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div", "a"]:
                child = element.find(tag, class_=pattern)
                if child:
                    text = child.get_text(strip=True)
                    if text and len(text) > 2:
                        return text

        # Fallback to element text
        text = element.get_text(strip=True)
        if text and len(text) > 2:
            return text

        return ""

    @classmethod
    def _extract_price(cls, element) -> float:
        """Extract product price from element."""
        # Check class names for price indicators
        classes = element.get("class", [])
        for css_class in classes:
            if any(re.search(p, css_class) for p in cls.PRICE_SELECTORS):
                text = element.get_text()
                price = cls._parse_price(text)
                if price > 0:
                    return price

        # Check child elements
        for tag in ["span", "div", "p", "strong", "b"]:
            child = element.find(tag)
            if child:
                text = child.get_text()
                price = cls._parse_price(text)
                if price > 0:
                    return price

        # Check data attributes
        price_data = element.get("data-price") or element.get("data-cost")
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

        # Remove currency symbols and commas
        cleaned = re.sub(r"[^\d.]", "", text)

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @classmethod
    def _deduplicate(cls, products: List[Product]) -> List[Product]:
        """Remove duplicate products by name."""
        seen = set()
        unique = []
        for product in products:
            name_key = product.name.lower().strip()
            if name_key not in seen:
                seen.add(name_key)
                unique.append(product)
        return unique
