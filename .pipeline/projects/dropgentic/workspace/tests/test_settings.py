"""Tests for Settings configuration."""

import pytest
from dropgentic.config.settings import Settings


class TestSettingsInit:
    """Test Settings initialization."""

    def test_default_values(self):
        settings = Settings()
        assert settings.app_name == "DropGentic"
        assert settings.version == "0.1.0"
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.data_dir == "./data"
        assert settings.cache_dir == "./cache"
        assert settings.supplier_api_keys == {}
        assert settings.default_currency == "USD"
        assert settings.default_platform_fee_pct == 0.15
        assert settings.default_payment_processing_fee_pct == 0.029
        assert settings.default_fixed_payment_fee == 0.30
        assert settings.min_net_margin_pct == 5.0
        assert settings.max_lead_time_days == 30
        assert settings.min_supplier_rating == 0.0
        assert settings.min_gross_margin_pct == 20.0
        assert settings.max_products_per_plan == 100
        assert settings.max_suppliers_per_plan == 50
        assert settings.enable_cache is True
        assert settings.cache_ttl_seconds == 3600

    def test_custom_values(self):
        settings = Settings(
            app_name="CustomApp",
            log_level="DEBUG",
            debug=True,
            data_dir="/custom/data",
            default_currency="EUR",
            min_net_margin_pct=10.0,
            max_lead_time_days=14,
        )
        assert settings.app_name == "CustomApp"
        assert settings.log_level == "DEBUG"
        assert settings.debug is True
        assert settings.data_dir == "/custom/data"
        assert settings.default_currency == "EUR"
        assert settings.min_net_margin_pct == 10.0
        assert settings.max_lead_time_days == 14


class TestSettingsSerialization:
    """Test Settings serialization."""

    def test_to_dict(self):
        settings = Settings()
        d = settings.to_dict()
        assert d["app_name"] == "DropGentic"
        assert d["version"] == "0.1.0"
        assert d["log_level"] == "INFO"
        assert d["default_currency"] == "USD"

    def test_from_dict(self):
        data = {
            "app_name": "CustomApp",
            "version": "1.0.0",
            "log_level": "DEBUG",
            "debug": True,
            "data_dir": "/custom/data",
            "default_currency": "GBP",
            "min_net_margin_pct": 15.0,
        }
        settings = Settings.from_dict(data)
        assert settings.app_name == "CustomApp"
        assert settings.version == "1.0.0"
        assert settings.log_level == "DEBUG"
        assert settings.debug is True
        assert settings.data_dir == "/custom/data"
        assert settings.default_currency == "GBP"
        assert settings.min_net_margin_pct == 15.0

    def test_round_trip(self):
        settings = Settings(
            app_name="TestApp",
            log_level="WARNING",
            debug=True,
            default_currency="JPY",
            min_net_margin_pct=8.0,
        )
        d = settings.to_dict()
        settings2 = Settings.from_dict(d)
        assert settings2.app_name == settings.app_name
        assert settings2.log_level == settings.log_level
        assert settings2.debug == settings.debug
        assert settings2.default_currency == settings.default_currency
        assert settings2.min_net_margin_pct == settings.min_net_margin_pct


class TestSettingsValidation:
    """Test Settings validation."""

    def test_negative_min_net_margin(self):
        with pytest.raises(ValueError, match="min_net_margin_pct must be non-negative"):
            Settings(min_net_margin_pct=-1.0)

    def test_zero_min_net_margin(self):
        # Should not raise
        settings = Settings(min_net_margin_pct=0.0)
        assert settings.min_net_margin_pct == 0.0

    def test_negative_max_lead_time(self):
        with pytest.raises(ValueError, match="max_lead_time_days must be positive"):
            Settings(max_lead_time_days=-1)

    def test_zero_max_lead_time(self):
        # Should not raise
        settings = Settings(max_lead_time_days=0)
        assert settings.max_lead_time_days == 0

    def test_negative_min_supplier_rating(self):
        with pytest.raises(ValueError, match="min_supplier_rating must be non-negative"):
            Settings(min_supplier_rating=-1.0)

    def test_negative_min_gross_margin(self):
        with pytest.raises(ValueError, match="min_gross_margin_pct must be non-negative"):
            Settings(min_gross_margin_pct=-1.0)

    def test_zero_min_gross_margin(self):
        # Should not raise
        settings = Settings(min_gross_margin_pct=0.0)
        assert settings.min_gross_margin_pct == 0.0

    def test_negative_max_products(self):
        with pytest.raises(ValueError, match="max_products_per_plan must be positive"):
            Settings(max_products_per_plan=-1)

    def test_zero_max_products(self):
        # Should not raise
        settings = Settings(max_products_per_plan=0)
        assert settings.max_products_per_plan == 0

    def test_negative_max_suppliers(self):
        with pytest.raises(ValueError, match="max_suppliers_per_plan must be positive"):
            Settings(max_suppliers_per_plan=-1)

    def test_zero_max_suppliers(self):
        # Should not raise
        settings = Settings(max_suppliers_per_plan=0)
        assert settings.max_suppliers_per_plan == 0

    def test_negative_cache_ttl(self):
        with pytest.raises(ValueError, match="cache_ttl_seconds must be non-negative"):
            Settings(cache_ttl_seconds=-1)

    def test_zero_cache_ttl(self):
        # Should not raise
        settings = Settings(cache_ttl_seconds=0)
        assert settings.cache_ttl_seconds == 0


class TestSettingsRepr:
    """Test Settings repr."""

    def test_repr(self):
        settings = Settings(app_name="TestApp")
        r = repr(settings)
        assert "TestApp" in r
        assert "0.1.0" in r
