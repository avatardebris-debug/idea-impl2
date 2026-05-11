"""YouTube integration service for video management platform.

Handles YouTube API interactions including:
- Video upload and publishing
- Thumbnail management
- Playlist management
- Video scheduling
- Analytics retrieval
- Channel management
"""

import os
import json
import logging
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class YouTubeAuthMethod(Enum):
    API_KEY = "api_key"
    OAUTH = "oauth"


@dataclass
class YouTubeConfig:
    """YouTube API configuration."""
    channel_id: str = ""
    api_key: str = ""
    access_token: str = ""
    refresh_token: str = ""
    token_expiry: Optional[datetime] = None
    is_connected: bool = False
    auth_method: YouTubeAuthMethod = YouTubeAuthMethod.API_KEY


@dataclass
class YouTubeVideoStats:
    """YouTube video statistics."""
    video_id: str
    title: str
    views: int = 0
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    shares: int = 0
    estimated_revenue: float = 0.0
    average_view_duration: str = ""
    audience_retention: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class YouTubeAnalytics:
    """YouTube analytics data."""
    total_videos: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_revenue: float = 0.0
    average_views_per_video: float = 0.0
    top_videos: list[YouTubeVideoStats] = field(default_factory=list)
    daily_stats: list[dict] = field(default_factory=list)
    subscriber_count: int = 0
    subscriber_growth: float = 0.0


@dataclass
class YouTubePlaylist:
    """YouTube playlist information."""
    playlist_id: str
    title: str
    description: str = ""
    video_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class YouTubeUploadResult:
    """Result of a YouTube video upload."""
    video_id: str
    status: str
    error: Optional[str] = None
    upload_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class YouTubeService:
    """Service for interacting with YouTube API."""

    def __init__(self, config: YouTubeConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def test_connection(self) -> bool:
        """Test the YouTube API connection."""
        try:
            if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                response = await self.client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={
                        "part": "snippet",
                        "mine": "true",
                        "key": self.config.api_key,
                    },
                )
            else:
                if not self._is_token_valid():
                    await self._refresh_access_token()

                headers = {
                    "Authorization": f"Bearer {self.config.access_token}",
                }
                response = await self.client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "snippet", "mine": "true"},
                    headers=headers,
                )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"YouTube connection test failed: {e}")
            return False

    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        category_id: str = "22",  # People & Blogs
        privacy_status: str = "private",
        schedule_time: Optional[datetime] = None,
        thumbnail_path: Optional[str] = None,
    ) -> YouTubeUploadResult:
        """Upload a video to YouTube.

        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            tags: Video tags
            category_id: YouTube category ID
            privacy_status: Video privacy status (private, public, unlisted)
            schedule_time: Optional scheduled publish time
            thumbnail_path: Optional path to thumbnail image

        Returns:
            YouTubeUploadResult with video ID and status
        """
        try:
            # Step 1: Initialize upload
            upload_url = await self._initialize_upload(
                title=title,
                description=description,
                tags=tags or [],
                category_id=category_id,
                privacy_status=privacy_status,
                schedule_time=schedule_time,
            )

            if not upload_url:
                return YouTubeUploadResult(
                    video_id="",
                    status="error",
                    error="Failed to initialize upload",
                )

            # Step 2: Upload video file
            video_id = await self._upload_video_file(upload_url, video_path)

            if not video_id:
                return YouTubeUploadResult(
                    video_id="",
                    status="error",
                    error="Failed to upload video file",
                )

            # Step 3: Upload thumbnail if provided
            thumbnail_url = None
            if thumbnail_path:
                thumbnail_url = await self._upload_thumbnail(video_id, thumbnail_path)

            return YouTubeUploadResult(
                video_id=video_id,
                status="success",
                upload_url=upload_url,
                thumbnail_url=thumbnail_url,
            )

        except Exception as e:
            logger.error(f"Video upload failed: {e}")
            return YouTubeUploadResult(
                video_id="",
                status="error",
                error=str(e),
            )

    async def get_video_stats(self, video_id: str) -> YouTubeVideoStats:
        """Get statistics for a specific video."""
        try:
            if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                response = await self.client.get(
                    f"https://www.googleapis.com/youtube/v3/videos",
                    params={
                        "part": "statistics,snippet",
                        "id": video_id,
                        "key": self.config.api_key,
                    },
                )
            else:
                if not self._is_token_valid():
                    await self._refresh_access_token()

                headers = {
                    "Authorization": f"Bearer {self.config.access_token}",
                }
                response = await self.client.get(
                    f"https://www.googleapis.com/youtube/v3/videos",
                    params={"part": "statistics,snippet", "id": video_id},
                    headers=headers,
                )

            if response.status_code != 200:
                logger.error(f"Failed to get video stats: {response.text}")
                return YouTubeVideoStats(video_id=video_id, title="Unknown")

            data = response.json()
            if not data.get("items"):
                return YouTubeVideoStats(video_id=video_id, title="Unknown")

            item = data["items"][0]
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})

            return YouTubeVideoStats(
                video_id=video_id,
                title=snippet.get("title", "Unknown"),
                views=int(statistics.get("viewCount", 0)),
                likes=int(statistics.get("likeCount", 0)),
                dislikes=int(statistics.get("dislikeCount", 0)),
                comments=int(statistics.get("commentCount", 0)),
                last_updated=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Failed to get video stats: {e}")
            return YouTubeVideoStats(video_id=video_id, title="Unknown")

    async def get_channel_analytics(self, time_range: str = "30d") -> YouTubeAnalytics:
        """Get channel analytics for a specified time range."""
        try:
            # Get channel info
            channel_stats = await self._get_channel_stats()

            # Get video statistics
            videos = await self._get_channel_videos()

            # Calculate totals
            total_views = 0
            total_likes = 0
            total_comments = 0
            total_revenue = 0.0
            top_videos = []

            for video in videos:
                stats = await self.get_video_stats(video["id"])
                total_views += stats.views
                total_likes += stats.likes
                total_comments += stats.comments
                # Estimate revenue (rough estimate: $1-5 per 1000 views)
                total_revenue += (stats.views / 1000) * 2.0
                top_videos.append(stats)

            # Sort by views and get top 10
            top_videos.sort(key=lambda v: v.views, reverse=True)
            top_videos = top_videos[:10]

            # Calculate daily stats
            daily_stats = await self._get_daily_stats(time_range)

            return YouTubeAnalytics(
                total_videos=len(videos),
                total_views=total_views,
                total_likes=total_likes,
                total_comments=total_comments,
                total_revenue=total_revenue,
                average_views_per_video=total_views / max(len(videos), 1),
                top_videos=top_videos,
                daily_stats=daily_stats,
                subscriber_count=channel_stats.get("subscriberCount", 0),
                subscriber_growth=channel_stats.get("subscriberGrowth", 0.0),
            )

        except Exception as e:
            logger.error(f"Failed to get channel analytics: {e}")
            return YouTubeAnalytics()

    async def create_playlist(self, title: str, description: str = "") -> Optional[str]:
        """Create a new YouTube playlist.

        Returns:
            Playlist ID if successful, None otherwise
        """
        try:
            if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                response = await self.client.post(
                    "https://www.googleapis.com/youtube/v3/playlists",
                    params={
                        "part": "snippet,contentDetails",
                        "key": self.config.api_key,
                    },
                    json={
                        "snippet": {
                            "title": title,
                            "description": description,
                        },
                        "contentDetails": {
                            "privacyStatus": "private",
                        },
                    },
                )
            else:
                if not self._is_token_valid():
                    await self._refresh_access_token()

                headers = {
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json",
                }
                response = await self.client.post(
                    "https://www.googleapis.com/youtube/v3/playlists",
                    params={"part": "snippet,contentDetails"},
                    headers=headers,
                    json={
                        "snippet": {
                            "title": title,
                            "description": description,
                        },
                        "contentDetails": {
                            "privacyStatus": "private",
                        },
                    },
                )

            if response.status_code == 200:
                data = response.json()
                return data["id"]

            logger.error(f"Failed to create playlist: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            return None

    async def add_video_to_playlist(self, playlist_id: str, video_id: str) -> bool:
        """Add a video to a YouTube playlist."""
        try:
            if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                response = await self.client.post(
                    "https://www.googleapis.com/youtube/v3/playlistItems",
                    params={
                        "part": "snippet",
                        "key": self.config.api_key,
                    },
                    json={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id,
                            },
                        },
                    },
                )
            else:
                if not self._is_token_valid():
                    await self._refresh_access_token()

                headers = {
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json",
                }
                response = await self.client.post(
                    "https://www.googleapis.com/youtube/v3/playlistItems",
                    params={"part": "snippet"},
                    headers=headers,
                    json={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id,
                            },
                        },
                    },
                )

            return response.status_code in (200, 201)

        except Exception as e:
            logger.error(f"Failed to add video to playlist: {e}")
            return False

    async def get_playlists(self) -> list[YouTubePlaylist]:
        """Get all playlists for the connected channel."""
        try:
            if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                response = await self.client.get(
                    "https://www.googleapis.com/youtube/v3/playlists",
                    params={
                        "part": "snippet,contentDetails",
                        "mine": "true",
                        "key": self.config.api_key,
                    },
                )
            else:
                if not self._is_token_valid():
                    await self._refresh_access_token()

                headers = {
                    "Authorization": f"Bearer {self.config.access_token}",
                }
                response = await self.client.get(
                    "https://www.googleapis.com/youtube/v3/playlists",
                    params={"part": "snippet,contentDetails", "mine": "true"},
                    headers=headers,
                )

            if response.status_code != 200:
                logger.error(f"Failed to get playlists: {response.text}")
                return []

            data = response.json()
            playlists = []

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})

                playlists.append(YouTubePlaylist(
                    playlist_id=item["id"],
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    video_count=content_details.get("itemCount", 0),
                    created_at=datetime.fromisoformat(snippet.get("publishedAt", "").replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(snippet.get("publishedAt", "").replace("Z", "+00:00")),
                ))

            return playlists

        except Exception as e:
            logger.error(f"Failed to get playlists: {e}")
            return []

    async def _initialize_upload(
        self,
        title: str,
        description: str,
        tags: list[str],
        category_id: str,
        privacy_status: str,
        schedule_time: Optional[datetime] = None,
    ) -> Optional[str]:
        """Initialize a resumable upload session."""
        try:
            snippet = {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            }

            status = {
                "privacyStatus": privacy_status,
            }

            if schedule_time:
                status["scheduledPublishTime"] = schedule_time.isoformat()

            if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                response = await self.client.post(
                    "https://www.googleapis.com/upload/youtube/v3/videos",
                    params={
                        "part": "snippet,status",
                        "key": self.config.api_key,
                    },
                    json={
                        "snippet": snippet,
                        "status": status,
                    },
                )
            else:
                if not self._is_token_valid():
                    await self._refresh_access_token()

                headers = {
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json",
                    "X-Upload-Content-Type": "video/*",
                    "X-Upload-Content-Length": "0",  # Will be set during actual upload
                }
                response = await self.client.post(
                    "https://www.googleapis.com/upload/youtube/v3/videos",
                    params={"part": "snippet,status"},
                    headers=headers,
                    json={
                        "snippet": snippet,
                        "status": status,
                    },
                )

            if response.status_code == 200:
                return response.json().get("id")
            elif response.status_code == 201:
                # Resumable upload - get upload URL from headers
                upload_url = response.headers.get("location")
                return upload_url
            else:
                logger.error(f"Failed to initialize upload: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Failed to initialize upload: {e}")
            return None

    async def _upload_video_file(self, upload_url: str, video_path: str) -> Optional[str]:
        """Upload video file to YouTube."""
        try:
            with open(video_path, "rb") as f:
                video_data = f.read()

            headers = {
                "Content-Length": str(len(video_data)),
                "Content-Type": "application/octet-stream",
            }

            response = await self.client.put(
                upload_url,
                headers=headers,
                content=video_data,
            )

            if response.status_code in (200, 201):
                data = response.json()
                return data.get("id")

            logger.error(f"Failed to upload video file: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Failed to upload video file: {e}")
            return None

    async def _upload_thumbnail(self, video_id: str, thumbnail_path: str) -> Optional[str]:
        """Upload thumbnail for a video."""
        try:
            with open(thumbnail_path, "rb") as f:
                thumbnail_data = f.read()

            if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                response = await self.client.post(
                    f"https://www.googleapis.com/upload/youtube/v3/videos/{video_id}/thumbnail",
                    params={"key": self.config.api_key},
                    content=thumbnail_data,
                )
            else:
                if not self._is_token_valid():
                    await self._refresh_access_token()

                headers = {
                    "Authorization": f"Bearer {self.config.access_token}",
                }
                response = await self.client.post(
                    f"https://www.googleapis.com/upload/youtube/v3/videos/{video_id}/thumbnail",
                    headers=headers,
                    content=thumbnail_data,
                )

            if response.status_code == 200:
                return f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

            logger.error(f"Failed to upload thumbnail: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Failed to upload thumbnail: {e}")
            return None

    async def _get_channel_stats(self) -> dict:
        """Get channel statistics."""
        try:
            if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                response = await self.client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={
                        "part": "statistics,snippet",
                        "mine": "true",
                        "key": self.config.api_key,
                    },
                )
            else:
                if not self._is_token_valid():
                    await self._refresh_access_token()

                headers = {
                    "Authorization": f"Bearer {self.config.access_token}",
                }
                response = await self.client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "statistics,snippet", "mine": "true"},
                    headers=headers,
                )

            if response.status_code != 200:
                return {}

            data = response.json()
            if not data.get("items"):
                return {}

            item = data["items"][0]
            statistics = item.get("statistics", {})

            return {
                "subscriberCount": int(statistics.get("subscriberCount", 0)),
                "videoCount": int(statistics.get("videoCount", 0)),
                "viewCount": int(statistics.get("viewCount", 0)),
            }

        except Exception as e:
            logger.error(f"Failed to get channel stats: {e}")
            return {}

    async def _get_channel_videos(self) -> list[dict]:
        """Get all videos for the connected channel."""
        try:
            videos = []
            page_token = None

            while True:
                if self.config.auth_method == YouTubeAuthMethod.API_KEY:
                    response = await self.client.get(
                        "https://www.googleapis.com/youtube/v3/search",
                        params={
                            "part": "snippet",
                            "channelId": self.config.channel_id,
                            "type": "video",
                            "maxResults": 50,
                            "key": self.config.api_key,
                            "pageToken": page_token,
                        },
                    )
                else:
                    if not self._is_token_valid():
                        await self._refresh_access_token()

                    headers = {
                        "Authorization": f"Bearer {self.config.access_token}",
                    }
                    response = await self.client.get(
                        "https://www.googleapis.com/youtube/v3/search",
                        params={
                            "part": "snippet",
                            "channelId": self.config.channel_id,
                            "type": "video",
                            "maxResults": 50,
                            "pageToken": page_token,
                        },
                        headers=headers,
                    )

                if response.status_code != 200:
                    break

                data = response.json()
                items = data.get("items", [])

                for item in items:
                    video_id = item["id"]["videoId"]
                    snippet = item.get("snippet", {})
                    videos.append({
                        "id": video_id,
                        "title": snippet.get("title", ""),
                        "published_at": snippet.get("publishedAt", ""),
                    })

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            return videos

        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            return []

    async def _get_daily_stats(self, time_range: str) -> list[dict]:
        """Get daily statistics for the specified time range."""
        # This is a simplified implementation
        # In production, you would use YouTube Analytics API
        daily_stats = []
        end_date = datetime.now()

        if time_range == "7d":
            days = 7
        elif time_range == "30d":
            days = 30
        elif time_range == "90d":
            days = 90
        else:
            days = 365

        for i in range(days):
            date = end_date - timedelta(days=days - i - 1)
            daily_stats.append({
                "date": date.strftime("%Y-%m-%d"),
                "views": 0,  # Would come from YouTube Analytics API
                "likes": 0,
                "subscribers": 0,
            })

        return daily_stats

    def _is_token_valid(self) -> bool:
        """Check if the access token is still valid."""
        if not self.config.access_token or not self.config.token_expiry:
            return False
        return datetime.now(timezone.utc) < self.config.token_expiry

    async def _refresh_access_token(self) -> bool:
        """Refresh the YouTube access token."""
        # This would typically involve making a request to Google's OAuth token endpoint
        # For now, we'll just log that it's needed
        logger.warning("Access token refresh not implemented")
        return False
