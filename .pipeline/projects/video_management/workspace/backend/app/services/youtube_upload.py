"""YouTube upload service for publishing videos to YouTube."""

import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from ..models import YouTubeChannel
from ..schemas import YouTubeUploadResponse
from ..config import settings


class YouTubeUploadService:
    """Service for uploading videos to YouTube."""

    def __init__(self, db: Session):
        self.db = db
        self.channel = db.query(YouTubeChannel).first()
        if not self.channel or not self.channel.is_connected:
            raise ValueError("No YouTube channel connected.")

    async def upload_video(
        self,
        title: str,
        description: str = "",
        status: str = "unlisted",
        tags: list[str] | None = None,
        publish_at: datetime | None = None,
        thumbnail_url: str | None = None,
    ) -> YouTubeUploadResponse:
        """Upload a video to YouTube."""
        access_token = self._refresh_tokens()
        if not access_token:
            return YouTubeUploadResponse(
                success=False,
                youtube_video_id=None,
                message="Token refresh failed.",
                error="No valid access token.",
            )

        valid_statuses = {"public", "private", "unlisted"}
        if status not in valid_statuses:
            return YouTubeUploadResponse(
                success=False,
                youtube_video_id=None,
                message="Invalid status.",
                error=f"Status must be one of {valid_statuses}",
            )

        try:
            async with httpx.AsyncClient() as client:
                video_resource = {
                    "snippet": {
                        "title": title,
                        "description": description,
                        "tags": tags or [],
                    },
                    "status": {
                        "privacyStatus": status,
                    }
                }

                if publish_at:
                    video_resource["status"]["publishAt"] = publish_at.isoformat()

                if thumbnail_url:
                    video_resource["snippet"]["thumbnails"] = {
                        "high": {"url": thumbnail_url}
                    }

                resp = await client.post(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={"part": "snippet,status"},
                    json=video_resource,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                resp.raise_for_status()
                result = resp.json()

            return YouTubeUploadResponse(
                success=True,
                youtube_video_id=result.get("id"),
                message="Video uploaded successfully.",
            )

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.text
            except Exception:
                error_detail = str(e)
            return YouTubeUploadResponse(
                success=False,
                youtube_video_id=None,
                message="YouTube API error.",
                error=error_detail,
            )
        except Exception as e:
            return YouTubeUploadResponse(
                success=False,
                youtube_video_id=None,
                message="Failed to upload video.",
                error=str(e),
            )

    def _refresh_tokens(self) -> str | None:
        """Refresh access token if needed."""
        if not self.channel.refresh_token or not self.channel.token_expiry:
            return self.channel.access_token

        if self.channel.token_expiry < datetime.now(timezone.utc) - __import__("datetime").timedelta(minutes=5):
            async def _do_refresh():
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "grant_type": "refresh_token",
                            "client_id": settings.google_client_id,
                            "client_secret": settings.google_client_secret,
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
