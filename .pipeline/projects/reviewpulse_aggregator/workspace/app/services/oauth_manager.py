"""OAuth2 token management helpers for platform integrations.

Provides utilities for token refresh, URL construction, and platform-specific
OAuth grant flows.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from app.services.credential_store import CredentialStore

logger = logging.getLogger(__name__)


class OAuthManager:
    """Handles OAuth2 token refresh and grant flows for various platforms."""

    # Platform-specific OAuth endpoints
    OAUTH_ENDPOINTS = {
        "yelp": {
            "token_url": "https://api.yelp.com/oauth2/token",
            "authorize_url": "https://www.yelp.com/oauth2/authorize",
        },
        "facebook": {
            "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
            "authorize_url": "https://www.facebook.com/v18.0/dialog/oauth",
        },
    }

    def __init__(self, credential_store: CredentialStore):
        self.credential_store = credential_store

    def refresh_token(
        self,
        business_id: int,
        platform: str,
    ) -> Optional[str]:
        """Refresh an OAuth2 access token for a platform.

        Returns the new access token, or None on failure.
        """
        cred = self.credential_store.get_credential(business_id, platform)
        if not cred or not cred.refresh_token:
            logger.warning(f"No refresh token available for {platform} (business {business_id})")
            return None

        if not cred.api_key or not cred.api_secret:
            logger.warning(f"Missing API key/secret for {platform} (business {business_id})")
            return None

        endpoint = self.OAUTH_ENDPOINTS.get(platform)
        if not endpoint:
            logger.error(f"Unknown platform for OAuth: {platform}")
            return None

        try:
            response = requests.post(
                endpoint["token_url"],
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": cred.refresh_token,
                    "client_id": cred.api_key,
                    "client_secret": cred.api_secret,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            new_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            new_refresh_token = data.get("refresh_token", cred.refresh_token)

            if new_token:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                self.credential_store.set_access_token(
                    business_id=business_id,
                    platform=platform,
                    access_token=new_token,
                    access_token_expires_at=expires_at,
                    refresh_token=new_refresh_token,
                )
                logger.info(f"Token refreshed for {platform} (business {business_id})")
                return new_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh failed for {platform}: {e}")
            self.credential_store.invalidate_token(business_id, platform)

        return None

    def get_valid_token(
        self,
        business_id: int,
        platform: str,
    ) -> Optional[str]:
        """Get a valid access token, refreshing if necessary."""
        cred = self.credential_store.get_credential(business_id, platform)

        if cred and self.credential_store.is_token_valid(cred):
            return cred.access_token

        # Token missing or expired — try to refresh
        if cred and cred.refresh_token:
            new_token = self.refresh_token(business_id, platform)
            return new_token

        return None

    def get_authorize_url(
        self,
        platform: str,
        redirect_uri: str,
        state: str,
    ) -> Optional[str]:
        """Generate an OAuth authorization URL for a platform."""
        endpoint = self.OAUTH_ENDPOINTS.get(platform)
        if not endpoint:
            return None

        return (
            f"{endpoint['authorize_url']}?"
            f"client_id={endpoint['client_id'] if hasattr(endpoint, 'client_id') else ''}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&state={state}"
        )
