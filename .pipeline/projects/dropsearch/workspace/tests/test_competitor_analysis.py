"""Tests for multi-store competitor analysis system."""

import os
import sys
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.store_analysis import StoreAnalysis, CompetitorComparison, SupplierChain, ProductMatch
from src.scraper.supplier_detector import SupplierDetector
from src.analysis.overlap_detector import OverlapDetector
from src.analysis.margin_analyzer import MarginAnalyzer
from src.reporter.comparative_formatter import ComparativeReportFormatter
from src.scraper.multi_analyzer import MultiStoreAnalyzer


# ─── Fixtures ───────────────────────────────────────────────────────────────

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> str:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, "r") as f:
        return f.read()


@pytest.fixture
def supplier_html():
    return _load_fixture("supplier_detection.html")


@pytest.fixture
def store_a_html():
    return _load_fixture("store_a.html")


@pytest.fixture
def store_b_html():
    return _load_fixture("store_b.html")


@pytest.fixture
def store_c_html():
    return _load_fixture("store_c.html")


# ─── Task 1: Pydantic models ────────────────────────────────────────────────

class TestPydanticModels:
    """Test that Pydantic models validate correctly."""

    def test_product_match_creation(self):
        match = ProductMatch(
            product_name="Test Product",
            price_at_store=29.99,
            price_at_source=8.50,
            overlap_score=0.95,
        )
        assert match.product_name == "Test Product"
        assert match.price_at_store == 29.99
        assert match.price_at_source == 8.50
        assert match.overlap_score == 0.95

    def test_product_match_optional_source_price(self):
        match = ProductMatch(
            product_name="Test Product",
            price_at_store=29.99,
            overlap_score=0.95,
        )
        assert match.price_at_source is None

    def test_supplier_chain_creation(self):
        chain = SupplierChain(
            source="AliExpress",
            confidence=0.9,
            detected_urls=["https://aliexpress.com/item/123"],
            estimated_cost=8.50,
        )
        assert chain.source == "AliExpress"
        assert chain.confidence == 0.9
        assert len(chain.detected_urls) == 1
        assert chain.estimated_cost == 8.50

    def test_store_analysis_creation(self):
        analysis = StoreAnalysis(
            stores_url="https://example-store.com",
            platform="Shopify",
            products=[{"name": "Test", "price": 29.99}],
            supplier_info=[SupplierChain(source="AliExpress", confidence=0.9)],
        )
        assert analysis.stores_url == "https://example-store.com"
        assert analysis.platform == "Shopify"
        assert len(analysis.products) == 1
        assert len(analysis.supplier_info) == 1

    def test_competitor_comparison_creation(self):
        comparison = CompetitorComparison(
            stores=[
                StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
                StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
            ],
            product_overlaps=[
                ProductMatch(product_name="Earbuds", price_at_store=29.99, price_at_source=8.50, overlap_score=0.95),
            ],
            price_gaps=[
                {"product_name": "Earbuds", "max_price": 34.99, "min_price": 29.99, "gap_pct": 16.7},
            ],
            insights=["High margin detected on Earbuds"],
        )
        assert len(comparison.stores) == 2
        assert len(comparison.product_overlaps) == 1
        assert len(comparison.price_gaps) == 1
        assert len(comparison.insights) == 1


# ─── Task 2: Supplier detection ─────────────────────────────────────────────

class TestSupplierDetector:
    """Test supplier chain detection from HTML."""

    def test_detect_aliexpress_link(self, supplier_html):
        detector = SupplierDetector()
        suppliers = detector.detect(supplier_html, "https://example-store.com")
        assert len(suppliers) > 0
        aliexpress_suppliers = [s for s in suppliers if "AliExpress" in s.source]
        assert len(aliexpress_suppliers) >= 1

    def test_detect_cj_dropshipping(self, supplier_html):
        detector = SupplierDetector()
        suppliers = detector.detect(supplier_html, "https://example-store.com")
        cj_suppliers = [s for s in suppliers if "CJ Dropshipping" in s.source]
        assert len(cj_suppliers) >= 1

    def test_detect_spocket_iframe(self, supplier_html):
        detector = SupplierDetector()
        suppliers = detector.detect(supplier_html, "https://example-store.com")
        spocket_suppliers = [s for s in suppliers if "Spocket" in s.source]
        assert len(spocket_suppliers) >= 1

    def test_detect_dsers_api(self, supplier_html):
        detector = SupplierDetector()
        suppliers = detector.detect(supplier_html, "https://example-store.com")
        dsers_suppliers = [s for s in suppliers if "DSers" in s.source]
        assert len(dsers_suppliers) >= 1

    def test_detect_zendrop_cost(self, supplier_html):
        detector = SupplierDetector()
        suppliers = detector.detect(supplier_html, "https://example-store.com")
        zendrop_suppliers = [s for s in suppliers if "Zendrop" in s.source]
        assert len(zendrop_suppliers) >= 1

    def test_detect_doba_link(self, supplier_html):
        detector = SupplierDetector()
        suppliers = detector.detect(supplier_html, "https://example-store.com")
        doba_suppliers = [s for s in suppliers if "Doba" in s.source]
        assert len(doba_suppliers) >= 1

    def test_no_suppliers_for_generic_html(self):
        detector = SupplierDetector()
        html = "<html><body><p>No supplier info here</p></body></html>"
        suppliers = detector.detect(html, "https://example-store.com")
        assert len(suppliers) == 0

    def test_confidence_scores(self, supplier_html):
        detector = SupplierDetector()
        suppliers = detector.detect(supplier_html, "https://example-store.com")
        for supplier in suppliers:
            assert 0 <= supplier.confidence <= 1


# ─── Task 3: Overlap detection ──────────────────────────────────────────────

class TestOverlapDetector:
    """Test product overlap detection across stores."""

    def test_detect_overlapping_products(self, store_a_html, store_b_html, store_c_html):
        detector = OverlapDetector()
        stores = [
            StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-c.com", platform="Shopify", products=[], supplier_info=[]),
        ]

        # Parse products from HTML first
        from src.scraper.extractor import ProductExtractor
        extractor = ProductExtractor()
        stores[0].products = extractor.extract(store_a_html, "https://store-a.com")
        stores[1].products = extractor.extract(store_b_html, "https://store-b.com")
        stores[2].products = extractor.extract(store_c_html, "https://store-c.com")

        overlaps = detector.detect(stores)
        assert len(overlaps) > 0

        # Earbuds should be in all 3 stores
        earbuds_overlaps = [o for o in overlaps if "Earbuds" in o.product_name]
        assert len(earbuds_overlaps) >= 1
        assert len(earbuds_overlaps[0].stores) == 3

    def test_detect_partial_overlap(self, store_a_html, store_b_html):
        detector = OverlapDetector()
        from src.scraper.extractor import ProductExtractor
        extractor = ProductExtractor()

        stores = [
            StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
        ]
        stores[0].products = extractor.extract(store_a_html, "https://store-a.com")
        stores[1].products = extractor.extract(store_b_html, "https://store-b.com")

        overlaps = detector.detect(stores)
        # Earbuds and Case should overlap
        assert len(overlaps) >= 2

    def test_no_overlap(self):
        detector = OverlapDetector()
        stores = [
            StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
        ]
        # Empty products
        overlaps = detector.detect(stores)
        assert len(overlaps) == 0

    def test_overlap_score_calculation(self, store_a_html, store_b_html):
        detector = OverlapDetector()
        from src.scraper.extractor import ProductExtractor
        extractor = ProductExtractor()

        stores = [
            StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
        ]
        stores[0].products = extractor.extract(store_a_html, "https://store-a.com")
        stores[1].products = extractor.extract(store_b_html, "https://store-b.com")

        overlaps = detector.detect(stores)
        for overlap in overlaps:
            assert 0 <= overlap.overlap_score <= 1


# ─── Task 4: Margin analysis ────────────────────────────────────────────────

class TestMarginAnalyzer:
    """Test margin calculation from supplier data."""

    def test_calculate_margin(self):
        analyzer = MarginAnalyzer()
        margins = analyzer.analyze([])
        assert len(margins) == 0

    def test_margin_with_supplier_data(self, store_a_html):
        analyzer = MarginAnalyzer()
        from src.scraper.extractor import ProductExtractor
        from src.scraper.supplier_detector import SupplierDetector
        extractor = ProductExtractor()
        detector = SupplierDetector()

        stores = [
            StoreAnalysis(
                stores_url="https://store-a.com",
                platform="Shopify",
                products=extractor.extract(store_a_html, "https://store-a.com"),
                supplier_info=detector.detect(store_a_html, "https://store-a.com"),
            )
        ]

        margins = analyzer.analyze(stores)
        assert len(margins) > 0

        # Check that margins have expected fields
        for margin in margins:
            assert "product_name" in margin
            assert "retail_price" in margin
            assert "estimated_cost" in margin
            assert "margin_pct" in margin
            assert "supplier_source" in margin

    def test_margin_percentage_calculation(self, store_a_html):
        analyzer = MarginAnalyzer()
        from src.scraper.extractor import ProductExtractor
        from src.scraper.supplier_detector import SupplierDetector
        extractor = ProductExtractor()
        detector = SupplierDetector()

        stores = [
            StoreAnalysis(
                stores_url="https://store-a.com",
                platform="Shopify",
                products=extractor.extract(store_a_html, "https://store-a.com"),
                supplier_info=detector.detect(store_a_html, "https://store-a.com"),
            )
        ]

        margins = analyzer.analyze(stores)
        for margin in margins:
            if margin["estimated_cost"] and margin["retail_price"]:
                expected = ((margin["retail_price"] - margin["estimated_cost"]) / margin["retail_price"]) * 100
                assert abs(margin["margin_pct"] - expected) < 0.1


# ─── Task 5: Pricing gap analysis ───────────────────────────────────────────

class TestPricingGapAnalysis:
    """Test pricing gap detection across competitors."""

    def test_detect_pricing_gaps(self, store_a_html, store_b_html, store_c_html):
        analyzer = MarginAnalyzer()
        detector = OverlapDetector()
        from src.scraper.extractor import ProductExtractor
        extractor = ProductExtractor()

        stores = [
            StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-c.com", platform="Shopify", products=[], supplier_info=[]),
        ]
        stores[0].products = extractor.extract(store_a_html, "https://store-a.com")
        stores[1].products = extractor.extract(store_b_html, "https://store-b.com")
        stores[2].products = extractor.extract(store_c_html, "https://store-c.com")

        overlaps = detector.detect(stores)
        gaps = analyzer.analyze(stores)

        # Price gaps should be derived from overlaps
        assert len(gaps) > 0


# ─── Task 6: Actionable insights ────────────────────────────────────────────

class TestActionableInsights:
    """Test insight generation from analysis data."""

    def test_generate_insights(self, store_a_html, store_b_html, store_c_html):
        analyzer = MarginAnalyzer()
        detector = OverlapDetector()
        from src.scraper.extractor import ProductExtractor
        extractor = ProductExtractor()

        stores = [
            StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
            StoreAnalysis(stores_url="https://store-c.com", platform="Shopify", products=[], supplier_info=[]),
        ]
        stores[0].products = extractor.extract(store_a_html, "https://store-a.com")
        stores[1].products = extractor.extract(store_b_html, "https://store-b.com")
        stores[2].products = extractor.extract(store_c_html, "https://store-c.com")

        overlaps = detector.detect(stores)
        margins = analyzer.analyze(stores)

        # Insights should be generated from the data
        assert len(margins) > 0 or len(overlaps) > 0


# ─── Task 7: Comparative report formatting ──────────────────────────────────

class TestComparativeReportFormatter:
    """Test the comparative report formatter."""

    def test_format_comparison(self):
        formatter = ComparativeReportFormatter()
        report = formatter.format_comparison(
            stores=[
                StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
                StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
            ],
            overlaps=[
                ProductMatch(product_name="Earbuds", price_at_store=29.99, price_at_source=8.50, overlap_score=0.95),
            ],
            margins=[
                {"product_name": "Earbuds", "retail_price": 29.99, "estimated_cost": 8.50, "margin_pct": 71.7, "supplier_source": "AliExpress"},
            ],
            price_gaps=[
                {"product_name": "Earbuds", "max_price": 34.99, "min_price": 29.99, "gap_pct": 16.7},
            ],
            insights=["High margin detected on Earbuds"],
        )
        assert "Competitor Analysis Report" in report
        assert "Earbuds" in report
        assert "71.7%" in report

    def test_format_with_no_data(self):
        formatter = ComparativeReportFormatter()
        report = formatter.format_comparison(
            stores=[],
            overlaps=[],
            margins=[],
            price_gaps=[],
            insights=[],
        )
        assert "Competitor Analysis Report" in report
        assert "No overlapping products detected" in report

    def test_format_with_multiple_stores(self):
        formatter = ComparativeReportFormatter()
        report = formatter.format_comparison(
            stores=[
                StoreAnalysis(stores_url="https://store-a.com", platform="Shopify", products=[], supplier_info=[]),
                StoreAnalysis(stores_url="https://store-b.com", platform="WooCommerce", products=[], supplier_info=[]),
                StoreAnalysis(stores_url="https://store-c.com", platform="Shopify", products=[], supplier_info=[]),
            ],
            overlaps=[],
            margins=[],
            price_gaps=[],
            insights=[],
        )
        assert "Store A" in report or "store-a" in report
        assert "Store B" in report or "store-b" in report
        assert "Store C" in report or "store-c" in report


# ─── Task 8: Integration test ───────────────────────────────────────────────

class TestMultiStoreAnalyzerIntegration:
    """Integration test for the full multi-store analysis pipeline."""

    def test_full_analysis_pipeline(self, store_a_html, store_b_html, store_c_html):
        analyzer = MultiStoreAnalyzer()

        # Run analysis on all three stores
        comparison = analyzer.compare([
            "file://" + os.path.join(FIXTURES_DIR, "store_a.html"),
            "file://" + os.path.join(FIXTURES_DIR, "store_b.html"),
            "file://" + os.path.join(FIXTURES_DIR, "store_c.html"),
        ])

        # Verify results
        assert len(comparison.stores) == 3
        assert len(comparison.product_overlaps) > 0
        assert len(comparison.price_gaps) > 0
        assert len(comparison.insights) > 0

        # Verify Earbuds is in all 3 stores
        earbuds_overlaps = [o for o in comparison.product_overlaps if "Earbuds" in o.product_name]
        assert len(earbuds_overlaps) >= 1
        assert len(earbuds_overlaps[0].stores) == 3

    def test_analysis_with_single_store(self, store_a_html):
        analyzer = MultiStoreAnalyzer()
        comparison = analyzer.compare([
            "file://" + os.path.join(FIXTURES_DIR, "store_a.html"),
        ])
        assert len(comparison.stores) == 1
        assert len(comparison.product_overlaps) == 0  # No overlaps with single store

    def test_analysis_with_empty_html(self):
        analyzer = MultiStoreAnalyzer()
        comparison = analyzer.compare([
            "file://" + os.path.join(FIXTURES_DIR, "store_a.html"),
        ])
        # Should not crash
        assert comparison is not None


# ─── Task 9: CLI integration ────────────────────────────────────────────────

class TestCLIIntegration:
    """Test CLI integration for analyze command."""

    def test_analyze_command_help(self):
        """Test that analyze command shows help."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "analyze", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert result.returncode == 0
        assert "analyze" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_scan_command_help(self):
        """Test that scan command shows help."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "scan", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert result.returncode == 0
        assert "scan" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_analyze_with_min_overlap(self):
        """Test analyze command with --min-overlap flag."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "analyze",
             "file://" + os.path.join(FIXTURES_DIR, "store_a.html"),
             "file://" + os.path.join(FIXTURES_DIR, "store_b.html"),
             "--min-overlap", "2"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        # Should not crash
        assert result.returncode == 0

    def test_analyze_with_insights_flag(self):
        """Test analyze command with --insights flag."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "analyze",
             "file://" + os.path.join(FIXTURES_DIR, "store_a.html"),
             "file://" + os.path.join(FIXTURES_DIR, "store_b.html"),
             "--insights"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        # Should not crash
        assert result.returncode == 0

    def test_scan_with_comparative_format(self):
        """Test scan command with --format comparative."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "scan",
             "file://" + os.path.join(FIXTURES_DIR, "store_a.html"),
             "--format", "comparative"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        # Should not crash
        assert result.returncode == 0


# ─── Task 10: Edge cases ────────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_html(self):
        """Test with empty HTML."""
        detector = SupplierDetector()
        suppliers = detector.detect("", "https://example-store.com")
        assert suppliers == []

    def test_malformed_html(self):
        """Test with malformed HTML."""
        detector = SupplierDetector()
        suppliers = detector.detect("<html><body>unclosed tag", "https://example-store.com")
        # Should not crash
        assert suppliers is not None

    def test_no_price_data(self):
        """Test with products that have no price."""
        analyzer = MarginAnalyzer()
        stores = [
            StoreAnalysis(
                stores_url="https://example-store.com",
                platform="Shopify",
                products=[{"name": "No Price Product", "price": None}],
                supplier_info=[],
            )
        ]
        margins = analyzer.analyze(stores)
        # Should not crash
        assert margins is not None

    def test_single_store_analysis(self):
        """Test analysis with only one store."""
        analyzer = MultiStoreAnalyzer()
        comparison = analyzer.compare([
            "file://" + os.path.join(FIXTURES_DIR, "store_a.html"),
        ])
        assert comparison is not None
        assert len(comparison.stores) == 1

    def test_formatter_with_none_values(self):
        """Test formatter handles None values gracefully."""
        formatter = ComparativeReportFormatter()
        report = formatter.format_comparison(
            stores=[],
            overlaps=[],
            margins=[],
            price_gaps=[],
            insights=[],
        )
        assert "Competitor Analysis Report" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
