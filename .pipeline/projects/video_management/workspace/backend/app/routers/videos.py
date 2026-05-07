"""CRUD API endpoints for video records."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Video, VideoStatus, TableMetadata
from ..schemas import (
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoListResponse,
)

router = APIRouter(tags=["videos"])


def _get_default_table(db: Session) -> TableMetadata:
    """Return the default videos table, creating it if it doesn't exist."""
    table = db.query(TableMetadata).filter(TableMetadata.name == "Videos").first()
    if not table:
        table = TableMetadata(name="Videos", description="Default video library")
        db.add(table)
        db.commit()
        db.refresh(table)
    return table


@router.get("", response_model=VideoListResponse)
def list_videos(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[VideoStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    db: Session = Depends(get_db),
):
    """List videos with pagination and optional filters."""
    table = _get_default_table(db)

    query = db.query(Video).filter(Video.table_id == table.id)

    if status:
        query = query.filter(Video.status == status)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Video.title.ilike(search_term)) | (Video.description.ilike(search_term))
        )

    total = query.count()

    items = (
        query.order_by(Video.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return VideoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[VideoResponse.model_validate(v) for v in items],
    )


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    """Get a single video by ID."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoResponse.model_validate(video)


@router.post("", response_model=VideoResponse, status_code=201)
def create_video(
    video_data: VideoCreate,
    db: Session = Depends(get_db),
):
    """Create a new video record."""
    table = _get_default_table(db)

    # Validate custom field types against table fields
    table_fields = {f.name: f for f in table.fields if not f.is_deleted}
    for field_name, field_value in video_data.custom_fields.items():
        if field_name in table_fields:
            field_def = table_fields[field_name]
            _validate_field_value(field_def, field_value)

    video = Video(
        table_id=table.id,
        title=video_data.title,
        description=video_data.description,
        status=video_data.status,
        tags=video_data.tags,
        publish_date=video_data.publish_date,
        thumbnail_url=video_data.thumbnail_url,
        youtube_video_id=video_data.youtube_video_id,
        custom_fields=video_data.custom_fields,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return VideoResponse.model_validate(video)


@router.put("/{video_id}", response_model=VideoResponse)
def update_video(
    video_id: str,
    video_data: VideoUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing video record."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    table_fields = {f.name: f for f in video.table.fields if not f.is_deleted}

    update_data = video_data.model_dump(exclude_unset=True)

    # Validate custom field types
    if "custom_fields" in update_data and update_data["custom_fields"]:
        for field_name, field_value in update_data["custom_fields"].items():
            if field_name in table_fields:
                _validate_field_value(table_fields[field_name], field_value)

    for key, value in update_data.items():
        setattr(video, key, value)

    db.commit()
    db.refresh(video)
    return VideoResponse.model_validate(video)


@router.delete("/{video_id}", status_code=204)
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """Delete a video record."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    db.delete(video)
    db.commit()
    return None


def _validate_field_value(field_def, value):
    """Validate a value against a field definition."""
    if field_def.field_type == "number" and value is not None:
        try:
            float(value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field_def.name}' expects a number",
            )
    elif field_def.field_type == "date" and value is not None:
        try:
            from datetime import datetime
            if isinstance(value, str):
                datetime.fromisoformat(value)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field_def.name}' expects a valid date",
            )
    elif field_def.field_type == "url" and value is not None:
        if not value.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field_def.name}' expects a valid URL",
            )
