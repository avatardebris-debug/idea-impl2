"""Models package."""

from backend.models.product import Niche, Product, Catalog, CatalogProduct, ShopifyStore, SyncJob
from backend.models.supplier import SupplierConnection, SupplierProduct
from backend.models.sync_log import SyncLog
from backend.models.margin_rule import MarginRule
from backend.models.alert import Alert
from backend.models.store import Store, StoreTemplate, TemplateSection, TemplateStyle
from backend.models.order import Order, OrderItem, OrderFulfillment
from backend.models.analytics import DailyMetrics, ProductPerformance, AnalyticsSnapshot
from backend.models.user import User, Team, TeamMember, Role

__all__ = [
    "Niche", "Product", "Catalog", "CatalogProduct", "ShopifyStore", "SyncJob",
    "SupplierConnection", "SupplierProduct",
    "SyncLog",
    "MarginRule",
    "Alert",
    "Store", "StoreTemplate", "TemplateSection", "TemplateStyle",
    "Order", "OrderItem", "OrderFulfillment",
    "DailyMetrics", "ProductPerformance", "AnalyticsSnapshot",
    "User", "Team", "TeamMember", "Role",
]
