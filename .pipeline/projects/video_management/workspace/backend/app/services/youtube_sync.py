"""YouTube sync service for pulling videos from a connected channel."""

import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from ..models import YouTubeChannel, Video, VideoStatus, TableMetadata
from ..schemas import SyncResponse


class YouTubeSyncService:
    """Service for syncing videos from YouTube."""

    def __init__(self, db: Session):
        self.db = db
        self.channel = db.query(YouTubeChannel).first()
        if not self.channel or not self.channel.is_connected:
            raise ValueError("No YouTube channel connected.")

    async def sync_all_videos(self) -> SyncResponse:
        """Sync all videos from the connected YouTube channel."""
        access_token = self._refresh_tokens()
        if not access_token:
            raise ValueError("Token refresh failed.")

        synced = 0
        failed = 0
        total = 0

        # Get uploads playlist ID
        async with httpx.AsyncClient() as client:
            channel_resp = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "contentDetails", "id": self.channel.channel_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            channel_resp.raise_for_status()
            uploads_playlist_id = channel_resp.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            page_token = None
            while True:
                playlist_resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/playlistItems",
                    params={
                        "part": "snippet,contentDetails",
                        "playlistId": uploads_playlist_id,
                        "maxResults": 50,
                    },
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                playlist_resp.raise_for_status()
                playlist_data = playlist_resp.json()

                for item in playlist_data.get("items", []):
                    video_id = item["snippet"]["resourceId"]["videoId"]
                    video_resp = await client.get(
                        "https://www.googleapis.com/youtube/v3/videos",
                        params={"part": "snippet,statistics,contentDetails", "id": video_id},
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    video_resp.raise_for_status()
                    video_data = video_resp.json()["items"][0]

                    try:
                        self._upsert_video(video_data)
                        synced += 1
                    except Exception as e:
                        failed += 1
                        self.channel.sync_error = f"Failed to sync video {video_id}: {str(e)}"

                    total += 1

                page_token = playlist_data.get("nextPageToken")
                if not page_token:
                    break

        # Update sync metadata
        self.channel.last_sync_at = datetime.now(timezone.utc)
        self.channel.sync_error = None
        self.db.commit()

        return SyncResponse(total=total, synced=synced, failed=failed, last_sync_at=self.channel.last_sync_at)

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

    def _upsert_video(self, video_data: dict):
        """Upsert a video from YouTube data."""
        snippet = video_data["snippet"]
        statistics = video_data.get("statistics", {})
        thumbnails = snippet.get("thumbnails", {})
        high_thumb = thumbnails.get("high", {}) or thumbnails.get("default", {})

        existing = self.db.query(Video).filter_by(youtube_video_id=video_data["id"]).first()
        if existing:
            existing.title = snippet.get("title", existing.title)
            existing.description = snippet.get("description", existing.description)
            existing.thumbnail_url = high_thumb.get("url", existing.thumbnail_url)
            existing.tags = snippet.get("tags", [])
            existing.updated_at = datetime.now(timezone.utc)
        else:
            table = self.db.query(TableMetadata).first()
            if not table:
                raise ValueError("No videos table found.")

            new_video = Video(
                table_id=table.id,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                status=VideoStatus.PUBLISHED,
                tags=snippet.get("tags", []),
                thumbnail_url=high_thumb.get("url", ""),
                youtube_video_id=video_data["id"],
                publish_date=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")).replace(tzinfo=None),
            )
            self.db.add(new_video)
