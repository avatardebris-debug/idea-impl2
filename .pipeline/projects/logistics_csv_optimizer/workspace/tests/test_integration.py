"""Integration tests for the Logistics CSV Optimizer.

Tests the full pipeline: Importer -> CostCalculator -> ScheduleGenerator -> CLI.
"""

import csv
import json
import os
import tempfile
from io import StringIO

import pytest

from logistics_csv_optimizer.importer import Importer
from logistics_csv_optimizer.calculator import CostCalculator
from logistics_csv_optimizer.scheduler import ScheduleGenerator
from logistics_csv_optimizer.cli import main, build_parser


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def sample_csv_content():
    """Return a sample CSV manifest as a string."""
    return (
        "origin,destination,priority,weight,length,width,height\n"
        "New York,Chicago,standard,10.0,30,20,10\n"
        "Los Angeles,Dallas,express,20.0,40,30,20\n"
        "Chicago,New York,overnight,15.0,25,15,10\n"
    )


@pytest.fixture
def sample_csv_file(sample_csv_content):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
        fh.write(sample_csv_content)
        fh.flush()
        yield fh.name
    os.unlink(fh.name)


@pytest.fixture
def sample_shipments():
    """Return a list of sample shipment dicts."""
    return [
        {"origin": "New York", "destination": "Chicago", "priority": "standard", "weight": 10.0, "length": 30, "width": 20, "height": 10},
        {"origin": "Los Angeles", "destination": "Dallas", "priority": "express", "weight": 20.0, "length": 40, "width": 30, "height": 20},
        {"origin": "Chicago", "destination": "New York", "priority": "overnight", "weight": 15.0, "length": 25, "width": 15, "height": 10},
    ]


# ── Full Pipeline Integration ─────────────────────────────────────────────────

class TestFullPipeline:
    """Test the full pipeline from CSV to JSON output."""

    def test_csv_to_json_pipeline(self, sample_csv_file):
        """Test that CSV input produces valid JSON output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            output_path = fh.name

        try:
            exit_code = main(["--input", sample_csv_file, "--output", output_path, "--verbose"])
            assert exit_code == 0

            with open(output_path, "r", encoding="utf-8") as fh:
                output = json.load(fh)

            assert "shipments" in output
            assert "total_cost" in output
            assert "schedule" in output
            assert len(output["shipments"]) == 3
            assert len(output["schedule"]) == 3
            assert output["total_cost"] > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_pipeline_with_empty_csv(self):
        """Test pipeline handles empty CSV gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
            fh.write("origin,destination,priority,weight,length,width,height\n")
            fh.flush()
            csv_path = fh.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            output_path = fh.name

        try:
            exit_code = main(["--input", csv_path, "--output", output_path])
            assert exit_code == 0

            with open(output_path, "r", encoding="utf-8") as fh:
                output = json.load(fh)

            assert len(output["shipments"]) == 0
            assert output["total_cost"] == 0
            assert len(output["schedule"]) == 0
        finally:
            os.unlink(csv_path)
            os.unlink(output_path)

    def test_pipeline_with_missing_dimensions(self):
        """Test pipeline handles missing dimension fields."""
        csv_content = (
            "origin,destination,priority,weight\n"
            "New York,Chicago,standard,10.0\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
            fh.write(csv_content)
            fh.flush()
            csv_path = fh.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            output_path = fh.name

        try:
            exit_code = main(["--input", csv_path, "--output", output_path])
            assert exit_code == 0

            with open(output_path, "r", encoding="utf-8") as fh:
                output = json.load(fh)

            assert len(output["shipments"]) == 1
            assert output["total_cost"] > 0
        finally:
            os.unlink(csv_path)
            os.unlink(output_path)


# ── CLI Argument Parsing ─────────────────────────────────────────────────

class TestCLIArgumentParsing:
    """Test CLI argument parsing."""

    def test_required_arguments(self):
        """Test that required arguments are parsed correctly."""
        parser = build_parser()
        args = parser.parse_args(["--input", "test.csv", "--output", "out.json"])
        assert args.input == "test.csv"
        assert args.output == "out.json"
        assert args.verbose is False

    def test_verbose_flag(self):
        """Test that verbose flag is parsed correctly."""
        parser = build_parser()
        args = parser.parse_args(["--input", "test.csv", "--output", "out.json", "--verbose"])
        assert args.verbose is True

    def test_short_arguments(self):
        """Test that short argument forms work."""
        parser = build_parser()
        args = parser.parse_args(["-i", "test.csv", "-o", "out.json", "-v"])
        assert args.input == "test.csv"
        assert args.output == "out.json"
        assert args.verbose is True

    def test_missing_required_argument(self):
        """Test that missing required argument raises SystemExit."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--input", "test.csv"])


# ── CLI Error Handling ─────────────────────────────────────────────────

class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_nonexistent_input_file(self):
        """Test that nonexistent input file returns error code."""
        exit_code = main(["--input", "nonexistent.csv", "--output", "out.json"])
        assert exit_code == 1

    def test_invalid_csv_format(self):
        """Test that invalid CSV format returns error code."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
            fh.write("invalid,data\n")
            fh.flush()
            csv_path = fh.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            output_path = fh.name

        try:
            exit_code = main(["--input", csv_path, "--output", output_path])
            assert exit_code == 1
        finally:
            os.unlink(csv_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


# ── End-to-End with Real Data ─────────────────────────────────────────────────

class TestEndToEnd:
    """End-to-end tests with realistic data."""

    def test_large_manifest(self):
        """Test processing a larger manifest."""
        lines = ["origin,destination,priority,weight,length,width,height"]
        for i in range(100):
            lines.append(f"City{i % 10},Dest{i % 5},{'standard' if i % 3 == 0 else 'express' if i % 3 == 1 else 'overnight'},{i + 1}.0,{10 + i},{10 + i},{10 + i}")

        csv_content = "\n".join(lines) + "\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
            fh.write(csv_content)
            fh.flush()
            csv_path = fh.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            output_path = fh.name

        try:
            exit_code = main(["--input", csv_path, "--output", output_path])
            assert exit_code == 0

            with open(output_path, "r", encoding="utf-8") as fh:
                output = json.load(fh)

            assert len(output["shipments"]) == 100
            assert output["total_cost"] > 0
            assert len(output["schedule"]) == 100
        finally:
            os.unlink(csv_path)
            os.unlink(output_path)

    def test_output_json_structure(self):
        """Test that output JSON has the correct structure."""
        csv_content = (
            "origin,destination,priority,weight,length,width,height\n"
            "New York,Chicago,standard,10.0,30,20,10\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
            fh.write(csv_content)
            fh.flush()
            csv_path = fh.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            output_path = fh.name

        try:
            main(["--input", csv_path, "--output", output_path])

            with open(output_path, "r", encoding="utf-8") as fh:
                output = json.load(fh)

            # Check top-level keys
            assert set(output.keys()) == {"shipments", "total_cost", "schedule"}

            # Check shipments structure
            assert isinstance(output["shipments"], list)
            assert len(output["shipments"]) == 1
            shipment = output["shipments"][0]
            assert "cost" in shipment
            assert "distance_factor" in shipment
            assert "origin" in shipment
            assert "destination" in shipment
            assert "priority" in shipment
            assert "weight" in shipment

            # Check schedule structure
            assert isinstance(output["schedule"], list)
            assert len(output["schedule"]) == 1
            entry = output["schedule"][0]
            assert "origin" in entry
            assert "destination" in entry
            assert "priority" in entry
            assert "weight" in entry

            # Check total_cost is a number
            assert isinstance(output["total_cost"], (int, float))
        finally:
            os.unlink(csv_path)
            os.unlink(output_path)
