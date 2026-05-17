"""Tests for droppain.exceptions module."""

import pytest

from droppain.exceptions import (
    APIError,
    ConfigurationError,
    DroppainError,
    PublishingError,
    ValidationError,
)


class TestDroppainError:
    """Tests for the base DroppainError class."""

    def test_basic_error(self):
        """Test basic error message."""
        err = DroppainError("Something went wrong")
        assert str(err) == "Something went wrong"

    def test_error_with_details(self):
        """Test error with details dict."""
        err = DroppainError("Error", details={"key": "value"})
        assert "Details: {'key': 'value'}" in str(err)


class TestAPIError:
    """Tests for APIError."""

    def test_basic_api_error(self):
        """Test basic API error."""
        err = APIError("Connection failed", status_code=500, endpoint="/api/products")
        assert "Connection failed" in str(err)
        assert "Status: 500" in str(err)
        assert "Endpoint: /api/products" in str(err)

    def test_api_error_with_details(self):
        """Test API error with details."""
        err = APIError("Rate limited", status_code=429, details={"retry_after": 60})
        assert "Rate limited" in str(err)
        assert "Details: {'retry_after': 60}" in str(err)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_basic_config_error(self):
        """Test basic configuration error."""
        err = ConfigurationError("Missing key", config_key="API_KEY")
        assert "Missing key" in str(err)
        assert "Config key: API_KEY" in str(err)


class TestValidationError:
    """Tests for ValidationError."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        err = ValidationError("Invalid price", field="price", value="-10")
        assert "Invalid price" in str(err)
        assert "Field: price" in str(err)
        assert "Value: -10" in str(err)


class TestPublishingError:
    """Tests for PublishingError."""

    def test_basic_publishing_error(self):
        """Test basic publishing error."""
        err = PublishingError("Failed to post", channel="facebook")
        assert "Failed to post" in str(err)
        assert "Channel: facebook" in str(err)
