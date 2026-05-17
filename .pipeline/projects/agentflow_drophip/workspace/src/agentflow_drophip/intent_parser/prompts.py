"""LLM prompt templates for intent extraction."""

from __future__ import annotations

EXTRACTION_SYSTEM_PROMPT: str = (
    "You are a business specification extractor for a dropshipping platform. "
    "Given a user's natural-language description of their dropshipping business, "
    "extract the relevant fields and return a JSON object with the following keys: "
    "niche, supplier, storefront, target_market (with countries, currency, language), "
    "pricing (with markup_multiplier, pricing_strategy), fulfillment, branding (with brand_name), "
    "description, max_product_cost, min_profit_margin, auto_reorder_threshold. "
    "Use the following enum values for supplier: aliexpress, spocket, cj_dropshipping, dropshipmobile, custom. "
    "Use the following enum values for storefront: shopify, woocommerce, ecommerce_platform, custom. "
    "Use the following enum values for fulfillment: auto, manual, hybrid. "
    "If a field is not mentioned, use sensible defaults."
)

EXTRACTION_USER_TEMPLATE: str = (
    "Extract the business specification from the following user input:\n\n"
    "{user_input}"
)

COMBINED_EXTRACTION_PROMPT: str = (
    EXTRACTION_SYSTEM_PROMPT + "\n\n" + EXTRACTION_USER_TEMPLATE
)

RULE_BASED_PROMPT: str = (
    "Rule-based fallback parser. When LLM is unavailable, use regex/heuristic "
    "patterns to extract business specification fields from user input."
)
