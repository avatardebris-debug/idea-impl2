"""Tests for PantryManager."""

import pytest
from datetime import date

from pantrychef_core.database import Database
from pantrychef_core.models import PantryItem
from pantrychef_core.pantry_manager import PantryManager


@pytest.fixture
def db():
    return Database(":memory:")


@pytest.fixture
def pm(db):
    return PantryManager(db)


class TestAddItem:
    def test_add_item_returns_pantry_item(self, pm):
        item = pm.add_item("Eggs", 12, "pieces", "dairy")
        assert isinstance(item, PantryItem)
        assert item.name == "Eggs"
        assert item.quantity == 12
        assert item.unit == "pieces"
        assert item.category == "dairy"
        assert item.id is not None

    def test_add_item_with_expiry(self, pm):
        exp = date(2025, 12, 31)
        item = pm.add_item("Milk", 1, "liter", "dairy", expiry_date=exp)
        assert item.expiry_date == exp

    def test_add_item_without_expiry(self, pm):
        item = pm.add_item("Rice", 5, "kg", "grains")
        assert item.expiry_date is None


class TestRemoveItem:
    def test_remove_existing_item(self, pm):
        item = pm.add_item("Cheese", 100, "grams", "dairy")
        assert pm.remove_item(item.id) is True

    def test_remove_nonexistent_item(self, pm):
        assert pm.remove_item(9999) is False

    def test_remove_item_disappears_from_list(self, pm):
        item = pm.add_item("Yogurt", 500, "grams", "dairy")
        pm.remove_item(item.id)
        items = pm.list_items()
        assert len(items) == 0


class TestListItems:
    def test_list_empty(self, pm):
        assert pm.list_items() == []

    def test_list_multiple_items(self, pm):
        pm.add_item("Eggs", 12, "pieces", "dairy")
        pm.add_item("Bread", 1, "loaf", "grains")
        items = pm.list_items()
        assert len(items) == 2
        names = {i.name for i in items}
        assert "Eggs" in names
        assert "Bread" in names


class TestGetItem:
    def test_get_existing_item(self, pm):
        item = pm.add_item("Butter", 200, "grams", "dairy")
        fetched = pm.get_item(item.id)
        assert fetched is not None
        assert fetched.name == "Butter"

    def test_get_nonexistent_item(self, pm):
        assert pm.get_item(9999) is None
