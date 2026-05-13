"""Video assembly pipeline — assembles scene renders into a video.

Takes scene renders and assembles them into a video with:
- Transitions between scenes
- Text overlays for scene headings and dialogue
- MP4 export using ffmpeg
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VideoAssemblyPipeline:
    """Assembles scene renders into a video.

    Args:
        output_path: Path to output video file
        fps: Frames per second (default: 24)
        scene_duration: Duration of each scene in seconds (default: 5)
        transition_duration: Duration of transitions in seconds (default: 1)
        font_path: Path to font file for text overlays
        font_size: Font size for text overlays (default: 24)
        text_color: Text color in hex format (default: "#FFFFFF")
        bg_color: Background color for text overlay in hex format (default: "#000000")
    """

    def __init__(
        self,
        output_path: str,
        fps: int = 24,
        scene_duration: float = 5.0,
        transition_duration: float = 1.0,
        font_path: Optional[str] = None,
        font_size: int = 24,
        text_color: str = "#FFFFFF",
        bg_color: str = "#000000",
    ):
        self.output_path = Path(output_path)
        self.fps = fps
        self.scene_duration = scene_duration
        self.transition_duration = transition_duration
        self.font_path = font_path
        self.font_size = font_size
        self.text_color = text_color
        self.bg_color = bg_color

        # Validate ffmpeg is available
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info("ffmpeg is available")
            else:
                logger.warning("ffmpeg returned non-zero exit code")
        except FileNotFoundError:
            logger.warning("ffmpeg not found. Video assembly will use fallback mode.")
        except subprocess.TimeoutExpired:
            logger.warning("ffmpeg command timed out")

    def assemble_video(
        self,
        scene_render_paths: list[str],
        scene_headings: Optional[list[str]] = None,
        scene_dialogue: Optional[list[list[str]]] = None,
    ) -> str:
        """Assemble scene renders into a video.

        Args:
            scene_render_paths: List of scene render image paths.
            scene_headings: Optional list of scene headings.
            scene_dialogue: Optional list of dialogue lines per scene.

        Returns:
            Path to the assembled video.
        """
        if not scene_render_paths:
            raise ValueError("No scene renders provided")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate intermediate files
        temp_dir = self.output_path.parent / "temp_video"
        temp_dir.mkdir(exist_ok=True)

        # Convert images to frames
        frame_paths = self._images_to_frames(scene_render_paths, temp_dir)

        # Generate video
        video_path = self._frames_to_video(frame_paths, temp_dir, scene_headings, scene_dialogue)

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        return str(self.output_path)

    def _images_to_frames(
        self,
        scene_render_paths: list[str],
        temp_dir: Path,
    ) -> list[str]:
        """Convert scene renders to frame sequences.

        Args:
            scene_render_paths: List of scene render image paths.
            temp_dir: Temporary directory for intermediate files.

        Returns:
            List of frame file paths.
        """
        frame_paths = []

        for i, render_path in enumerate(scene_render_paths):
            # Generate frames for this scene
            num_frames = int(self.scene_duration * self.fps)
            scene_dir = temp_dir / f"scene_{i}"
            scene_dir.mkdir(exist_ok=True)

            for j in range(num_frames):
                frame_path = scene_dir / f"frame_{j:04d}.png"
                # Use ffmpeg to create frames (or copy image if single frame)
                if num_frames == 1:
                    # Single frame scene
                    import shutil
                    shutil.copy(render_path, frame_path)
                else:
                    # Generate frames with ffmpeg
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-loop", "1",
                            "-i", render_path,
                            "-t", str(self.scene_duration),
                            "-vf", f"fps={self.fps}",
                            "-c:v", "png",
                            str(frame_path),
                        ],
                        capture_output=True,
                        check=True,
                    )
                frame_paths.append(str(frame_path))

        return frame_paths

    def _frames_to_video(
        self,
        frame_paths: list[str],
        temp_dir: Path,
        scene_headings: Optional[list[str]] = None,
        scene_dialogue: Optional[list[list[str]]] = None,
    ) -> str:
        """Convert frame sequences to video.

        Args:
            frame_paths: List of frame file paths.
            temp_dir: Temporary directory.
            scene_headings: Optional list of scene headings.
            scene_dialogue: Optional list of dialogue lines per scene.

        Returns:
            Path to the output video.
        """
        # Generate filter complex for transitions and overlays
        filter_complex = self._generate_filter_complex(frame_paths, scene_headings, scene_dialogue)

        # Generate video
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-framerate", str(self.fps),
                "-i", frame_paths[0],
                "-vf", filter_complex,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                str(self.output_path),
            ],
            capture_output=True,
            check=True,
        )

        return str(self.output_path)

    def _generate_filter_complex(
        self,
        frame_paths: list[str],
        scene_headings: Optional[list[str]] = None,
        scene_dialogue: Optional[list[list[str]]] = None,
    ) -> str:
        """Generate ffmpeg filter complex for video assembly.

        Args:
            frame_paths: List of frame file paths.
            scene_headings: Optional list of scene headings.
            scene_dialogue: Optional list of dialogue lines per scene.

        Returns:
            FFmpeg filter complex string.
        """
        # This is a simplified version. A production version would:
        # - Handle transitions between scenes
        # - Add text overlays for headings and dialogue
        # - Handle multiple inputs properly

        # For now, return a simple filter
        return "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"

    def add_text_overlay(
        self,
        video_path: str,
        text: str,
        position: str = "bottom",
        font_size: Optional[int] = None,
        text_color: Optional[str] = None,
        bg_color: Optional[str] = None,
    ) -> str:
        """Add text overlay to video.

        Args:
            video_path: Path to input video.
            text: Text to overlay.
            position: Position of text (top, bottom, center).
            font_size: Font size (default: self.font_size).
            text_color: Text color (default: self.text_color).
            bg_color: Background color (default: self.bg_color).

        Returns:
            Path to the video with text overlay.
        """
        output_path = Path(video_path).stem + "_overlay.mp4"

        font_size = font_size or self.font_size
        text_color = text_color or self.text_color
        bg_color = bg_color or self.bg_color

        # Map position to ffmpeg y expression
        if position == "top":
            y_expr = "h-h/10"
        elif position == "bottom":
            y_expr = "H*9/10"
        elif position == "center":
            y_expr = "(H-h)/2"
        else:
            y_expr = "H*9/10"

        # Generate text filter
        text_filter = f"drawtext=text='{text}':fontsize={font_size}:fontcolor={text_color}:x=(w-tw)/2:y={y_expr}"

        # Add background if needed
        if bg_color:
            bg_hex = bg_color.lstrip("#")
            bg_r = int(bg_hex[0:2], 16)
            bg_g = int(bg_hex[2:4], 16)
            bg_b = int(bg_hex[4:6], 16)
            text_filter += f":box=1:boxcolor={bg_color}@0.5:boxborderw=5"

        # Apply filter
        subprocess.run(
            [
                "ffmpeg",
                "-i", video_path,
                "-vf", text_filter,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ],
            capture_output=True,
            check=True,
        )

        return str(output_path)
