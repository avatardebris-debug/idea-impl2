"""Settings module for DropGentic.

Application settings with direct attributes and validation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class Settings:
    """Application settings with direct attributes.

    Attributes:
        app_name: Application name.
        version: Application version.
        log_level: Logging level.
        debug: Debug mode flag.
        data_dir: Data directory path.
        cache_dir: Cache directory path.
        supplier_api_keys: Dictionary of supplier API keys.
        default_currency: Default currency code.
        default_platform_fee_pct: Default platform fee percentage.
        default_payment_processing_fee_pct: Default payment processing fee percentage.
        default_fixed_payment_fee: Default fixed payment fee.
        min_net_margin_pct: Minimum net margin percentage.
        max_lead_time_days: Maximum lead time in days.
        min_supplier_rating: Minimum supplier rating.
        min_gross_margin_pct: Minimum gross margin percentage.
        max_products_per_plan: Maximum products per plan.
        max_suppliers_per_plan: Maximum suppliers per plan.
        enable_cache: Enable caching.
        cache_ttl_seconds: Cache time-to-live in seconds.
    """
    app_name: str = "DropGentic"
    version: str = "0.1.0"
    log_level: str = "INFO"
    debug: bool = False
    data_dir: str = "./data"
    cache_dir: str = "./cache"
    supplier_api_keys: Dict[str, str] = None  # type: ignore
    default_currency: str = "USD"
    default_platform_fee_pct: float = 0.15
    default_payment_processing_fee_pct: float = 0.029
    default_fixed_payment_fee: float = 0.30
    min_net_margin_pct: float = 5.0
    max_lead_time_days: int = 30
    min_supplier_rating: float = 0.0
    min_gross_margin_pct: float = 20.0
    max_products_per_plan: int = 100
    max_suppliers_per_plan: int = 50
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if self.supplier_api_keys is None:
            self.supplier_api_keys = {}
        if self.min_net_margin_pct < 0:
            raise ValueError("min_net_margin_pct must be non-negative")
        if self.max_lead_time_days < 0:
            raise ValueError("max_lead_time_days must be positive")
        if self.min_supplier_rating < 0:
            raise ValueError("min_supplier_rating must be non-negative")
        if self.min_gross_margin_pct < 0:
            raise ValueError("min_gross_margin_pct must be non-negative")
        if self.max_products_per_plan < 0:
            raise ValueError("max_products_per_plan must be positive")
        if self.max_suppliers_per_plan < 0:
            raise ValueError("max_suppliers_per_plan must be positive")
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Settings:
        """Create from dictionary."""
        return cls(**data)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Settings(app_name={self.app_name}, version={self.version})"
