"""Tests for droppain.cli module."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from droppain.cli import (
    create_parser,
    cmd_health_check,
    cmd_create_plan,
    cmd_execute,
    main,
)
from droppain.planner import CampaignPlan, ChannelConfig, ContentBrief
from droppain.models import Product, Variant


class TestCreateParser:
    """Tests for create_parser."""

    def test_parser_created(self):
        """Test that parser is created."""
        parser = create_parser()
        assert parser is not None

    def test_subcommands_exist(self):
        """Test that subcommands are registered."""
        parser = create_parser()
        # Parse help to verify subcommands
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])


class TestCmdHealthCheck:
    """Tests for cmd_health_check."""

    def test_health_check_no_json(self, capsys):
        """Test health check without JSON output."""
        args = type("Args", (), {"fix": False, "json": False})()
        result = cmd_health_check(args)
        captured = capsys.readouterr()
        assert result == 0  # No errors expected

    def test_health_check_json(self, capsys):
        """Test health check with JSON output."""
        args = type("Args", (), {"fix": False, "json": True})()
        result = cmd_health_check(args)
        captured = capsys.readouterr()
        assert result == 0
        # Should be valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, list)


class TestCmdCreatePlan:
    """Tests for cmd_create_plan."""

    def test_create_plan_no_products(self, capsys):
        """Test create plan with no products file."""
        args = type("Args", (), {"products": None, "name": None, "budget": None, "json": False})()
        result = cmd_create_plan(args)
        assert result == 1

    def test_create_plan_with_products(self, capsys):
        """Test create plan with products file."""
        # Create temp products file
        products_data = [
            {
                "id": "1",
                "title": "Test Product",
                "description": "A test product",
                "price": 29.99,
                "variants": [{"id": "v1", "title": "Default", "price": 29.99, "sku": "SKU1"}],
                "tags": ["test"],
            }
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(products_data, f)
            temp_path = f.name

        try:
            args = type("Args", (), {
                "products": temp_path,
                "name": "Test Campaign",
                "budget": 100.0,
                "json": False,
            })()
            result = cmd_create_plan(args)
            assert result == 0
        finally:
            os.unlink(temp_path)

    def test_create_plan_json_output(self, capsys):
        """Test create plan with JSON output."""
        products_data = [
            {
                "id": "1",
                "title": "Test Product",
                "description": "A test product",
                "price": 29.99,
                "variants": [{"id": "v1", "title": "Default", "price": 29.99, "sku": "SKU1"}],
                "tags": ["test"],
            }
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(products_data, f)
            temp_path = f.name

        try:
            args = type("Args", (), {
                "products": temp_path,
                "name": "Test Campaign",
                "budget": 100.0,
                "json": True,
            })()
            result = cmd_create_plan(args)
            captured = capsys.readouterr()
            assert result == 0
            data = json.loads(captured.out)
            assert "campaign_name" in data
        finally:
            os.unlink(temp_path)


class TestCmdExecute:
    """Tests for cmd_execute."""

    def test_execute_with_plan(self, capsys):
        """Test execute with a plan file."""
        plan_data = {
            "campaign_name": "Test Campaign",
            "total_budget": 100.0,
            "channels": [
                {
                    "platform": "facebook",
                    "frequency": "daily",
                    "budget": 50.0,
                    "target_audience": "test",
                }
            ],
            "content_briefs": [
                {
                    "title": "Test Brief",
                    "copy": "Test copy",
                    "platform": "facebook",
                    "target_audience": "test",
                }
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(plan_data, f)
            temp_path = f.name

        try:
            args = type("Args", (), {
                "plan": temp_path,
                "json": False,
            })()
            result = cmd_execute(args)
            assert result == 0
        finally:
            os.unlink(temp_path)


class TestMain:
    """Tests for main function."""

    def test_main_no_command(self, capsys):
        """Test main with no command."""
        result = main([])
        assert result == 1

    def test_main_health_command(self, capsys):
        """Test main with health command."""
        result = main(["health"])
        assert result == 0

    def test_main_plan_command(self, capsys):
        """Test main with plan command (should fail without products)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["plan"])
        assert exc_info.value.code == 2  # argparse error for missing required args
