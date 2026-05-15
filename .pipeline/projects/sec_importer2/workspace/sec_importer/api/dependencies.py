"""Shared dependencies for the API."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from ..storage import get_session
from .config import APIConfig


from typing import Generator

def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def get_config() -> APIConfig:
    """Get the API configuration."""
    return APIConfig()
