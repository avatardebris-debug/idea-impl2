# Phase 2: YouTube Integration Tasks

## Task 1: YouTube OAuth 2.0 Integration

**Goal:** Enable users to connect their YouTube channel via OAuth 2.0 and store credentials securely.

**Scope:**
- Backend: Create `YouTubeChannel` model for storing OAuth tokens and channel metadata
- Backend: Implement OAuth 2.0 authorization code flow endpoints (authorize, callback, token refresh)
- Backend: Create `YouTubeAPIService` with methods for authenticated YouTube API calls
- Backend: Add YouTube API configuration via environment variables (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REDIRECT_URI)
- Backend: Add `youtube_channel_id` field to `Video` model to link videos to the connected channel
- Frontend: Add "Connect YouTube Channel" button in the settings/header area
- Frontend: Create `YouTubeConnect` component showing connection status (connected/disconnected)
- Frontend: Add disconnect functionality that clears stored tokens

**Files to create/modify:**
- `backend/models.py` - Add `YouTubeChannel` model, add `youtube_channel_id` to `Video`
- `backend/schemas.py` - Add `YouTubeChannelResponse`, `YouTubeChannelCreate` schemas
- `backend/routers/oauth.py` - New file: OAuth flow endpoints
- `backend/services/youtube_service.py` - New file: YouTube API client wrapper
- `backend/routers/__init__.py` - Register new oauth router
- `frontend/src/components/YouTubeConnect.tsx` - New file: Connection UI component
- `frontend/src/components/Header.tsx` - Add connection status indicator
- `frontend/src/api.ts` - Add YouTube API client methods
- `frontend/src/App.tsx` - Add YouTubeConnect route

**Dependencies:** None (foundation task)

---

## Task 2: Video Sync Engine

**Goal:** Automatically pull existing YouTube videos into the platform and keep them in sync.

**Scope:**
- Backend: Create `VideoSyncService` with methods for:
  - Fetching channel's uploaded videos via YouTube Data API
  - Mapping YouTube video metadata to platform `Video` schema
  - Creating new platform videos for YouTube videos not yet in the system
  - Updating existing platform videos when YouTube metadata changes
  - Detecting and handling deleted YouTube videos (soft-delete or mark as unavailable)
  - Incremental sync using `updated_at` timestamps to minimize API calls
- Backend: Add sync configuration fields to `YouTubeChannel` model (last_sync_at, sync_enabled)
- Backend: Create `/api/youtube/sync` endpoint to trigger manual sync
- Backend: Add sync status tracking (in_progress, completed, failed) with error messages
- Backend: Handle YouTube API rate limiting with exponential backoff
- Frontend: Add "Sync Videos" button in the video list header
- Frontend: Display sync status (last sync time, number of videos synced, any errors)
- Frontend: Show sync progress indicator during active sync operations

**Files to create/modify:**
- `backend/models.py` - Add sync status fields to `YouTubeChannel`
- `backend/services/sync_service.py` - New file: Sync engine implementation
- `backend/routers/sync.py` - New file: Sync endpoints
- `backend/routers/__init__.py` - Register new sync router
- `frontend/src/components/VideoList.tsx` - Add sync button and status display
- `frontend/src/api.ts` - Add sync API client methods
- `frontend/src/components/SyncStatus.tsx` - New file: Sync status component

**Dependencies:** Task 1 (requires OAuth tokens to be available)

---

## Task 3: YouTube Upload Endpoint

**Goal:** Allow users to publish videos from the platform to their connected YouTube channel.

**Scope:**
- Backend: Create `YouTubeUploadService` with methods for:
  - Uploading video files to YouTube via the Media Upload API
  - Setting video metadata (title, description, tags, thumbnail, scheduled publish time)
  - Handling upload progress tracking for large files
  - Managing YouTube privacy settings (public, private, unlisted)
  - Handling YouTube API errors (quota exceeded, invalid metadata, etc.)
- Backend: Add `upload_status` field to `Video` model (none, uploading, uploaded, failed)
- Backend: Add `youtube_video_id` auto-population when upload succeeds
- Backend: Create `/api/videos/{id}/upload` endpoint to trigger YouTube upload
- Backend: Add validation to ensure YouTube channel is connected before upload
- Backend: Add retry logic for failed uploads with configurable max retries
- Frontend: Add "Upload to YouTube" button in the video form
- Frontend: Show upload progress in the video form when uploading
- Frontend: Display YouTube video link after successful upload
- Frontend: Show upload error messages with retry option

**Files to create/modify:**
- `backend/models.py` - Add `upload_status` to `Video` model
- `backend/services/upload_service.py` - New file: YouTube upload service
- `backend/routers/upload.py` - New file: Upload endpoints
- `backend/routers/__init__.py` - Register new upload router
- `frontend/src/components/VideoForm.tsx` - Add upload button and progress UI
- `frontend/src/api.ts` - Add upload API client methods
- `frontend/src/components/UploadProgress.tsx` - New file: Upload progress component

**Dependencies:** Task 1 (requires OAuth tokens), Task 2 (benefits from sync infrastructure)

---

## Task 4: Channel Stats Dashboard

**Goal:** Display YouTube channel statistics and video performance metrics.

**Scope:**
- Backend: Create `ChannelStatsService` with methods for:
  - Fetching channel-level stats (subscriber count, total views, total videos, total revenue)
  - Fetching video-level stats (views, likes, comments, shares for each video)
  - Caching stats to avoid excessive API calls (cache for 1 hour)
  - Periodic background stats updates (via scheduled task or on-demand)
- Backend: Add `ChannelStats` model for storing cached stats
- Backend: Create `/api/youtube/stats` endpoint to fetch channel stats
- Backend: Create `/api/youtube/stats/videos/{video_id}` endpoint to fetch video-specific stats
- Backend: Add stats refresh trigger endpoint
- Frontend: Create `ChannelStatsDashboard` component showing:
  - Channel overview (subscribers, total views, total revenue)
  - Recent video performance (top 5 videos by views)
  - Stats refresh button with last updated timestamp
  - Loading states and error handling
- Frontend: Add stats dashboard to the main navigation or as a tab in the video list

**Files to create/modify:**
- `backend/models.py` - Add `ChannelStats` model
- `backend/services/stats_service.py` - New file: Stats fetch and cache service
- `backend/routers/stats.py` - New file: Stats endpoints
- `backend/routers/__init__.py` - Register new stats router
- `frontend/src/components/ChannelStatsDashboard.tsx` - New file: Stats dashboard component
- `frontend/src/api.ts` - Add stats API client methods
- `frontend/src/App.tsx` - Add stats route

**Dependencies:** Task 1 (requires OAuth tokens)

---

## Task 5: Sync Status & Conflict Resolution

**Goal:** Provide comprehensive sync status tracking and resolve conflicts between platform and YouTube data.

**Scope:**
- Backend: Enhance sync service with conflict detection:
  - Detect when platform video metadata differs from YouTube metadata
  - Detect when YouTube video is deleted but platform video still exists
  - Detect when platform video has `youtube_video_id` but YouTube API returns 404
- Backend: Create conflict resolution API:
  - `/api/youtube/sync/conflicts` endpoint to list detected conflicts
  - `/api/youtube/sync/conflicts/{conflict_id}/resolve` endpoint to resolve conflicts
  - Support resolution strategies: keep_platform, keep_youtube, merge
- Backend: Add `SyncConflict` model to track conflicts
- Backend: Add sync history tracking (log of all sync operations with results)
- Backend: Create `/api/youtube/sync/history` endpoint to view sync history
- Frontend: Create `SyncConflictResolver` component:
  - Display list of detected conflicts with side-by-side comparison
  - Allow user to choose resolution strategy per conflict
  - Show resolution results
- Frontend: Create `SyncHistory` component:
  - Display chronological list of sync operations
  - Show sync duration, videos processed, errors encountered
  - Allow filtering by status (success, failed, partial)
- Frontend: Add sync status indicator in the header showing last sync time and status
- Frontend: Add manual sync trigger with confirmation dialog

**Files to create/modify:**
- `backend/models.py` - Add `SyncConflict` and `SyncHistory` models
- `backend/services/sync_service.py` - Enhance with conflict detection and resolution
- `backend/routers/sync.py` - Add conflict and history endpoints
- `frontend/src/components/SyncConflictResolver.tsx` - New file: Conflict resolution UI
- `frontend/src/components/SyncHistory.tsx` - New file: Sync history UI
- `frontend/src/components/Header.tsx` - Add sync status indicator
- `frontend/src/api.ts` - Add conflict and history API client methods

**Dependencies:** Task 2 (requires sync engine), Task 4 (benefits from stats infrastructure)

---

## Task Summary

| Task | Description | Dependencies |
|------|-------------|--------------|
| 1 | YouTube OAuth 2.0 Integration | None |
| 2 | Video Sync Engine | Task 1 |
| 3 | YouTube Upload Endpoint | Task 1, Task 2 |
| 4 | Channel Stats Dashboard | Task 1 |
| 5 | Sync Status & Conflict Resolution | Task 2, Task 4 |

## Execution Order

1. **Task 1** - Must be first as it provides the OAuth foundation for all other tasks
2. **Task 2** - Builds on OAuth to enable video synchronization
3. **Task 3** - Builds on OAuth and sync infrastructure for publishing
4. **Task 4** - Builds on OAuth for stats fetching
5. **Task 5** - Final polish with conflict resolution and sync history

## Notes

- All YouTube API calls should use the `YouTubeAPIService` from Task 1
- OAuth tokens should be stored encrypted in the database
- YouTube API rate limits must be respected (quota management)
- All new models need migration scripts
- All new endpoints should follow the existing API patterns
- Frontend components should use the existing styling conventions
- Error handling should be consistent across all new services
