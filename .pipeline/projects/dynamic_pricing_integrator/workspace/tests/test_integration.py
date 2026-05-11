"""Integration tests for PricingIntegrator, exporters, and YouTube Studio."""

import json
import pytest
from datetime import datetime

from dynamic_pricing.config import PricingConfig
from dynamic_pricing.discount_engine import PriceGapRule, DiscountEngine
from dynamic_pricing.integrator import PricingIntegrator
from dynamic_pricing.models import (
    Product,
    ProductMetadata,
    PriceSnapshot,
    MarginStatusEnum,
)
from dynamic_pricing.exporters.json_exporter import JSONExporter
from dynamic_pricing.exporters.csv_exporter import CSVExporter
from youtube_studio.youtube_studio import YouTubeStudio
from youtube_studio.seo_optimizer import SEOOptimizer


class TestPricingIntegrator:
    """Tests for PricingIntegrator class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        integrator = PricingIntegrator()
        assert integrator.config is not None
        assert integrator.price_tracker is not None
        assert integrator.discount_engine is not None
        assert integrator.margin_optimizer is not None

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = PricingConfig(
            polling_interval=300,
            margin_floor=0.20,
            competitor_sources=["source1", "source2"],
            real_time_polling=True,
            seo_integration=True,
            approval_required=True,
            currency="EUR",
            ceiling_multiplier=2.0,
            target_margin=0.25,
        )
        integrator = PricingIntegrator(config=config)
        assert integrator.config.polling_interval == 300
        assert integrator.config.margin_floor == 0.20
        assert integrator.config.competitor_sources == ["source1", "source2"]
        assert integrator.config.real_time_polling is True
        assert integrator.config.seo_integration is True
        assert integrator.config.approval_required is True
        assert integrator.config.currency == "EUR"
        assert integrator.config.ceiling_multiplier == 2.0
        assert integrator.config.target_margin == 0.25

    def test_add_discount_rule(self):
        """Test adding a discount rule."""
        integrator = PricingIntegrator()
        rule = PriceGapRule(gap_threshold=0.10, discount_pct=0.05)
        integrator.add_discount_rule(rule)
        assert len(integrator.discount_engine.rules) == 1

    def test_poll_prices(self):
        """Test polling prices."""
        integrator = PricingIntegrator()
        snapshots = integrator.poll_prices("test_product")
        assert isinstance(snapshots, list)

    def test_get_pricing_insights(self):
        """Test getting pricing insights."""
        integrator = PricingIntegrator()
        insights = integrator.get_pricing_insights("test_product")
        assert "competitive_position" in insights
        assert "recommended_action" in insights
        assert "recommended_discount" in insights
        assert "margin_status" in insights
        assert "recommended_price" in insights
        assert "floor_price" in insights
        assert "ceiling_price" in insights

    def test_merge_with_seo(self):
        """Test merging SEO data with pricing data."""
        integrator = PricingIntegrator()
        seo_metadata = {
            "name": "Test Product",
            "base_price": 100.0,
            "currency": "USD",
            "category": "Electronics",
            "seo_title": "Test Product Title",
            "seo_description": "Test Product Description",
            "seo_tags": ["electronics", "tech"],
        }
        metadata = integrator.merge_with_seo(seo_metadata, "test_product")
        assert metadata.product_id == "test_product"
        assert metadata.name == "Test Product"
        assert metadata.base_price == 100.0
        assert metadata.currency == "USD"
        assert metadata.category == "Electronics"
        assert metadata.seo_title == "Test Product Title"
        assert metadata.seo_description == "Test Product Description"
        assert metadata.seo_tags == ["electronics", "tech"]

    def test_merge_with_seo_discount_applied(self):
        """Test merging SEO data with discount applied."""
        integrator = PricingIntegrator()
        rule = PriceGapRule(gap_threshold=0.10, discount_pct=0.15)
        integrator.add_discount_rule(rule)
        seo_metadata = {
            "name": "Test Product",
            "base_price": 100.0,
            "currency": "USD",
            "category": "Electronics",
            "seo_title": "Test Product Title",
            "seo_description": "Test Product Description",
            "seo_tags": ["electronics"],
        }
        metadata = integrator.merge_with_seo(seo_metadata, "test_product")
        assert metadata.discount_pct == 0.15
        assert metadata.effective_price == 85.0
        assert "discount" in metadata.seo_tags
        assert "sale" in metadata.seo_tags

    def test_approval_required_pending(self):
        """Test approval required with pending status."""
        config = PricingConfig(approval_required=True)
        integrator = PricingIntegrator(config=config)
        seo_metadata = {
            "name": "Test Product",
            "base_price": 100.0,
            "currency": "USD",
            "category": "Electronics",
            "seo_title": "Test Product Title",
            "seo_description": "Test Product Description",
            "seo_tags": ["electronics"],
        }
        metadata = integrator.merge_with_seo(seo_metadata, "test_product")
        assert metadata.approval_status == "pending"

    def test_approval_submit_and_approve(self):
        """Test submitting and approving pricing."""
        config = PricingConfig(approval_required=True)
        integrator = PricingIntegrator(config=config)
        metadata = ProductMetadata(
            product_id="test_product",
            name="Test Product",
            base_price=100.0,
            effective_price=100.0,
            discount_pct=0.0,
            margin_status=MarginStatusEnum.WITHIN,
            recommended_price=100.0,
            floor_price=85.0,
            ceiling_price=150.0,
            competitive_position="at market",
            seo_title="Test",
            seo_description="Test",
            seo_tags=[],
            currency="USD",
            category="Electronics",
        )
        result = integrator.submit_for_approval("test_product", metadata)
        assert result is True
        result = integrator.approve("test_product")
        assert result is True

    def test_approval_reject(self):
        """Test rejecting pricing."""
        config = PricingConfig(approval_required=True)
        integrator = PricingIntegrator(config=config)
        metadata = ProductMetadata(
            product_id="test_product",
            name="Test Product",
            base_price=100.0,
            effective_price=100.0,
            discount_pct=0.0,
            margin_status=MarginStatusEnum.WITHIN,
            recommended_price=100.0,
            floor_price=85.0,
            ceiling_price=150.0,
            competitive_position="at market",
            seo_title="Test",
            seo_description="Test",
            seo_tags=[],
            currency="USD",
            category="Electronics",
        )
        integrator.submit_for_approval("test_product", metadata)
        result = integrator.reject("test_product")
        assert result is True

    def test_generate_seo_report(self):
        """Test generating SEO report."""
        integrator = PricingIntegrator()
        products = [
            Product(id="prod1", name="Product 1", base_price=100.0, currency="USD", category="Electronics"),
            Product(id="prod2", name="Product 2", base_price=200.0, currency="USD", category="Home"),
        ]
        report = integrator.generate_seo_report(products)
        assert len(report) == 2
        assert isinstance(report[0], ProductMetadata)
        assert isinstance(report[1], ProductMetadata)


class TestJSONExporter:
    """Tests for JSONExporter class."""

    def test_export_single(self):
        """Test exporting a single ProductMetadata to JSON."""
        exporter = JSONExporter(indent=2)
        metadata = ProductMetadata(
            product_id="test_product",
            name="Test Product",
            base_price=100.0,
            effective_price=90.0,
            discount_pct=0.10,
            margin_status=MarginStatusEnum.BELOW,
            recommended_price=95.0,
            floor_price=85.0,
            ceiling_price=150.0,
            competitive_position="below market",
            seo_title="Test Title",
            seo_description="Test Description",
            seo_tags=["test", "product"],
            currency="USD",
            category="Electronics",
            approval_status="approved",
        )
        json_str = exporter.export(metadata)
        data = json.loads(json_str)
        assert data["product_id"] == "test_product"
        assert data["name"] == "Test Product"
        assert data["base_price"] == 100.0
        assert data["effective_price"] == 90.0
        assert data["discount_pct"] == 0.10
        assert data["margin_status"] == "below"
        assert data["recommended_price"] == 95.0
        assert data["floor_price"] == 85.0
        assert data["ceiling_price"] == 150.0
        assert data["competitive_position"] == "below market"
        assert data["seo_title"] == "Test Title"
        assert data["seo_description"] == "Test Description"
        assert data["seo_tags"] == ["test", "product"]
        assert data["currency"] == "USD"
        assert data["category"] == "Electronics"
        assert data["approval_status"] == "approved"

    def test_export_batch(self):
        """Test exporting a batch of ProductMetadata to JSON."""
        exporter = JSONExporter(indent=2)
        metadatas = [
            ProductMetadata(
                product_id="prod1",
                name="Product 1",
                base_price=100.0,
                effective_price=90.0,
                discount_pct=0.10,
                margin_status=MarginStatusEnum.BELOW,
                recommended_price=95.0,
                floor_price=85.0,
                ceiling_price=150.0,
                competitive_position="below market",
                seo_title="Test Title 1",
                seo_description="Test Description 1",
                seo_tags=["test"],
                currency="USD",
                category="Electronics",
                approval_status="approved",
            ),
            ProductMetadata(
                product_id="prod2",
                name="Product 2",
                base_price=200.0,
                effective_price=180.0,
                discount_pct=0.10,
                margin_status=MarginStatusEnum.ABOVE,
                recommended_price=190.0,
                floor_price=170.0,
                ceiling_price=300.0,
                competitive_position="above market",
                seo_title="Test Title 2",
                seo_description="Test Description 2",
                seo_tags=["test"],
                currency="USD",
                category="Home",
                approval_status="pending",
            ),
        ]
        json_str = exporter.export_batch(metadatas)
        data = json.loads(json_str)
        assert len(data) == 2
        assert data[0]["product_id"] == "prod1"
        assert data[1]["product_id"] == "prod2"


class TestCSVExporter:
    """Tests for CSVExporter class."""

    def test_export_single(self):
        """Test exporting a single ProductMetadata to CSV."""
        exporter = CSVExporter(delimiter=",")
        metadata = ProductMetadata(
            product_id="test_product",
            name="Test Product",
            base_price=100.0,
            effective_price=90.0,
            discount_pct=0.10,
            margin_status=MarginStatusEnum.BELOW,
            recommended_price=95.0,
            floor_price=85.0,
            ceiling_price=150.0,
            competitive_position="below market",
            seo_title="Test Title",
            seo_description="Test Description",
            seo_tags=["test", "product"],
            currency="USD",
            category="Electronics",
            approval_status="approved",
        )
        csv_str = exporter.export(metadata)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 2  # header + 1 data row
        header = lines[0].split(",")
        assert "product_id" in header
        assert "name" in header
        assert "base_price" in header
        data = lines[1].split(",")
        assert data[0] == "test_product"
        assert data[1] == "Test Product"
        assert data[2] == "100.0"
        assert data[3] == "90.0"
        assert data[4] == "0.1"
        assert data[5] == "below"
        assert data[6] == "95.0"
        assert data[7] == "85.0"
        assert data[8] == "150.0"
        assert data[9] == "below market"
        assert data[10] == "Test Title"
        assert data[11] == "Test Description"
        assert data[12] == "test|product"
        assert data[13] == "USD"
        assert data[14] == "Electronics"
        assert data[15] == "approved"

    def test_export_batch(self):
        """Test exporting a batch of ProductMetadata to CSV."""
        exporter = CSVExporter(delimiter=",")
        metadatas = [
            ProductMetadata(
                product_id="prod1",
                name="Product 1",
                base_price=100.0,
                effective_price=90.0,
                discount_pct=0.10,
                margin_status=MarginStatusEnum.BELOW,
                recommended_price=95.0,
                floor_price=85.0,
                ceiling_price=150.0,
                competitive_position="below market",
                seo_title="Test Title 1",
                seo_description="Test Description 1",
                seo_tags=["test"],
                currency="USD",
                category="Electronics",
                approval_status="approved",
            ),
            ProductMetadata(
                product_id="prod2",
                name="Product 2",
                base_price=200.0,
                effective_price=180.0,
                discount_pct=0.10,
                margin_status=MarginStatusEnum.ABOVE,
                recommended_price=190.0,
                floor_price=170.0,
                ceiling_price=300.0,
                competitive_position="above market",
                seo_title="Test Title 2",
                seo_description="Test Description 2",
                seo_tags=["test"],
                currency="USD",
                category="Home",
                approval_status="pending",
            ),
        ]
        csv_str = exporter.export_batch(metadatas)
        lines = csv_str.strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows
        assert lines[0].split(",")[0] == "product_id"
        assert lines[1].split(",")[0] == "prod1"
        assert lines[2].split(",")[0] == "prod2"


class TestYouTubeStudio:
    """Tests for YouTubeStudio class."""

    def test_init(self):
        """Test initialization."""
        studio = YouTubeStudio(channel_id="test_channel")
        assert studio.channel_id == "test_channel"
        assert studio.integrator is not None

    def test_init_with_config(self):
        """Test initialization with config."""
        config = PricingConfig(currency="EUR")
        studio = YouTubeStudio(channel_id="test_channel", config=config)
        assert studio.config.currency == "EUR"

    def test_generate_product_metadata(self):
        """Test generating product metadata."""
        studio = YouTubeStudio(channel_id="test_channel")
        product = Product(
            id="prod1",
            name="Test Product",
            base_price=100.0,
            currency="USD",
            category="Electronics",
        )
        metadata = studio.generate_product_metadata(product, "video123")
        assert metadata.product_id == "prod1"
        assert metadata.name == "Test Product"
        assert metadata.base_price == 100.0
        assert metadata.currency == "USD"
        assert metadata.category == "Electronics"
        assert "video123" in metadata.seo_title
        assert "video123" in metadata.seo_tags

    def test_generate_batch_metadata(self):
        """Test generating batch metadata."""
        studio = YouTubeStudio(channel_id="test_channel")
        products = [
            Product(id="prod1", name="Product 1", base_price=100.0, currency="USD", category="Electronics"),
            Product(id="prod2", name="Product 2", base_price=200.0, currency="USD", category="Home"),
        ]
        metadata_list = studio.generate_batch_metadata(products, "video123")
        assert len(metadata_list) == 2
        assert metadata_list[0].product_id == "prod1"
        assert metadata_list[1].product_id == "prod2"

    def test_get_channel_insights(self):
        """Test getting channel insights."""
        studio = YouTubeStudio(channel_id="test_channel")
        insights = studio.get_channel_insights("video123")
        assert insights["video_id"] == "video123"
        assert insights["channel_id"] == "test_channel"
        assert "avg_discount" in insights
        assert "avg_margin" in insights
        assert "total_products" in insights


class TestSEOOptimizer:
    """Tests for SEOOptimizer class."""

    def test_optimize_title(self):
        """Test optimizing title."""
        optimizer = SEOOptimizer(max_title_length=60)
        title = "Test Product - Best Price Online"
        optimized = optimizer.optimize_title(title, "Test Product")
        assert "Test Product" in optimized
        assert len(optimized) <= 60

    def test_optimize_title_too_long(self):
        """Test optimizing title that is too long."""
        optimizer = SEOOptimizer(max_title_length=30)
        title = "This is a very long title that exceeds the limit"
        optimized = optimizer.optimize_title(title, "Test Product")
        assert len(optimized) <= 30

    def test_optimize_description(self):
        """Test optimizing description."""
        optimizer = SEOOptimizer(max_description_length=500)
        description = "This is a product description."
        optimized = optimizer.optimize_description(description, "Test Product", 100.0, "USD")
        assert "100.00 USD" in optimized
        assert len(optimized) <= 500

    def test_optimize_description_too_long(self):
        """Test optimizing description that is too long."""
        optimizer = SEOOptimizer(max_description_length=50)
        description = "This is a very long description that exceeds the limit and should be truncated."
        optimized = optimizer.optimize_description(description, "Test Product", 100.0, "USD")
        assert len(optimized) <= 50

    def test_optimize_tags(self):
        """Test optimizing tags."""
        optimizer = SEOOptimizer(max_tags_count=10)
        tags = ["test", "product"]
        optimized = optimizer.optimize_tags(tags, "Test Product")
        assert "test product" in optimized
        assert len(optimized) <= 10

    def test_optimize_tags_too_many(self):
        """Test optimizing tags that are too many."""
        optimizer = SEOOptimizer(max_tags_count=3)
        tags = ["tag1", "tag2", "tag3", "tag4", "tag5"]
        optimized = optimizer.optimize_tags(tags, "Test Product")
        assert len(optimized) <= 3

    def test_optimize_metadata(self):
        """Test optimizing all SEO fields."""
        optimizer = SEOOptimizer(max_title_length=60, max_description_length=500, max_tags_count=15)
        metadata = ProductMetadata(
            product_id="test_product",
            name="Test Product",
            base_price=100.0,
            effective_price=90.0,
            discount_pct=0.10,
            margin_status=MarginStatusEnum.BELOW,
            recommended_price=95.0,
            floor_price=85.0,
            ceiling_price=150.0,
            competitive_position="below market",
            seo_title="Test Title",
            seo_description="Test Description",
            seo_tags=["test", "product"],
            currency="USD",
            category="Electronics",
            approval_status="approved",
        )
        optimized = optimizer.optimize_metadata(metadata)
        assert optimized.seo_title == optimizer.optimize_title(metadata.seo_title, metadata.name)
        assert optimized.seo_description == optimizer.optimize_description(metadata.seo_description, metadata.name, metadata.effective_price, metadata.currency)
        assert optimized.seo_tags == optimizer.optimize_tags(metadata.seo_tags, metadata.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
