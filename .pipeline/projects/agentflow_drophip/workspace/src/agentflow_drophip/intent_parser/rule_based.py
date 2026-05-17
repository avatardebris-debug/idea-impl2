"""Rule-based fallback parser for intent extraction.

Uses regex and heuristic patterns to extract business specification
fields from natural-language input when the LLM is unavailable.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from agentflow_drophip.models.business_spec import (
    BrandingConfig,
    FulfillmentType,
    PricingConfig,
    SupplierType,
    StorefrontType,
    TargetMarket,
)
from agentflow_drophip.models.business_spec import BusinessSpec


class RuleBasedParser:
    """Fallback parser that uses regex/heuristics to extract BusinessSpec fields."""

    # Supplier keywords
    SUPPLIER_PATTERNS: Dict[str, str] = {
        "aliexpress": r"\bali\s*express\b",
        "spocket": r"\bspocket\b",
        "cj_dropshipping": r"\bcj\s*(drop)?shipping\b",
        "dropshipmobile": r"\bdrops?hip\s*mobile\b",
        "custom": r"\bcustom\s*(supplier|source)\b",
    }

    # Storefront keywords
    STOREFRONT_PATTERNS: Dict[str, str] = {
        "shopify": r"\bshopify\b",
        "woocommerce": r"\bwoocommerce\b",
        "ecommerce_platform": r"\bwoocommerce|wix|squarespace|bigcommerce\b",
        "custom": r"\bcustom\s*(store|platform)\b",
    }

    # Fulfillment keywords
    FULFILLMENT_PATTERNS: Dict[str, str] = {
        "auto": r"\bauto\s*(matic)?\s*fulfillment\b|\bfulfill\s*automatically\b|\bfully\s*automated\b",
        "manual": r"\bmanual\s*fulfillment\b|\bfulfill\s*manually\b",
        "hybrid": r"\bhybrid\s*fulfillment\b|\bpartially\s*automated\b",
    }

    # Pricing keywords
    MARKUP_PATTERNS: list = [
        (r"\b(\d+\.?\d*)\s*x\s*markup\b", "markup_multiplier"),
        (r"\b(\d+\.?\d*)\s*percent\s*(markup|margin)\b", "markup_multiplier"),
        (r"\b(\d+\.?\d*)\s*percent\s*profit\b", "markup_multiplier"),
        (r"\bmarkup\s*(of|at)\s*(\d+\.?\d*)\b", "markup_multiplier"),
    ]

    PRICING_STRATEGY_PATTERNS: Dict[str, str] = {
        "markup": r"\bmarkup\s*(strategy)?\b",
        "competitive": r"\bcompetitive\s*(pricing|price)\b",
        "premium": r"\bpremium\s*(pricing|price)\b",
    }

    # Country keywords
    COUNTRY_PATTERNS: Dict[str, str] = {
        "US": r"\b(united\s*states|usa|america|us)\b",
        "CA": r"\b(canada|ca)\b",
        "UK": r"\b(united\s*kingdom|uk|britain)\b",
        "AU": r"\b(australia|au)\b",
        "DE": r"\b(germany|de)\b",
        "FR": r"\b(france|fr)\b",
    }

    # Currency keywords
    CURRENCY_PATTERNS: Dict[str, str] = {
        "USD": r"\b(usd|dollars?)\b",
        "CAD": r"\b(cad|cad dollars?)\b",
        "GBP": r"\b(gbp|pounds?)\b",
        "EUR": r"\b(eur|euros?)\b",
        "AUD": r"\b(aud|australian\s*dollars?)\b",
    }

    def parse(self, text: str) -> BusinessSpec:
        """Parse natural-language text into a BusinessSpec using rule-based heuristics.

        Args:
            text: Natural-language description of the dropshipping business.

        Returns:
            A validated BusinessSpec object.
        """
        lower_text = text.lower()

        # Extract niche (first meaningful noun phrase after common prefixes)
        niche = self._extract_niche(text)

        # Extract supplier
        supplier = self._extract_supplier(lower_text)

        # Extract storefront
        storefront = self._extract_storefront(lower_text)

        # Extract target market
        target_market = self._extract_target_market(lower_text)

        # Extract pricing
        pricing = self._extract_pricing(lower_text)

        # Extract fulfillment
        fulfillment = self._extract_fulfillment(lower_text)

        # Extract branding
        branding = self._extract_branding(lower_text)

        # Extract additional fields
        max_product_cost = self._extract_max_product_cost(lower_text)
        min_profit_margin = self._extract_min_profit_margin(lower_text)
        auto_reorder_threshold = self._extract_auto_reorder_threshold(lower_text)

        return BusinessSpec(
            niche=niche,
            supplier=supplier,
            storefront=storefront,
            target_market=target_market,
            pricing=pricing,
            fulfillment=fulfillment,
            branding=branding,
            description=text.strip(),
            max_product_cost=max_product_cost,
            min_profit_margin=min_profit_margin,
            auto_reorder_threshold=auto_reorder_threshold,
        )

    def _extract_niche(self, text: str) -> str:
        """Extract the product niche from text."""
        # Try to find patterns like "sell X", "niche: X", "X products"
        patterns = [
            r"(?:sell|niche|category|products?)[:\s]+([a-zA-Z\s]+?)(?:\s*(?:from|to|at|for|with|by|\.|$))",
            r"(?:want|looking|need)\s+(?:to\s+)?(?:sell|offer|list)\s+(?:to\s+)?([a-zA-Z\s]+?)(?:\s*(?:from|to|at|for|with|by|\.|$))",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                niche = match.group(1).strip()
                if niche:
                    return niche

        # Fallback: extract first meaningful phrase
        words = text.split()
        skip_words = {"i", "want", "to", "sell", "a", "the", "my", "for", "from", "with", "and", "of", "in", "on", "at", "by", "about", "looking", "need", "offer", "list"}
        for i, word in enumerate(words):
            if word.lower() not in skip_words and len(word) > 2:
                # Take next few words as niche
                end = min(i + 4, len(words))
                niche = " ".join(words[i:end])
                return niche.strip()

        return "general"

    def _extract_supplier(self, text: str) -> SupplierType:
        """Extract supplier type from text."""
        for supplier_type, pattern in self.SUPPLIER_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return SupplierType(supplier_type)
        return SupplierType.ALIEXPRESS  # default

    def _extract_storefront(self, text: str) -> StorefrontType:
        """Extract storefront type from text."""
        for storefront_type, pattern in self.STOREFRONT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return StorefrontType(storefront_type)
        return StorefrontType.SHOPIFY  # default

    def _extract_target_market(self, text: str) -> TargetMarket:
        """Extract target market from text."""
        countries = []
        currency = "USD"
        language = "en"

        for country_code, pattern in self.COUNTRY_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                if country_code not in countries:
                    countries.append(country_code)

        for curr_code, pattern in self.CURRENCY_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                currency = curr_code
                break

        if not countries:
            countries = ["US"]  # default

        return TargetMarket(countries=countries, currency=currency, language=language)

    def _extract_pricing(self, text: str) -> PricingConfig:
        """Extract pricing configuration from text."""
        markup_multiplier = 1.0
        pricing_strategy = "markup"

        # Check for pricing strategy first
        for strategy, pattern in self.PRICING_STRATEGY_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                pricing_strategy = strategy
                break

        # Check for markup multiplier
        for pattern, field in self.MARKUP_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1))
                    if val > 0:
                        markup_multiplier = val
                        break
                except (ValueError, IndexError):
                    continue

        return PricingConfig(markup_multiplier=markup_multiplier, pricing_strategy=pricing_strategy)

    def _extract_fulfillment(self, text: str) -> FulfillmentType:
        """Extract fulfillment type from text."""
        for fulfillment_type, pattern in self.FULFILLMENT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return FulfillmentType(fulfillment_type)
        return FulfillmentType.AUTO  # default

    def _extract_branding(self, text: str) -> BrandingConfig:
        """Extract branding configuration from text."""
        brand_name = None
        custom_packaging = False

        brand_match = re.search(r"(?:brand|store)\s*(?:name)?[:\s]+([A-Za-z][A-Za-z0-9\s]+?)(?:\s*(?:\.|$|,))", text, re.IGNORECASE)
        if brand_match:
            brand_name = brand_match.group(1).strip()

        if re.search(r"custom\s*(packaging|pack)\b", text, re.IGNORECASE):
            custom_packaging = True

        return BrandingConfig(brand_name=brand_name, custom_packaging=custom_packaging)

    def _extract_max_product_cost(self, text: str) -> Optional[float]:
        """Extract max product cost from text."""
        match = re.search(r"(?:max\s*)?(?:product\s*)?cost[:\s]+\$?(\d+\.?\d*)", text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    def _extract_min_profit_margin(self, text: str) -> Optional[float]:
        """Extract min profit margin from text."""
        match = re.search(r"(?:min\s*)?(?:profit\s*)?margin[:\s]+(\d+\.?\d*)\s*%", text, re.IGNORECASE)
        if match:
            return float(match.group(1)) / 100.0
        return None

    def _extract_auto_reorder_threshold(self, text: str) -> Optional[int]:
        """Extract auto-reorder threshold from text."""
        match = re.search(r"(?:auto\s*reorder|reorder)\s*(?:threshold|when|at)\s*(?:below|under|less\s*than)\s*(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
