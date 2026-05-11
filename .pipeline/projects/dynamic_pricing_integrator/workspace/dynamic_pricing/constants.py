"""Default constants for the dynamic pricing module."""

DEFAULT_POLLING_INTERVAL = 900  # seconds
DEFAULT_CURRENCY = "USD"
DEFAULT_MARGIN_FLOOR = 0.15  # 15%

# Pricing strategy constants
PRICING_STRATEGY_PRICE_GAP = "PriceGap"
PRICING_STRATEGY_INVENTORY_AGE = "InventoryAge"
PRICING_STRATEGY_MARGIN_FLOOR = "MarginFloor"
PRICING_STRATEGY_COMPETITOR_MATCH = "CompetitorMatch"

# Default thresholds
DEFAULT_GAP_THRESHOLD = 0.05  # 5% price gap triggers discount
DEFAULT_INVENTORY_DAYS_THRESHOLD = 30  # days in inventory
DEFAULT_MARGIN_FLOOR_THRESHOLD = 0.10  # 10% margin floor
DEFAULT_DISCOUNT_PERCENT = 0.10  # 10% default discount
DEFAULT_CEILING_MULTIPLIER = 1.5  # ceiling is 1.5x base price
