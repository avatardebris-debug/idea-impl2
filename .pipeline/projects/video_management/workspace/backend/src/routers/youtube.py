"""YouTube integration API router.

Provides REST endpoints for:
- YouTube configuration management
- Video upload and management
- Analytics retrieval
- Playlist management
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.database import get_db
from src.models.youtube_models import (
    YouTubeConfig,
    YouTubeConfigCreate,
    YouTubeConfigUpdate,
    YouTubeConfigDB,
    YouTubeVideoStats,
    YouTubeVideoStatsDB,
    YouTubePlaylist,
    YouTubePlaylistDB,
    YouTubeUploadTask,
    YouTubeUploadTaskDB,
)
from ..services.youtube_service import YouTubeService, YouTubeConfig as ServiceConfig, YouTubeAuthMethod

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


def get_youtube_config(db: Session) -> Optional[YouTubeConfigDB]:
    """Get the current YouTube configuration."""
    stmt = select(YouTubeConfigDB).limit(1)
    result = db.exec(stmt).first()
    return result


def create_youtube_service(config: YouTubeConfigDB) -> YouTubeService:
    """Create a YouTubeService instance from database config."""
    service_config = ServiceConfig(
        channel_id=config.channel_id,
        api_key=config.api_key,
        access_token=config.access_token,
        refresh_token=config.refresh_token,
        token_expiry=config.token_expiry,
        is_connected=config.is_connected,
        auth_method=YouTubeAuthMethod.API_KEY if config.auth_method == "api_key" else YouTubeAuthMethod.OAUTH,
    )
    return YouTubeService(service_config)


@router.get("/config")
async def get_config(db: Session = Depends(get_db)):
    """Get the current YouTube configuration."""
    config = get_youtube_config(db)
    if not config:
        return {"is_connected": False}

    # Don't return sensitive data
    return {
        "id": config.id,
        "channel_id": config.channel_id,
        "api_key": "***" + config.api_key[-8:] if config.api_key else "",
        "access_token": "***" + config.access_token[-8:] if config.access_token else "",
        "refresh_token": "***" + config.refresh_token[-8:] if config.refresh_token else "",
        "is_connected": config.is_connected,
        "auth_method": config.auth_method,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


@router.post("/config")
async def update_config(
    config_data: YouTubeConfigCreate,
    db: Session = Depends(get_db),
):
    """Create or update YouTube configuration."""
    # Check if config exists
    existing = get_youtube_config(db)

    if existing:
        # Update existing config
        update_data = config_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        for key, value in update_data.items():
            setattr(existing, key, value)

        db.add(existing)
        db.commit()
        db.refresh(existing)

        logger.info(f"Updated YouTube config: {existing.channel_id}")
    else:
        # Create new config
        db_config = YouTubeConfigDB(**config_data.model_dump())
        db.add(db_config)
        db.commit()
        db.refresh(db_config)

        logger.info(f"Created YouTube config: {db_config.channel_id}")

    return get_config(db)


@router.delete("/config")
async def delete_config(db: Session = Depends(get_db)):
    """Delete YouTube configuration."""
    config = get_youtube_config(db)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    db.delete(config)
    db.commit()

    return {"message": "Configuration deleted"}


@router.post("/connect")
async def connect_youtube(
    config_data: YouTubeConfigCreate,
    db: Session = Depends(get_db),
):
    """Connect to YouTube and verify the configuration."""
    try:
        # Create or update config
        existing = get_youtube_config(db)

        if existing:
            update_data = config_data.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()

            for key, value in update_data.items():
                setattr(existing, key, value)

            db.add(existing)
            db.commit()
            db.refresh(existing)
        else:
            db_config = YouTubeConfigDB(**config_data.model_dump())
            db.add(db_config)
            db.commit()
            db.refresh(db_config)
            existing = db_config

        # Test the connection
        service = create_youtube_service(existing)
        channel_stats = await service._get_channel_stats()

        if not channel_stats:
            raise HTTPException(status_code=400, detail="Failed to connect to YouTube. Please check your credentials.")

        # Update config with channel info
        existing.channel_id = channel_stats.get("channelId", existing.channel_id)
        existing.is_connected = True
        existing.updated_at = datetime.utcnow()

        db.add(existing)
        db.commit()
        db.refresh(existing)

        return {
            "message": "Successfully connected to YouTube",
            "channel_id": existing.channel_id,
            "subscriber_count": channel_stats.get("subscriberCount", 0),
        }

    except Exception as e:
        logger.error(f"Failed to connect to YouTube: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/videos")
async def get_youtube_videos(
    db: Session = Depends(get_db),
    time_range: str = "30d",
):
    """Get YouTube video statistics."""
    config = get_youtube_config(db)
    if not config or not config.is_connected:
        raise HTTPException(status_code=400, detail="YouTube not connected")

    service = create_youtube_service(config)
    analytics = await service.get_channel_analytics(time_range)

    return {
        "total_videos": analytics.total_videos,
        "total_views": analytics.total_views,
        "total_likes": analytics.total_likes,
        "total_comments": analytics.total_comments,
        "total_revenue": analytics.total_revenue,
        "average_views_per_video": analytics.average_views_per_video,
        "subscriber_count": analytics.subscriber_count,
        "subscriber_growth": analytics.subscriber_growth,
        "top_videos": [
            {
                "video_id": v.video_id,
                "title": v.title,
                "views": v.views,
                "likes": v.likes,
                "comments": v.comments,
            }
            for v in analytics.top_videos
        ],
        "daily_stats": analytics.daily_stats,
    }


@router.post("/upload")
async def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list[str] = [],
    category_id: str = "22",
    privacy_status: str = "private",
    thumbnail_path: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Upload a video to YouTube."""
    config = get_youtube_config(db)
    if not config or not config.is_connected:
        raise HTTPException(status_code=400, detail="YouTube not connected")

    service = create_youtube_service(config)

    # Create upload task
    upload_task = YouTubeUploadTaskDB(
        video_id=video_path,
        status="pending",
    )
    db.add(upload_task)
    db.commit()
    db.refresh(upload_task)

    try:
        result = await service.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            privacy_status=privacy_status,
            thumbnail_path=thumbnail_path,
        )

        # Update upload task
        upload_task.youtube_video_id = result.video_id
        upload_task.status = result.status
        upload_task.error_message = result.error
        upload_task.updated_at = datetime.utcnow()

        db.add(upload_task)
        db.commit()
        db.refresh(upload_task)

        return {
            "video_id": result.video_id,
            "status": result.status,
            "upload_url": result.upload_url,
            "thumbnail_url": result.thumbnail_url,
            "error": result.error,
        }

    except Exception as e:
        upload_task.status = "failed"
        upload_task.error_message = str(e)
        upload_task.updated_at = datetime.utcnow()

        db.add(upload_task)
        db.commit()

        logger.error(f"Video upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playlists")
async def get_playlists(db: Session = Depends(get_db)):
    """Get YouTube playlists."""
    config = get_youtube_config(db)
    if not config or not config.is_connected:
        raise HTTPException(status_code=400, detail="YouTube not connected")

    service = create_youtube_service(config)
    playlists = await service.get_playlists()

    return [
        {
            "playlist_id": p.playlist_id,
            "title": p.title,
            "description": p.description,
            "video_count": p.video_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in playlists
    ]


@router.post("/playlists")
async def create_playlist(
    title: str,
    description: str = "",
    db: Session = Depends(get_db),
):
    """Create a YouTube playlist."""
    config = get_youtube_config(db)
    if not config or not config.is_connected:
        raise HTTPException(status_code=400, detail="YouTube not connected")

    service = create_youtube_service(config)
    playlist_id = await service.create_playlist(title, description)

    if not playlist_id:
        raise HTTPException(status_code=500, detail="Failed to create playlist")

    return {"playlist_id": playlist_id, "message": "Playlist created"}


@router.post("/playlists/{playlist_id}/videos")
async def add_video_to_playlist(
    playlist_id: str,
    video_id: str,
    db: Session = Depends(get_db),
):
    """Add a video to a YouTube playlist."""
    config = get_youtube_config(db)
    if not config or not config.is_connected:
        raise HTTPException(status_code=400, detail="YouTube not connected")

    service = create_youtube_service(config)
    success = await service.add_video_to_playlist(playlist_id, video_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to add video to playlist")

    return {"message": "Video added to playlist"}


@router.get("/stats/{video_id}")
async def get_video_stats(
    video_id: str,
    db: Session = Depends(get_db),
):
    """Get statistics for a specific video."""
    config = get_youtube_config(db)
    if not config or not config.is_connected:
        raise HTTPException(status_code=400, detail="YouTube not connected")

    service = create_youtube_service(config)
    stats = await service.get_video_stats(video_id)

    return {
        "video_id": stats.video_id,
        "title": stats.title,
        "views": stats.views,
        "likes": stats.likes,
        "dislikes": stats.dislikes,
        "comments": stats.comments,
        "last_updated": stats.last_updated.isoformat() if stats.last_updated else None,
    }
