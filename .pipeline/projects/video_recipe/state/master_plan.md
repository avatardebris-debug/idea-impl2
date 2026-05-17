# Master Plan: Video Recipe — Deconstruct Video Actions into Step-by-Step Recipes

## Goal
Build a system that takes a video (URL or file) and produces a structured, human-readable recipe describing how to perform the task shown in the video — breaking down actions into discrete, ordered steps with timestamps, descriptions, and inferred tools/materials.

## Core Deliverable
A CLI tool that accepts a video input and outputs a structured recipe (JSON + markdown) of the actions depicted in the video.

## Phase 1: Core Deconstruction Engine — MVP
- **Description**: Build the foundational pipeline that accepts a video file/URL, extracts key frames and audio, and uses an LLM to produce a structured recipe with timestamped steps. This is a fully functional end-to-end tool — it takes video in and outputs a recipe out.
- **Deliverable**: A working CLI tool (`video_recipe/`) that:
  - Accepts a video file path or YouTube URL as input
  - Extracts key frames at regular intervals (e.g., every 2 seconds)
  - Extracts audio transcript via speech-to-text
  - Sends key frames + transcript to an LLM with a structured prompt
  - Outputs a JSON recipe with fields: `title`, `steps` (array of `{timestamp, description, inferred_tools, inferred_materials}`), `summary`
  - Optionally renders the same recipe as markdown
- **Dependencies**: none
- **Success criteria**:
  - Can process a 30-second cooking demo video and produce a recipe with at least 5 timestamped steps
  - Output JSON is valid and parseable
  - CLI accepts `--input <path_or_url>` and `--format json|markdown` flags
  - Recipe steps are temporally ordered and describe distinct actions (not redundant)

## Phase 2: Recipe Enrichment & Structured Output
- **Description**: Enhance the recipe output with inferred metadata — ingredient lists, equipment needed, difficulty estimation, estimated total time, and alternative phrasing suggestions. Add support for multiple video formats and improve frame extraction quality.
- **Deliverable**: 
  - Recipe objects with enriched fields: `ingredients`, `equipment`, `difficulty` (easy/medium/hard), `estimated_time_minutes`, `key_takeaways`
  - Support for MP4, MOV, AVI, and YouTube URLs
  - Adaptive frame extraction (more frames during fast-motion, fewer during static shots)
  - A `--enrich` flag that triggers the enrichment pipeline
- **Dependencies**: Phase 1
- **Success criteria**:
  - Processing the same 30-second video now produces 7+ enriched fields
  - Ingredient list contains at least 3 items for cooking videos (validated against ground truth)
  - Adaptive frame extraction reduces total frames processed by ~30% without losing step detection accuracy
  - All supported video formats produce equivalent output quality

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
