"""YouTube integration database models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel, Column, Text
from sqlalchemy import Text as SQLAlchemyText


class YouTubeConfigBase(BaseModel):
    """YouTube configuration base model."""
    channel_id: str = Field(..., description="YouTube channel ID")
    api_key: str = Field(..., description="YouTube API key")
    access_token: str = Field(default="", description="OAuth access token")
    refresh_token: str = Field(default="", description="OAuth refresh token")
    token_expiry: Optional[datetime] = Field(default=None, description="Token expiry time")
    is_connected: bool = Field(default=False, description="Whether the channel is connected")
    auth_method: str = Field(default="api_key", description="Authentication method")


class YouTubeConfigCreate(YouTubeConfigBase):
    """YouTube configuration creation model."""
    pass


class YouTubeConfigUpdate(BaseModel):
    """YouTube configuration update model."""
    channel_id: Optional[str] = None
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    is_connected: Optional[bool] = None
    auth_method: Optional[str] = None


class YouTubeConfig(YouTubeConfigBase):
    """YouTube configuration model."""
    id: int = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))


class YouTubeConfigDB(SQLModel, table=True):
    """YouTube configuration database model."""
    __tablename__ = "youtube_configs"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    channel_id: str = SQLField(sa_column=Column(SQLAlchemyText))
    api_key: str = SQLField(sa_column=Column(SQLAlchemyText))
    access_token: str = SQLField(default="", sa_column=Column(SQLAlchemyText))
    refresh_token: str = SQLField(default="", sa_column=Column(SQLAlchemyText))
    token_expiry: Optional[datetime] = None
    is_connected: bool = False
    auth_method: str = "api_key"
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))


class YouTubeVideoStatsBase(BaseModel):
    """YouTube video statistics base model."""
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    views: int = Field(default=0, description="View count")
    likes: int = Field(default=0, description="Like count")
    dislikes: int = Field(default=0, description="Dislike count")
    comments: int = Field(default=0, description="Comment count")
    shares: int = Field(default=0, description="Share count")
    estimated_revenue: float = Field(default=0.0, description="Estimated revenue")
    average_view_duration: str = Field(default="", description="Average view duration")
    audience_retention: float = Field(default=0.0, description="Audience retention percentage")


class YouTubeVideoStatsCreate(YouTubeVideoStatsBase):
    """YouTube video statistics creation model."""
    pass


class YouTubeVideoStatsUpdate(BaseModel):
    """YouTube video statistics update model."""
    views: Optional[int] = None
    likes: Optional[int] = None
    dislikes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    estimated_revenue: Optional[float] = None
    average_view_duration: Optional[str] = None
    audience_retention: Optional[float] = None


class YouTubeVideoStats(YouTubeVideoStatsBase):
    """YouTube video statistics model."""
    id: int = Field(default=None)
    video_id: str = Field(..., description="YouTube video ID")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))


class YouTubeVideoStatsDB(SQLModel, table=True):
    """YouTube video statistics database model."""
    __tablename__ = "youtube_video_stats"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    video_id: str = SQLField(sa_column=Column(SQLAlchemyText, unique=True))
    title: str = SQLField(sa_column=Column(SQLAlchemyText))
    views: int = 0
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    shares: int = 0
    estimated_revenue: float = 0.0
    average_view_duration: str = ""
    audience_retention: float = 0.0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))


class YouTubePlaylistBase(BaseModel):
    """YouTube playlist base model."""
    playlist_id: str = Field(..., description="YouTube playlist ID")
    title: str = Field(..., description="Playlist title")
    description: str = Field(default="", description="Playlist description")
    video_count: int = Field(default=0, description="Number of videos in playlist")


class YouTubePlaylistCreate(YouTubePlaylistBase):
    """YouTube playlist creation model."""
    pass


class YouTubePlaylistUpdate(BaseModel):
    """YouTube playlist update model."""
    title: Optional[str] = None
    description: Optional[str] = None
    video_count: Optional[int] = None


class YouTubePlaylist(YouTubePlaylistBase):
    """YouTube playlist model."""
    id: int = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))


class YouTubePlaylistDB(SQLModel, table=True):
    """YouTube playlist database model."""
    __tablename__ = "youtube_playlists"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    playlist_id: str = SQLField(sa_column=Column(SQLAlchemyText, unique=True))
    title: str = SQLField(sa_column=Column(SQLAlchemyText))
    description: str = SQLField(default="", sa_column=Column(SQLAlchemyText))
    video_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class YouTubeUploadTaskBase(BaseModel):
    """YouTube upload task base model."""
    video_id: str = Field(..., description="Internal video ID")
    youtube_video_id: Optional[str] = Field(default=None, description="YouTube video ID")
    status: str = Field(default="pending", description="Upload status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class YouTubeUploadTaskCreate(YouTubeUploadTaskBase):
    """YouTube upload task creation model."""
    pass


class YouTubeUploadTaskUpdate(BaseModel):
    """YouTube upload task update model."""
    youtube_video_id: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None


class YouTubeUploadTask(YouTubeUploadTaskBase):
    """YouTube upload task model."""
    id: int = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))


class YouTubeUploadTaskDB(SQLModel, table=True):
    """YouTube upload task database model."""
    __tablename__ = "youtube_upload_tasks"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    video_id: str = SQLField(sa_column=Column(SQLAlchemyText))
    youtube_video_id: Optional[str] = SQLField(default=None, sa_column=Column(SQLAlchemyText))
    status: str = "pending"
    error_message: Optional[str] = SQLField(default=None, sa_column=Column(SQLAlchemyText))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
