"""SQLAlchemy models for the video management platform."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SAEnum,
    Index,
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship

from .database import Base


class FieldTypeId(str, PyEnum):
    """Supported field types for custom columns."""
    TEXT = "text"
    DATE = "date"
    SELECT = "select"
    CHECKBOX = "checkbox"
    NUMBER = "number"
    URL = "url"
    TAGS = "tags"
    OBJECT = "object"


class VideoStatus(str, PyEnum):
    """Lifecycle status of a video."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class TableMetadata(Base):
    """Metadata about a table (e.g. the videos table)."""
    __tablename__ = "table_metadata"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    fields = relationship("TableField", back_populates="table", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="table", cascade="all, delete-orphan")


class TableField(Base):
    """Definition of a column in a table."""
    __tablename__ = "table_fields"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("table_metadata.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    field_type = Column(SAEnum(FieldTypeId), nullable=False)
    is_deleted = Column(Boolean, default=False)
    options = Column(JSON, default=list)  # For SELECT type: list of options
    is_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    table = relationship("TableMetadata", back_populates="fields")

    __table_args__ = (
        Index("ix_table_fields_table_id", "table_id"),
        Index("ix_table_fields_name", "name"),
    )


class Video(Base):
    """A video record stored in the platform."""
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("table_metadata.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False, default="")
    description = Column(Text, default="")
    status = Column(SAEnum(VideoStatus), default=VideoStatus.DRAFT)
    tags = Column(JSON, default=list)
    publish_date = Column(DateTime, nullable=True)
    thumbnail_url = Column(String, default="")
    youtube_video_id = Column(String, nullable=True)
    custom_fields = Column(JSON, default=dict)  # Stores values for custom fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    table = relationship("TableMetadata", back_populates="videos")

    __table_args__ = (
        Index("ix_videos_table_id", "table_id"),
        Index("ix_videos_status", "status"),
        Index("ix_videos_publish_date", "publish_date"),
    )
