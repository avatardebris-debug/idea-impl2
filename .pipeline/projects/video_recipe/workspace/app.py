"""FastAPI web app for video_recipe — browse, compare, annotate, and export recipes."""

import json
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from video_recipe.storage import RecipeStore
from video_recipe.task_type_detector import detect_task_type
from video_recipe.models import Video, Recipe, RecipeStep

app = FastAPI(title="Video Recipe Browser")

store = RecipeStore()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

# Mount static files
static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── Helpers ────────────────────────────────────────────────────────

def _recipe_to_dict(recipe_row: dict) -> dict:
    """Convert a DB recipe row to a serializable dict."""
    return {
        "id": recipe_row["recipe_id"],
        "video_id": recipe_row["video_id"],
        "filename": recipe_row["filename"],
        "task_type": recipe_row["task_type"],
        "duration": recipe_row["duration"],
        "created_at": recipe_row["created_at"],
        "json_content": json.loads(recipe_row["json_content"]),
    }


# ── Routes ─────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page — list all recipes."""
    videos = store.get_all_videos()
    return templates.TemplateResponse("index.html", {"request": request, "videos": videos})


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    task_type: str = Form(default=""),
):
    """Upload a video and process it."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid file type. Please upload a video file."},
        )
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid file name."},
        )
    valid_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"}
    ext = Path(file.filename).suffix.lower()
    if ext not in valid_extensions:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid file type. Please upload a video file."},
        )
    # Save uploaded file
    upload_dir = Path(__file__).resolve().parent.parent / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Detect task type if not provided
    if not task_type:
        task_type = detect_task_type(file.filename) or detect_task_type(content.decode("utf-8", errors="ignore"))

    # Add video entry
    video_id = str(uuid.uuid4())
    video = Video(
        video_id=video_id,
        filename=file.filename,
        task_type=task_type,
        duration=None,
        original_path=str(file_path),
    )
    store.add_video(video)

    # Generate recipe (mock for now — in production, call the pipeline)
    recipe = Recipe(
        video_id=video_id,
        title=f"Recipe for {file.filename}",
        summary="Auto-generated recipe from video.",
        steps=[
            RecipeStep(
                step_index=0,
                description="Step 1: Prepare ingredients",
                timestamp=0.0,
                inferred_tools=[],
                inferred_materials=[],
            ),
            RecipeStep(
                step_index=1,
                description="Step 2: Execute main action",
                timestamp=5.0,
                inferred_tools=[],
                inferred_materials=[],
            ),
            RecipeStep(
                step_index=2,
                description="Step 3: Finalize",
                timestamp=10.0,
                inferred_tools=[],
                inferred_materials=[],
            ),
        ],
    )
    recipe_id = store.add_recipe(video_id, recipe)

    recipe_data = store.get_recipe(recipe_id)
    return JSONResponse({"recipe": recipe_data})


@app.get("/recipe/{recipe_id}")
async def view_recipe(recipe_id: str):
    """View a single recipe."""
    recipe_data = store.get_recipe(recipe_id)
    if not recipe_data:
        raise HTTPException(status_code=404, detail="Recipe not found")
    annotations = store.get_annotations(recipe_id)
    return JSONResponse({"recipe": recipe_data, "annotations": annotations})


@app.get("/compare", response_class=HTMLResponse)
async def compare(request: Request):
    """Compare two recipes side-by-side."""
    videos = store.get_all_videos()
    # Convert videos to a list of tuples to avoid Jinja2 cache hashing issues
    videos_hashable = tuple(tuple(sorted(v.items())) for v in videos)
    return templates.TemplateResponse("compare.html", {"request": request, "videos": videos_hashable})


@app.post("/compare")
async def compare_recipes(
    recipe_id_1: str = Form(...),
    recipe_id_2: str = Form(...),
):
    """Compare two recipes."""
    recipe_1_data = store.get_recipe(recipe_id_1)
    recipe_2_data = store.get_recipe(recipe_id_2)
    if not recipe_1_data or not recipe_2_data:
        raise HTTPException(status_code=404, detail="One or both recipes not found")
    return JSONResponse({"recipe_1": recipe_1_data, "recipe_2": recipe_2_data})


@app.post("/recipe/{recipe_id}/annotate")
async def annotate_recipe(recipe_id: str, step_index: int = Form(...), user_note: str = Form(...)):
    """Add an annotation to a recipe step."""
    store.add_annotation(recipe_id, step_index, user_note)
    return JSONResponse({"status": "ok"})


@app.get("/export/{recipe_id}/pdf")
async def export_pdf(recipe_id: str):
    """Export recipe as PDF (simplified — returns markdown for now)."""
    recipe_data = store.get_recipe(recipe_id)
    if not recipe_data:
        raise HTTPException(status_code=404, detail="Recipe not found")
    # In production, use reportlab or weasyprint to generate PDF
    # For now, return markdown as a text file
    md = _recipe_to_markdown(recipe_data)
    return PlainTextResponse(md, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename={recipe_id}.md"})


@app.get("/export/{recipe_id}/text")
async def export_text(recipe_id: str):
    """Export recipe as plain text."""
    recipe_data = store.get_recipe(recipe_id)
    if not recipe_data:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return PlainTextResponse(_recipe_to_markdown(recipe_data), media_type="text/plain")


@app.get("/search")
async def search_recipes(task_type: str = ""):
    """Search recipes by task type (JSON API)."""
    if not task_type:
        videos = store.get_all_videos()
        return JSONResponse(videos)
    results = store.search_by_task_type(task_type)
    return JSONResponse(results)


# ── Markdown helper ────────────────────────────────────────────────

def _recipe_to_markdown(recipe: dict) -> str:
    """Convert recipe dict to markdown string."""
    lines = [f"# {recipe.get('title', 'Untitled')}", ""]
    summary = recipe.get("summary", "")
    if summary:
        lines.append(f"{summary}\n")
    lines.append("## Steps")
    lines.append("")
    for i, step in enumerate(recipe.get("steps", []), 1):
        lines.append(f"{i}. **{step.get('description', 'Step ' + str(i))}**")
        tools = step.get("inferred_tools", [])
        materials = step.get("inferred_materials", [])
        if tools:
            lines.append(f"   - Tools: {', '.join(tools)}")
        if materials:
            lines.append(f"   - Materials: {', '.join(materials)}")
        lines.append("")
    return "\n".join(lines)
