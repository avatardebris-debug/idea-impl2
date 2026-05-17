"""Tests for ecommercecatalog_optimizer.exporter — CatalogExporter class."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from ecommercecatalog_optimizer.catalog_analyzer import CatalogRecord
from ecommercecatalog_optimizer.exporter import CatalogExporter, ExportResult, OUTPUT_COLUMNS
from ecommercecatalog_optimizer.metadata_optimizer import MetadataOptimizationResult


class TestCatalogExporterInit(TestCase):
    """Test CatalogExporter initialization."""

    def test_default_output_dir(self):
        """Default output_dir should be current directory."""
        exporter = CatalogExporter()
        self.assertEqual(exporter.output_dir, Path("."))

    def test_custom_output_dir(self):
        """Custom output_dir should be created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            self.assertTrue(Path(tmpdir).exists())

    def test_output_dir_created(self):
        """Output directory should be created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "sub", "nested", "dir")
            exporter = CatalogExporter(new_dir)
            self.assertTrue(Path(new_dir).exists())


class TestExportCsv(TestCase):
    """Test CatalogExporter.export_csv method."""

    def setUp(self):
        """Create test records and exporter."""
        self.records = [
            CatalogRecord(
                product_id="P001",
                title="Test Product 1",
                price=29.99,
                description="A test product",
                category="Electronics",
                brand="TestBrand",
                sku="SKU-001",
                image_url="http://example.com/img1.jpg",
                weight=1.5,
                dimensions="10x20x30",
                color="Red",
                keywords="test, electronics",
                tags="new, featured",
                meta_title="Test Product 1",
                meta_description="A test product description",
                meta_keywords="test, electronics",
                url="http://example.com/p1",
                availability="in_stock",
                rating=4.5,
                review_count=100,
            ),
            CatalogRecord(
                product_id="P002",
                title="Test Product 2",
                price=19.0,
                description="Another test product",
                category="Books",
                brand="BookCo",
                sku="SKU-002",
                image_url=None,
                weight=None,
                dimensions=None,
                color=None,
                keywords=None,
                tags=None,
                meta_title=None,
                meta_description=None,
                meta_keywords=None,
                url="http://example.com/p2",
                availability="out_of_stock",
                rating=None,
                review_count=0,
            ),
        ]
        self.exporter = CatalogExporter()

    def test_export_csv_creates_file(self):
        """export_csv should create a CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            result = exporter.export_csv(self.records, "test_output.csv")
            self.assertTrue(Path(tmpdir, "test_output.csv").exists())
            self.assertIsInstance(result, ExportResult)
            self.assertEqual(result.records_exported, 2)
            self.assertEqual(result.format, "csv")

    def test_export_csv_header_columns(self):
        """CSV header should match OUTPUT_COLUMNS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            exporter.export_csv(self.records, "test_output.csv")
            with open(Path(tmpdir, "test_output.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader)
            self.assertEqual(header, OUTPUT_COLUMNS)

    def test_export_csv_data_rows(self):
        """CSV data rows should match record fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            exporter.export_csv(self.records, "test_output.csv")
            with open(Path(tmpdir, "test_output.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            # First row should match first record
            self.assertEqual(rows[0][0], "P001")  # product_id
            self.assertEqual(rows[0][1], "Test Product 1")  # title
            self.assertEqual(rows[0][2], "29.99")  # price
            self.assertEqual(rows[0][3], "A test product")  # description
            self.assertEqual(rows[0][4], "Electronics")  # category
            self.assertEqual(rows[0][5], "TestBrand")  # brand

    def test_export_csv_float_formatting(self):
        """Float values should be formatted correctly (no trailing zeros)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            exporter.export_csv(self.records, "test_output.csv")
            with open(Path(tmpdir, "test_output.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                next(reader)  # skip header
                rows = list(reader)
            # P001 price is 29.99 (should stay as 29.99)
            self.assertEqual(rows[0][2], "29.99")
            # P002 price is 19.0 (should be "19" — no trailing zero)
            self.assertEqual(rows[1][2], "19")
            # P001 rating is 4.5 (should be "4.50")
            self.assertEqual(rows[0][18], "4.50")

    def test_export_csv_none_values(self):
        """None values should be empty strings in CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            exporter.export_csv(self.records, "test_output.csv")
            with open(Path(tmpdir, "test_output.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                next(reader)  # skip header
                rows = list(reader)
            # P002 has many None values
            self.assertEqual(rows[1][7], "")  # image_url (index 7)
            self.assertEqual(rows[1][8], "")  # weight (index 8)
            self.assertEqual(rows[1][9], "")  # dimensions (index 9)
            self.assertEqual(rows[1][10], "")  # color (index 10)
            self.assertEqual(rows[1][11], "")  # keywords (index 11)
            self.assertEqual(rows[1][12], "")  # tags (index 12)
            self.assertEqual(rows[1][13], "")  # meta_title (index 13)
            self.assertEqual(rows[1][14], "")  # meta_description (index 14)
            self.assertEqual(rows[1][15], "")  # meta_keywords (index 15)
            self.assertEqual(rows[1][18], "")  # rating (index 18)

    def test_export_csv_include_metadata_requires_results(self):
        """include_metadata=True without metadata_results should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            with self.assertRaises(ValueError) as ctx:
                exporter.export_csv(
                    self.records,
                    "test_output.csv",
                    include_metadata=True,
                    metadata_results=None,
                )
            self.assertIn("metadata_results is required", str(ctx.exception))

    def test_export_csv_include_metadata_length_mismatch(self):
        """include_metadata=True with wrong-length metadata_results should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            bad_results = [
                MetadataOptimizationResult(
                    product_id="P001",
                    original_meta_title=None,
                    optimized_meta_title="Optimized Title",
                    original_meta_description=None,
                    optimized_meta_description="Optimized Description",
                    original_meta_keywords=None,
                    optimized_meta_keywords="opt, keywords",
                    changes_made=["meta_title: generated"],
                ),
            ]  # Only 1 result for 2 records
            with self.assertRaises(ValueError) as ctx:
                exporter.export_csv(
                    self.records,
                    "test_output.csv",
                    include_metadata=True,
                    metadata_results=bad_results,
                )
            self.assertIn("does not match records length", str(ctx.exception))

    def test_export_csv_include_metadata_correct_columns(self):
        """When include_metadata=True, header should have extra metadata columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            metadata_results = [
                MetadataOptimizationResult(
                    product_id="P001",
                    original_meta_title=None,
                    optimized_meta_title="Optimized Title 1",
                    original_meta_description=None,
                    optimized_meta_description="Optimized Desc 1",
                    original_meta_keywords=None,
                    optimized_meta_keywords="opt, kw1",
                    changes_made=["meta_title: generated", "meta_description: generated"],
                ),
                MetadataOptimizationResult(
                    product_id="P002",
                    original_meta_title="Original Title 2",
                    optimized_meta_title="Optimized Title 2",
                    original_meta_description="Original Desc 2",
                    optimized_meta_description="Optimized Desc 2",
                    original_meta_keywords="orig, kw",
                    optimized_meta_keywords="opt, kw2",
                    changes_made=["meta_title: optimized"],
                ),
            ]
            result = exporter.export_csv(
                self.records,
                "test_output.csv",
                include_metadata=True,
                metadata_results=metadata_results,
            )
            self.assertEqual(result.records_exported, 2)

            with open(Path(tmpdir, "test_output.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader)
                rows = list(reader)

            # Header should have base columns + 4 metadata columns
            expected_cols = OUTPUT_COLUMNS + [
                "optimized_meta_title",
                "optimized_meta_description",
                "optimized_meta_keywords",
                "metadata_changes",
            ]
            self.assertEqual(header, expected_cols)

            # Data rows should have metadata values
            self.assertEqual(rows[0][20], "Optimized Title 1")  # optimized_meta_title
            self.assertEqual(rows[0][21], "Optimized Desc 1")  # optimized_meta_description
            self.assertEqual(rows[0][22], "opt, kw1")  # optimized_meta_keywords
            self.assertEqual(rows[0][23], "meta_title: generated; meta_description: generated")  # metadata_changes

    def test_export_csv_empty_records(self):
        """Exporting empty records list should create file with header only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            result = exporter.export_csv([], "empty_output.csv")
            self.assertEqual(result.records_exported, 0)
            self.assertTrue(Path(tmpdir, "empty_output.csv").exists())
            with open(Path(tmpdir, "empty_output.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader)
                rows = list(reader)
            self.assertEqual(header, OUTPUT_COLUMNS)
            self.assertEqual(len(rows), 0)

    def test_export_csv_special_characters(self):
        """CSV should handle special characters correctly."""
        record = CatalogRecord(
            product_id="P003",
            title='Product with "quotes" and, commas',
            price=10.0,
            description="Line1\nLine2",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            exporter.export_csv([record], "special_output.csv")
            with open(Path(tmpdir, "special_output.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                next(reader)  # skip header
                rows = list(reader)
            self.assertEqual(rows[0][1], 'Product with "quotes" and, commas')
            self.assertEqual(rows[0][3], "Line1\nLine2")

    def test_export_csv_unicode_characters(self):
        """CSV should handle unicode characters correctly."""
        record = CatalogRecord(
            product_id="P004",
            title="日本語製品",
            price=100.0,
            description="Émoji: 🎉🚀",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            exporter.export_csv([record], "unicode_output.csv")
            with open(Path(tmpdir, "unicode_output.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                next(reader)  # skip header
                rows = list(reader)
            self.assertEqual(rows[0][1], "日本語製品")
            self.assertEqual(rows[0][3], "Émoji: 🎉🚀")


class TestExportResult(TestCase):
    """Test ExportResult dataclass."""

    def test_export_result_creation(self):
        """ExportResult should be creatable with required fields."""
        result = ExportResult(records_exported=5, format="csv", output_path="/tmp/test.csv")
        self.assertEqual(result.records_exported, 5)
        self.assertEqual(result.format, "csv")
        self.assertEqual(result.output_path, "/tmp/test.csv")

    def test_export_result_default_output_path(self):
        """ExportResult should have None as default output_path."""
        result = ExportResult(output_path=None, records_exported=5, format="csv")
        self.assertIsNone(result.output_path)


class TestOutputColumns(TestCase):
    """Test OUTPUT_COLUMNS constant."""

    def test_output_columns_count(self):
        """OUTPUT_COLUMNS should have 20 base columns."""
        self.assertEqual(len(OUTPUT_COLUMNS), 20)

    def test_output_columns_content(self):
        """OUTPUT_COLUMNS should contain expected column names."""
        expected = [
            "product_id",
            "title",
            "price",
            "description",
            "category",
            "brand",
            "sku",
            "image_url",
            "weight",
            "dimensions",
            "color",
            "keywords",
            "tags",
            "meta_title",
            "meta_description",
            "meta_keywords",
            "url",
            "availability",
            "rating",
            "review_count",
        ]
        self.assertEqual(OUTPUT_COLUMNS, expected)


class TestCatalogExporterIntegration(TestCase):
    """Integration tests for CatalogExporter."""

    def test_full_export_with_metadata(self):
        """Full export with metadata should produce correct CSV."""
        records = [
            CatalogRecord(
                product_id="P001",
                title="Widget",
                price=9.99,
                category="Tools",
                brand="ToolCo",
                meta_title=None,
                meta_description=None,
                meta_keywords=None,
            ),
        ]
        metadata_results = [
            MetadataOptimizationResult(
                product_id="P001",
                original_meta_title=None,
                optimized_meta_title="ToolCo Widget - Tools",
                original_meta_description=None,
                optimized_meta_description="Widget by ToolCo. Category: Tools.",
                original_meta_keywords=None,
                optimized_meta_keywords="widget, toolco, tools",
                changes_made=[
                    "meta_title: generated",
                    "meta_description: generated",
                    "meta_keywords: generated",
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CatalogExporter(tmpdir)
            result = exporter.export_csv(
                records,
                "full_export.csv",
                include_metadata=True,
                metadata_results=metadata_results,
            )

            self.assertEqual(result.records_exported, 1)
            self.assertEqual(result.format, "csv")
            self.assertTrue(Path(tmpdir, "full_export.csv").exists())

            with open(Path(tmpdir, "full_export.csv"), newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                header = next(reader)
                rows = list(reader)

            self.assertEqual(len(rows), 1)
            # Check metadata columns are present and correct
            self.assertEqual(rows[0][20], "ToolCo Widget - Tools")
            self.assertEqual(rows[0][21], "Widget by ToolCo. Category: Tools.")
            self.assertEqual(rows[0][22], "widget, toolco, tools")
            self.assertIn("meta_title: generated", rows[0][23])
            self.assertIn("meta_description: generated", rows[0][23])
            self.assertIn("meta_keywords: generated", rows[0][23])


if __name__ == "__main__":
    import unittest
    unittest.main()
