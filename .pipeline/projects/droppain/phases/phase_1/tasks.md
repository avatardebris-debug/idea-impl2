# Phase 1 Tasks

- [x] Task 1: Project scaffold and configuration
  - What: Create the Python package structure for droppain with a config module that handles project settings, API keys, and environment variables
  - Files: droppain/__init__.py, droppain/config.py, droppain/exceptions.py, pyproject.toml
  - Done when: Package is importable (`import droppain` works), config module loads defaults and reads env vars for API keys (SHOPIFY_API_KEY, etc.)

- [x] Task 2: Product model and Shopify sync adapter
  - What: Define a Product data model and a Shopify adapter class that can fetch products from a Shopify store via the Shopify Admin API (REST or GraphQL)
  - Files: droppain/models.py, droppain/adapters/shopify.py
  - Done when: Product model has fields (id, title, price, image_url, description, tags). Shopify adapter has a method `fetch_products()` that returns a list of Product objects. Adapter uses real Shopify API calls (with mock/test mode for API key).

- [x] Task 3: Campaign planner core
  - What: Build the CampaignPlanner class that takes a list of products and generates a structured marketing campaign plan including channels, schedules, and content briefs
  - Files: droppain/planner.py
  - Done when: CampaignPlanner class has a `plan(products)` method that returns a CampaignPlan object with fields: campaign name, channels (list of channel configs with platform, frequency, budget), content_briefs (list of briefs with title, copy, target_audience, platform), and schedule. Output is deterministic given the same input.

- [x] Task 4: Content generator module
  - What: Implement a ContentGenerator that produces marketing copy (social media posts, email drafts, ad copy) based on campaign briefs
  - Files: droppain/content_generator.py
  - Done when: ContentGenerator class has a `generate(brief)` method that returns formatted marketing copy strings for the specified platform. Supports at least: Facebook/Instagram post, email subject + body, and Google/Facebook ad copy. Output is importable and testable.

- [x] Task 5: Campaign execution engine
  - What: Build the CampaignEngine that orchestrates the full flow: load products → plan campaign → generate content → publish to channels (with real Shopify integration and mock channel publishers)
  - Files: droppain/engine.py
  - Done when: CampaignEngine class has a `run(products, plan)` method that executes the full pipeline end-to-end. Returns a CampaignResult with status, published_items (list of published content records), and errors. Works with a mock publisher for testing. Core flow is importable and callable.