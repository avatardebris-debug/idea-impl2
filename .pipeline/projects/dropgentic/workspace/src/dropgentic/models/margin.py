"""Margin calculation models and calculator for DropGentic."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class MarginResult:
    """Result of a margin calculation.

    Attributes:
        product_id: Product identifier (set during evaluation).
        supplier_id: Supplier identifier (set during evaluation).
        cost_price: Cost price from the supplier.
        shipping_cost: Shipping cost per unit.
        total_cost: Total cost (cost_price + shipping_cost).
        retail_price: Suggested retail price.
        gross_profit: Profit before fees (retail_price - total_cost).
        gross_margin_pct: Gross margin as decimal (0-1).
        net_margin_pct: Net margin after fees as decimal (0-1).
        recommended_action: One of 'List', 'Review', 'Reject'.
        platform_fee: Platform fee amount.
        payment_fee: Payment processing fee amount.
        total_fees: Total fees (platform_fee + payment_fee).
        net_profit: Net profit after all fees.
        currency: Currency code.
    """
    product_id: str = ""
    supplier_id: str = ""
    cost_price: float = 0.0
    shipping_cost: float = 0.0
    total_cost: float = 0.0
    retail_price: float = 0.0
    gross_profit: float = 0.0
    gross_margin_pct: float = 0.0
    net_margin_pct: float = 0.0
    recommended_action: str = ""
    platform_fee: float = 0.0
    payment_fee: float = 0.0
    total_fees: float = 0.0
    net_profit: float = 0.0
    currency: str = "USD"

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MarginResult:
        """Create from dictionary.

        Args:
            data: Dictionary with margin result fields.

        Returns:
            MarginResult instance.
        """
        return cls(**data)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MarginResult(cost_price={self.cost_price}, retail_price={self.retail_price}, "
            f"gross_margin={self.gross_margin_pct:.2%}, net_margin={self.net_margin_pct:.2%}, "
            f"action={self.recommended_action})"
        )


class MarginCalculator:
    """Calculate margins for dropshipping products.

    Attributes:
        platform_fee_pct: Platform fee percentage (default 0.15).
        payment_processing_fee_pct: Payment processing fee percentage (default 0.03).
        fixed_payment_fee: Fixed payment processing fee (default 0.30).
        currency: Currency code (default 'USD').
    """

    def __init__(
        self,
        platform_fee_pct: float = 0.15,
        payment_processing_fee_pct: float = 0.029,
        fixed_payment_fee: float = 0.30,
        currency: str = "USD",
    ) -> None:
        """Initialize MarginCalculator.

        Args:
            platform_fee_pct: Platform fee percentage.
            payment_processing_fee_pct: Payment processing fee percentage.
            fixed_payment_fee: Fixed payment processing fee.
            currency: Currency code.
        """
        self.platform_fee_pct = platform_fee_pct
        self.payment_processing_fee_pct = payment_processing_fee_pct
        self.fixed_payment_fee = fixed_payment_fee
        self.currency = currency

    def calculate(
        self,
        cost_price: float,
        shipping_cost: float,
        retail_price: float,
        platform_fee_pct: Optional[float] = None,
        payment_processing_fee_pct: Optional[float] = None,
        fixed_payment_fee: Optional[float] = None,
    ) -> MarginResult:
        """Calculate margins for a product.

        Args:
            cost_price: Cost price from the supplier.
            shipping_cost: Shipping cost per unit.
            retail_price: Suggested retail price.
            platform_fee_pct: Override platform fee percentage.
            payment_processing_fee_pct: Override payment processing fee percentage.
            fixed_payment_fee: Override fixed payment processing fee.

        Returns:
            MarginResult with calculated values.
        """
        if cost_price < 0:
            raise ValueError("cost_price must be non-negative")
        if shipping_cost < 0:
            raise ValueError("shipping_cost must be non-negative")
        if retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        if retail_price < cost_price:
            raise ValueError("retail_price must be >= cost_price")

        pf_pct = platform_fee_pct if platform_fee_pct is not None else self.platform_fee_pct
        ppf_pct = payment_processing_fee_pct if payment_processing_fee_pct is not None else self.payment_processing_fee_pct
        fp_fee = fixed_payment_fee if fixed_payment_fee is not None else self.fixed_payment_fee

        total_cost = cost_price + shipping_cost
        gross_profit = retail_price - total_cost

        if retail_price > 0:
            gross_margin_pct = gross_profit / retail_price
        else:
            gross_margin_pct = 0.0

        platform_fee = retail_price * pf_pct if retail_price > 0 else 0.0
        payment_fee = retail_price * ppf_pct + fp_fee if retail_price > 0 else fp_fee
        total_fees = platform_fee + payment_fee
        net_profit = gross_profit - total_fees

        if retail_price > 0:
            net_margin_pct = net_profit / retail_price
        else:
            net_margin_pct = 0.0

        recommended_action = self._recommend_action(gross_margin_pct, net_margin_pct)

        return MarginResult(
            cost_price=cost_price,
            shipping_cost=shipping_cost,
            total_cost=total_cost,
            retail_price=retail_price,
            gross_profit=gross_profit,
            gross_margin_pct=gross_margin_pct,
            net_margin_pct=net_margin_pct,
            recommended_action=recommended_action,
            platform_fee=platform_fee,
            payment_fee=payment_fee,
            total_fees=total_fees,
            net_profit=net_profit,
            currency=self.currency,
        )

    def _recommend_action(self, gross_margin_pct: float, net_margin_pct: float) -> str:
        """Recommend action based on margins.

        Args:
            gross_margin_pct: Gross margin as decimal (0-1).
            net_margin_pct: Net margin as decimal (0-1).

        Returns:
            Recommended action: 'List', 'Review', or 'Reject'.
        """
        if net_margin_pct < 0.10:
            return "Reject"
        if gross_margin_pct < 0.15:
            return "Reject"
        if gross_margin_pct < 0.20:
            return "Review"
        if net_margin_pct < 0.15:
            return "Review"
        return "List"

    def calculate_shipping(
        self,
        weight_kg: float,
        supplier_shipping_cost_per_unit: float = 5.0,
        supplier_shipping_weight_factor: float = 0.0,
    ) -> float:
        """Calculate shipping cost.

        Args:
            weight_kg: Weight in kilograms.
            supplier_shipping_cost_per_unit: Base shipping cost.
            supplier_shipping_weight_factor: Weight factor for shipping.

        Returns:
            Calculated shipping cost.
        """
        if weight_kg < 0:
            raise ValueError("weight_kg must be non-negative")
        if supplier_shipping_cost_per_unit < 0:
            raise ValueError("supplier_shipping_cost_per_unit must be non-negative")
        if supplier_shipping_weight_factor < 0:
            raise ValueError("supplier_shipping_weight_factor must be non-negative")
        return supplier_shipping_cost_per_unit + weight_kg * supplier_shipping_weight_factor

    def calculate_platform_fee(self, retail_price: float) -> float:
        """Calculate platform fee.

        Args:
            retail_price: Retail price.

        Returns:
            Platform fee amount.
        """
        if retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        return retail_price * self.platform_fee_pct

    def calculate_payment_fee(self, retail_price: float) -> float:
        """Calculate payment processing fee.

        Args:
            retail_price: Retail price.

        Returns:
            Payment processing fee amount.
        """
        if retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        if retail_price <= 0:
            return self.fixed_payment_fee
        return retail_price * self.payment_processing_fee_pct + self.fixed_payment_fee
