"""
app.py — Flask web app for Video Babbel Enhanced.

Routes:
    GET  /upload          — Upload page
    GET  /clips           — Clip listing page
    GET  /watch/<clip_id> — Watch page for a clip
    GET  /drill           — Drill page
    GET  /lipsync/<clip_id> — Lip sync page
    POST /extract         — Trigger extraction pipeline
    GET  /clips           — REST: list all clips as JSON
    GET  /stats           — REST: session statistics
    POST /review/<clip_id> — REST: record a review
    GET  /review/history/<clip_id> — REST: review history
    POST /sessions        — REST: create session
    GET  /sessions        — REST: list sessions
    GET  /sessions/<id>   — REST: session details
    POST /export          — REST: export clips
    GET  /export/<session_id> — REST: export session data
    POST /lipsync/<clip_id> — REST: trigger lip sync
"""
from __future__ import annotations
import json
import os
import pathlib
import uuid
from datetime import datetime

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB upload limit
UPLOAD_FOLDER = pathlib.Path("uploads")
CLIPS_FOLDER = pathlib.Path("clips")
DB_PATH = pathlib.Path("video_babbel.db")

UPLOAD_FOLDER.mkdir(exist_ok=True)
CLIPS_FOLDER.mkdir(exist_ok=True)


# ─── Upload page ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("upload_page"))


@app.route("/upload")
def upload_page():
    return render_template("upload.html")


@app.route("/clips")
def clips_page():
    return render_template("clips.html")


# ─── Watch page ────────────────────────────────────────────────────────────

@app.route("/watch/<clip_id>")
def watch_page(clip_id: str):
    return render_template("watch.html", clip_id=clip_id)


# ─── Drill page ────────────────────────────────────────────────────────────

@app.route("/drill")
def drill_page():
    return render_template("drill.html")


# ─── Lip sync page ─────────────────────────────────────────────────────────

@app.route("/lipsync/<clip_id>")
def lipsync_page(clip_id: str):
    return render_template("lipsync.html", clip_id=clip_id)


# ─── REST API: Upload + Extract ────────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Handle file upload. Saves the video file and returns its path."""
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    if video_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Save the uploaded file
    filename = f"{uuid.uuid4().hex}_{video_file.filename}"
    save_path = UPLOAD_FOLDER / filename
    video_file.save(str(save_path))

    return jsonify({
        "status": "ok",
        "filename": filename,
        "path": str(save_path),
    })


@app.route("/api/extract", methods=["POST"])
def api_extract():
    """Trigger the extraction pipeline on an uploaded video."""
    data = request.get_json(force=True) if request.is_json else {}
    filename = data.get("filename") or request.form.get("filename")
    target_lang = data.get("target_lang") or request.form.get("target_lang", "es")
    source_lang = data.get("source_lang") or request.form.get("source_lang", "en")
    top_n = int(data.get("top_n") or request.form.get("top_n", 50))

    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    video_path = UPLOAD_FOLDER / filename
    if not video_path.exists():
        return jsonify({"error": f"Video file not found: {video_path}"}), 404

    # Run extraction pipeline
    try:
        from video_babbel_enhanced.transcriber import transcribe
        from video_babbel_enhanced.translator import translate
        from video_babbel_enhanced.frequency_scorer import score_segments
        from video_babbel_enhanced.clip_extractor import extract_clips
        from video_babbel_enhanced.session_db import import_clips_from_json, init_db

        # Initialize DB
        init_db(DB_PATH)

        # Step 1: Transcribe
        segments = transcribe(str(video_path), language=source_lang if source_lang != "auto" else None)
        if not segments:
            return jsonify({"error": "No speech detected"}), 400

        # Step 2: Translate
        segments = translate(segments, target_lang=target_lang, source_lang=source_lang)

        # Step 3: Score
        segments = score_segments(segments)

        # Step 4: Extract clips
        clips = extract_clips(str(video_path), segments, CLIPS_FOLDER, top_n=top_n)

        # Import clips into DB
        json_files = [str(CLIPS_FOLDER / f"clip_{i:03d}.json") for i in range(len(clips))]
        imported = import_clips_from_json(json_files, DB_PATH)

        return jsonify({
            "status": "ok",
            "clips_extracted": len(clips),
            "clips_imported": imported,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── REST API: Clips ───────────────────────────────────────────────────────

@app.route("/api/clips")
def api_clips():
    """Return all clips as JSON."""
    from video_babbel_enhanced.session_db import get_all_clips, init_db
    init_db(DB_PATH)
    clips = get_all_clips(DB_PATH)
    return jsonify(clips)


# ─── REST API: Stats ───────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    """Return session statistics."""
    from video_babbel_enhanced.session_db import get_session_stats, init_db
    init_db(DB_PATH)
    stats = get_session_stats(DB_PATH)
    return jsonify(stats)


# ─── REST API: Review ──────────────────────────────────────────────────────

@app.route("/api/review/<clip_id>", methods=["POST"])
def api_review(clip_id: str):
    """Record a review quality rating."""
    data = request.get_json(force=True) if request.is_json else {}
    quality = int(data.get("quality") or request.form.get("quality", 0))
    session_id = data.get("session_id")

    if quality < 0 or quality > 5:
        return jsonify({"error": "Quality must be 0-5"}), 400

    from video_babbel_enhanced.session_db import record_review, init_db
    init_db(DB_PATH)

    try:
        updated_clip = record_review(clip_id, quality, session_id, DB_PATH)
        return jsonify({"status": "ok", "clip": updated_clip})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/review/history/<clip_id>")
def api_review_history(clip_id: str):
    """Return review history for a clip."""
    from video_babbel_enhanced.session_db import init_db
    init_db(DB_PATH)
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    try:
        rows = conn.execute(
            "SELECT quality, review_date, session_id FROM reviews WHERE clip_id = ? ORDER BY review_date DESC",
            (clip_id,),
        ).fetchall()
        history = [
            {"quality": r[0], "review_date": r[1], "session_id": r[2]}
            for r in rows
        ]
        return jsonify(history)
    finally:
        conn.close()


# ─── REST API: Sessions ────────────────────────────────────────────────────

@app.route("/api/sessions", methods=["POST"])
def api_create_session():
    """Create a new drill session."""
    data = request.get_json(force=True) if request.is_json else {}
    name = data.get("name") or request.form.get("name", "Drill Session")
    description = data.get("description") or request.form.get("description", "")

    from video_babbel_enhanced.session_db import create_session, init_db
    init_db(DB_PATH)
    session_id = create_session(name, description, DB_PATH)
    return jsonify({"status": "ok", "session_id": session_id})


@app.route("/api/sessions")
def api_list_sessions():
    """List all sessions."""
    from video_babbel_enhanced.session_db import init_db
    init_db(DB_PATH)
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    try:
        rows = conn.execute(
            "SELECT id, name, created_at, description FROM sessions ORDER BY created_at DESC"
        ).fetchall()
        sessions = [
            {"id": r[0], "name": r[1], "created_at": r[2], "description": r[3]}
            for r in rows
        ]
        return jsonify(sessions)
    finally:
        conn.close()


@app.route("/api/sessions/<session_id>")
def api_session_details(session_id: int):
    """Get session details."""
    from video_babbel_enhanced.session_db import init_db
    init_db(DB_PATH)
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    try:
        row = conn.execute(
            "SELECT id, name, created_at, description FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return jsonify({"error": "Session not found"}), 404

        # Get clips reviewed in this session
        clips = conn.execute(
            """SELECT c.*, r.quality, r.review_date
               FROM reviews r
               JOIN clips c ON r.clip_id = c.clip_id
               WHERE r.session_id = ?
               ORDER BY r.review_date""",
            (session_id,),
        ).fetchall()

        cols = [d[0] for d in conn.execute("SELECT * FROM clips LIMIT 1").description]
        session_data = {
            "id": row[0],
            "name": row[1],
            "created_at": row[2],
            "description": row[3],
            "clips": [dict(zip(cols, r)) for r in clips],
        }
        return jsonify(session_data)
    finally:
        conn.close()


# ─── REST API: Export ──────────────────────────────────────────────────────

@app.route("/api/export", methods=["POST"])
def api_export():
    """Export clips to Anki deck."""
    data = request.get_json(force=True) if request.is_json else {}
    deck_name = data.get("deck_name") or request.form.get("deck_name", "Video Babbel")
    output_path = data.get("output_path") or request.form.get("output_path", "video_babbel_deck.apkg")

    from video_babbel_enhanced.anki_export import export_anki
    export_anki(deck_name, DB_PATH, output_path)
    return jsonify({"status": "ok", "output": output_path})


# ─── REST API: Lip Sync ────────────────────────────────────────────────────

@app.route("/api/lipsync/<clip_id>", methods=["POST"])
def api_lipsync(clip_id: str):
    """Trigger lip sync for a clip."""
    from video_babbel_enhanced.session_db import init_db
    init_db(DB_PATH)
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    try:
        row = conn.execute("SELECT * FROM clips WHERE clip_id = ?", (clip_id,)).fetchone()
        if not row:
            return jsonify({"error": "Clip not found"}), 404
    finally:
        conn.close()

    # Trigger lip sync (async in production)
    try:
        from video_babbel_enhanced.lip_sync import generate_lipsync
        generate_lipsync(clip_id, DB_PATH)
        return jsonify({"status": "ok", "message": "Lip sync generated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Run ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
