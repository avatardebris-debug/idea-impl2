"""DSL and workflow templates for standard dropshipping operations."""

from __future__ import annotations

from agentflow_drophip.models.business_spec import BusinessSpec
from agentflow_drophip.workflow.dag import DAG, Node
from agentflow_drophip.workflow.task import Task, TaskStatus


def standard_dropshipping_workflow(spec: BusinessSpec) -> DAG:
    """Generate a standard dropshipping workflow DAG from a BusinessSpec.

    Creates a comprehensive workflow with the following stages:
    1. Product Sourcing (find products from supplier)
    2. Product Selection (filter and rank products)
    3. Listing Creation (create storefront listings)
    4. Pricing Configuration (set prices based on markup)
    5. Fulfillment Setup (configure auto-fulfillment)
    6. Inventory Sync (set up inventory synchronization)
    7. Order Processing (configure order handling)
    8. Customer Service (set up CS workflows)
    9. Analytics Setup (configure tracking)
    10. Launch (go live)

    Args:
        spec: The business specification.

    Returns:
        A DAG representing the workflow.
    """
    dag = DAG()

    # Define tasks
    tasks = [
        Task(
            id="sourcing",
            name="Product Sourcing",
            agent_type="sourcing",
            data={
                "supplier": spec.supplier.value,
                "niche": spec.niche,
                "max_product_cost": spec.max_product_cost,
            },
        ),
        Task(
            id="selection",
            name="Product Selection",
            agent_type="selection",
            data={
                "min_profit_margin": spec.min_profit_margin,
                "target_market": spec.target_market,
            },
        ),
        Task(
            id="listing",
            name="Listing Creation",
            agent_type="listing",
            data={
                "storefront": spec.storefront.value,
                "branding": spec.branding,
            },
        ),
        Task(
            id="pricing",
            name="Pricing Configuration",
            agent_type="pricing",
            data={
                "pricing": spec.pricing,
                "target_market": spec.target_market,
            },
        ),
        Task(
            id="fulfillment",
            name="Fulfillment Setup",
            agent_type="fulfillment",
            data={
                "fulfillment": spec.fulfillment,
                "supplier": spec.supplier,
            },
        ),
        Task(
            id="inventory",
            name="Inventory Sync",
            agent_type="inventory",
            data={
                "auto_reorder_threshold": spec.auto_reorder_threshold,
            },
        ),
        Task(
            id="orders",
            name="Order Processing",
            agent_type="orders",
            data={
                "fulfillment": spec.fulfillment,
            },
        ),
        Task(
            id="customer_service",
            name="Customer Service Setup",
            agent_type="customer_service",
            data={
                "target_market": spec.target_market,
            },
        ),
        Task(
            id="analytics",
            name="Analytics Setup",
            agent_type="analytics",
            data={
                "target_market": spec.target_market,
            },
        ),
        Task(
            id="launch",
            name="Launch",
            agent_type="launch",
            data={
                "storefront": spec.storefront,
                "branding": spec.branding,
            },
        ),
    ]

    # Add nodes to DAG
    for task in tasks:
        dag.add_node(Node(id=task.id, label=task.name, dependencies=task.dependencies))

    # Add edges (dependencies)
    # Sourcing -> Selection
    dag.add_edge("sourcing", "selection")

    # Selection -> Listing, Pricing
    dag.add_edge("selection", "listing")
    dag.add_edge("selection", "pricing")

    # Listing -> Launch
    dag.add_edge("listing", "launch")

    # Pricing -> Launch
    dag.add_edge("pricing", "launch")

    # Fulfillment -> Orders
    dag.add_edge("fulfillment", "orders")

    # Inventory -> Orders
    dag.add_edge("inventory", "orders")

    # Orders -> Launch
    dag.add_edge("orders", "launch")

    # Customer Service -> Launch
    dag.add_edge("customer_service", "launch")

    # Analytics -> Launch
    dag.add_edge("analytics", "launch")

    # Fulfillment and Inventory can run in parallel with Listing/Pricing
    # They depend on sourcing
    dag.add_edge("sourcing", "fulfillment")
    dag.add_edge("sourcing", "inventory")

    # Customer Service and Analytics can run after sourcing
    dag.add_edge("sourcing", "customer_service")
    dag.add_edge("sourcing", "analytics")

    return dag


def get_workflow_template(workflow_type: str = "standard") -> DAG:
    """Get a pre-defined workflow template.

    Args:
        workflow_type: Type of workflow template.

    Returns:
        A DAG representing the workflow template.
    """
    if workflow_type == "standard":
        # Create a dummy spec for template generation
        from agentflow_drophip.models.business_spec import (
            BusinessSpec,
            FulfillmentType,
            PricingConfig,
            SupplierType,
            StorefrontType,
            TargetMarket,
        )
        dummy_spec = BusinessSpec(
            niche="general",
            supplier=SupplierType.ALIEXPRESS,
            storefront=StorefrontType.SHOPIFY,
            target_market=TargetMarket(countries=["US"], currency="USD", language="en"),
            pricing=PricingConfig(markup_multiplier=2.0, pricing_strategy="markup"),
            fulfillment=FulfillmentType.AUTO,
            branding=None,
            description="Template",
        )
        return standard_dropshipping_workflow(dummy_spec)
    else:
        raise ValueError(f"Unknown workflow template: {workflow_type}")
