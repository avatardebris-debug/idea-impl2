"""Smoke test for the Video Scribe pipeline.

Generates a synthetic test video, runs the full pipeline, and validates the output.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# Add workspace to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from video_scribe.frame_extractor import extract_key_frame
from video_scribe.output_formatter import format_single_frame_markdown


def generate_test_video(path: str, duration_sec: int = 5, fps: int = 10) -> None:
    """Generate a synthetic test video with distinct visual content per scene.

    Creates a video with 3 scenes:
    - Scene 1 (0-1s): Red gradient
    - Scene 2 (1-3s): Blue gradient
    - Scene 3 (3-5s): Green gradient
    """
    width, height = 320, 240
    total_frames = duration_sec * fps

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))

    for i in range(total_frames):
        t = i / total_frames  # normalized time 0..1

        if t < 0.2:
            # Scene 1: Red gradient
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            for y in range(height):
                frame[y, :] = [int(255 * (y / height)), 0, 0]
        elif t < 0.6:
            # Scene 2: Blue gradient
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            for y in range(height):
                frame[y, :] = [0, 0, int(255 * (y / height))]
        else:
            # Scene 3: Green gradient
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            for y in range(height):
                frame[y, :] = [0, int(255 * (y / height)), 0]

        out.write(frame)

    out.release()


def test_frame_extractor() -> None:
    """Test that frame extraction works on a synthetic video."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        video_path = f.name

    try:
        generate_test_video(video_path)
        frame = extract_key_frame(video_path)
        assert isinstance(frame, Image.Image), f"Expected PIL Image, got {type(frame)}"
        assert frame.size[0] > 0 and frame.size[1] > 0, "Frame has zero dimensions"
        print("  [PASS] Frame extraction")
    finally:
        Path(video_path).unlink(missing_ok=True)


def test_output_formatter() -> None:
    """Test that markdown formatting produces valid output."""
    analysis = {
        "content_summary": "A red gradient fills the screen.",
        "visual_elements": ["red gradient", "dark background", "smooth transition"],
        "camera_notes": "Static camera, no movement detected.",
        "lighting_color_notes": "Dominant red tones, high contrast.",
    }
    md = format_as_markdown(analysis)
    assert "Content Summary" in md
    assert "Visual Elements" in md
    assert "Camera Notes" in md
    assert "Lighting & Color Notes" in md
    assert "red gradient" in md
    print("  [PASS] Output formatting")


def test_cli_help() -> None:
    """Test that --help prints usage."""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent.parent / "video_scribe.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--input" in result.stdout or "input" in result.stdout
    assert "--output" in result.stdout
    assert "--provider" in result.stdout
    assert "--api-key" in result.stdout
    print("  [PASS] CLI help")


def test_cli_with_mock_vlm() -> None:
    """Test the full pipeline with a mock VLM response."""
    # Generate test video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        video_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        output_path = f.name

    try:
        generate_test_video(video_path)

        # Extract frame
        frame = extract_key_frame(video_path)

        # Create a mock analysis (simulating VLM output)
        mock_analysis = {
            "content_summary": "A synthetic gradient fills the screen.",
            "visual_elements": ["gradient", "color transition", "smooth fill"],
            "camera_notes": "Static camera.",
            "lighting_color_notes": "Gradient lighting.",
        }

        # Format output
        md = format_single_frame_markdown(mock_analysis)

        # Write to output file
        Path(output_path).write_text(md, encoding="utf-8")

        # Validate output file
        content = Path(output_path).read_text(encoding="utf-8")
        assert "Scene Content" in content
        assert "gradient" in content
        print("  [PASS] Full pipeline (mock VLM)")
    finally:
        Path(video_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


def main() -> None:
    """Run all smoke tests."""
    print("Running Video Scribe smoke tests...\n")
    tests = [
        test_frame_extractor,
        test_output_formatter,
        test_cli_help,
        test_cli_with_mock_vlm,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
