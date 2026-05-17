"""VideoDescriber — Parse text descriptions into structured editing instructions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EditingInstructions:
    """Structured representation of video editing instructions parsed from text."""

    effect: Optional[str] = None
    grayscale: bool = False
    sepia: bool = False
    cinematic: bool = False
    blur_amount: Optional[int] = None
    brightness: Optional[int] = None
    contrast: Optional[int] = None
    rotation: Optional[int] = None
    crop: Optional[int] = None
    zoom_amount: Optional[int] = None
    speed_multiplier: Optional[float] = None
    duration: Optional[float] = None
    transition: Optional[str] = None
    overlay_text: Optional[str] = None
    overlay_position: Optional[str] = None
    raw_description: str = ""

    @property
    def has_effects(self) -> bool:
        """Return True if any effect is enabled."""
        return any([
            self.effect,
            self.grayscale,
            self.sepia,
            self.cinematic,
            self.blur_amount,
            self.brightness,
            self.contrast,
            self.rotation,
            self.crop,
            self.zoom_amount,
            self.speed_multiplier,
            self.overlay_text,
        ])


class VideoDescriber:
    """Parse natural-language video editing descriptions into structured instructions.

    Supports keywords for:
      - Effects: grayscale, sepia, cinematic, blur, brightness, contrast
      - Transformations: rotation, crop, zoom
      - Timing: speed, duration
      - Overlays: text, position
      - Transitions: fade, dissolve, wipe
    """

    # Effect keywords (case-insensitive matching)
    EFFECT_MAP = {
        "grayscale": "grayscale",
        "grey": "grayscale",
        "black and white": "grayscale",
        "sepia": "sepia",
        "cinematic": "cinematic",
        "letterbox": "cinematic",
        "blur": "blur",
        "blurry": "blur",
        "brightness": "brightness",
        "bright": "brightness",
        "contrast": "contrast",
    }

    # Transition keywords
    TRANSITION_MAP = {
        "fade": "fade",
        "dissolve": "dissolve",
        "wipe": "wipe",
        "crossfade": "crossfade",
    }

    # Overlay position keywords
    POSITION_MAP = {
        "top left": "top_left",
        "top right": "top_right",
        "bottom left": "bottom_left",
        "bottom right": "bottom_right",
        "center": "center",
        "top": "top",
        "bottom": "bottom",
        "left": "left",
        "right": "right",
    }

    @classmethod
    def parse(cls, description: str) -> EditingInstructions:
        """Parse a text description into EditingInstructions.

        Args:
            description: Natural-language description of video edits.

        Returns:
            EditingInstructions with parsed values.
        """
        if not description or not description.strip():
            return EditingInstructions(raw_description=description or "")

        lower = description.lower()
        result = EditingInstructions(raw_description=description)

        # Detect effects
        result = cls._detect_effects(lower, result)

        # Detect transitions
        result = cls._detect_transitions(lower, result)

        # Detect timing
        result = cls._detect_timing(lower, result)

        # Detect overlays
        result = cls._detect_overlays(description, lower, result)

        # Detect transformations
        result = cls._detect_transformations(lower, result)

        return result

    @classmethod
    def _detect_effects(cls, lower: str, result: EditingInstructions) -> EditingInstructions:
        """Detect visual effects from the description."""
        # Check for explicit effect keywords
        for keyword, effect in cls.EFFECT_MAP.items():
            if keyword in lower:
                result.effect = effect
                if effect == "grayscale":
                    result.grayscale = True
                elif effect == "sepia":
                    result.sepia = True
                elif effect == "cinematic":
                    result.cinematic = True
                elif effect == "blur":
                    result.blur_amount = 5  # default blur amount

        # Check for brightness/contrast with numeric values
        brightness_match = re.search(r"brightness\s*(\d+)", lower)
        if brightness_match:
            result.brightness = int(brightness_match.group(1))
            result.effect = "brightness"

        contrast_match = re.search(r"contrast\s*(\d+)", lower)
        if contrast_match:
            result.contrast = int(contrast_match.group(1))
            result.effect = "contrast"

        return result

    @classmethod
    def _detect_transitions(cls, lower: str, result: EditingInstructions) -> EditingInstructions:
        """Detect transition effects."""
        for keyword, transition in cls.TRANSITION_MAP.items():
            if keyword in lower:
                result.transition = transition
                break
        return result

    @classmethod
    def _detect_timing(cls, lower: str, result: EditingInstructions) -> EditingInstructions:
        """Detect timing-related parameters."""
        # Duration: "X seconds", "X sec", "X second"
        duration_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:seconds?|sec)\b", lower)
        if duration_match:
            result.duration = float(duration_match.group(1))

        # Speed: "X speed", "Xx speed", "speed X", "slow motion", "fast forward"
        speed_match = re.search(r"(\d+(?:\.\d+)?)\s*x?\s*speed", lower)
        if speed_match:
            result.speed_multiplier = float(speed_match.group(1))

        slow_match = re.search(r"slow\s*motion", lower)
        if slow_match:
            result.speed_multiplier = 0.5

        fast_match = re.search(r"fast\s*forward", lower)
        if fast_match:
            result.speed_multiplier = 2.0

        return result

    @classmethod
    def _detect_overlays(cls, original: str, lower: str, result: EditingInstructions) -> EditingInstructions:
        """Detect text overlay instructions."""
        # Overlay text: "text: '...'", "overlay: '...'", "text '...'", "overlay text '...'"
        # Try multiple patterns to capture text with original case
        text_match = re.search(r'(?:text|overlay)\s*[:"]?\s*([\'"])(.+?)\1', original)
        if text_match:
            result.overlay_text = text_match.group(2)

        # Overlay position
        for keyword, position in cls.POSITION_MAP.items():
            if keyword in lower:
                result.overlay_position = position
                break

        return result

    @classmethod
    def _detect_transformations(cls, lower: str, result: EditingInstructions) -> EditingInstructions:
        """Detect geometric transformations."""
        # Rotation: "rotate X degrees", "X degree rotation"
        rotation_match = re.search(r"rotate\s*(\d+)\s*degrees?", lower)
        if not rotation_match:
            rotation_match = re.search(r"(\d+)\s*degrees?\s*rotation", lower)
        if rotation_match:
            result.rotation = int(rotation_match.group(1))

        # Crop: "crop X", "X pixel crop"
        crop_match = re.search(r"crop\s*(\d+)", lower)
        if crop_match:
            result.crop = int(crop_match.group(1))

        # Zoom: "zoom X", "Xx zoom", "zoom in X"
        zoom_match = re.search(r"zoom\s*(\d+)", lower)
        if not zoom_match:
            zoom_match = re.search(r"(\d+)\s*x?\s*zoom", lower)
        if not zoom_match:
            zoom_match = re.search(r"zoom\s*in\s*(\d+)", lower)
        if zoom_match:
            result.zoom_amount = int(zoom_match.group(1))
        elif "zoom" in lower:
            # "zoom" without a number defaults to 5
            result.zoom_amount = 5

        return result
