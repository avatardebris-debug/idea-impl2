"""Settings module for DropGentic.

Configuration with sensible defaults, validation, and serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional


@dataclass
class Settings:
    """Application settings with validation and serialization.

    Attributes:
        app_name: Application name.
        version: Application version.
        log_level: Logging level.
        debug: Debug mode flag.
        data_dir: Data directory path.
        cache_dir: Cache directory path.
        supplier_api_keys: Supplier API keys mapping.
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
    supplier_api_keys: Dict[str, str] = field(default_factory=dict)
    default_currency: str = "USD"
    default_platform_fee_pct: float = 0.15
    default_payment_processing_fee_pct: float = 0.029
    default_fixed_payment_fee: float = 0.30
    min_net_margin_pct: float = 5.0
    max_lead_time_days: int = 30
    min_supplier_rating: float = 0.0
    min_gross_margin_pct: float = 0.0
    max_products_per_plan: int = 50
    max_suppliers_per_plan: int = 50
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if self.min_net_margin_pct < 0:
            raise ValueError("min_net_margin_pct must be non-negative")
        if self.max_lead_time_days < 0:
            raise ValueError("max_lead_time_days must be non-negative")
        if self.min_supplier_rating < 0 or self.min_supplier_rating > 5:
            raise ValueError("min_supplier_rating must be between 0 and 5")
        if self.min_gross_margin_pct < 0:
            raise ValueError("min_gross_margin_pct must be non-negative")
        if self.max_products_per_plan < 0:
            raise ValueError("max_products_per_plan must be non-negative")
        if self.max_suppliers_per_plan < 0:
            raise ValueError("max_suppliers_per_plan must be non-negative")
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize settings to a dictionary.

        Returns:
            Dictionary representation of settings.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create Settings from a dictionary.

        Args:
            data: Dictionary with settings values.

        Returns:
            Settings instance.
        """
        # Filter out any extra keys not in the dataclass
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Settings(app_name={self.app_name}, version={self.version}, "
            f"log_level={self.log_level}, debug={self.debug})"
        )
