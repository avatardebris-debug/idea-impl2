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


# ── Importer Tests ─────────────────────────────────────────

class TestImporter:
    """Tests for the CSV Importer."""

    def test_import_csv_returns_list_of_dicts(self, sample_csv_file):
        """Importer should return a list of dicts from a valid CSV."""
        result = Importer.import_csv(sample_csv_file)
        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], dict)

    def test_import_csv_has_required_fields(self, sample_csv_file):
        """Each imported shipment should have required fields."""
        result = Importer.import_csv(sample_csv_file)
        for shipment in result:
            assert "origin" in shipment
            assert "destination" in shipment
            assert "priority" in shipment
            assert "weight" in shipment

    def test_import_csv_missing_file_raises(self):
        """Importer should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            Importer.import_csv("/nonexistent/file.csv")

    def test_import_csv_missing_columns_raises(self):
        """Importer should raise ValueError for CSVs missing required columns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
            fh.write("origin,destination,priority\n")
            fh.write("New York,Chicago,standard\n")
            fh.flush()
            tmpname = fh.name
        try:
            with pytest.raises(ValueError):
                Importer.import_csv(tmpname)
        finally:
            os.unlink(tmpname)

    def test_import_csv_handles_missing_dimensions(self):
        """Importer should handle CSVs with missing dimension columns."""
        csv_content = "origin,destination,priority,weight\nNew York,Chicago,standard,10.0\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as fh:
            fh.write(csv_content)
            fh.flush()
            tmpname = fh.name
        try:
            result = Importer.import_csv(tmpname)
            assert len(result) == 1
            assert result[0]["length"] == 0
            assert result[0]["width"] == 0
            assert result[0]["height"] == 0
        finally:
            os.unlink(tmpname)


# ── CostCalculator Tests ───────────────────────────────────

class TestCostCalculator:
    """Tests for the Cost Calculator."""

    def test_calculate_costs_returns_list(self, sample_shipments):
        """calculate_costs should return a list of dicts."""
        result = CostCalculator.calculate_costs(sample_shipments)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_calculate_costs_adds_cost_field(self, sample_shipments):
        """Each result should have a 'cost' field."""
        result = CostCalculator.calculate_costs(sample_shipments)
        for shipment in result:
            assert "cost" in shipment
            assert isinstance(shipment["cost"], (int, float))

    def test_calculate_costs_adds_distance_factor(self, sample_shipments):
        """Each result should have a 'distance_factor' field."""
        result = CostCalculator.calculate_costs(sample_shipments)
        for shipment in result:
            assert "distance_factor" in shipment
            assert isinstance(shipment["distance_factor"], (int, float))

    def test_calculate_costs_empty_input(self):
        """calculate_costs should return empty list for empty input."""
        result = CostCalculator.calculate_costs([])
        assert result == []

    def test_total_cost(self, sample_shipments):
        """total_cost should sum all costs."""
        costed = CostCalculator.calculate_costs(sample_shipments)
        total = CostCalculator.total_cost(costed)
        assert isinstance(total, (int, float))
        assert total > 0

    def test_total_cost_empty_input(self):
        """total_cost should return 0 for empty input."""
        assert CostCalculator.total_cost([]) == 0


# ── ScheduleGenerator Tests ────────────────────────────────

class TestScheduleGenerator:
    """Tests for the Schedule Generator."""

    def test_generate_returns_list(self, sample_shipments):
        """generate should return a list."""
        result = ScheduleGenerator.generate(sample_shipments)
        assert isinstance(result, list)

    def test_generate_preserves_entries(self, sample_shipments):
        """generate should preserve all entries."""
        result = ScheduleGenerator.generate(sample_shipments)
        assert len(result) == len(sample_shipments)

    def test_generate_groups_by_destination(self, sample_shipments):
        """Entries should be grouped by destination."""
        result = ScheduleGenerator.generate(sample_shipments)
        destinations = [e["destination"] for e in result]
        # Chicago, Dallas, New York - sorted alphabetically
        assert destinations == ["Chicago", "Dallas", "New York"]

    def test_generate_sorts_by_priority_within_group(self):
        """Within a destination group, overnight should come before express before standard."""
        entries = [
            {"origin": "A", "destination": "Z", "priority": "standard", "weight": 10},
            {"origin": "B", "destination": "Z", "priority": "overnight", "weight": 20},
            {"origin": "C", "destination": "Z", "priority": "express", "weight": 15},
        ]
        result = ScheduleGenerator.generate(entries)
        priorities = [e["priority"] for e in result]
        assert priorities == ["overnight", "express", "standard"]

    def test_generate_empty_input(self):
        """generate should return empty list for empty/None input."""
        assert ScheduleGenerator.generate([]) == []
        assert ScheduleGenerator.generate(None) == []

    def test_generate_deterministic(self, sample_shipments):
        """generate should produce deterministic output."""
        result1 = ScheduleGenerator.generate(sample_shipments)
        result2 = ScheduleGenerator.generate(sample_shipments)
        assert result1 == result2


# ── CLI Tests ────────────────────────────────────────────

class TestCLI:
    """Tests for the CLI interface."""

    def test_build_parser_returns_parser(self):
        """build_parser should return an ArgumentParser."""
        parser = build_parser()
        assert parser is not None

    def test_main_returns_zero_on_success(self, sample_csv_file):
        """main should return 0 on successful execution."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            tmpname = fh.name
        try:
            exit_code = main(["-i", sample_csv_file, "-o", tmpname])
            assert exit_code == 0
        finally:
            os.unlink(tmpname)

    def test_main_writes_valid_json(self, sample_csv_file):
        """main should write valid JSON to the output file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            tmpname = fh.name
        try:
            main(["-i", sample_csv_file, "-o", tmpname])
            with open(tmpname, "r") as fh:
                data = json.load(fh)
            assert "shipments" in data
            assert "total_cost" in data
            assert "schedule" in data
        finally:
            os.unlink(tmpname)

    def test_main_output_has_correct_structure(self, sample_csv_file):
        """Output JSON should have the correct structure."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            tmpname = fh.name
        try:
            main(["-i", sample_csv_file, "-o", tmpname])
            with open(tmpname, "r") as fh:
                data = json.load(fh)
            assert isinstance(data["shipments"], list)
            assert isinstance(data["total_cost"], (int, float))
            assert isinstance(data["schedule"], list)
            assert len(data["shipments"]) == 3
            assert len(data["schedule"]) == 3
        finally:
            os.unlink(tmpname)

    def test_main_shipments_have_required_fields(self, sample_csv_file):
        """Each shipment in output should have required fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            tmpname = fh.name
        try:
            main(["-i", sample_csv_file, "-o", tmpname])
            with open(tmpname, "r") as fh:
                data = json.load(fh)
            for shipment in data["shipments"]:
                assert "cost" in shipment
                assert "distance_factor" in shipment
                assert "origin" in shipment
                assert "destination" in shipment
                assert "priority" in shipment
                assert "weight" in shipment
        finally:
            os.unlink(tmpname)

    def test_main_schedule_has_required_fields(self, sample_csv_file):
        """Each schedule entry should have required fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            tmpname = fh.name
        try:
            main(["-i", sample_csv_file, "-o", tmpname])
            with open(tmpname, "r") as fh:
                data = json.load(fh)
            for entry in data["schedule"]:
                assert "origin" in entry
                assert "destination" in entry
                assert "priority" in entry
                assert "weight" in entry
        finally:
            os.unlink(tmpname)

    def test_main_returns_one_on_missing_file(self):
        """main should return 1 when input file is missing."""
        exit_code = main(["-i", "/nonexistent/file.csv", "-o", "/tmp/out.json"])
        assert exit_code == 1

    def test_main_verbose_flag(self, sample_csv_file):
        """main should work with verbose flag."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
            tmpname = fh.name
        try:
            exit_code = main(["-i", sample_csv_file, "-o", tmpname, "-v"])
            assert exit_code == 0
        finally:
            os.unlink(tmpname)
