"""IntentParser — parses natural language descriptions into structured business specifications."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from agentflow_drophip.exceptions import ParserError
from agentflow_drophip.models.business_spec import (
    BrandingConfig,
    BusinessSpec,
    FulfillmentType,
    PricingConfig,
    PricingStrategy,
    StorefrontType,
    SupplierType,
    TargetMarket,
)


class IntentParser:
    """Parses natural language descriptions into structured business specifications."""

    # Keywords for entity extraction
    SUPPLIER_KEYWORDS = {
        SupplierType.ALIEXPRESS: ["aliexpress", "ali express", "alibaba", "china", "chinese"],
        SupplierType.CJ_DROPSHIPPING: ["cj drop", "cjdropshipping", "cj"],
        SupplierType.SPOCKET: ["spocket"],
        SupplierType.DROPSHIPMOBILE: ["dropship mobile", "dropshipmobile"],
        SupplierType.CUSTOM: ["custom supplier", "custom supplier"],
    }

    STOREFRONT_KEYWORDS = {
        StorefrontType.SHOPIFY: ["shopify", "shop"],
        StorefrontType.WOOCOMMERCE: ["woocommerce", "woo", "wordpress"],
        StorefrontType.ECOMMERCE_PLATFORM: ["ecommerce", "e-commerce", "online store"],
        StorefrontType.CUSTOM: ["custom storefront", "custom storefront"],
    }

    FULFILLMENT_KEYWORDS = {
        FulfillmentType.AUTO: ["auto", "automatic", "automated", "fully automated"],
        FulfillmentType.MANUAL: ["manual", "hand", "personal", "custom"],
        FulfillmentType.HYBRID: ["hybrid", "mixed", "semi-auto", "semi-automatic"],
    }

    PRICING_KEYWORDS = {
        PricingStrategy.MARKUP: ["markup", "percentage", "percent", "%", "multiplier"],
        PricingStrategy.COMPETITIVE: ["competitive", "competitor", "market", "price match"],
        PricingStrategy.PREMIUM: ["premium", "luxury", "high-end", "exclusive"],
    }

    def parse(self, description: str) -> BusinessSpec:
        """Parse a natural language description into a BusinessSpec.

        Args:
            description: Natural language description of the business.

        Returns:
            Parsed BusinessSpec.

        Raises:
            ParserError: If parsing fails.
        """
        if not description or not description.strip():
            raise ParserError("Empty description provided")

        try:
            # Extract entities
            niche = self._extract_niche(description)
            supplier_type = self._extract_supplier(description)
            storefront_type = self._extract_storefront(description)
            fulfillment_type = self._extract_fulfillment(description)
            pricing_strategy = self._extract_pricing(description)

            # Extract numeric values
            max_product_cost = self._extract_max_cost(description)
            auto_reorder_threshold = self._extract_reorder_threshold(description)

            # Extract branding
            branding = self._extract_branding(description)

            # Extract budget
            budget = self._extract_budget(description)

            # Extract target market
            target_market = self._extract_target_market(description)

            # Build PricingConfig
            pricing_config = PricingConfig(
                markup_multiplier=budget.get("markup_multiplier", 2.0),
                pricing_strategy=pricing_strategy,
            )

            # Build BrandingConfig
            branding_config = BrandingConfig(
                brand_name=branding.get("brand_name"),
                color_scheme=branding.get("color_scheme"),
            )

            # Build TargetMarket
            target_market_obj = TargetMarket(
                countries=budget.get("countries", ["US"]),
                currency=budget.get("currency", "USD"),
                language=budget.get("language", "en"),
            )

            # Build spec
            spec = BusinessSpec(
                niche=niche,
                supplier=supplier_type,
                storefront=storefront_type,
                fulfillment=fulfillment_type,
                pricing=pricing_config,
                branding=branding_config,
                target_market=target_market_obj,
                max_product_cost=max_product_cost,
                auto_reorder_threshold=auto_reorder_threshold,
                description=description,
            )

            return spec

        except Exception as e:
            raise ParserError(
                f"Failed to parse description: {e}",
                description=description,
            ) from e

    def _extract_niche(self, description: str) -> str:
        """Extract the niche from the description."""
        # Look for common niche patterns
        niche_patterns = [
            r"(?:in|for|about|niche)\s+([a-zA-Z\s]+?)(?:\s+(?:market|business|store|shop|product|category|space))",
            r"([a-zA-Z]+)\s+(?:products?|items?|goods?)",
            r"([a-zA-Z]+)\s+(?:store|shop)",
        ]

        for pattern in niche_patterns:
            match = re.search(pattern, description.lower())
            if match:
                niche = match.group(1).strip()
                if niche:
                    return niche

        # Default niche
        return "general"

    def _extract_supplier(self, description: str) -> SupplierType:
        """Extract the supplier type from the description."""
        desc_lower = description.lower()

        for supplier_type, keywords in self.SUPPLIER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return supplier_type

        # Default supplier
        return SupplierType.ALIEXPRESS

    def _extract_storefront(self, description: str) -> StorefrontType:
        """Extract the storefront type from the description."""
        desc_lower = description.lower()

        for storefront_type, keywords in self.STOREFRONT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return storefront_type

        # Default storefront
        return StorefrontType.SHOPIFY

    def _extract_fulfillment(self, description: str) -> FulfillmentType:
        """Extract the fulfillment type from the description."""
        desc_lower = description.lower()

        for fulfillment_type, keywords in self.FULFILLMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return fulfillment_type

        # Default fulfillment
        return FulfillmentType.AUTO

    def _extract_pricing(self, description: str) -> PricingStrategy:
        """Extract the pricing strategy from the description."""
        desc_lower = description.lower()

        for pricing_strategy, keywords in self.PRICING_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return pricing_strategy

        # Default pricing
        return PricingStrategy.MARKUP

    def _extract_max_cost(self, description: str) -> float:
        """Extract the maximum product cost from the description."""
        # Look for price patterns
        price_patterns = [
            r"(?:max|maximum|up to|under)\s+(?:cost|price|budget)\s+[\$€£]?\s*(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*(?:dollars?|usd|us\$)",
        ]

        for pattern in price_patterns:
            match = re.search(pattern, description.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        # Default max cost
        return 50.0

    def _extract_reorder_threshold(self, description: str) -> int:
        """Extract the auto-reorder threshold from the description."""
        # Look for threshold patterns
        threshold_patterns = [
            r"(?:reorder|restock|threshold)\s+(?:at|when|below|under)\s+(\d+)",
            r"(\d+)\s*(?:units?|items?|stock)",
        ]

        for pattern in threshold_patterns:
            match = re.search(pattern, description.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        # Default threshold
        return 10

    def _extract_branding(self, description: str) -> Dict[str, Any]:
        """Extract branding information from the description."""
        branding = {}

        # Look for brand name
        brand_patterns = [
            r"(?:brand|name)\s+(?:is|called|named)\s+([a-zA-Z\s]+)",
            r"call\s+(?:it|the\s+store)\s+([a-zA-Z\s]+)",
        ]

        for pattern in brand_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                branding["brand_name"] = match.group(1).strip()
                break

        # Look for color scheme
        color_patterns = [
            r"(?:color|colour)\s+(?:scheme|theme)\s+([a-zA-Z\s]+)",
            r"([a-zA-Z]+)\s+(?:color|colour)",
        ]

        for pattern in color_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                branding["color_scheme"] = match.group(1).strip()
                break

        return branding

    def _extract_budget(self, description: str) -> Dict[str, Any]:
        """Extract budget information from the description."""
        budget = {}

        # Look for budget patterns
        budget_patterns = [
            r"(?:budget|investment)\s+(?:is|of|of\s+[\$€£]?)\s*[\$€£]?\s*(\d+\.?\d*)",
            r"spend\s+(?:up\s+to|around|approximately)\s*[\$€£]?\s*(\d+\.?\d*)",
        ]

        for pattern in budget_patterns:
            match = re.search(pattern, description.lower())
            if match:
                try:
                    budget["total"] = float(match.group(1))
                except ValueError:
                    continue

        # Look for markup multiplier
        markup_patterns = [
            r"(?:markup|multiplier)\s+(?:of|is|:)\s*(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*x\s*(?:markup|multiplier)",
        ]

        for pattern in markup_patterns:
            match = re.search(pattern, description.lower())
            if match:
                try:
                    budget["markup_multiplier"] = float(match.group(1))
                except ValueError:
                    continue

        # Look for countries
        country_patterns = [
            r"(?:target|market|ship\s+to)\s+(?:countries?|regions?)?\s*[:=]?\s*([A-Z]{2}(?:\s*,\s*[A-Z]{2})*)",
            r"(?:in|for)\s+([A-Z]{2}(?:\s*,\s*[A-Z]{2})*)",
        ]

        for pattern in country_patterns:
            match = re.search(pattern, description)
            if match:
                countries_str = match.group(1)
                countries = [c.strip() for c in countries_str.split(",")]
                if countries:
                    budget["countries"] = countries
                break

        return budget

    def _extract_target_market(self, description: str) -> Dict[str, Any]:
        """Extract target market information from the description."""
        market = {}

        # Look for currency
        currency_patterns = [
            r"(?:currency|money)\s+(?:is|:)\s*(USD|EUR|GBP|CAD|AUD)",
        ]

        for pattern in currency_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                market["currency"] = match.group(1)
                break

        # Look for language
        language_patterns = [
            r"(?:language|lang)\s+(?:is|:)\s*(en|es|fr|de|ja|zh)",
        ]

        for pattern in language_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                market["language"] = match.group(1)
                break

        return market
