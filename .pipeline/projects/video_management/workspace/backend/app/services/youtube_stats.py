"""YouTube channel stats service."""

import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from ..models import YouTubeChannel
from ..schemas import ChannelStatsResponse


class YouTubeStatsService:
    """Service for fetching and managing YouTube channel statistics."""

    def __init__(self, db: Session):
        self.db = db
        self.channel = db.query(YouTubeChannel).first()
        if not self.channel or not self.channel.is_connected:
            raise ValueError("No YouTube channel connected.")

    async def get_stats(self) -> ChannelStatsResponse:
        """Fetch current channel statistics from YouTube."""
        access_token = self._refresh_tokens()
        if not access_token:
            raise ValueError("Token refresh failed.")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "statistics,snippet", "id": self.channel.channel_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            channel_data = resp.json()["items"][0]

        stats = channel_data.get("statistics", {})

        # Update stored stats
        self.channel.channel_stats = {
            "subscriberCount": stats.get("subscriberCount"),
            "viewCount": stats.get("viewCount"),
            "videoCount": stats.get("videoCount"),
            "hiddenSubscriberCount": stats.get("hiddenSubscriberCount"),
        }
        self.db.commit()

        return ChannelStatsResponse(
            subscriber_count=int(stats.get("subscriberCount", 0)) if stats.get("subscriberCount") else None,
            view_count=int(stats.get("viewCount", 0)) if stats.get("viewCount") else None,
            video_count=int(stats.get("videoCount", 0)) if stats.get("videoCount") else None,
            hidden_subscriber_count=stats.get("hiddenSubscriberCount"),
            last_updated=datetime.now(timezone.utc),
        )

    def _refresh_tokens(self) -> str | None:
        """Refresh access token if needed."""
        if not self.channel.refresh_token or not self.channel.token_expiry:
            return self.channel.access_token

        expiry = self.channel.token_expiry
        if expiry.tzinfo is None:
            from datetime import timezone
            expiry = expiry.replace(tzinfo=timezone.utc)
        
        if expiry < datetime.now(timezone.utc) - __import__("datetime").timedelta(minutes=5):
            async def _do_refresh():
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "grant_type": "refresh_token",
                            "client_id": __import__("os").environ.get("GOOGLE_CLIENT_ID", ""),
                            "client_secret": __import__("os").environ.get("GOOGLE_CLIENT_SECRET", ""),
                            "refresh_token": self.channel.refresh_token,
                        },
                    )
                    resp.raise_for_status()
                    return resp.json()

            token_data = asyncio.run(_do_refresh())
            self.channel.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                self.channel.refresh_token = token_data["refresh_token"]
            self.channel.token_expiry = datetime.now(timezone.utc) + __import__("datetime").timedelta(seconds=token_data.get("expires_in", 3600))
            self.db.commit()

        return self.channel.access_token
