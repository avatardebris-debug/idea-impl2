## Phase 3: Web UI + Lip Sync Integration

**Goal:** Flask web app for upload → configure → watch → drill. Optional video_langfake lip sync.

**Deliverables:**
- `app.py` — Flask app with routes: `/upload`, `/configure`, `/watch`, `/drill`, `/export`
- Upload page: drop video, select source language + target language, set N clips
- Watch page: video player with toggle L1/L2 audio track + dual subtitles
- Drill page: web-based SM-2 drill loop (JS + fetch API)
- Optional: trigger `video_langfake` workspace on selected clips → dubbed .mp4 variant
- REST API: `POST /extract`, `GET /clips`, `POST /review/{clip_id}`

**Success Criteria:**
- [ ] Web app starts with `python app.py` and is accessible at localhost:5000
- [ ] Full pipeline runnable from the UI: upload → extract → watch/drill
- [ ] L1/L2 audio track toggle works in the player
- [ ] Drill loop records scores and respects SM-2 next_review dates
- [ ] If video_langfake workspace exists, dubbed clip generation can be triggered
- [ ] All integration tests pass