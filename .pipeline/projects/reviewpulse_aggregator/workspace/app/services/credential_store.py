"""Credential store service for platform API credentials.

Provides CRUD operations and token management for platform credentials
(stored in the PlatformCredential model).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import PlatformCredential

logger = logging.getLogger(__name__)


class CredentialStore:
    """Service for managing platform credentials."""

    def __init__(self, db: Session):
        self.db = db

    def get_credential(
        self,
        business_id: int,
        platform: str,
    ) -> Optional[PlatformCredential]:
        """Get an active credential for a business and platform."""
        cred = (
            self.db.execute(
                select(PlatformCredential).where(
                    PlatformCredential.business_id == business_id,
                    PlatformCredential.platform == platform,
                    PlatformCredential.is_active == True,
                )
            )
            .scalar_one_or_none()
        )
        return cred

    def get_or_create_credential(
        self,
        business_id: int,
        platform: str,
    ) -> PlatformCredential:
        """Get existing or create a new credential record."""
        cred = self.get_credential(business_id, platform)
        if cred:
            return cred

        cred = PlatformCredential(
            business_id=business_id,
            platform=platform,
            is_active=True,
        )
        self.db.add(cred)
        self.db.flush()
        return cred

    def set_api_key(
        self,
        business_id: int,
        platform: str,
        api_key: str,
        api_secret: Optional[str] = None,
    ) -> PlatformCredential:
        """Set or update API key/secret for a platform."""
        cred = self.get_or_create_credential(business_id, platform)
        cred.api_key = api_key
        cred.api_secret = api_secret
        cred.is_active = True
        self.db.flush()
        return cred

    def set_access_token(
        self,
        business_id: int,
        platform: str,
        access_token: str,
        access_token_expires_at: Optional[datetime] = None,
        refresh_token: Optional[str] = None,
    ) -> PlatformCredential:
        """Set or update OAuth access token for a platform."""
        cred = self.get_or_create_credential(business_id, platform)
        cred.access_token = access_token
        cred.refresh_token = refresh_token
        cred.access_token_expires_at = access_token_expires_at
        cred.is_active = True
        self.db.flush()
        return cred

    def is_token_valid(self, cred: Optional[PlatformCredential]) -> bool:
        """Check if an access token is still valid."""
        if not cred or not cred.access_token:
            return False
        if cred.access_token_expires_at is None:
            return True
        # Consider token valid if it expires in more than 5 minutes
        return cred.access_token_expires_at > datetime.now(timezone.utc) + timedelta(minutes=5)

    def invalidate_token(self, business_id: int, platform: str) -> None:
        """Invalidate (deactivate) a credential."""
        cred = self.get_credential(business_id, platform)
        if cred:
            cred.is_active = False
            self.db.flush()

    def delete_credential(self, business_id: int, platform: str) -> bool:
        """Delete a credential record."""
        cred = self.get_credential(business_id, platform)
        if cred:
            self.db.delete(cred)
            self.db.flush()
            return True
        return False
