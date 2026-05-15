"""Tests for YouTube integration."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models import YouTubeChannel, Video
from app.schemas import YouTubeUploadResponse, ChannelStatsResponse
from app.services.youtube_upload import YouTubeUploadService
from app.services.youtube_stats import YouTubeStatsService


@pytest.fixture
def mock_channel(db_session):
    """Create a mock YouTube channel for testing."""
    channel = YouTubeChannel(
        channel_id="test_channel_id",
        channel_name="Test Channel",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True,
    )
    db_session.add(channel)
    db_session.commit()
    return channel


@pytest.fixture
def upload_service(mock_channel, db_session):
    """Create YouTubeUploadService instance."""
    return YouTubeUploadService(db_session)


@pytest.fixture
def stats_service(mock_channel, db_session):
    """Create YouTubeStatsService instance."""
    return YouTubeStatsService(db_session)


class TestYouTubeUploadService:
    """Tests for YouTubeUploadService."""

    @pytest.mark.asyncio
    async def test_upload_video_success(self, upload_service, db_session):
        """Test successful video upload."""
        from unittest.mock import AsyncMock
        with patch("app.services.youtube_upload.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "test_video_id"}
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            mock_client.return_value = mock_client_instance

            result = await upload_service.upload_video(
                title="Test Video",
                description="Test Description",
                status="public",
                tags=["test", "video"],
            )

            assert result.success is True
            assert result.youtube_video_id == "test_video_id"
            assert result.message == "Video uploaded successfully."

    @pytest.mark.asyncio
    async def test_upload_video_invalid_status(self, upload_service):
        """Test video upload with invalid status."""
        result = await upload_service.upload_video(
            title="Test Video",
            status="invalid",
        )

        assert result.success is False
        assert "Invalid status" in result.message

    @pytest.mark.asyncio
    async def test_upload_video_token_refresh_failure(self, mock_channel, db_session):
        """Test video upload when token refresh fails."""
        mock_channel.refresh_token = None
        mock_channel.token_expiry = None
        mock_channel.access_token = None
        db_session.commit()

        service = YouTubeUploadService(db_session)
        result = await service.upload_video(
            title="Test Video",
        )

        assert result.success is False
        assert "Token refresh failed" in result.message

    @pytest.mark.asyncio
    async def test_upload_video_with_thumbnail(self, upload_service, db_session):
        """Test video upload with thumbnail URL."""
        from unittest.mock import AsyncMock
        with patch("app.services.youtube_upload.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "test_video_id"}
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            mock_client.return_value = mock_client_instance

            result = await upload_service.upload_video(
                title="Test Video",
                thumbnail_url="https://example.com/thumb.jpg",
            )

            assert result.success is True
            assert result.youtube_video_id == "test_video_id"


class TestYouTubeStatsService:
    """Tests for YouTubeStatsService."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, stats_service, db_session):
        """Test successful stats retrieval."""
        from unittest.mock import AsyncMock
        with patch("app.services.youtube_stats.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [{
                    "statistics": {
                        "subscriberCount": "1000",
                        "viewCount": "50000",
                        "videoCount": "100",
                    }
                }]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.get = AsyncMock(return_value=mock_response)

            mock_client.return_value = mock_client_instance

            result = await stats_service.get_stats()

            assert result.subscriber_count == 1000
            assert result.view_count == 50000
            assert result.video_count == 100
            assert result.last_updated is not None

    @pytest.mark.asyncio
    async def test_get_stats_no_channel(self, db_session):
        """Test stats retrieval with no connected channel."""
        db_session.query = MagicMock()
        db_session.query.return_value.first = MagicMock(return_value=None)

        with pytest.raises(ValueError, match="No YouTube channel connected"):
            service = YouTubeStatsService(db_session)
            await service.get_stats()
