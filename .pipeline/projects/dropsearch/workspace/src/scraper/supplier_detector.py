"""Supplier chain detection — find embedded supplier links in competitor store HTML."""

import re
import logging
from typing import List

from src.models.store_analysis import SupplierChain

logger = logging.getLogger(__name__)

# Characters that terminate a URL in HTML attributes
URL_TERMINATORS = r"[^\s'\">]"


class SupplierDetector:
    """Scans competitor store HTML for embedded supplier links and pricing hints."""

    # Known supplier domains and their confidence weights
    SUPPLIER_PATTERNS = {
        "AliExpress": {
            "domains": [r"aliexpress\.com", r"alibaba\.com"],
            "confidence": 0.9,
        },
        "CJ Dropshipping": {
            "domains": [r"cjdropshipping\.com", r"cj\.com"],
            "confidence": 0.85,
        },
        "Spocket": {
            "domains": [r"spocket\.co", r"spocket\.io"],
            "confidence": 0.8,
        },
        "AliDrop": {
            "domains": [r"alidrop\.io", r"alidropwireframe\.com"],
            "confidence": 0.85,
        },
        "DSers": {
            "domains": [r"dsers\.com"],
            "confidence": 0.85,
        },
        "Zendrop": {
            "domains": [r"zendrop\.com"],
            "confidence": 0.8,
        },
        "Doba": {
            "domains": [r"doba\.com"],
            "confidence": 0.75,
        },
        "SaleHoo": {
            "domains": [r"salehoo\.com"],
            "confidence": 0.7,
        },
        "Wholesale88": {
            "domains": [r"wholesale88\.com"],
            "confidence": 0.7,
        },
        "Banggood": {
            "domains": [r"banggood\.com"],
            "confidence": 0.75,
        },
        "Temu": {
            "domains": [r"temu\.com"],
            "confidence": 0.7,
        },
        "DHgate": {
            "domains": [r"dhgate\.com"],
            "confidence": 0.7,
        },
    }

    # Patterns for hidden supplier prices in data attributes
    PRICE_ATTR_PATTERNS = [
        r'data-supplier-price="([\d.]+)"',
        r'data-cost="([\d.]+)"',
        r'data-wholesale-price="([\d.]+)"',
        r'data-supplier_cost="([\d.]+)"',
        r'"supplier_price"\s*:\s*([\d.]+)',
        r'"cost"\s*:\s*([\d.]+)',
    ]

    # Patterns for supplier iframe embeds
    IFRAME_PATTERNS = [
        r'<iframe[^>]*src=["\']([^"\']*?(?:aliexpress|cjdropshipping|spocket|alidrop|dsers|zendrop)[^"\']*)["\']',
    ]

    # Patterns for supplier API endpoints
    API_PATTERNS = [
        r'https?://[^"\']*(?:aliexpress|cjdropshipping|spocket|alidrop|dsers|zendrop)[^"\']*?/api',
    ]

    def detect(self, html: str, base_url: str = "") -> List[SupplierChain]:
        """Detect supplier chains in HTML.

        Args:
            html: Rendered HTML of the store page.
            base_url: Base URL of the store (unused but kept for API compatibility).

        Returns:
            List of SupplierChain objects.
        """
        if not html:
            return []

        chains: List[SupplierChain] = []
        seen_sources: set = set()

        # 1. Domain-based detection
        for source, info in self.SUPPLIER_PATTERNS.items():
            for domain_pattern in info["domains"]:
                matches = re.findall(domain_pattern, html, re.IGNORECASE)
                if matches:
                    # Extract actual URLs
                    url_pattern = r"https?://" + URL_TERMINATORS + r"*" + domain_pattern.replace(r"\.", r"[" + URL_TERMINATORS + r"]*")
                    urls = re.findall(url_pattern, html, re.IGNORECASE)
                    if not urls:
                        # Fallback: find any URL containing the domain
                        urls = re.findall(r"https?://" + URL_TERMINATORS + r"*" + domain_pattern.replace(r"\.", r"[" + URL_TERMINATORS + r"]*"), html, re.IGNORECASE)
                    if not urls:
                        clean_domain = domain_pattern.replace(r'\.', '').replace(r'[', '').replace(r']', '').replace(r'\d', 'example')
                        urls = [f"https://{clean_domain}"]

                    chain = SupplierChain(
                        source=source,
                        confidence=info["confidence"],
                        detected_urls=urls[:10],  # Cap URLs
                    )
                    chains.append(chain)
                    seen_sources.add(source)

        # 2. Hidden price attribute detection
        for pattern in self.PRICE_ATTR_PATTERNS:
            matches = re.findall(pattern, html)
            if matches:
                # Try to infer supplier from context
                for match in matches:
                    # Look for nearby supplier context
                    context_start = max(0, html.find(match) - 200)
                    context_end = min(len(html), html.find(match) + 200)
                    context = html[context_start:context_end].lower()

                    for source, info in self.SUPPLIER_PATTERNS.items():
                        for domain in info["domains"]:
                            if re.search(domain, context, re.IGNORECASE):
                                estimated_cost = float(match) if match else None
                                chain = SupplierChain(
                                    source=source,
                                    confidence=0.6,  # Lower confidence for price-only detection
                                    estimated_cost=estimated_cost,
                                )
                                if source not in seen_sources:
                                    chains.append(chain)
                                    seen_sources.add(source)
                                break

        # 3. Iframe embed detection
        for pattern in self.IFRAME_PATTERNS:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                for source, info in self.SUPPLIER_PATTERNS.items():
                    for domain in info["domains"]:
                        if re.search(domain, match, re.IGNORECASE):
                            chain = SupplierChain(
                                source=source,
                                confidence=0.75,
                                detected_urls=[match],
                            )
                            if source not in seen_sources:
                                chains.append(chain)
                                seen_sources.add(source)
                            break

        # 4. API endpoint detection
        for pattern in self.API_PATTERNS:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                for source, info in self.SUPPLIER_PATTERNS.items():
                    for domain in info["domains"]:
                        if re.search(domain, match, re.IGNORECASE):
                            chain = SupplierChain(
                                source=source,
                                confidence=0.7,
                                detected_urls=[match],
                            )
                            if source not in seen_sources:
                                chains.append(chain)
                                seen_sources.add(source)
                            break

        # Deduplicate by source, keeping highest confidence
        seen: dict = {}
        for chain in chains:
            if chain.source not in seen or chain.confidence > seen[chain.source].confidence:
                seen[chain.source] = chain
        chains = list(seen.values())

        logger.info(f"Detected {len(chains)} supplier chain(s): {[c.source for c in chains]}")
        return chains
