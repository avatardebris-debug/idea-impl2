"""FulfillmentAgent — handles order fulfillment and shipping."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agentflow_drophip.agents.base import AgentResult, BaseAgent
from agentflow_drophip.models.business_spec import BusinessSpec, FulfillmentType, SupplierType


class FulfillmentAgent(BaseAgent):
    """Agent that handles order fulfillment and shipping."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        fulfillment_type: Optional[FulfillmentType] = None,
        supplier_type: Optional[SupplierType] = None,
    ):
        """Initialize the fulfillment agent.

        Args:
            config: Configuration dictionary.
            fulfillment_type: Type of fulfillment (auto/manual/hybrid).
            supplier_type: Type of supplier.
        """
        super().__init__(name="fulfillment_agent", config=config)
        self.fulfillment_type = fulfillment_type or FulfillmentType.AUTO
        self.supplier_type = supplier_type or SupplierType.ALIEXPRESS

    def execute(
        self,
        spec: Optional[BusinessSpec] = None,
        orders: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Execute fulfillment for orders.

        Args:
            spec: Business specification.
            orders: List of orders to fulfill.
            **kwargs: Additional parameters.

        Returns:
            AgentResult with fulfillment status.
        """
        self.execution_count += 1

        if not orders:
            return AgentResult(
                success=False,
                error="No orders provided for fulfillment",
                metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
            )

        # Process each order
        fulfillment_results = []
        for order in orders:
            fulfillment = self._fulfill_order(order)
            fulfillment_results.append(fulfillment)

        result = AgentResult(
            success=True,
            data={
                "fulfillment_type": self.fulfillment_type.value,
                "supplier_type": self.supplier_type.value,
                "orders_processed": len(fulfillment_results),
                "successful": sum(1 for f in fulfillment_results if f["success"]),
                "failed": sum(1 for f in fulfillment_results if not f["success"]),
            },
            products=fulfillment_results,
            metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        self.last_result = result
        return result

    def _fulfill_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Fulfill a single order.

        Args:
            order: Order details.

        Returns:
            Dictionary with fulfillment status.
        """
        order_id = order.get("id", "unknown")

        if self.fulfillment_type == FulfillmentType.AUTO:
            # Auto-fulfillment: automatically place order with supplier
            estimated_delivery = (datetime.now(timezone.utc) + __import__('datetime').timedelta(days=7)).isoformat()
            return {
                "order_id": order_id,
                "success": True,
                "status": "fulfilled",
                "supplier_order_id": f"sup_{order_id}",
                "tracking_number": f"TRK{order_id}",
                "estimated_delivery": estimated_delivery,
                "fulfillment_method": "auto",
            }
        elif self.fulfillment_type == FulfillmentType.MANUAL:
            # Manual fulfillment: require human approval
            return {
                "order_id": order_id,
                "success": False,
                "status": "pending_approval",
                "fulfillment_method": "manual",
                "message": "Manual fulfillment requires human approval",
            }
        else:
            # Hybrid: auto-fulfill with monitoring
            estimated_delivery = (datetime.now(timezone.utc) + __import__('datetime').timedelta(days=7)).isoformat()
            return {
                "order_id": order_id,
                "success": True,
                "status": "fulfilled",
                "supplier_order_id": f"sup_{order_id}",
                "tracking_number": f"TRK{order_id}",
                "estimated_delivery": estimated_delivery,
                "fulfillment_method": "hybrid",
                "monitoring": True,
            }

    def track_order(self, order_id: str) -> AgentResult:
        """Track an order's fulfillment status.

        Args:
            order_id: ID of the order to track.

        Returns:
            AgentResult with tracking information.
        """
        self.execution_count += 1

        # Simulate tracking
        tracking_info = {
            "order_id": order_id,
            "status": "in_transit",
            "tracking_number": f"TRK{order_id}",
            "current_location": "Distribution Center",
            "estimated_delivery": (datetime.now(timezone.utc) + __import__('datetime').timedelta(days=3)).isoformat(),
            "history": [
                {
                    "status": "order_placed",
                    "timestamp": (datetime.now(timezone.utc) - __import__('datetime').timedelta(days=5)).isoformat(),
                    "location": "Supplier Warehouse",
                },
                {
                    "status": "shipped",
                    "timestamp": (datetime.now(timezone.utc) - __import__('datetime').timedelta(days=4)).isoformat(),
                    "location": "Origin Country",
                },
                {
                    "status": "in_transit",
                    "timestamp": (datetime.now(timezone.utc) - __import__('datetime').timedelta(days=2)).isoformat(),
                    "location": "International Transit",
                },
            ],
        }

        result = AgentResult(
            success=True,
            data={"order_id": order_id},
            products=[tracking_info],
            metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
        )

        self.last_result = result
        return result
