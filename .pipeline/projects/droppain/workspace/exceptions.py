"""Custom exception classes for droppain."""

from typing import Any, Dict, Optional


class DroppainError(Exception):
    """Base exception for all droppain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class APIError(DroppainError):
    """Exception raised for API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.status_code = status_code
        self.endpoint = endpoint

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class ConfigurationError(DroppainError):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.config_key = config_key

    def __str__(self) -> str:
        parts = [self.message]
        if self.config_key:
            parts.append(f"Config key: {self.config_key}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class ValidationError(DroppainError):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.field = field
        self.value = value

    def __str__(self) -> str:
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.value:
            parts.append(f"Value: {self.value}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)


class PublishingError(DroppainError):
    """Exception raised when publishing to a channel fails."""

    def __init__(self, message: str, channel: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.channel = channel

    def __str__(self) -> str:
        parts = [self.message]
        if self.channel:
            parts.append(f"Channel: {self.channel}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " - ".join(parts)
