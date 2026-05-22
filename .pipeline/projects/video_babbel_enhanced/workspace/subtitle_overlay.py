"""
subtitle_overlay.py — Overlay translated subtitles onto video clips.

Uses ffmpeg to burn subtitles into video clips, producing a bilingual
learning video with source and target language subtitles.

Usage:
    python -m video_babbel_enhanced overlay-clips --clips clips/ --output overlayed/
    python video_babbel_enhanced/subtitle_overlay.py --clips clips/ --output overlayed/
"""
from __future__ import annotations
import json
import os
import pathlib
import subprocess
import sys
from typing import Any


def _generate_srt(segments: list[dict[str, Any]], target_lang: str = "en") -> str:
    """Generate SRT subtitle content from clip segments.

    Args:
        segments: List of clip dicts with start/end times and text.
        target_lang: Target language code for subtitle track name.

    Returns:
        SRT formatted string.
    """
    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = seg.get("start", seg.get("start_time", 0))
        end = seg.get("end", seg.get("end_time", 0))
        l1 = seg.get("l1_text", "")
        l2 = seg.get("l2_text", "")

        # Format time as SRT: HH:MM:SS,mmm
        def fmt_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

        start_str = fmt_time(start)
        end_str = fmt_time(end)

        # Combine L1 and L2 for bilingual subtitles
        subtitle_text = f"{l1}\n{l2}" if l1 and l2 else (l1 or l2)

        srt_lines.append(f"{i}\n{start_str} --> {end_str}\n{subtitle_text}")

    return "\n\n".join(srt_lines)


def overlay_subtitles(
    clip_path: str | pathlib.Path,
    segments: list[dict[str, Any]],
    output_path: str | pathlib.Path,
    font_size: int = 24,
    font_color: str = "white",
    border_color: str = "black",
    border_width: int = 2,
    position: str = "bottom",
) -> pathlib.Path:
    """Overlay subtitles onto a video clip using ffmpeg.

    Args:
        clip_path: Path to the input video file.
        segments: List of clip dicts with timing and text.
        output_path: Path for the output video file.
        font_size: Font size for subtitles.
        font_color: Font color (ffmpeg color name).
        border_color: Subtitle border color.
        border_width: Subtitle border width in pixels.
        position: Subtitle position ('bottom', 'top', 'middle').

    Returns:
        Path to the output video file.
    """
    clip_path = pathlib.Path(clip_path)
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate SRT content
    srt_content = _generate_srt(segments)

    # Write SRT to a temporary file
    srt_path = output_path.with_suffix(".srt")
    srt_path.write_text(srt_content, encoding="utf-8")

    try:
        # Build ffmpeg command with subtitle filter
        border_style = f"\\b{border_width}\\c&H{border_color[0:6]}&"
        font_color_hex = f"&H{font_color[0:6]}&" if len(font_color) >= 6 else "&HFFFFFF&"

        # Position mapping
        pos_map = {
            "bottom": "h-h*0.9",
            "top": "h*0.1",
            "middle": "h*0.5",
        }
        y_pos = pos_map.get(position, "h-h*0.9")

        # FFmpeg subtitle filter
        sub_filter = (
            f"subtitles={srt_path.as_posix()}"
            f":force_style='FontName=Arial,FontSize={font_size},"
            f"PrimaryColour={font_color_hex},"
            f"OutlineColour={border_style},"
            f"BorderStyle=1,Outline={border_width},"
            f"Alignment=2,MarginV=10'"
        )

        cmd = [
            "ffmpeg",
            "-i", str(clip_path),
            "-vf", sub_filter,
            "-c:a", "copy",  # Copy audio without re-encoding
            "-y",  # Overwrite output
            str(output_path),
        ]

        print(f"  Processing: {clip_path.name} → {output_path.name}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            print(f"  ✗ ffmpeg error: {result.stderr[:200]}")
            raise subprocess.CalledProcessError(result.returncode, cmd)

        print(f"  ✓ Created: {output_path}")
        return output_path

    finally:
        # Clean up temporary SRT file
        if srt_path.exists():
            srt_path.unlink()


def overlay_clips(
    clips_dir: str | pathlib.Path,
    output_dir: str | pathlib.Path,
    font_size: int = 24,
    font_color: str = "white",
    border_color: str = "black",
    border_width: int = 2,
    position: str = "bottom",
) -> list[pathlib.Path]:
    """Overlay subtitles on all clips in a directory.

    Args:
        clips_dir: Directory containing clip JSON files and video files.
        output_dir: Directory for output videos.
        font_size: Font size for subtitles.
        font_color: Font color.
        border_color: Border color.
        border_width: Border width.
        position: Subtitle position.

    Returns:
        List of output video paths.
    """
    clips_dir = pathlib.Path(clips_dir)
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not clips_dir.exists():
        print(f"  ✗ Clips directory not found: {clips_dir}")
        return []

    # Find all clip JSON files
    json_files = sorted(clips_dir.glob("clip_*.json"))
    if not json_files:
        print(f"  ✗ No clip JSON files found in {clips_dir}")
        return []

    print(f"  Found {len(json_files)} clip(s) to process")

    output_paths = []
    for json_file in json_files:
        try:
            # Load clip metadata
            meta = json.loads(json_file.read_text(encoding="utf-8"))
            clip_id = meta.get("clip_id", json_file.stem)

            # Find corresponding video file
            video_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
            video_file = None
            for ext in video_extensions:
                candidate = clips_dir / f"{clip_id}{ext}"
                if candidate.exists():
                    video_file = candidate
                    break
                # Also try without clip_id prefix
                candidate = clips_dir / f"{json_file.stem}{ext}"
                if candidate.exists():
                    video_file = candidate
                    break

            if not video_file:
                print(f"  ⚠ No video file found for {clip_id}, skipping")
                continue

            # Generate output path
            output_file = output_dir / f"{clip_id}_subtitled.mp4"

            # Overlay subtitles
            result = overlay_subtitles(
                video_file,
                [meta],
                output_file,
                font_size=font_size,
                font_color=font_color,
                border_color=border_color,
                border_width=border_width,
                position=position,
            )
            output_paths.append(result)

        except Exception as e:
            print(f"  ✗ Error processing {json_file.name}: {e}")
            continue

    print(f"\n  ✓ Processed {len(output_paths)}/{len(json_files)} clips")
    return output_paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Overlay subtitles on video clips"
    )
    parser.add_argument("--clips", "-c", required=True, help="Directory with clip JSON files")
    parser.add_argument("--output", "-o", default="overlayed", help="Output directory")
    parser.add_argument("--font-size", type=int, default=24, help="Subtitle font size")
    parser.add_argument("--font-color", default="white", help="Subtitle font color")
    parser.add_argument("--border-color", default="black", help="Subtitle border color")
    parser.add_argument("--border-width", type=int, default=2, help="Subtitle border width")
    parser.add_argument("--position", default="bottom", choices=["top", "middle", "bottom"], help="Subtitle position")
    args = parser.parse_args()

    overlay_clips(
        clips_dir=args.clips,
        output_dir=args.output,
        font_size=args.font_size,
        font_color=args.font_color,
        border_color=args.border_color,
        border_width=args.border_width,
        position=args.position,
    )
