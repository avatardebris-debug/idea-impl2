## Phase 3: Interactive Recipe Browser & Comparison
- **Description**: Build a lightweight web interface for browsing, comparing, and exporting recipes. Users can upload multiple videos, compare their generated recipes side-by-side, annotate steps, and export to common formats (PDF, Notion markdown, plain text).
- **Deliverable**:
  - Flask/FastAPI web app with routes: `/upload`, `/recipe/<id>`, `/compare`, `/export`
  - Recipe storage in SQLite with indexing by task type (cooking, repair, craft, etc.)
  - Side-by-side comparison view for 2+ recipes
  - Export to PDF, markdown, and plain text
  - Annotate/edit steps before finalizing
- **Dependencies**: Phase 1, Phase 2
- **Success criteria**:
  - Can upload 3 different videos and view all 3 recipes in the browser
  - Side-by-side comparison renders correctly with synchronized scrolling
  - Exported PDF matches the on-screen recipe layout
  - Recipe search by task type returns relevant results within 1 second

## Architecture Notes
- **Tech Stack**: Python, FFmpeg (frame extraction), Whisper/Whisper.cpp (speech-to-text), OpenAI API or local LLM (recipe generation), SQLite (storage), FastAPI (web layer)
- **Frame Extraction**: Use FFmpeg's `fps` and `select` filters to extract key frames. For YouTube, use `yt-dlp` to download first.
- **LLM Prompt Design**: Use a structured prompt with system instructions to output JSON. Include few-shot examples of video-to-recipe mappings.
- **Storage**: SQLite with tables: `videos` (id, url, path, duration, task_type), `recipes` (id, video_id, json_content, enriched_json), `annotations` (id, recipe_id, step_index, user_note)
- **Extensibility**: Design the LLM client as an abstract interface so any LLM backend can be swapped in.

## Risks
1. **LLM accuracy on visual actions**: The LLM may hallucinate steps or miss subtle actions. Mitigation: use high frame rate extraction + audio transcript as complementary signals; add a validation step.
2. **Video processing performance**: Long videos will be slow to process. Mitigation: adaptive frame extraction (Phase 2) and optional duration limits in Phase 1.
3. **Speech recognition quality**: Poor audio (background noise, accents) will degrade recipe quality. Mitigation: use Whisper-large model; allow manual transcript override.
4. **YouTube URL access**: yt-dlp may break with YouTube API changes. Mitigation: pin yt-dlp version; provide fallback for local files only.
5. **Task type diversity**: The system needs to handle cooking, repair, crafts, fitness, etc. Mitigation: Phase 1 uses a generic prompt; Phase 2 adds task-type detection and specialized prompt templates.