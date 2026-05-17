"""Pipeline — End-to-end video generation from text descriptions."""

from __future__ import annotations

from typing import Optional

from videopow.core import VideoProcessor
from videopow.describer import VideoDescriber


def generate_video(
    description: str,
    input_video_path: str,
    output_path: Optional[str] = None,
    overlay_text: Optional[str] = None,
    overlay_position: Optional[str] = None,
    fps: Optional[float] = None,
) -> dict:
    """Generate a video transformation from a text description.

    This is the main entry point for the VideoPow pipeline. It:
      1. Parses the text description into structured editing instructions
      2. Applies the transformations to the input video
      3. Returns details about the processed video

    Args:
        description: Natural-language description of the desired video edit.
            Examples:
                - "slow zoom on a forest"
                - "grayscale with 5 second duration"
                - "sepia tone with text overlay at bottom center"
                - "cinematic with blur and brightness 30"
        input_video_path: Path to the input video file.
        output_path: Optional output file path. Auto-generated if None.
        overlay_text: Optional text to overlay on the video.
        overlay_position: Optional position for the text overlay.

    Returns:
        Dictionary with keys:
            - output_path: Path to the generated video
            - frames_processed: Number of frames processed
            - duration_seconds: Duration of the output video
            - width: Output video width
            - height: Output video height
            - fps: Output video frame rate
            - effect_applied: Name of the primary effect applied
            - instructions: Parsed EditingInstructions object

    Raises:
        FileNotFoundError: If the input video does not exist.
        ValueError: If the description is empty or the format is unsupported.
        RuntimeError: If processing fails.
    """
    if not description or not description.strip():
        raise ValueError("Description cannot be empty")

    # Step 1: Parse the description
    instructions = VideoDescriber.parse(description)

    # Step 2: Process the video
    processor = VideoProcessor(input_video_path)

    try:
        result = processor.process(
            effect=instructions.effect,
            grayscale=instructions.grayscale,
            sepia=instructions.sepia,
            blur_amount=instructions.blur_amount,
            brightness=instructions.brightness,
            contrast=instructions.contrast,
            rotation=instructions.rotation,
            crop=instructions.crop,
            zoom_amount=instructions.zoom_amount,
            speed_multiplier=instructions.speed_multiplier,
            overlay_text=overlay_text or instructions.overlay_text,
            overlay_position=overlay_position or instructions.overlay_position,
            output_path=output_path,
        )
    finally:
        processor.close()

    return {
        "output_path": result.output_path,
        "frames_processed": result.frames_processed,
        "duration_seconds": result.duration_seconds,
        "width": result.width,
        "height": result.height,
        "fps": result.fps,
        "effect_applied": result.effect_applied,
        "instructions": instructions,
    }
