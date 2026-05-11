"""YouTube OAuth 2.0 and API endpoints."""

import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import YouTubeChannel
from ..schemas import (
    YouTubeChannelResponse,
    SyncResponse,
    ChannelStatsResponse,
    SyncStatusResponse,
    YouTubeUploadRequest,
    YouTubeUploadResponse,
)
from ..config import settings

router = APIRouter(prefix="/api/youtube", tags=["youtube"])

# OAuth 2.0 constants
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# OAuth scopes
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
SCOPE_STRING = " ".join(YOUTUBE_SCOPES)


def _get_or_create_channel(db: Session) -> YouTubeChannel:
    """Get existing channel or create a new empty one."""
    channel = db.query(YouTubeChannel).first()
    if not channel:
        channel = YouTubeChannel()
        db.add(channel)
        db.commit()
        db.refresh(channel)
    return channel


def _refresh_tokens_if_needed(channel: YouTubeChannel, db: Session) -> Optional[str]:
    """Refresh access token if expired. Returns new access token or None on failure."""
    if not channel.refresh_token or not channel.token_expiry:
        return channel.access_token

    # Check if token is expired or about to expire (within 5 minutes)
    if channel.token_expiry < datetime.now(timezone.utc) - timedelta(minutes=5):
        try:
            async def _refresh():
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        GOOGLE_TOKEN_URL,
                        data={
                            "grant_type": "refresh_token",
                            "client_id": settings.google_client_id,
                            "client_secret": settings.google_client_secret,
                            "refresh_token": channel.refresh_token,
                        },
                    )
                    resp.raise_for_status()
                    return resp.json()

            # Run async in sync context
            import asyncio
            token_data = asyncio.run(_refresh())

            channel.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                channel.refresh_token = token_data["refresh_token"]
            expires_in = token_data.get("expires_in", 3600)
            channel.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            db.commit()
            return channel.access_token

        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

    return channel.access_token


def _make_youtube_request(
    db: Session,
    channel: YouTubeChannel,
    endpoint: str,
    params: dict,
    method: str = "GET",
    files: Optional[dict] = None,
) -> dict:
    """Make a request to the YouTube Data API."""
    access_token = _refresh_tokens_if_needed(channel, db)
    if not access_token:
        raise HTTPException(status_code=401, detail="Not connected to YouTube")

    url = f"{GOOGLE_YOUTUBE_API_BASE}/{endpoint}"

    headers = {"Authorization": f"Bearer {access_token}"}

    async def _request():
        async with httpx.AsyncClient() as client:
            if method == "GET":
                resp = await client.get(url, params=params, headers=headers)
            elif method == "POST":
                if files:
                    resp = await client.post(url, params=params, headers=headers, files=files)
                else:
                    resp = await client.post(url, params=params, json=params.get("json", {}), headers=headers)
            else:
                raise HTTPException(status_code=405, detail=f"Method {method} not supported")
            resp.raise_for_status()
            return resp.json()

    import asyncio
    return asyncio.run(_request())


@router.get("/auth")
def get_auth_url():
    """Generate Google OAuth 2.0 authorization URL."""
    if not settings.google_client_id:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID environment variable."
        )

    state = str(uuid.uuid4())
    auth_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": SCOPE_STRING,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    query_string = "&".join(f"{k}={v}" for k, v in auth_params.items())
    auth_url = f"{GOOGLE_AUTH_URL}?{query_string}"

    return {"auth_url": auth_url, "state": state}


@router.get("/callback")
async def oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle OAuth 2.0 callback and exchange code for tokens."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth not configured.")

    # Exchange code for tokens
    async def _exchange():
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                },
            )
            resp.raise_for_status()
            return resp.json()

    token_data = await _exchange()

    # Get channel info
    async def _get_channel_info():
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            resp.raise_for_status()
            return resp.json()

    channel_info = await _get_channel_info()

    # Save channel
    channel = _get_or_create_channel(db)
    channel.channel_id = channel_info.get("id")
    channel.channel_name = channel_info.get("name")
    channel.channel_avatar = channel_info.get("picture")
    channel.access_token = token_data["access_token"]
    channel.refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    channel.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    channel.is_connected = True
    channel.sync_error = None
    db.commit()
    db.refresh(channel)

    return YouTubeChannelResponse.model_validate(channel)


@router.get("/status", response_model=YouTubeChannelResponse)
def get_channel_status(db: Session = Depends(get_db)):
    """Get current YouTube connection status."""
    channel = db.query(YouTubeChannel).first()
    if not channel:
        return YouTubeChannelResponse(
            id=str(uuid.uuid4()),
            channel_id=None,
            channel_name=None,
            channel_avatar=None,
            is_connected=False,
            channel_stats={},
            last_sync_at=None,
            sync_error=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    return YouTubeChannelResponse.model_validate(channel)


@router.delete("/disconnect")
def disconnect_channel(db: Session = Depends(get_db)):
    """Disconnect YouTube channel and revoke tokens."""
    channel = db.query(YouTubeChannel).first()
    if not channel:
        return {"message": "No channel connected."}

    # Revoke token if we have one
    if channel.access_token:
        try:
            async def _revoke():
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        GOOGLE_REVOKE_URL,
                        params={"token": channel.access_token},
                    )
                    # Google returns 200 on success, 400 if token already revoked
                    return resp.status_code

            import asyncio
            asyncio.run(_revoke())
        except Exception:
            pass  # Best effort revocation

    channel.access_token = None
    channel.refresh_token = None
    channel.token_expiry = None
    channel.channel_id = None
    channel.channel_name = None
    channel.channel_avatar = None
    channel.is_connected = False
    channel.sync_error = None
    db.commit()

    return {"message": "Disconnected from YouTube."}


@router.post("/sync")
async def sync_videos(db: Session = Depends(get_db)):
    """Trigger a full sync of YouTube channel videos."""
    channel = db.query(YouTubeChannel).first()
    if not channel or not channel.is_connected:
        raise HTTPException(status_code=401, detail="Not connected to YouTube.")

    access_token = _refresh_tokens_if_needed(channel, db)
    if not access_token:
        raise HTTPException(status_code=401, detail="Token refresh failed.")

    total_synced = 0
    total_failed = 0
    total_videos = 0

    # Fetch all videos from YouTube
    async def _fetch_all_videos():
        videos = []
        page_token = None
        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    "part": "snippet,statistics,contentDetails",
                    "mine": "true",
                    "maxResults": 50,
                    "fields": "items(id,snippet(title,description,thumbnails,publishedAt),statistics(viewCount,likeCount,commentCount),contentDetails(duration))",
                }
                if page_token:
                    params["pageToken"] = page_token

                resp = await client.get(
                    f"{GOOGLE_YOUTUBE_API_BASE}/channels",
                    params={**params, "part": "contentDetails"},
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if resp.status_code == 403:
                    # Try listing uploads via the uploads playlist
                    channel_resp = await client.get(
                        f"{GOOGLE_YOUTUBE_API_BASE}/channels",
                        params={"part": "contentDetails", "id": channel.channel_id},
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    channel_resp.raise_for_status()
                    channel_data = channel_resp.json()["items"][0]
                    uploads_playlist_id = channel_data["contentDetails"]["relatedPlaylists"]["uploads"]

                    page_token = None
                    while True:
                        playlist_params = {
                            "part": "snippet,contentDetails",
                            "playlistId": uploads_playlist_id,
                            "maxResults": 50,
                        }
                        if page_token:
                            playlist_params["pageToken"] = page_token

                        resp = await client.get(
                            f"{GOOGLE_YOUTUBE_API_BASE}/playlistItems",
                            params=playlist_params,
                            headers={"Authorization": f"Bearer {access_token}"},
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        for item in data.get("items", []):
                            video_id = item["snippet"]["resourceId"]["videoId"]
                            # Get video details
                            video_resp = await client.get(
                                f"{GOOGLE_YOUTUBE_API_BASE}/videos",
                                params={"part": "snippet,statistics,contentDetails", "id": video_id},
                                headers={"Authorization": f"Bearer {access_token}"},
                            )
                            video_resp.raise_for_status()
                            video_data = video_resp.json()["items"][0]
                            videos.append(video_data)

                        page_token = data.get("nextPageToken")
                        if not page_token:
                            break
                    break

                resp.raise_for_status()
                data = resp.json()
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        return videos

    # Use a simpler approach: get channel's uploads playlist
    try:
        async def _sync():
            nonlocal total_synced, total_failed, total_videos
            async with httpx.AsyncClient() as client:
                # Get channel's uploads playlist ID
                channel_resp = await client.get(
                    f"{GOOGLE_YOUTUBE_API_BASE}/channels",
                    params={"part": "contentDetails", "id": channel.channel_id},
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                channel_resp.raise_for_status()
                channel_data = channel_resp.json()["items"][0]
                uploads_playlist_id = channel_data["contentDetails"]["relatedPlaylists"]["uploads"]

                page_token = None
                while True:
                    playlist_params = {
                        "part": "snippet,contentDetails",
                        "playlistId": uploads_playlist_id,
                        "maxResults": 50,
                    }
                    if page_token:
                        playlist_params["pageToken"] = page_token

                    resp = await client.get(
                        f"{GOOGLE_YOUTUBE_API_BASE}/playlistItems",
                        params=playlist_params,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    resp.raise_for_status()
                    playlist_data = resp.json()

                    for item in playlist_data.get("items", []):
                        video_id = item["snippet"]["resourceId"]["videoId"]
                        # Get video details
                        video_resp = await client.get(
                            f"{GOOGLE_YOUTUBE_API_BASE}/videos",
                            params={"part": "snippet,statistics,contentDetails", "id": video_id},
                            headers={"Authorization": f"Bearer {access_token}"},
                        )
                        video_resp.raise_for_status()
                        video_data = video_resp.json()["items"][0]

                        # Import Video model here to avoid circular issues
                        from ..models import Video, VideoStatus

                        # Upsert video
                        existing = db.query(Video).filter_by(youtube_video_id=video_id).first()
                        if existing:
                            # Update existing
                            snippet = video_data["snippet"]
                            statistics = video_data.get("statistics", {})
                            existing.title = snippet.get("title", existing.title)
                            existing.description = snippet.get("description", existing.description)
                            thumbnails = snippet.get("thumbnails", {})
                            high_thumb = thumbnails.get("high", {}) or thumbnails.get("default", {})
                            existing.thumbnail_url = high_thumb.get("url", existing.thumbnail_url)
                            existing.tags = snippet.get("tags", [])
                            existing.updated_at = datetime.now(timezone.utc)
                            total_synced += 1
                        else:
                            # Create new
                            snippet = video_data["snippet"]
                            statistics = video_data.get("statistics", {})
                            thumbnails = snippet.get("thumbnails", {})
                            high_thumb = thumbnails.get("high", {}) or thumbnails.get("default", {})

                            # Find default table
                            from ..models import TableMetadata
                            table = db.query(TableMetadata).first()
                            if not table:
                                raise HTTPException(status_code=400, detail="No videos table found. Create one first.")

                            new_video = Video(
                                table_id=table.id,
                                title=snippet.get("title", ""),
                                description=snippet.get("description", ""),
                                status=VideoStatus.PUBLISHED,
                                tags=snippet.get("tags", []),
                                thumbnail_url=high_thumb.get("url", ""),
                                youtube_video_id=video_id,
                                publish_date=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")).replace(tzinfo=None),
                            )
                            db.add(new_video)
                            total_synced += 1

                        total_videos += 1

                    page_token = playlist_data.get("nextPageToken")
                    if not page_token:
                        break

            return total_synced, total_failed, total_videos

        synced, failed, total = await _sync()
        db.commit()

        # Update sync metadata
        channel.last_sync_at = datetime.now(timezone.utc)
        channel.sync_error = None
        db.commit()

        return SyncResponse(
            total=total,
            synced=synced,
            failed=failed,
            last_sync_at=channel.last_sync_at,
        )

    except Exception as e:
        db.rollback()
        channel.sync_error = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/stats", response_model=ChannelStatsResponse)
def get_channel_stats(db: Session = Depends(get_db)):
    """Get current channel statistics."""
    channel = db.query(YouTubeChannel).first()
    if not channel or not channel.is_connected:
        raise HTTPException(status_code=401, detail="Not connected to YouTube.")

    access_token = _refresh_tokens_if_needed(channel, db)
    if not access_token:
        raise HTTPException(status_code=401, detail="Token refresh failed.")

    async def _fetch_stats():
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GOOGLE_YOUTUBE_API_BASE}/channels",
                params={"part": "statistics,snippet", "id": channel.channel_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json()["items"][0]

    channel_data = asyncio.run(_fetch_stats())
    stats = channel_data.get("statistics", {})

    # Update stored stats
    channel.channel_stats = {
        "subscriberCount": stats.get("subscriberCount"),
        "viewCount": stats.get("viewCount"),
        "videoCount": stats.get("videoCount"),
        "hiddenSubscriberCount": stats.get("hiddenSubscriberCount"),
    }
    db.commit()

    return ChannelStatsResponse(
        subscriber_count=int(stats.get("subscriberCount", 0)) if stats.get("subscriberCount") else None,
        view_count=int(stats.get("viewCount", 0)) if stats.get("viewCount") else None,
        video_count=int(stats.get("videoCount", 0)) if stats.get("videoCount") else None,
        hidden_subscriber_count=stats.get("hiddenSubscriberCount"),
        last_updated=datetime.now(timezone.utc),
    )


@router.post("/stats/refresh")
async def refresh_stats(db: Session = Depends(get_db)):
    """Manually refresh channel statistics."""
    stats = await get_channel_stats(db)
    return stats


@router.get("/sync-status", response_model=SyncStatusResponse)
def get_sync_status(db: Session = Depends(get_db)):
    """Get sync status including last sync time and next scheduled sync."""
    channel = db.query(YouTubeChannel).first()
    if not channel:
        return SyncStatusResponse(
            is_connected=False,
            last_sync_at=None,
            next_sync_at=None,
            sync_error=None,
            channel_name=None,
        )

    # Calculate next sync time (15 minutes after last sync)
    next_sync = None
    if channel.last_sync_at:
        next_sync = channel.last_sync_at + timedelta(minutes=settings.stats_refresh_interval_minutes)

    return SyncStatusResponse(
        is_connected=channel.is_connected,
        last_sync_at=channel.last_sync_at,
        next_sync_at=next_sync,
        sync_error=channel.sync_error,
        channel_name=channel.channel_name,
    )


@router.post("/videos", response_model=YouTubeUploadResponse)
async def upload_to_youtube(
    request: YouTubeUploadRequest,
    db: Session = Depends(get_db),
):
    """Publish a video to YouTube."""
    channel = db.query(YouTubeChannel).first()
    if not channel or not channel.is_connected:
        raise HTTPException(status_code=401, detail="Not connected to YouTube.")

    access_token = _refresh_tokens_if_needed(channel, db)
    if not access_token:
        raise HTTPException(status_code=401, detail="Token refresh failed.")

    # Validate status
    valid_statuses = {"public", "private", "unlisted"}
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")

    try:
        async def _upload():
            async with httpx.AsyncClient() as client:
                # Create the video resource
                video_resource = {
                    "snippet": {
                        "title": request.title,
                        "description": request.description,
                        "tags": request.tags,
                    },
                    "status": {
                        "privacyStatus": request.status,
                    }
                }

                if request.publish_at:
                    video_resource["status"]["publishAt"] = request.publish_at.isoformat()

                if request.thumbnail_url:
                    video_resource["snippet"]["thumbnails"] = {
                        "high": {"url": request.thumbnail_url}
                    }

                # Upload the video
                resp = await client.post(
                    f"{GOOGLE_YOUTUBE_API_BASE}/videos",
                    params={"part": "snippet,status"},
                    json=video_resource,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                resp.raise_for_status()
                return resp.json()

        result = await _upload()

        # Update local video if youtube_video_id was provided in custom_fields
        # For now, just return the result
        return YouTubeUploadResponse(
            success=True,
            youtube_video_id=result.get("id"),
            message="Video uploaded successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        return YouTubeUploadResponse(
            success=False,
            youtube_video_id=None,
            message="Failed to upload video.",
            error=str(e),
        )
