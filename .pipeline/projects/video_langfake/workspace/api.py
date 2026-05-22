"""REST API for video_langfake using Flask.

Provides endpoints for video translation, language detection, and health checks.

Usage:
    python -m video_langfake.api  # runs on http://0.0.0.0:5000
"""

import os
import json
import logging
import tempfile
import shutil
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify, send_file

from video_langfake.pipeline import VideoLangFake
from video_langfake.translate import SUPPORTED_LANGUAGES, LANG_NAMES
from video_langfake.exceptions import PipelineError, VideoLangFakeError

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("video_langfake.api")

# In-memory job tracking (for demo; use Redis in production)
_active_jobs: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error_response(message: str, status_code: int = 400) -> tuple:
    """Return a JSON error response tuple."""
    return jsonify({"error": message, "status": status_code}), status_code


def _success_response(data: dict, status_code: int = 200) -> tuple:
    """Return a JSON success response tuple."""
    return jsonify({"status": "success", **data}), status_code


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "video_langfake",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    })


@app.route("/languages", methods=["GET"])
def languages():
    """Return the list of supported languages."""
    lang_list = []
    for code, name in LANG_NAMES.items():
        lang_list.append({"code": code, "name": name})
    return jsonify({
        "supported_languages": lang_list,
        "count": len(lang_list),
    })


@app.route("/translate", methods=["POST"])
def translate():
    """Translate a video to a target language.

    Expects a multipart form with:
        - video: video file (mp4, avi, mov, etc.)
        - target_language: target language code (e.g. 'es', 'fr')
        - source_language: optional source language code
        - output_filename: optional output filename (default: translated.mp4)

    Returns:
        JSON with job_id and status, or the output video file directly.
    """
    # Validate request
    if "video" not in request.files:
        return _error_response("Missing 'video' file in request", 400)

    video_file = request.files["video"]
    if video_file.filename == "":
        return _error_response("Empty video filename", 400)

    target_language = request.form.get("target_language")
    if not target_language:
        return _error_response("Missing 'target_language' parameter", 400)

    source_language = request.form.get("source_language")
    output_filename = request.form.get("output_filename", "translated.mp4")

    # Validate language
    if target_language not in SUPPORTED_LANGUAGES:
        return _error_response(
            f"Unsupported target language '{target_language}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}",
            400,
        )

    # Create temp directory for processing
    tmp_dir = tempfile.mkdtemp(prefix="api_")
    video_path = os.path.join(tmp_dir, video_file.filename)
    output_path = os.path.join(tmp_dir, output_filename)

    try:
        video_file.save(video_path)

        # Generate a job ID
        job_id = f"job_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{os.getpid()}"

        # Track the job
        _active_jobs[job_id] = {
            "status": "processing",
            "started_at": datetime.utcnow().isoformat(),
            "target_language": target_language,
            "source_language": source_language,
            "output_path": output_path,
        }

        # Run the pipeline
        pipeline = VideoLangFake()
        try:
            pipeline.process(
                video_path=video_path,
                target_language=target_language,
                output_path=output_path,
                source_language=source_language,
            )
        finally:
            pipeline.cleanup()

        # Update job status
        _active_jobs[job_id]["status"] = "completed"
        _active_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

        # Return the output file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype="video/mp4",
        )

    except PipelineError as e:
        _active_jobs[job_id]["status"] = "failed"
        _active_jobs[job_id]["error"] = str(e)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return _error_response(f"Pipeline error: {e}", 500)
    except Exception as e:
        _active_jobs[job_id]["status"] = "failed"
        _active_jobs[job_id]["error"] = str(e)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        logger.exception("Unexpected error in translate endpoint")
        return _error_response(f"Internal server error: {str(e)}", 500)


@app.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id: str):
    """Get the status of a translation job."""
    if job_id not in _active_jobs:
        return _error_response(f"Job '{job_id}' not found", 404)

    job = _active_jobs[job_id]
    return jsonify({
        "job_id": job_id,
        "status": job["status"],
        "target_language": job.get("target_language"),
        "source_language": job.get("source_language"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "error": job.get("error"),
    })


@app.route("/jobs", methods=["GET"])
def list_jobs():
    """List all active jobs."""
    jobs = []
    for job_id, job in _active_jobs.items():
        jobs.append({
            "job_id": job_id,
            "status": job["status"],
            "target_language": job.get("target_language"),
            "started_at": job.get("started_at"),
        })
    return jsonify({"jobs": jobs, "count": len(jobs)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    """Factory function to create the Flask app (for gunicorn, etc.)."""
    return app


def main():
    """Run the API server."""
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
