## Phase 2: YouTube Suite Integration

**Goal**: Connect the platform to real YouTube data so videos are not just local records.

**Description**: Integrate with YouTube Data API v3 to sync channel data, video metadata, and upload capabilities. Users authenticate their YouTube channel, and the platform pulls in existing videos, channel stats, and allows creating new videos directly from the platform. This bridges the gap between a local organizer and a real publishing workflow.

**Deliverable**:
- OAuth 2.0 YouTube channel connection flow
- Video sync engine (pull existing videos, thumbnails, stats)
- YouTube upload endpoint (create video with metadata via API)
- Channel stats dashboard (subscribers, views, revenue)
- Sync status indicator and conflict resolution

**Dependencies**: Phase 1 (data model for storing synced video records)

**Success Criteria**:
- [ ] User can connect their YouTube channel via OAuth
- [ ] All existing channel videos are synced into the platform within 5 minutes
- [ ] New videos created in the platform can be published to YouTube
- [ ] Channel stats update automatically (every 15 min or on demand)
- [ ] Sync handles deleted/removed YouTube videos gracefully

---

