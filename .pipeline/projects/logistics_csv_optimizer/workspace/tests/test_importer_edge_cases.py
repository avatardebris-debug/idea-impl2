"""Edge case and boundary tests for the Importer module.

Tests:
- Missing required columns
- Invalid priority values
- Negative weight
- Zero weight
- Non-numeric weight
- Empty file
- File with only headers
- Whitespace in fields
- Case-insensitive column names
- Extra columns
- Missing optional columns
- Unicode characters in fields
- Very long field values
- Special characters in fields
- Multiple rows with mixed valid/invalid data
- Row with missing optional fields
- File with BOM
- File with different line endings
"""

import os
import tempfile
import pytest
from logistics_csv_optimizer.importer import Importer, REQUIRED_COLUMNS, VALID_PRIORITIES


# ── Fixtures ──

def _make_csv_content(headers, rows):
    """Helper to create CSV content with proper quoting."""
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([str(v) for v in row])
    return output.getvalue()


def _create_temp_csv(content):
    """Create a temporary CSV file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


# ── Missing required columns ──

class TestMissingRequiredColumns:
    """Tests for missing required columns."""

    def test_missing_origin(self):
        content = _make_csv_content(
            ["destination", "weight", "priority"],
            [["Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="Missing required columns.*origin"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_missing_destination(self):
        content = _make_csv_content(
            ["origin", "weight", "priority"],
            [["New York", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="Missing required columns.*destination"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_missing_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "priority"],
            [["New York", "Chicago", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="Missing required columns.*weight"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_missing_priority(self):
        content = _make_csv_content(
            ["origin", "destination", "weight"],
            [["New York", "Chicago", "10.0"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="Missing required columns.*priority"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_missing_all_required(self):
        content = _make_csv_content(
            ["foo", "bar"],
            [["a", "b"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)


# ── Invalid data ──

class TestInvalidData:
    """Tests for invalid data handling."""

    def test_invalid_priority(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", "super_fast"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="priority.*must be one of"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_negative_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "-10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="weight.*must be positive"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_zero_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="weight.*must be positive"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_non_numeric_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "abc", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="weight.*must be a number"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_empty_origin(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="origin.*is empty"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_empty_destination(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="destination.*is empty"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_empty_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="weight.*is empty"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_empty_priority(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", ""]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="priority.*must be one of"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)


# ── Empty file ──

class TestEmptyFile:
    """Tests for empty file handling."""

    def test_completely_empty_file(self):
        path = _create_temp_csv("")
        try:
            result = Importer.load_manifest(path)
            assert result == []
        finally:
            os.unlink(path)

    def test_whitespace_only_file(self):
        path = _create_temp_csv("   \n\n  \n")
        try:
            result = Importer.load_manifest(path)
            assert result == []
        finally:
            os.unlink(path)


# ── Headers only ──

class TestHeadersOnly:
    """Tests for files with only headers."""

    def test_headers_only(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            []
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result == []
        finally:
            os.unlink(path)


# ── Whitespace handling ──

class TestWhitespaceHandling:
    """Tests for whitespace handling."""

    def test_whitespace_in_origin(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["  New York  ", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["origin"] == "New York"
        finally:
            os.unlink(path)

    def test_whitespace_in_destination(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "  Chicago  ", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["destination"] == "Chicago"
        finally:
            os.unlink(path)

    def test_whitespace_in_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "  10.0  ", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["weight"] == 10.0
        finally:
            os.unlink(path)

    def test_whitespace_in_priority(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", "  EXPRESS  "]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["priority"] == "express"
        finally:
            os.unlink(path)

    def test_whitespace_in_optional_fields(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "length", "width", "height", "description"],
            [["New York", "Chicago", "10.0", "standard", "  50  ", "  40  ", "  30  ", "  Test  "]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["length"] == 50.0
            assert result[0]["width"] == 40.0
            assert result[0]["height"] == 30.0
            # Description is free-text and should be preserved as-is
            assert result[0]["description"] == "  Test  "
        finally:
            os.unlink(path)


# ── Case-insensitive columns ──

class TestCaseInsensitiveColumns:
    """Tests for case-insensitive column names."""

    def test_uppercase_columns(self):
        content = _make_csv_content(
            ["ORIGIN", "DESTINATION", "WEIGHT", "PRIORITY"],
            [["New York", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 1
        finally:
            os.unlink(path)

    def test_mixed_case_columns(self):
        content = _make_csv_content(
            ["Origin", "Destination", "Weight", "Priority"],
            [["New York", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 1
        finally:
            os.unlink(path)

    def test_uppercase_optional_columns(self):
        content = _make_csv_content(
            ["ORIGIN", "DESTINATION", "WEIGHT", "PRIORITY", "LENGTH", "WIDTH", "HEIGHT", "DESCRIPTION"],
            [["New York", "Chicago", "10.0", "standard", "50", "40", "30", "Test"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["length"] == 50.0
            assert result[0]["width"] == 40.0
            assert result[0]["height"] == 30.0
            assert result[0]["description"] == "Test"
        finally:
            os.unlink(path)


# ── Extra columns ──

class TestExtraColumns:
    """Tests for extra columns."""

    def test_extra_columns_ignored(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "extra_col"],
            [["New York", "Chicago", "10.0", "standard", "extra_value"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 1
            assert "extra_col" not in result[0]
        finally:
            os.unlink(path)

    def test_extra_optional_columns(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "length", "width", "height", "description", "extra"],
            [["New York", "Chicago", "10.0", "standard", "50", "40", "30", "Test", "extra"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 1
            assert "extra" not in result[0]
        finally:
            os.unlink(path)


# ── Missing optional columns ──

class TestMissingOptionalColumns:
    """Tests for missing optional columns."""

    def test_missing_optional_columns_defaults(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["length"] == 0.0
            assert result[0]["width"] == 0.0
            assert result[0]["height"] == 0.0
            assert result[0]["description"] == ""
        finally:
            os.unlink(path)

    def test_partial_optional_columns(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "length"],
            [["New York", "Chicago", "10.0", "standard", "50"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["length"] == 50.0
            assert result[0]["width"] == 0.0
            assert result[0]["height"] == 0.0
            assert result[0]["description"] == ""
        finally:
            os.unlink(path)


# ── Unicode characters ──

class TestUnicodeCharacters:
    """Tests for Unicode character handling."""

    def test_unicode_in_origin(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["São Paulo", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["origin"] == "São Paulo"
        finally:
            os.unlink(path)

    def test_unicode_in_destination(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "München", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["destination"] == "München"
        finally:
            os.unlink(path)

    def test_unicode_in_description(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "description"],
            [["New York", "Chicago", "10.0", "standard", "Fragile: 脆弱物品"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["description"] == "Fragile: 脆弱物品"
        finally:
            os.unlink(path)

    def test_cyrillic_characters(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["Москва", "Чикаго", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["origin"] == "Москва"
        finally:
            os.unlink(path)


# ── Very long field values ──

class TestLongFieldValues:
    """Tests for very long field values."""

    def test_long_origin(self):
        long_origin = "A" * 10000
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [[long_origin, "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["origin"] == long_origin
        finally:
            os.unlink(path)

    def test_long_description(self):
        long_desc = "Test " * 1000
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "description"],
            [["New York", "Chicago", "10.0", "standard", long_desc]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["description"] == long_desc
        finally:
            os.unlink(path)


# ── Special characters ──

class TestSpecialCharacters:
    """Tests for special character handling."""

    def test_comma_in_description(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "description"],
            [["New York", "Chicago", "10.0", "standard", "Item 1, Item 2"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["description"] == "Item 1, Item 2"
        finally:
            os.unlink(path)

    def test_quotes_in_description(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "description"],
            [["New York", "Chicago", "10.0", "standard", '"Fragile" item']]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["description"] == '"Fragile" item'
        finally:
            os.unlink(path)

    def test_newline_in_description(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "description"],
            [["New York", "Chicago", "10.0", "standard", "Line 1\nLine 2"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["description"] == "Line 1\nLine 2"
        finally:
            os.unlink(path)

    def test_special_chars_in_origin(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York @#$%", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["origin"] == "New York @#$%"
        finally:
            os.unlink(path)


# ── Multiple rows ──

class TestMultipleRows:
    """Tests for multiple rows."""

    def test_multiple_valid_rows(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [
                ["New York", "Chicago", "10.0", "standard"],
                ["Los Angeles", "Seattle", "20.0", "express"],
                ["Miami", "Boston", "30.0", "overnight"],
            ]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 3
        finally:
            os.unlink(path)

    def test_mixed_valid_invalid_rows(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [
                ["New York", "Chicago", "10.0", "standard"],
                ["Los Angeles", "Seattle", "-5.0", "express"],
                ["Miami", "Boston", "30.0", "overnight"],
            ]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="weight.*must be positive"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)

    def test_row_number_in_error(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [
                ["New York", "Chicago", "10.0", "standard"],
                ["Los Angeles", "Seattle", "abc", "express"],
            ]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="Row 3.*weight.*must be a number"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)


# ── File with BOM ──

class TestFileWithBOM:
    """Tests for files with BOM."""

    def test_utf8_bom(self):
        content = "\ufeff" + _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 1
        finally:
            os.unlink(path)


# ── Different line endings ──

class TestDifferentLineEndings:
    """Tests for different line endings."""

    def test_crlf_line_endings(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", "standard"]]
        ).replace("\n", "\r\n")
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 1
        finally:
            os.unlink(path)

    def test_mixed_line_endings(self):
        content = "origin,destination,weight,priority\r\nNew York,Chicago,10.0,standard\nLos Angeles,Seattle,20.0,express"
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 2
        finally:
            os.unlink(path)


# ── Priority case handling ──

class TestPriorityCaseHandling:
    """Tests for priority case handling."""

    def test_uppercase_priority(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", "STANDARD"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["priority"] == "standard"
        finally:
            os.unlink(path)

    def test_mixed_case_priority(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", "ExPrEsS"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["priority"] == "express"
        finally:
            os.unlink(path)

    def test_all_valid_priorities(self):
        for priority in VALID_PRIORITIES:
            content = _make_csv_content(
                ["origin", "destination", "weight", "priority"],
                [["New York", "Chicago", "10.0", priority.upper()]]
            )
            path = _create_temp_csv(content)
            try:
                result = Importer.load_manifest(path)
                assert result[0]["priority"] == priority
            finally:
                os.unlink(path)


# ── Weight format variations ──

class TestWeightFormatVariations:
    """Tests for weight format variations."""

    def test_integer_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["weight"] == 10.0
        finally:
            os.unlink(path)

    def test_float_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.5", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["weight"] == 10.5
        finally:
            os.unlink(path)

    def test_scientific_notation_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "1e2", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["weight"] == 100.0
        finally:
            os.unlink(path)

    def test_very_small_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "0.001", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["weight"] == 0.001
        finally:
            os.unlink(path)


# ── Optional field format variations ──

class TestOptionalFieldFormatVariations:
    """Tests for optional field format variations."""

    def test_integer_dimensions(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "length", "width", "height"],
            [["New York", "Chicago", "10.0", "standard", "50", "40", "30"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["length"] == 50.0
            assert result[0]["width"] == 40.0
            assert result[0]["height"] == 30.0
        finally:
            os.unlink(path)

    def test_float_dimensions(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "length", "width", "height"],
            [["New York", "Chicago", "10.0", "standard", "50.5", "40.5", "30.5"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["length"] == 50.5
            assert result[0]["width"] == 40.5
            assert result[0]["height"] == 30.5
        finally:
            os.unlink(path)

    def test_empty_optional_fields(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority", "length", "width", "height", "description"],
            [["New York", "Chicago", "10.0", "standard", "", "", "", ""]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["length"] == 0.0
            assert result[0]["width"] == 0.0
            assert result[0]["height"] == 0.0
            assert result[0]["description"] == ""
        finally:
            os.unlink(path)


# ── Column name variations ──

class TestColumnNameVariations:
    """Tests for column name variations."""

    def test_spaces_in_column_names(self):
        content = _make_csv_content(
            [" origin ", " destination ", " weight ", " priority "],
            [["New York", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 1
        finally:
            os.unlink(path)

    def test_underscore_in_column_names(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert len(result) == 1
        finally:
            os.unlink(path)


# ── File not found ──

class TestFileNotFound:
    """Tests for file not found handling."""

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            Importer.load_manifest("/nonexistent/path/to/file.csv")

    def test_directory_instead_of_file(self):
        with pytest.raises(FileNotFoundError):
            Importer.load_manifest("/tmp")


# ── Edge case row data ──

class TestEdgeCaseRowData:
    """Tests for edge case row data."""

    def test_single_character_origin(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["A", "B", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["origin"] == "A"
        finally:
            os.unlink(path)

    def test_single_character_destination(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["A", "B", "10.0", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["destination"] == "B"
        finally:
            os.unlink(path)

    def test_very_large_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "1e10", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["weight"] == 1e10
        finally:
            os.unlink(path)

    def test_very_small_positive_weight(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "1e-10", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["weight"] == 1e-10
        finally:
            os.unlink(path)

    def test_weight_just_above_zero(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "0.0000001", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            result = Importer.load_manifest(path)
            assert result[0]["weight"] == 0.0000001
        finally:
            os.unlink(path)

    def test_weight_just_below_zero(self):
        content = _make_csv_content(
            ["origin", "destination", "weight", "priority"],
            [["New York", "Chicago", "-0.0000001", "standard"]]
        )
        path = _create_temp_csv(content)
        try:
            with pytest.raises(ValueError, match="weight.*must be positive"):
                Importer.load_manifest(path)
        finally:
            os.unlink(path)
