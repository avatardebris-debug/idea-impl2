"""Orchestrator — coordinates all agents and workflows for dropshipping operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agentflow_drophip.agents.fulfillment_agent import FulfillmentAgent
from agentflow_drophip.agents.listing_agent import ListingAgent
from agentflow_drophip.agents.sourcing_agent import SourcingAgent
from agentflow_drophip.config import get_config
from agentflow_drophip.exceptions import OrchestratorError
from agentflow_drophip.intent_parser.parser import IntentParser
from agentflow_drophip.models.business_spec import BusinessSpec
from agentflow_drophip.workflow.dsl import standard_dropshipping_workflow
from agentflow_drophip.workflow.engine import WorkflowEngine


class Orchestrator:
    """Main orchestrator that coordinates all agents and workflows."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the orchestrator.

        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        self.intent_parser = IntentParser()
        self.sourcing_agent = SourcingAgent()
        self.listing_agent = ListingAgent()
        self.fulfillment_agent = FulfillmentAgent()
        self._business_spec: Optional[BusinessSpec] = None
        self._workflow_engine: Optional[WorkflowEngine] = None
        self.execution_log: List[Dict[str, Any]] = []

    def setup_business(self, description: str) -> BusinessSpec:
        """Set up the business by parsing the description.

        Args:
            description: Natural-language description of the business.

        Returns:
            Parsed BusinessSpec.
        """
        try:
            self._business_spec = self.intent_parser.parse(description)
            self._log_action("business_setup", {
                "description": description,
                "spec": self._business_spec.to_dict(),
            })
            return self._business_spec
        except Exception as e:
            raise OrchestratorError(
                f"Failed to setup business: {e}",
                action="business_setup",
            ) from e

    def run_full_workflow(self) -> Dict[str, Any]:
        """Run the full dropshipping workflow.

        Returns:
            Dictionary with workflow results.
        """
        if not self._business_spec:
            raise OrchestratorError(
                "Business not set up. Call setup_business() first.",
                action="full_workflow",
            )

        try:
            # Generate workflow DAG
            dag = standard_dropshipping_workflow(self._business_spec)
            self._workflow_engine = WorkflowEngine(dag)

            # Define task handlers
            task_handlers = {
                "sourcing": self._handle_sourcing,
                "selection": self._handle_selection,
                "listing": self._handle_listing,
                "pricing": self._handle_pricing,
                "fulfillment": self._handle_fulfillment,
                "inventory": self._handle_inventory,
                "orders": self._handle_orders,
                "customer_service": self._handle_customer_service,
                "analytics": self._handle_analytics,
                "launch": self._handle_launch,
            }

            # Execute workflow
            result = self._workflow_engine.execute(task_handlers)

            self._log_action("workflow_execution", {
                "workflow_id": self._workflow_engine.workflow_id,
                "status": result.status,
                "duration_seconds": result.duration_seconds,
                "errors": result.errors,
            })

            return {
                "workflow_id": self._workflow_engine.workflow_id,
                "status": result.status,
                "tasks": {tid: t.to_dict() for tid, t in self._workflow_engine.tasks.items()},
                "errors": result.errors,
                "duration_seconds": result.duration_seconds,
            }

        except Exception as e:
            raise OrchestratorError(
                f"Workflow execution failed: {e}",
                action="full_workflow",
            ) from e

    def _handle_sourcing(self, task) -> Any:
        """Handle sourcing task."""
        result = self.sourcing_agent.execute(
            spec=self._business_spec,
            niche=self._business_spec.niche,
            max_price=self._business_spec.max_product_cost,
        )
        task.data["products"] = result.products
        return result

    def _handle_selection(self, task) -> Any:
        """Handle product selection task."""
        products = task.data.get("products", [])
        # Simple selection: filter by rating and stock
        selected = [
            p for p in products
            if p.get("rating", 0) >= 4.0 and p.get("stock", 0) > 0
        ][:10]  # Top 10 products
        task.data["selected_products"] = selected
        return type('obj', (object,), {
            'success': True,
            'data': {'selected_count': len(selected)},
            'products': selected,
        })

    def _handle_listing(self, task) -> Any:
        """Handle listing creation task."""
        products = task.data.get("selected_products", [])
        result = self.listing_agent.execute(
            spec=self._business_spec,
            products=products,
            branding=self._business_spec.branding,
        )
        task.data["listings"] = result.products
        return result

    def _handle_pricing(self, task) -> Any:
        """Handle pricing configuration task."""
        products = task.data.get("selected_products", [])
        pricing = self._business_spec.pricing

        # Apply pricing strategy
        for product in products:
            base_price = product.get("price", 0)
            if pricing.pricing_strategy == "markup":
                product["listing_price"] = base_price * pricing.markup_multiplier
            elif pricing.pricing_strategy == "competitive":
                product["listing_price"] = base_price * 1.5  # Simplified competitive pricing
            else:
                product["listing_price"] = base_price * 2.0

        task.data["priced_products"] = products
        return type('obj', (object,), {
            'success': True,
            'data': {'pricing_strategy': pricing.pricing_strategy},
            'products': products,
        })

    def _handle_fulfillment(self, task) -> Any:
        """Handle fulfillment setup task."""
        return type('obj', (object,), {
            'success': True,
            'data': {'fulfillment_type': self._business_spec.fulfillment.value},
            'products': [],
        })

    def _handle_inventory(self, task) -> Any:
        """Handle inventory sync task."""
        return type('obj', (object,), {
            'success': True,
            'data': {'auto_reorder_threshold': self._business_spec.auto_reorder_threshold},
            'products': [],
        })

    def _handle_orders(self, task) -> Any:
        """Handle order processing task."""
        return type('obj', (object,), {
            'success': True,
            'data': {'order_processing': 'configured'},
            'products': [],
        })

    def _handle_customer_service(self, task) -> Any:
        """Handle customer service setup task."""
        return type('obj', (object,), {
            'success': True,
            'data': {'cs_configured': True},
            'products': [],
        })

    def _handle_analytics(self, task) -> Any:
        """Handle analytics setup task."""
        return type('obj', (object,), {
            'success': True,
            'data': {'analytics_configured': True},
            'products': [],
        })

    def _handle_launch(self, task) -> Any:
        """Handle launch task."""
        return type('obj', (object,), {
            'success': True,
            'data': {'launch_status': 'ready'},
            'products': [],
        })

    def _log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log an action for audit trail."""
        self.execution_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "details": details,
        })

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the orchestrator."""
        return {
            "business_spec": self._business_spec.to_dict() if self._business_spec else None,
            "agents": {
                "sourcing": self.sourcing_agent.get_status(),
                "listing": self.listing_agent.get_status(),
                "fulfillment": self.fulfillment_agent.get_status(),
            },
            "execution_log_count": len(self.execution_log),
        }
