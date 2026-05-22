"""
clip_extractor.py — ffmpeg-based clip cutter.

For each top-N scored segment: runs ffmpeg to cut a short .mp4 clip,
then writes a companion .json with all metadata.

Output per clip:
    clips/clip_000.mp4
    clips/clip_000.json  — {clip_id, l1_text, l2_text, start, end, freq_score, word_count, source_video}
"""
from __future__ import annotations
import json
import pathlib
import subprocess
import sys
from typing import Any


def _check_ffmpeg() -> None:
    """Raise RuntimeError if ffmpeg is not on PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "ffmpeg not found. Install it and ensure it is on your PATH:\n"
            "  Windows: winget install ffmpeg\n"
            "  Linux:   sudo apt install ffmpeg\n"
            "  macOS:   brew install ffmpeg"
        )


def extract_clips(
    video_path: str | pathlib.Path,
    segments: list[dict[str, Any]],
    output_dir: str | pathlib.Path,
    top_n: int = 50,
) -> list[pathlib.Path]:
    """Cut the top-N scored segments from video_path into individual clips.

    Args:
        video_path:  Source video file (any ffmpeg-supported format).
        segments:    Scored + translated segment list (from score_segments()).
                     Must be sorted descending by freq_score already.
        output_dir:  Directory to write clip_NNN.mp4 and clip_NNN.json files.
        top_n:       Maximum number of clips to produce.

    Returns:
        List of Path objects for the produced .mp4 files.
    """
    video_path = pathlib.Path(video_path)
    output_dir = pathlib.Path(output_dir)

    top_segments = segments[:top_n]
    if not top_segments:
        return []

    _check_ffmpeg()
    output_dir.mkdir(parents=True, exist_ok=True)

    produced: list[pathlib.Path] = []

    for i, seg in enumerate(top_segments):
        clip_id = f"clip_{i:03d}"
        mp4_path = output_dir / f"{clip_id}.mp4"
        json_path = output_dir / f"{clip_id}.json"

        start = seg.get("start", 0.0)
        end = seg.get("end", start + 1.0)
        if end <= start:
            end = start + 1.0

        # Cut clip with ffmpeg
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", str(video_path),
            "-c:v", "libx264", "-c:a", "aac",
            "-preset", "fast",
            str(mp4_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  [clip_extractor] Warning: ffmpeg failed for {clip_id}: {result.stderr[-200:]}", file=sys.stderr)
            continue

        # Write metadata JSON
        meta = {
            "clip_id":      clip_id,
            "l1_text":      seg.get("text", seg.get("l1_text", "")),
            "l2_text":      seg.get("l2_text", ""),
            "start":        start,
            "end":          end,
            "duration":     round(end - start, 3),
            "freq_score":   seg.get("freq_score", 0.0),
            "word_count":   seg.get("word_count", 0),
            "source_video": str(video_path.resolve()),
        }
        json_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        produced.append(mp4_path)
        print(f"  [{i+1:3d}/{len(top_segments)}] {clip_id}  [{start:.1f}s–{end:.1f}s]  score={meta['freq_score']:.6f}")

    return produced
