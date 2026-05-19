"""Integration tests for csv-analyzer — end-to-end testing."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from csv_analyzer.cli.main import cli
from csv_analyzer.core.analyzer import AnalysisEngine
from csv_analyzer.io.csv_reader import CsvReader
from csv_analyzer.io.csv_writer import CsvWriter


class TestIntegrationReadWrite:
    """Integration tests for read-write cycle."""

    def test_full_read_write_cycle(self, tmp_path: Path) -> None:
        """Test reading a CSV, analyzing it, and writing it back."""
        # Create original CSV
        original_file = tmp_path / "original.csv"
        original_df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
            "score": [95.5, 88.0, 92.0],
            "city": ["NYC", "LA", "Chicago"],
        })
        original_df.to_csv(original_file, index=False)

        # Read and analyze
        reader = CsvReader()
        df = reader.read(original_file)
        engine = AnalysisEngine(df)
        profile = engine.profile()

        assert profile["row_count"] == 3
        assert profile["column_count"] == 4

        # Write back
        writer = CsvWriter(index=False)
        output_file = tmp_path / "output.csv"
        writer.write(df, output_file)

        # Verify round-trip
        read_back = pd.read_csv(output_file)
        pd.testing.assert_frame_equal(original_df, read_back)

    def test_read_write_with_missing_values(self, tmp_path: Path) -> None:
        """Test read-write cycle with missing values."""
        original_file = tmp_path / "original.csv"
        original_df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, None, 35],
            "score": [95.5, 88.0, None],
        })
        original_df.to_csv(original_file, index=False)

        reader = CsvReader()
        df = reader.read(original_file)
        engine = AnalysisEngine(df)
        profile = engine.profile()

        assert profile["missing_values"]["age"]["count"] == 1
        assert profile["missing_values"]["score"]["count"] == 1

        writer = CsvWriter(index=False)
        output_file = tmp_path / "output.csv"
        writer.write(df, output_file)

        read_back = pd.read_csv(output_file)
        pd.testing.assert_frame_equal(original_df, read_back)


class TestIntegrationCli:
    """Integration tests for CLI commands."""

    def test_cli_info_with_real_data(self, tmp_path: Path) -> None:
        """Test CLI info command with realistic data."""
        csv_file = tmp_path / "employees.csv"
        csv_file.write_text(
            "name,age,department,salary\n"
            "Alice,30,Engineering,75000\n"
            "Bob,25,Marketing,65000\n"
            "Charlie,35,Engineering,85000\n"
            "Diana,28,HR,70000\n"
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["info", str(csv_file)])

        assert result.exit_code == 0
        assert "Rows: 4" in result.output
        assert "Columns: 4" in result.output
        assert "Engineering" in result.output
        assert "mean" in result.output.lower()

    def test_cli_stats_with_real_data(self, tmp_path: Path) -> None:
        """Test CLI stats command with realistic data."""
        csv_file = tmp_path / "sales.csv"
        csv_file.write_text(
            "product,units_sold,revenue\n"
            "Widget A,100,5000\n"
            "Widget B,150,7500\n"
            "Widget C,75,3750\n"
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["stats", str(csv_file)])

        assert result.exit_code == 0
        assert "units_sold" in result.output
        assert "revenue" in result.output
        assert "mean" in result.output
        assert "std" in result.output

    def test_cli_head_with_real_data(self, tmp_path: Path) -> None:
        """Test CLI head command with realistic data."""
        csv_file = tmp_path / "products.csv"
        csv_file.write_text(
            "id,name,price,category\n"
            "1,Widget,19.99,Electronics\n"
            "2,Gadget,29.99,Electronics\n"
            "3,Tool,9.99,Hardware\n"
            "4,Device,49.99,Electronics\n"
            "5,Instrument,39.99,Hardware\n"
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["head", str(csv_file), "--n", "3"])

        assert result.exit_code == 0
        assert "Widget" in result.output
        assert "Gadget" in result.output
        assert "Tool" in result.output
        assert "Device" not in result.output
        assert "Instrument" not in result.output


class TestIntegrationEdgeCases:
    """Integration tests for edge cases."""

    def test_large_file_handling(self, tmp_path: Path) -> None:
        """Test handling of larger files."""
        csv_file = tmp_path / "large.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "value", "category"])
            for i in range(1000):
                writer.writerow([i, i * 10, f"cat_{i % 10}"])

        reader = CsvReader()
        df = reader.read(csv_file)
        engine = AnalysisEngine(df)
        profile = engine.profile()

        assert profile["row_count"] == 1000
        assert profile["column_count"] == 3

    def test_unicode_content(self, tmp_path: Path) -> None:
        """Test handling of Unicode content."""
        csv_file = tmp_path / "unicode.csv"
        csv_file.write_text(
            "name,city,country\n"
            "José García,México,México\n"
            "María López,España,España\n"
            "李明，北京，中国\n"
            "田中太郎，東京，日本\n"
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["head", str(csv_file)])

        assert result.exit_code == 0
        assert "José" in result.output
        assert "María" in result.output
        assert "李明" in result.output
        assert "田中太郎" in result.output

    def test_mixed_numeric_types(self, tmp_path: Path) -> None:
        """Test handling of mixed numeric types (int and float)."""
        csv_file = tmp_path / "mixed.csv"
        csv_file.write_text(
            "id,price,quantity\n"
            "1,19.99,100\n"
            "2,29.99,150\n"
            "3,9.99,75\n"
        )

        reader = CsvReader()
        df = reader.read(csv_file)
        engine = AnalysisEngine(df)
        profile = engine.profile()

        assert "price" in profile["numeric_stats"]
        assert "quantity" in profile["numeric_stats"]
        assert profile["numeric_stats"]["price"]["mean"] == 19.99
        assert profile["numeric_stats"]["quantity"]["mean"] == 108.33333333333333

    def test_empty_dataframe(self, tmp_path: Path) -> None:
        """Test handling of empty DataFrames."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("name,age,city\n")  # Header only

        reader = CsvReader()
        df = reader.read(csv_file)
        engine = AnalysisEngine(df)
        profile = engine.profile()

        assert profile["row_count"] == 0
        assert profile["column_count"] == 3
        assert profile["numeric_stats"] == {}

    def test_single_column(self, tmp_path: Path) -> None:
        """Test handling of single-column DataFrames."""
        csv_file = tmp_path / "single.csv"
        csv_file.write_text("value\n1\n2\n3\n4\n5\n")

        reader = CsvReader()
        df = reader.read(csv_file)
        engine = AnalysisEngine(df)
        profile = engine.profile()

        assert profile["row_count"] == 5
        assert profile["column_count"] == 1
        assert "value" in profile["numeric_stats"]
        assert profile["numeric_stats"]["value"]["mean"] == 3.0


class TestIntegrationPerformance:
    """Integration tests for performance characteristics."""

    def test_memory_efficiency(self, tmp_path: Path) -> None:
        """Test that the analyzer handles data efficiently."""
        csv_file = tmp_path / "performance.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "value", "category"])
            for i in range(10000):
                writer.writerow([i, i * 10, f"cat_{i % 100}"])

        reader = CsvReader()
        df = reader.read(csv_file)
        engine = AnalysisEngine(df)
        profile = engine.profile()

        assert profile["row_count"] == 10000
        assert profile["column_count"] == 3

    def test_consistent_results(self, tmp_path: Path) -> None:
        """Test that results are consistent across multiple runs."""
        csv_file = tmp_path / "consistent.csv"
        csv_file.write_text(
            "name,age,score\n"
            "Alice,30,95.5\n"
            "Bob,25,88.0\n"
            "Charlie,35,92.0\n"
        )

        runner = CliRunner()

        # Run multiple times
        results = []
        for _ in range(3):
            result = runner.invoke(cli, ["stats", str(csv_file)])
            results.append(result.output)

        # All results should be identical
        assert all(r == results[0] for r in results)


class TestIntegrationErrorHandling:
    """Integration tests for error handling."""

    def test_invalid_csv_format(self, tmp_path: Path) -> None:
        """Test handling of malformed CSV files."""
        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25\n")  # Missing column

        reader = CsvReader()
        df = reader.read(csv_file)

        # Should handle gracefully
        assert len(df) == 2
        assert "city" in df.columns

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Test handling of non-existent files."""
        runner = CliRunner()
        result = runner.invoke(cli, ["info", str(tmp_path / "nonexistent.csv")])

        # Click returns exit code 2 for argument validation errors (file not found)
        assert result.exit_code == 2
        assert "Error" in result.output

    def test_permission_denied(self, tmp_path: Path) -> None:
        """Test handling of permission errors."""
        csv_file = tmp_path / "readonly.csv"
        csv_file.write_text("name,age\nAlice,30\n")
        csv_file.chmod(0o000)

        try:
            reader = CsvReader()
            df = reader.read(csv_file)
            # If we get here, the file was readable (e.g., running as root)
            assert len(df) == 1
        except PermissionError:
            # Expected if running as non-root user
            pass
        finally:
            csv_file.chmod(0o644)  # Restore permissions
