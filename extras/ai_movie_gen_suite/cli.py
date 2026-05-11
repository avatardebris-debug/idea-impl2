"""CLI for the AI Movie Generation Suite."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from ai_movie_gen_suite.config import AppConfig, load_config, save_config
from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.project_manager import (
    create_project,
    load_project,
    run_full_pipeline,
    save_project,
    regenerate_downstream,
)
from ai_movie_gen_suite.formatters.screenplay_formatter import format_screenplay_text

app = typer.Typer(
    name="ai-movie",
    help="AI Movie Generation Suite — Generate screenplays with AI",
)


def _get_config(ctx: typer.Context) -> AppConfig:
    """Get config from context or load from disk."""
    return ctx.obj if ctx.obj else AppConfig()


@app.command()
def init(
    logline: str = typer.Argument(..., help="The logline for your screenplay"),
    title: str = typer.Option("Untitled", "--title", "-t", help="Project title"),
    genre: str = typer.Option("drama", "--genre", "-g", help="Genre of the screenplay"),
    tone: str = typer.Option("", "--tone", help="Tone/mood of the screenplay"),
    project_dir: str = typer.Option("./projects/my_movie", "--project-dir", "-p", help="Output directory"),
    config_file: str = typer.Option("config.json", "--config", "-c", help="Config file path"),
):
    """Create a new screenplay project."""
    config = load_config(Path(config_file))
    project = create_project(
        title=title,
        logline=logline,
        genre=genre,
        tone=tone,
    )
    project_dir_path = Path(project_dir)
    save_project(project, project_dir_path)
    typer.echo(f"✅ Project created: {project_dir_path / 'project.json'}")
    typer.echo(f"   Title: {title}")
    typer.echo(f"   Logline: {logline}")
    typer.echo(f"   Genre: {genre}")
    typer.echo(f"\nRun 'ai-movie generate' to start the pipeline.")


@app.command()
def generate(
    project_dir: str = typer.Option("./projects/my_movie", "--project-dir", "-p", help="Project directory"),
    config_file: str = typer.Option("config.json", "--config", "-c", help="Config file path"),
):
    """Run the full AI pipeline: beats → characters → script → scenes."""
    config = load_config(Path(config_file))
    project, _ = load_project(Path(project_dir))
    paths = run_full_pipeline(project, config, Path(project_dir))
    typer.echo("✅ Pipeline complete!")
    for name, path in paths.items():
        typer.echo(f"   {name}: {path}")


@app.command()
def edit(
    project_dir: str = typer.Option("./projects/my_movie", "--project-dir", "-p", help="Project directory"),
    config_file: str = typer.Option("config.json", "--config", "-c", help="Config file path"),
    element: str = typer.Option(..., "--element", "-e", help="Element to edit: beats, characters, script"),
    value: str = typer.Option(..., "--value", "-v", help="New value (JSON string)"),
):
    """Edit an element and regenerate downstream."""
    config = load_config(Path(config_file))
    project, _ = load_project(Path(project_dir))

    # Parse and update the element
    data = json.loads(value)
    if element == "beats":
        from ai_movie_gen_suite.models import BeatSheet
        project.beats = BeatSheet(**data)
    elif element == "characters":
        from ai_movie_gen_suite.models import CharacterRegistry
        project.characters = CharacterRegistry(**data)
    elif element == "script":
        from ai_movie_gen_suite.models import Script
        project.script = Script(**data)
    else:
        typer.echo(f"❌ Unknown element: {element}")
        raise typer.Exit(1)

    save_project(project, Path(project_dir))
    typer.echo(f"✅ {element} updated. Run 'ai-movie regenerate' to update downstream.")


@app.command()
def regenerate(
    project_dir: str = typer.Option("./projects/my_movie", "--project-dir", "-p", help="Project directory"),
    config_file: str = typer.Option("config.json", "--config", "-c", help="Config file path"),
    from_element: str = typer.Option("beats", "--from", "-f", help="Regenerate from: beats, characters, script, scenes"),
):
    """Regenerate downstream artifacts from a given element."""
    config = load_config(Path(config_file))
    project, _ = load_project(Path(project_dir))
    paths = regenerate_downstream(project, config, Path(project_dir), from_element)
    typer.echo("✅ Regeneration complete!")
    for name, path in paths.items():
        typer.echo(f"   {name}: {path}")


@app.command()
def format(
    project_dir: str = typer.Option("./projects/my_movie", "--project-dir", "-p", help="Project directory"),
    output: str = typer.Option("screenplay.txt", "--output", "-o", help="Output file path"),
):
    """Format the script as a screenplay text file."""
    project, _ = load_project(Path(project_dir))
    if not project.script:
        typer.echo("❌ No script found. Run 'generate' first.")
        raise typer.Exit(1)

    text = format_screenplay_text(project.script)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(text)
    typer.echo(f"✅ Screenplay formatted to: {output}")


@app.command()
def status(
    project_dir: str = typer.Option("./projects/my_movie", "--project-dir", "-p", help="Project directory"),
):
    """Show project status and available artifacts."""
    project, _ = load_project(Path(project_dir))
    typer.echo(f"📽️  Project: {project.title}")
    typer.echo(f"   Logline: {project.logline}")
    typer.echo(f"   Genre: {project.genre}")
    typer.echo(f"   Tone: {project.tone}")
    typer.echo(f"\n📁 Artifacts:")
    typer.echo(f"   Beats: {'✅' if project.beats else '❌'}")
    typer.echo(f"   Characters: {'✅' if project.characters else '❌'}")
    typer.echo(f"   Script: {'✅' if project.script else '❌'}")
    typer.echo(f"   Scenes: {'✅' if (Path(project_dir) / 'scenes').exists() else '❌'}")


@app.command()
def config_show():
    """Show current configuration."""
    config = load_config(Path("config.json"))
    typer.echo(json.dumps(config.to_dict(), indent=2))


@app.command()
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g., llm.api_key)"),
    value: str = typer.Argument(..., help="Config value"),
    config_file: str = typer.Option("config.json", "--config", "-c", help="Config file path"),
):
    """Set a configuration value."""
    config = load_config(Path(config_file))
    # Simple dot-path update
    parts = key.split(".")
    obj = config
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)
    save_config(config, Path(config_file))
    typer.echo(f"✅ Config updated: {key} = {value}")


if __name__ == "__main__":
    app()
