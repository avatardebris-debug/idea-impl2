"""Tests for ecommercecatalog_optimizer package.

Covers CatalogAnalyzer, MetadataOptimizer, and CatalogExporter.
"""

import csv
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the workspace root is on sys.path so imports work
_ws = Path(__file__).resolve().parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from ecommercecatalog_optimizer import CatalogAnalyzer, CatalogExporter, MetadataOptimizer
from ecommercecatalog_optimizer.catalog_analyzer import (
    CatalogRecord,
    CatalogAudit,
    ColumnInfo,
    _map_header,
    _parse_numeric,
    _parse_int,
    REQUIRED_PRODUCT_COLUMNS,
    OPTIONAL_PRODUCT_COLUMNS,
    COLUMN_ALIASES,
)
from ecommercecatalog_optimizer.metadata_optimizer import (
    MetadataOptimizationResult,
    MetadataOptimizer,
    STOP_WORDS,
    MAX_META_TITLE_LENGTH,
    MAX_META_DESCRIPTION_LENGTH,
    MAX_META_KEYWORDS_LENGTH,
)


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def sample_csv(tmp_path):
    """Create a temporary CSV file with sample product data."""
    csv_file = tmp_path / "sample_catalog.csv"
    csv_file.write_text(
        "product_id,title,price,description,category,brand,color\n"
        "1,Wireless Mouse,29.99,Comfortable wireless mouse,Electronics,BrandA,Black\n"
        "2,USB Keyboard,49.50,Mechanical keyboard,Electronics,BrandB,White\n"
        "3,Desk Lamp,15.00,LED desk lamp,Home,BrandC,Silver\n"
        "\n",
        encoding="utf-8",
    )
    return csv_file


@pytest.fixture
def minimal_csv(tmp_path):
    """Create a CSV with only required columns."""
    csv_file = tmp_path / "minimal.csv"
    csv_file.write_text(
        "product_id,title,price\n"
        "1,Widget,10.0\n"
        "\n",
        encoding="utf-8",
    )
    return csv_file


@pytest.fixture
def alias_csv(tmp_path):
    """Create a CSV with aliased column headers."""
    csv_file = tmp_path / "aliases.csv"
    csv_file.write_text(
        "id,product_title,unit_price,desc,manufacturer,colour\n"
        "100,Gadget,25.0,Great gadget,BrandX,Red\n"
        "\n",
        encoding="utf-8",
    )
    return csv_file


@pytest.fixture
def empty_csv(tmp_path):
    """Create a CSV with only headers, no data rows."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text(
        "product_id,title,price\n"
        "\n",
        encoding="utf-8",
    )
    return csv_file


@pytest.fixture
def optimizer():
    """Default MetadataOptimizer instance."""
    return MetadataOptimizer()


# ── CatalogAnalyzer tests ───────────────────────────────────────────


class TestCatalogAnalyzer:
    """Tests for CatalogAnalyzer."""

    def test_load_csv(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        assert len(analyzer.records) == 3

    def test_load_missing_file(self):
        analyzer = CatalogAnalyzer("/nonexistent/file.csv")
        with pytest.raises(FileNotFoundError):
            analyzer.load()

    def test_audit(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        audit = analyzer.audit()
        assert audit.total_rows == 3
        assert audit.total_columns == 7  # product_id, title, price, description, category, brand, color
        assert audit.missing_required == []
        assert audit.quality_score > 0

    def test_missing_required_columns(self, empty_csv):
        analyzer = CatalogAnalyzer(str(empty_csv))
        analyzer.load()
        audit = analyzer.audit()
        # empty_csv has all required columns (product_id, title, price)
        assert audit.missing_required == []

    def test_records_property(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        assert len(analyzer.records) == 3
        assert analyzer.records[0].product_id == "1"
        assert analyzer.records[0].title == "Wireless Mouse"
        assert analyzer.records[0].price == 29.99

    def test_header_map(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        assert "product_id" in analyzer.header_map.values()
        assert "title" in analyzer.header_map.values()

    def test_get_detected_columns(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        cols = analyzer.get_detected_columns()
        assert "product_id" in cols
        assert "title" in cols
        assert "price" in cols

    def test_get_field_values(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        values = analyzer.get_field_values("brand")
        assert values == ["BrandA", "BrandB", "BrandC"]

    def test_audit_before_load_raises(self):
        analyzer = CatalogAnalyzer("/tmp/x.csv")
        with pytest.raises(RuntimeError):
            analyzer.audit()

    def test_get_missing_fields_before_load_raises(self):
        analyzer = CatalogAnalyzer("/tmp/x.csv")
        with pytest.raises(RuntimeError):
            analyzer.get_missing_fields()

    def test_get_detected_columns_before_load_raises(self):
        analyzer = CatalogAnalyzer("/tmp/x.csv")
        with pytest.raises(RuntimeError):
            analyzer.get_detected_columns()

    def test_alias_headers(self, alias_csv):
        analyzer = CatalogAnalyzer(str(alias_csv))
        analyzer.load()
        assert len(analyzer.records) == 1
        rec = analyzer.records[0]
        assert rec.product_id == "100"
        assert rec.title == "Gadget"
        assert rec.price == 25.0
        assert rec.brand == "BrandX"
        assert rec.color == "Red"

    def test_numeric_parsing(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        rec = analyzer.records[0]
        assert isinstance(rec.price, float)
        assert rec.price == 29.99

    def test_empty_rows_skipped(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        assert len(analyzer.records) == 3  # trailing empty row skipped

    def test_quality_score_calculation(self, sample_csv):
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()
        audit = analyzer.audit()
        assert 0 <= audit.quality_score <= 100

    def test_empty_csv_audit(self, empty_csv):
        analyzer = CatalogAnalyzer(str(empty_csv))
        analyzer.load()
        audit = analyzer.audit()
        assert audit.total_rows == 0


# ── MetadataOptimizer tests ─────────────────────────────────────────


class TestMetadataOptimizer:
    """Tests for MetadataOptimizer."""

    def test_optimize_record_generates_title(self, optimizer):
        record = CatalogRecord(product_id="1", title="Widget", brand="BrandX")
        result = optimizer.optimize_record(record)
        assert result.optimized_meta_title is not None
        assert "Widget" in result.optimized_meta_title
        assert "BrandX" in result.optimized_meta_title

    def test_optimize_record_generates_description(self, optimizer):
        record = CatalogRecord(product_id="1", title="Widget", brand="BrandX")
        result = optimizer.optimize_record(record)
        assert result.optimized_meta_description is not None
        assert "Widget" in result.optimized_meta_description

    def test_optimize_record_generates_keywords(self, optimizer):
        record = CatalogRecord(product_id="1", title="Widget", brand="BrandX", category="Electronics")
        result = optimizer.optimize_record(record)
        assert result.optimized_meta_keywords is not None
        assert "widget" in result.optimized_meta_keywords.lower()
        assert "brandx" in result.optimized_meta_keywords.lower()

    def test_optimize_record_changes_made(self, optimizer):
        record = CatalogRecord(product_id="1", title="Widget", brand="BrandX")
        result = optimizer.optimize_record(record)
        assert len(result.changes_made) > 0

    def test_optimize_record_with_existing_metadata(self, optimizer):
        record = CatalogRecord(
            product_id="1",
            title="Widget",
            meta_title="Existing Title",
            meta_description="Existing desc",
            meta_keywords="existing, keywords",
        )
        result = optimizer.optimize_record(record)
        # Existing title should be preserved if it matches optimized
        assert result.original_meta_title == "Existing Title"

    def test_optimize_records(self, optimizer):
        records = [
            CatalogRecord(product_id="1", title="Widget A"),
            CatalogRecord(product_id="2", title="Widget B"),
        ]
        results = optimizer.optimize_records(records)
        assert len(results) == 2
        assert results[0].product_id == "1"
        assert results[1].product_id == "2"

    def test_truncate_title_length(self, optimizer):
        long_title = "A" * 200
        record = CatalogRecord(product_id="1", title=long_title)
        result = optimizer.optimize_record(record)
        assert len(result.optimized_meta_title) <= optimizer.max_title_length

    def test_truncate_description_length(self, optimizer):
        long_desc = "B" * 500
        record = CatalogRecord(product_id="1", description=long_desc)
        result = optimizer.optimize_record(record)
        assert len(result.optimized_meta_description) <= optimizer.max_description_length

    def test_truncate_keywords_length(self, optimizer):
        record = CatalogRecord(product_id="1", title="A" * 100)
        result = optimizer.optimize_record(record)
        assert len(result.optimized_meta_keywords) <= optimizer.max_keywords_length

    def test_no_brand_prefix(self, optimizer):
        optimizer.brand_prefix = False
        record = CatalogRecord(product_id="1", title="Widget", brand="BrandX")
        result = optimizer.optimize_record(record)
        assert "BrandX" not in result.optimized_meta_title

    def test_no_category_suffix(self, optimizer):
        optimizer.category_suffix = False
        record = CatalogRecord(product_id="1", title="Widget", category="Electronics")
        result = optimizer.optimize_record(record)
        assert "Electronics" not in result.optimized_meta_title

    def test_empty_record(self, optimizer):
        record = CatalogRecord(product_id="1")
        result = optimizer.optimize_record(record)
        assert result.optimized_meta_title is None
        assert result.optimized_meta_description is None
        assert result.optimized_meta_keywords is None

    def test_stop_words_excluded(self, optimizer):
        record = CatalogRecord(product_id="1", title="the quick brown fox")
        result = optimizer.optimize_record(record)
        assert result.optimized_meta_keywords is not None
        assert "the" not in result.optimized_meta_keywords.lower().split(", ")
        assert "quick" in result.optimized_meta_keywords.lower()

    def test_custom_max_lengths(self):
        opt = MetadataOptimizer(max_title_length=10, max_description_length=20, max_keywords_length=30)
        record = CatalogRecord(product_id="1", title="A very long title here", description="A very long description here", keywords="a, b, c, d, e, f, g, h, i, j")
        result = opt.optimize_record(record)
        assert len(result.optimized_meta_title) <= 10
        assert len(result.optimized_meta_description) <= 20
        assert len(result.optimized_meta_keywords) <= 30

    def test_metadata_optimization_result_fields(self, optimizer):
        record = CatalogRecord(product_id="1", title="Widget")
        result = optimizer.optimize_record(record)
        assert isinstance(result, MetadataOptimizationResult)
        assert result.product_id == "1"
        assert isinstance(result.changes_made, list)


# ── CatalogExporter tests ───────────────────────────────────────────


class TestCatalogExporter:
    """Tests for CatalogExporter."""

    def test_export_csv(self, tmp_path):
        exporter = CatalogExporter(str(tmp_path))
        records = [
            CatalogRecord(product_id="1", title="Widget", price=10.0),
            CatalogRecord(product_id="2", title="Gadget", price=20.0),
        ]
        result = exporter.export_csv(records, "test_output.csv")
        assert result.records_exported == 2
        assert result.format == "csv"
        assert Path(result.output_path).exists()

    def test_export_csv_with_metadata(self, tmp_path):
        exporter = CatalogExporter(str(tmp_path))
        records = [
            CatalogRecord(product_id="1", title="Widget", brand="BrandX"),
        ]
        optimizer = MetadataOptimizer()
        meta_results = optimizer.optimize_records(records)
        result = exporter.export_csv(
            records, "enriched.csv", include_metadata=True, metadata_results=meta_results
        )
        assert result.records_exported == 1
        # Verify the enriched columns are present
        output_path = Path(result.output_path)
        with open(output_path, newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert "optimized_meta_title" in headers
            assert "optimized_meta_description" in headers
            assert "optimized_meta_keywords" in headers
            assert "metadata_changes" in headers

    def test_export_csv_missing_metadata_raises(self, tmp_path):
        exporter = CatalogExporter(str(tmp_path))
        records = [CatalogRecord(product_id="1", title="Widget")]
        with pytest.raises(ValueError, match="metadata_results is required"):
            exporter.export_csv(records, "test.csv", include_metadata=True, metadata_results=None)

    def test_export_csv_length_mismatch_raises(self, tmp_path):
        exporter = CatalogExporter(str(tmp_path))
        records = [
            CatalogRecord(product_id="1", title="Widget"),
            CatalogRecord(product_id="2", title="Gadget"),
        ]
        optimizer = MetadataOptimizer()
        meta_results = optimizer.optimize_records(records[:1])  # mismatch
        with pytest.raises(ValueError, match="does not match records length"):
            exporter.export_csv(records, "test.csv", include_metadata=True, metadata_results=meta_results)

    def test_export_enriched(self, tmp_path):
        exporter = CatalogExporter(str(tmp_path))
        records = [CatalogRecord(product_id="1", title="Widget", brand="BrandX")]
        optimizer = MetadataOptimizer()
        meta_results = optimizer.optimize_records(records)
        result = exporter.export_enriched(records, meta_results, "enriched.csv")
        assert result.records_exported == 1
        assert Path(result.output_path).exists()

    def test_export_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as td:
            sub_dir = Path(td) / "sub" / "dir"
            exporter = CatalogExporter(str(sub_dir))
            records = [CatalogRecord(product_id="1", title="Widget")]
            exporter.export_csv(records, "test.csv")
            assert sub_dir.exists()

    def test_export_csv_float_formatting(self, tmp_path):
        exporter = CatalogExporter(str(tmp_path))
        records = [
            CatalogRecord(product_id="1", title="Widget", price=10.0),
            CatalogRecord(product_id="2", title="Gadget", price=10.50),
        ]
        result = exporter.export_csv(records, "float_test.csv")
        output_path = Path(result.output_path)
        with open(output_path, newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)
            # price column index
            price_idx = headers.index("price")
            assert rows[0][price_idx] == "10"
            assert rows[1][price_idx] == "10.50"

    def test_export_csv_empty_record(self, tmp_path):
        exporter = CatalogExporter(str(tmp_path))
        records = [CatalogRecord(product_id="1")]
        result = exporter.export_csv(records, "empty_test.csv")
        assert result.records_exported == 1
        assert Path(result.output_path).exists()


# ── Helper function tests ──────────────────────────────────────────


class TestHelperFunctions:
    """Tests for standalone helper functions."""

    def test_parse_numeric_valid(self):
        assert _parse_numeric("10.5") == 10.5
        assert _parse_numeric("$1,000.00") == 1000.0
        assert _parse_numeric("  42  ") == 42.0

    def test_parse_numeric_invalid(self):
        assert _parse_numeric("") is None
        assert _parse_numeric(None) is None
        assert _parse_numeric("abc") is None

    def test_parse_int_valid(self):
        assert _parse_int("42") == 42
        assert _parse_int("  100  ") == 100

    def test_parse_int_invalid(self):
        assert _parse_int("") is None
        assert _parse_int(None) is None
        assert _parse_int("abc") is None

    def test_map_header_known(self):
        assert _map_header("product_id") == "product_id"
        assert _map_header("product_title") == "title"
        assert _map_header("unit_price") == "price"
        assert _map_header("manufacturer") == "brand"
        assert _map_header("colour") == "color"

    def test_map_header_unknown(self):
        assert _map_header("unknown_column") is None

    def test_map_header_case_insensitive(self):
        assert _map_header("PRODUCT_ID") == "product_id"
        assert _map_header("Product_Title") == "title"

    def test_map_header_whitespace(self):
        assert _map_header("  product_id  ") == "product_id"

    def test_required_columns_present(self):
        for col in REQUIRED_PRODUCT_COLUMNS:
            assert col in COLUMN_ALIASES

    def test_optional_columns_present(self):
        for col in OPTIONAL_PRODUCT_COLUMNS:
            assert col in COLUMN_ALIASES

    def test_stop_words_defined(self):
        assert isinstance(STOP_WORDS, set)
        assert "the" in STOP_WORDS
        assert "and" in STOP_WORDS

    def test_max_lengths_defined(self):
        assert MAX_META_TITLE_LENGTH == 60
        assert MAX_META_DESCRIPTION_LENGTH == 160
        assert MAX_META_KEYWORDS_LENGTH == 200


# ── Integration tests ──────────────────────────────────────────────


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_pipeline(self, sample_csv):
        """Load catalog, optimize metadata, export enriched CSV."""
        analyzer = CatalogAnalyzer(str(sample_csv))
        analyzer.load()

        optimizer = MetadataOptimizer()
        results = optimizer.optimize_records(analyzer.records)

        with tempfile.TemporaryDirectory() as td:
            exporter = CatalogExporter(td)
            export_result = exporter.export_csv(
                analyzer.records,
                "enriched.csv",
                include_metadata=True,
                metadata_results=results,
            )

            assert export_result.records_exported == 3
            assert Path(export_result.output_path).exists()

            # Verify output content
            with open(export_result.output_path, newline="") as f:
                reader = csv.reader(f)
                headers = next(reader)
                rows = list(reader)
                assert len(rows) == 3
                assert "optimized_meta_title" in headers

    def test_pipeline_with_alias_headers(self, alias_csv):
        """Load catalog with aliased headers, optimize, export."""
        analyzer = CatalogAnalyzer(str(alias_csv))
        analyzer.load()
        assert len(analyzer.records) == 1

        optimizer = MetadataOptimizer()
        results = optimizer.optimize_records(analyzer.records)
        assert len(results) == 1

        with tempfile.TemporaryDirectory() as td:
            exporter = CatalogExporter(td)
            result = exporter.export_csv(
                analyzer.records,
                "output.csv",
                include_metadata=True,
                metadata_results=results,
            )
            assert result.records_exported == 1
