"""VideoProcessor — Load, transform, and write video frames."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass
class VideoTransformResult:
    """Result of applying video transformations."""

    output_path: str
    frames_processed: int = 0
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    effect_applied: Optional[str] = None


class VideoProcessor:
    """Core video processing engine.

    Handles:
      - Loading video files (any format supported by OpenCV)
      - Frame-by-frame extraction and modification
      - Applying visual effects (grayscale, sepia, blur, brightness, contrast)
      - Applying geometric transformations (rotation, crop, zoom)
      - Writing output video files
      - Adding text overlays
    """

    SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}

    def __init__(self, input_path: str):
        """Initialize with a video file path.

        Args:
            input_path: Path to the input video file.

        Raises:
            FileNotFoundError: If the input file does not exist.
            ValueError: If the file extension is not supported.
        """
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")

        suffix = self.input_path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported video format '{suffix}'. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        self.cap = cv2.VideoCapture(str(self.input_path))
        if not self.cap.isOpened():
            raise ValueError(f"Failed to open video file: {input_path}")

        # Capture video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.frame_count / self.fps if self.fps > 0 else 0.0

    def __del__(self):
        """Release the video capture resource."""
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()

    def process(
        self,
        effect: Optional[str] = None,
        grayscale: bool = False,
        sepia: bool = False,
        blur_amount: Optional[int] = None,
        brightness: Optional[int] = None,
        contrast: Optional[int] = None,
        rotation: Optional[int] = None,
        crop: Optional[int] = None,
        zoom_amount: Optional[int] = None,
        speed_multiplier: Optional[float] = None,
        overlay_text: Optional[str] = None,
        overlay_position: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> VideoTransformResult:
        """Apply transformations to the video and write the output.

        Args:
            effect: Predefined effect name (grayscale, sepia, cinematic, blur).
            grayscale: Apply grayscale filter.
            sepia: Apply sepia tone filter.
            blur_amount: Gaussian blur kernel size (1-20).
            brightness: Brightness adjustment (-100 to 100).
            contrast: Contrast adjustment (-100 to 100).
            rotation: Rotation angle in degrees.
            crop: Crop margin from each side in pixels.
            zoom_amount: Zoom scale factor (1-10).
            speed_multiplier: Playback speed multiplier (0.1-10.0).
            overlay_text: Text to overlay on the video.
            overlay_position: Position of the text overlay.
            output_path: Output file path (auto-generated if None).

        Returns:
            VideoTransformResult with details about the processed video.

        Raises:
            RuntimeError: If processing fails.
        """
        frames_processed = 0
        output_path = output_path or self._generate_output_path()

        # Determine output codec and format
        ext = Path(output_path).suffix.lower()
        if ext == ".mp4":
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        elif ext == ".avi":
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
        elif ext == ".mov":
            fourcc = cv2.VideoWriter_fourcc(*"avc1")
        else:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        # Calculate output dimensions (accounting for crop/zoom/rotation)
        out_width, out_height = self.width, self.height
        if crop:
            crop = min(crop, self.width // 4, self.height // 4)
            out_width = self.width - 2 * crop
            out_height = self.height - 2 * crop
        if zoom_amount and zoom_amount > 1:
            scale = 1.0 / zoom_amount
            out_width = int(self.width * scale)
            out_height = int(self.height * scale)
        if rotation and abs(rotation) % 180 == 90:
            out_width, out_height = out_height, out_width

        if out_width <= 0 or out_height <= 0:
            raise RuntimeError("Output dimensions would be zero or negative")

        # Calculate output frame count (accounting for speed)
        if speed_multiplier and speed_multiplier != 1.0:
            out_frame_count = max(1, int(self.frame_count / speed_multiplier))
        else:
            out_frame_count = self.frame_count

        out_fps = self.fps * speed_multiplier if speed_multiplier else self.fps

        out_writer = cv2.VideoWriter(output_path, fourcc, out_fps, (out_width, out_height))
        if not out_writer.isOpened():
            raise RuntimeError(f"Failed to create output video: {output_path}")

        try:
            # Determine which effects to apply
            effects = self._resolve_effects(effect, grayscale, sepia, blur_amount, brightness, contrast)

            for i in range(self.frame_count):
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Apply effects
                processed = self._apply_effects(frame, effects)

                # Apply transformations
                processed = self._apply_transformations(processed, rotation, crop, zoom_amount)

                # Apply overlay
                if overlay_text:
                    processed = self._apply_overlay(processed, overlay_text, overlay_position)

                # Write frame (downsample if speed_multiplier > 1)
                if speed_multiplier and speed_multiplier > 1.0:
                    frame_interval = int(speed_multiplier)
                    if i % frame_interval == 0:
                        out_writer.write(processed)
                        frames_processed += 1
                else:
                    out_writer.write(processed)
                    frames_processed += 1

        finally:
            out_writer.release()

        return VideoTransformResult(
            output_path=output_path,
            frames_processed=frames_processed,
            duration_seconds=frames_processed / out_fps if out_fps > 0 else 0.0,
            width=out_width,
            height=out_height,
            fps=out_fps,
            effect_applied=effect or (grayscale and "grayscale") or (sepia and "sepia") or None,
        )

    def _resolve_effects(
        self,
        effect: Optional[str],
        grayscale: bool,
        sepia: bool,
        blur_amount: Optional[int],
        brightness: Optional[int],
        contrast: Optional[int],
    ) -> dict:
        """Resolve all effect flags into a unified effects dict."""
        effects = {}

        if effect:
            effects["effect"] = effect
            if effect == "grayscale":
                effects["grayscale"] = True
            elif effect == "sepia":
                effects["sepia"] = True
            elif effect == "blur":
                effects["blur_amount"] = blur_amount or 5
            elif effect == "brightness":
                effects["brightness"] = brightness or 20
            elif effect == "contrast":
                effects["contrast"] = contrast or 20

        if grayscale:
            effects["grayscale"] = True
        if sepia:
            effects["sepia"] = True
        if blur_amount:
            effects["blur_amount"] = blur_amount
        if brightness:
            effects["brightness"] = brightness
        if contrast:
            effects["contrast"] = contrast

        return effects

    def _apply_effects(self, frame: np.ndarray, effects: dict) -> np.ndarray:
        """Apply visual effects to a single frame."""
        result = frame.copy()

        if effects.get("grayscale"):
            result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

        if effects.get("sepia"):
            result = self._apply_sepia(result)

        if effects.get("blur_amount"):
            k = min(effects["blur_amount"], 20)
            if k % 2 == 0:
                k += 1
            result = cv2.GaussianBlur(result, (k, k), 0)

        if effects.get("brightness"):
            alpha = 1.0
            beta = effects["brightness"] * 2.55
            result = cv2.convertScaleAbs(result, alpha=alpha, beta=beta)

        if effects.get("contrast"):
            alpha = 1.0 + effects["contrast"] / 100.0
            result = cv2.convertScaleAbs(result, alpha=alpha, beta=0)

        return result

    def _apply_sepia(self, frame: np.ndarray) -> np.ndarray:
        """Apply sepia tone to a frame."""
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131],
        ])
        result = cv2.transform(frame, sepia_matrix)
        return np.clip(result, 0, 255).astype(np.uint8)

    def _apply_transformations(
        self,
        frame: np.ndarray,
        rotation: Optional[int],
        crop: Optional[int],
        zoom_amount: Optional[int],
    ) -> np.ndarray:
        """Apply geometric transformations to a frame."""
        result = frame

        if crop:
            h, w = result.shape[:2]
            crop = min(crop, w // 4, h // 4)
            result = result[crop:h-crop, crop:w-crop]

        if zoom_amount and zoom_amount > 1:
            scale = 1.0 / zoom_amount
            h, w = result.shape[:2]
            new_w, new_h = int(w * scale), int(h * scale)
            result = cv2.resize(result, (new_w, new_h), interpolation=cv2.INTER_AREA)

        if rotation:
            h, w = result.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, rotation, 1.0)
            # For 90/270 degree rotations, swap width and height
            if abs(rotation) % 180 == 90:
                result = cv2.warpAffine(result, M, (h, w))
            else:
                result = cv2.warpAffine(result, M, (w, h))

        return result

    def _apply_overlay(
        self,
        frame: np.ndarray,
        text: str,
        position: Optional[str],
    ) -> np.ndarray:
        """Apply text overlay to a frame."""
        # Convert OpenCV BGR to PIL RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        draw = ImageDraw.Draw(pil_image)

        # Try to load a font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except (IOError, OSError):
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Determine position
        h, w = pil_image.size
        if position == "top_left":
            x, y = 10, 10
        elif position == "top_right":
            x, y = w - text_width - 10, 10
        elif position == "bottom_left":
            x, y = 10, h - text_height - 10
        elif position == "bottom_right":
            x, y = w - text_width - 10, h - text_height - 10
        elif position == "center":
            x, y = (w - text_width) // 2, (h - text_height) // 2
        elif position == "top":
            x, y = (w - text_width) // 2, 10
        elif position == "bottom":
            x, y = (w - text_width) // 2, h - text_height - 10
        elif position == "left":
            x, y = 10, (h - text_height) // 2
        elif position == "right":
            x, y = w - text_width - 10, (h - text_height) // 2
        else:
            x, y = 10, h - text_height - 10  # default: bottom left

        # Draw text with background for readability
        bg_bbox = (x - 5, y - 5, x + text_width + 5, y + text_height + 5)
        draw.rectangle(bg_bbox, fill=(0, 0, 0, 128))
        draw.text((x, y), text, fill=(255, 255, 255), font=font)

        # Convert back to OpenCV BGR
        result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return result

    def _generate_output_path(self) -> str:
        """Generate a unique output path in a temp directory."""
        tmp_dir = tempfile.mkdtemp(prefix="videopow_")
        base_name = self.input_path.stem
        output_path = os.path.join(tmp_dir, f"{base_name}_edited.mp4")
        return output_path

    def close(self):
        """Explicitly release the video capture resource."""
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()
