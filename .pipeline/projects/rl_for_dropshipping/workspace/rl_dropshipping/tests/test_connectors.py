"""Tests for platform API connectors and rate limiter."""

import pytest
import time
from rl_dropshipping.src.connectors import PlatformConnector
from rl_dropshipping.src.connectors.rate_limiter import RateLimiter


class TestPlatformConnector:
    """Tests for PlatformConnector."""

    def setup_method(self):
        """Create a fresh connector for each test."""
        self.connector = PlatformConnector(mock=True)

    def teardown_method(self):
        """Clean up after each test."""
        self.connector.close()

    # --- Product operations ---

    def test_get_products_returns_list(self):
        """get_products returns a list of products."""
        products = self.connector.get_products()
        assert isinstance(products, list)
        assert len(products) == 3

    def test_get_products_returns_correct_data(self):
        """get_products returns correct product data."""
        products = self.connector.get_products()
        assert products[0]["id"] == "p1"
        assert products[0]["name"] == "Phone Case"
        assert products[0]["price"] == 12.5
        assert products[0]["stock"] == 100

    def test_update_inventory_existing_product(self):
        """update_inventory updates existing product."""
        result = self.connector.update_inventory("p1", 50)
        assert result is True
        products = self.connector.get_products()
        p1 = [p for p in products if p["id"] == "p1"][0]
        assert p1["stock"] == 50

    def test_update_inventory_nonexistent_product(self):
        """update_inventory returns False for nonexistent product."""
        result = self.connector.update_inventory("p999", 50)
        assert result is False

    # --- Order operations ---

    def test_get_orders_empty(self):
        """get_orders returns empty list initially."""
        orders = self.connector.get_orders()
        assert isinstance(orders, list)
        assert len(orders) == 0

    # --- Ad campaign operations ---

    def test_create_ad_campaign(self):
        """create_ad_campaign creates a campaign and returns ID."""
        campaign_data = {"budget": 100.0, "platform": "facebook"}
        campaign_id = self.connector.create_ad_campaign(campaign_data)
        assert campaign_id.startswith("camp_")
        analytics = self.connector.get_analytics(campaign_id)
        assert analytics["campaign_id"] == campaign_id

    def test_update_budget(self):
        """update_budget updates campaign budget."""
        campaign_data = {"budget": 100.0, "platform": "google"}
        campaign_id = self.connector.create_ad_campaign(campaign_data)
        result = self.connector.update_budget(campaign_id, 200.0)
        assert result is True
        analytics = self.connector.get_analytics(campaign_id)
        assert analytics["budget"] == 200.0

    def test_update_budget_nonexistent_campaign(self):
        """update_budget returns False for nonexistent campaign."""
        result = self.connector.update_budget("camp_999", 200.0)
        assert result is False

    def test_get_analytics_nonexistent_campaign(self):
        """get_analytics returns empty dict for nonexistent campaign."""
        analytics = self.connector.get_analytics("camp_999")
        assert analytics == {}

    # --- Health check ---

    def test_health_check_healthy(self):
        """health_check returns True when healthy."""
        assert self.connector.health_check() is True

    def test_health_check_unhealthy_after_close(self):
        """health_check returns False after close."""
        self.connector.close()
        assert self.connector.health_check() is False

    def test_get_products_after_close_raises(self):
        """get_products raises after close."""
        self.connector.close()
        with pytest.raises(ConnectionError):
            self.connector.get_products()

    def test_update_inventory_after_close_returns_false(self):
        """update_inventory returns False after close."""
        self.connector.close()
        result = self.connector.update_inventory("p1", 50)
        assert result is False

    # --- Close ---

    def test_close(self):
        """close does not raise and sets healthy to False."""
        self.connector.close()
        assert self.connector.health_check() is False


class TestRateLimiter:
    """Tests for RateLimiter."""

    def setup_method(self):
        """Create a fresh rate limiter for each test."""
        self.limiter = RateLimiter(
            limits={"test_endpoint": 3},
            window_seconds=1.0,
            max_retries=3,
            base_delay=0.01,
        )

    # --- Basic rate limiting ---

    def test_initial_remaining(self):
        """Initial remaining equals the limit."""
        remaining = self.limiter.get_remaining("test_endpoint")
        assert remaining == 3

    def test_record_request_decrements_remaining(self):
        """record_request decrements remaining count."""
        self.limiter.record_request("test_endpoint")
        remaining = self.limiter.get_remaining("test_endpoint")
        assert remaining == 2

    def test_record_request_exhausts_remaining(self):
        """record_request exhausts remaining after limit."""
        for _ in range(3):
            self.limiter.record_request("test_endpoint")
        remaining = self.limiter.get_remaining("test_endpoint")
        assert remaining == 0

    def test_wait_if_needed_returns_zero_when_under_limit(self):
        """wait_if_needed returns 0 when under limit."""
        delay = self.limiter.wait_if_needed("test_endpoint")
        assert delay == 0.0

    def test_wait_if_needed_returns_positive_when_over_limit(self):
        """wait_if_needed returns positive delay when over limit."""
        for _ in range(3):
            self.limiter.record_request("test_endpoint")
        delay = self.limiter.wait_if_needed("test_endpoint")
        assert delay > 0.0

    def test_wait_if_needed_unknown_endpoint(self):
        """wait_if_needed uses default limit for unknown endpoints."""
        delay = self.limiter.wait_if_needed("unknown_endpoint")
        assert delay == 0.0

    def test_reset_clears_counts(self):
        """reset clears all request counts."""
        self.limiter.record_request("test_endpoint")
        self.limiter.reset()
        remaining = self.limiter.get_remaining("test_endpoint")
        assert remaining == 3

    def test_window_expiry_allows_new_requests(self):
        """Requests expire after the window."""
        self.limiter = RateLimiter(
            limits={"fast_endpoint": 2},
            window_seconds=0.1,
            max_retries=3,
            base_delay=0.01,
        )
        self.limiter.record_request("fast_endpoint")
        self.limiter.record_request("fast_endpoint")
        delay = self.limiter.wait_if_needed("fast_endpoint")
        assert delay > 0.0
        # Wait for window to expire
        time.sleep(0.15)
        delay = self.limiter.wait_if_needed("fast_endpoint")
        assert delay == 0.0

    def test_default_limits(self):
        """Default limits are set correctly."""
        limiter = RateLimiter()
        assert limiter.limits["products"] == 10
        assert limiter.limits["ads"] == 3
        assert limiter.limits["inventory"] == 5
