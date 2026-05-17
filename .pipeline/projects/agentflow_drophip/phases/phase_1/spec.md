## Phase 1 — MVP: Intent Parser + Core Workflow Engine

### Description

Build the foundational system that accepts a natural-language description of a dropshipping operation and produces an executable workflow. This includes:

- **Intent Parser**: A module that takes free-text business descriptions and outputs a structured `BusinessSpec` (supplier, niche, pricing, fulfillment, target market).
- **Workflow Engine**: A DAG-based orchestrator that translates `BusinessSpec` into a sequence of executable tasks.
- **Minimal Agent Pool**: Three starter agents — `SourcingAgent` (finds products), `ListingAgent` (creates product listings), and `FulfillmentAgent` (routes orders to suppliers).
- **Basic Integration**: One supplier adapter (AliExpress/AZAPI or Spocket) and one storefront adapter (Shopify or WooCommerce).
- **CLI Dashboard**: A terminal-based dashboard to monitor active workflows, view logs, and inspect agent decisions.

### Deliverable

A working CLI tool that:
1. Accepts a natural-language prompt describing a dropshipping operation.
2. Parses it into a structured business spec.
3. Generates and executes a DAG workflow to:
   - Source 10 products from a connected supplier.
   - Create listings on a connected storefront.
   - Set up auto-fulfillment rules.
4. Displays real-time status and logs via CLI dashboard.

### Dependencies

- Phase 0 (none — this is the starting point).
- External: LLM API key, supplier API credentials, storefront API credentials.

### Success Criteria

- [ ] Natural language input is parsed into a valid `BusinessSpec` with ≥90% field accuracy on test prompts.
- [ ] Workflow DAG is generated and executed without manual intervention for a standard dropshipping setup.
- [ ] 10 products are sourced and listed end-to-end in under 30 minutes.
- [ ] CLI dashboard shows real-time workflow status, agent decisions, and error logs.
- [ ] System handles one supplier and one storefront integration reliably.

---