"""Margin calculation models and calculator."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MarginResult:
    """Result of a margin calculation."""

    cost_price: float
    shipping_cost: float
    total_cost: float
    retail_price: float
    gross_profit: float
    gross_margin_pct: float
    net_margin_pct: float
    recommended_action: str
    platform_fee: float = 0.0
    payment_fee: float = 0.0
    total_fees: float = 0.0
    net_profit: float = 0.0
    currency: str = "USD"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "cost_price": self.cost_price,
            "shipping_cost": self.shipping_cost,
            "total_cost": self.total_cost,
            "retail_price": self.retail_price,
            "gross_profit": self.gross_profit,
            "gross_margin_pct": self.gross_margin_pct,
            "net_margin_pct": self.net_margin_pct,
            "recommended_action": self.recommended_action,
            "platform_fee": self.platform_fee,
            "payment_fee": self.payment_fee,
            "total_fees": self.total_fees,
            "net_profit": self.net_profit,
            "currency": self.currency,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarginResult":
        """Create from dictionary."""
        return cls(**data)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"MarginResult(cost_price={self.cost_price}, "
            f"retail_price={self.retail_price}, "
            f"gross_margin_pct={self.gross_margin_pct}, "
            f"net_margin_pct={self.net_margin_pct})"
        )


class MarginCalculator:
    """Calculate profit margins for products."""

    def __init__(
        self,
        platform_fee_pct: float = 0.15,
        payment_processing_fee_pct: float = 0.029,
        fixed_payment_fee: float = 0.30,
        currency: str = "USD",
    ) -> None:
        """Initialize margin calculator.

        Args:
            platform_fee_pct: Platform commission percentage (0-1).
            payment_processing_fee_pct: Payment processing percentage (0-1).
            fixed_payment_fee: Fixed payment processing fee.
            currency: Currency code (e.g., USD, EUR).
        """
        self.platform_fee_pct = platform_fee_pct
        self.payment_processing_fee_pct = payment_processing_fee_pct
        self.fixed_payment_fee = fixed_payment_fee
        self.currency = currency

    def calculate_shipping(
        self,
        weight_kg: float,
        supplier_shipping_cost_per_unit: float = 0.0,
        supplier_shipping_weight_factor: float = 0.0,
    ) -> float:
        """Calculate shipping cost.

        Args:
            weight_kg: Product weight in kilograms.
            supplier_shipping_cost_per_unit: Base shipping cost per unit.
            supplier_shipping_weight_factor: Additional cost per kg.

        Returns:
            Total shipping cost.
        """
        if weight_kg < 0:
            raise ValueError("weight_kg must be non-negative")
        if supplier_shipping_cost_per_unit < 0:
            raise ValueError("supplier_shipping_cost_per_unit must be non-negative")
        if supplier_shipping_weight_factor < 0:
            raise ValueError("supplier_shipping_weight_factor must be non-negative")

        base_cost = supplier_shipping_cost_per_unit
        weight_cost = supplier_shipping_weight_factor * weight_kg
        return base_cost + weight_cost

    def calculate_platform_fee(self, retail_price: float) -> float:
        """Calculate platform commission fee.

        Args:
            retail_price: Retail price of the product.

        Returns:
            Platform fee amount.
        """
        if retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        return retail_price * self.platform_fee_pct

    def calculate_payment_fee(self, retail_price: float) -> float:
        """Calculate payment processing fee.

        Args:
            retail_price: Retail price of the product.

        Returns:
            Payment processing fee amount.
        """
        if retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        return retail_price * self.payment_processing_fee_pct + self.fixed_payment_fee

    def _recommend_action(self, gross_margin_pct: float, net_margin_pct: float) -> str:
        """Recommend action based on margins.

        Args:
            gross_margin_pct: Gross margin percentage.
            net_margin_pct: Net margin percentage.

        Returns:
            Recommended action: "Reject", "Review", or "List".
        """
        if gross_margin_pct < 0.15 or net_margin_pct < 0.10:
            return "Reject"
        elif gross_margin_pct < 0.25 or net_margin_pct < 0.15:
            return "Review"
        else:
            return "List"

    def calculate(
        self,
        cost_price: float,
        shipping_cost: float,
        retail_price: float,
    ) -> MarginResult:
        """Calculate margins for a product.

        Args:
            cost_price: Product cost price.
            shipping_cost: Shipping cost per unit.
            retail_price: Retail selling price.

        Returns:
            MarginResult with calculated margins.
        """
        if cost_price < 0:
            raise ValueError("cost_price must be non-negative")
        if shipping_cost < 0:
            raise ValueError("shipping_cost must be non-negative")
        if retail_price < 0:
            raise ValueError("retail_price must be non-negative")
        if retail_price < cost_price:
            raise ValueError("retail_price must be >= cost_price")

        total_cost = cost_price + shipping_cost
        gross_profit = retail_price - total_cost

        if retail_price > 0:
            gross_margin_pct = gross_profit / retail_price
        else:
            gross_margin_pct = 0.0

        platform_fee = self.calculate_platform_fee(retail_price)
        payment_fee = self.calculate_payment_fee(retail_price)
        total_fees = platform_fee + payment_fee

        net_profit = retail_price - total_cost - total_fees

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
