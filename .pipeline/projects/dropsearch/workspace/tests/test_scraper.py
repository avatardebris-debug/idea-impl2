"""Tests for scraper modules."""

import unittest
from unittest.mock import MagicMock, patch

from src.scraper.browser import BrowserFetcher
from src.scraper.extractor import ProductExtractor
from src.scraper.multi_analyzer import MultiStoreAnalyzer
from src.scraper.supplier_detector import SupplierDetector
from src.scraper.anti_detect import AntiDetect
from src.models.product import Product


class TestAntiDetect(unittest.TestCase):
    """Tests for AntiDetect module."""

    def test_get_headers(self):
        """Test that headers are generated."""
        headers = AntiDetect.get_headers()
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept", headers)
        self.assertIn("Accept-Language", headers)

    def test_get_user_agent(self):
        """Test that user agent is a string."""
        ua = AntiDetect.get_user_agent()
        self.assertIsInstance(ua, str)
        self.assertIn("Mozilla", ua)

    def test_get_viewport(self):
        """Test that viewport has width and height."""
        viewport = AntiDetect.get_viewport()
        self.assertIn("width", viewport)
        self.assertIn("height", viewport)
        self.assertIsInstance(viewport["width"], int)
        self.assertIsInstance(viewport["height"], int)


class TestProductExtractor(unittest.TestCase):
    """Tests for ProductExtractor module."""

    def setUp(self):
        self.extractor = ProductExtractor()

    def test_extract_empty_html(self):
        """Test extraction with empty HTML."""
        products = self.extractor.extract("", "https://example.com")
        self.assertEqual(products, [])

    def test_extract_no_html(self):
        """Test extraction with None HTML."""
        products = self.extractor.extract(None, "https://example.com")
        self.assertEqual(products, [])

    def test_detect_platform_shopify(self):
        """Test Shopify platform detection."""
        html = '<script src="/cdn/shopify.com"></script>'
        platform = self.extractor._detect_platform(html)
        self.assertEqual(platform, "shopify")

    def test_detect_platform_woocommerce(self):
        """Test WooCommerce platform detection."""
        html = '<meta name="generator" content="WooCommerce">'
        platform = self.extractor._detect_platform(html)
        self.assertEqual(platform, "woocommerce")

    def test_detect_platform_generic(self):
        """Test generic platform detection."""
        html = '<html><body>No platform markers</body></html>'
        platform = self.extractor._detect_platform(html)
        self.assertEqual(platform, "generic")


class TestBrowserFetcher(unittest.TestCase):
    """Tests for BrowserFetcher module."""

    def test_fetch_invalid_url(self):
        """Test fetching an invalid URL."""
        fetcher = BrowserFetcher()
        result = fetcher.fetch("https://invalid.url.that.does.not.exist")
        self.assertIsNone(result)

    def test_fetch_with_retry(self):
        """Test fetch with retry logic."""
        fetcher = BrowserFetcher()
        result = fetcher.fetch_with_retry("https://invalid.url.that.does.not.exist", max_retries=1)
        self.assertIsNone(result)


class TestSupplierDetector(unittest.TestCase):
    """Tests for SupplierDetector module."""

    def setUp(self):
        self.detector = SupplierDetector()

    def test_detect_no_suppliers(self):
        """Test detection with no supplier indicators."""
        html = '<html><body>No supplier info</body></html>'
        suppliers = self.detector.detect(html)
        self.assertEqual(suppliers, [])

    def test_detect_printful(self):
        """Test Printful supplier detection."""
        html = '<img src="https://assets.printful.com/logo.png">'
        suppliers = self.detector.detect(html)
        self.assertTrue(len(suppliers) > 0)
        self.assertEqual(suppliers[0].source, "Printful")

    def test_detect_cj(self):
        """Test CJ Affiliate detection."""
        html = '<script src="https://www.cj.com/cj.js"></script>'
        suppliers = self.detector.detect(html)
        self.assertTrue(len(suppliers) > 0)
        self.assertEqual(suppliers[0].source, "CJ Affiliate")


class TestMultiStoreAnalyzer(unittest.TestCase):
    """Tests for MultiStoreAnalyzer module."""

    def test_analyze_empty_urls(self):
        """Test analysis with empty URL list."""
        analyzer = MultiStoreAnalyzer()
        results = analyzer.analyze([])
        self.assertEqual(results, [])

    def test_compare_empty_urls(self):
        """Test comparison with empty URL list."""
        analyzer = MultiStoreAnalyzer()
        comparison = analyzer.compare([])
        self.assertEqual(comparison.stores, [])


if __name__ == "__main__":
    unittest.main()
