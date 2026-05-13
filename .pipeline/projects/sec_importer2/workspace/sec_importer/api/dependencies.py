"""Shared dependencies for the API."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from ..storage import get_session
from .config import APIConfig


def get_db() -> Session:
    """Get a database session."""
    return next(get_session())


def get_config() -> APIConfig:
    """Get the API configuration."""
    return APIConfig()
