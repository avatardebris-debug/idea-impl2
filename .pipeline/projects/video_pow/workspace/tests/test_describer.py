"""Tests for VideoDescriber — parsing text descriptions into editing instructions."""

import pytest
from videopow.describer import VideoDescriber, EditingInstructions


class TestVideoDescriberParse:
    """Test the VideoDescriber.parse method."""

    def test_empty_description(self):
        """Empty description returns empty instructions."""
        result = VideoDescriber.parse("")
        assert result.raw_description == ""
        assert not result.has_effects

    def test_whitespace_only(self):
        """Whitespace-only description returns empty instructions."""
        result = VideoDescriber.parse("   \n  ")
        assert not result.has_effects

    def test_grayscale_detection(self):
        """Grayscale keyword is detected."""
        result = VideoDescriber.parse("make it grayscale")
        assert result.grayscale is True
        assert result.effect == "grayscale"

    def test_grey_alias(self):
        """'grey' is an alias for grayscale."""
        result = VideoDescriber.parse("make it grey")
        assert result.grayscale is True
        assert result.effect == "grayscale"

    def test_black_and_white(self):
        """'black and white' is an alias for grayscale."""
        result = VideoDescriber.parse("black and white filter")
        assert result.grayscale is True

    def test_sepia_detection(self):
        """Sepia keyword is detected."""
        result = VideoDescriber.parse("apply sepia tone")
        assert result.sepia is True
        assert result.effect == "sepia"

    def test_cinematic_detection(self):
        """Cinematic/letterbox keywords are detected."""
        result1 = VideoDescriber.parse("make it cinematic")
        assert result1.cinematic is True

        result2 = VideoDescriber.parse("add letterbox")
        assert result2.cinematic is True

    def test_blur_detection(self):
        """Blur keywords are detected with default amount."""
        result1 = VideoDescriber.parse("add blur effect")
        assert result1.effect == "blur"
        assert result1.blur_amount == 5

        result2 = VideoDescriber.parse("make it blurry")
        assert result2.effect == "blur"
        assert result2.blur_amount == 5

    def test_brightness_with_value(self):
        """Brightness with numeric value is detected."""
        result = VideoDescriber.parse("brightness 50")
        assert result.brightness == 50
        assert result.effect == "brightness"

    def test_contrast_with_value(self):
        """Contrast with numeric value is detected."""
        result = VideoDescriber.parse("contrast 30")
        assert result.contrast == 30
        assert result.contrast == 30

    def test_duration_detection(self):
        """Duration is parsed from various formats."""
        result1 = VideoDescriber.parse("5 seconds duration")
        assert result1.duration == 5.0

        result2 = VideoDescriber.parse("10 sec clip")
        assert result2.duration == 10.0

        result3 = VideoDescriber.parse("3.5 second video")
        assert result3.duration == 3.5

    def test_slow_motion(self):
        """Slow motion sets speed to 0.5."""
        result = VideoDescriber.parse("slow motion effect")
        assert result.speed_multiplier == 0.5

    def test_fast_forward(self):
        """Fast forward sets speed to 2.0."""
        result = VideoDescriber.parse("fast forward the clip")
        assert result.speed_multiplier == 2.0

    def test_speed_multiplier(self):
        """Explicit speed multiplier is detected."""
        result = VideoDescriber.parse("2x speed")
        assert result.speed_multiplier == 2.0

        result2 = VideoDescriber.parse("0.5x speed")
        assert result2.speed_multiplier == 0.5

    def test_overlay_text(self):
        """Overlay text is detected."""
        result = VideoDescriber.parse('overlay: "Hello World"')
        assert result.overlay_text == "Hello World"

        result2 = VideoDescriber.parse('text: "Test"')
        assert result2.overlay_text == "Test"

    def test_overlay_position(self):
        """Overlay position is detected."""
        result = VideoDescriber.parse('text: "Hi" at center')
        assert result.overlay_position == "center"

        result2 = VideoDescriber.parse('text: "Hi" at bottom right')
        assert result2.overlay_position == "bottom_right"

    def test_rotation(self):
        """Rotation angle is detected."""
        result = VideoDescriber.parse("rotate 90 degrees")
        assert result.rotation == 90

        result2 = VideoDescriber.parse("45 degrees rotation")
        assert result2.rotation == 45

    def test_crop(self):
        """Crop margin is detected."""
        result = VideoDescriber.parse("crop 50 pixels")
        assert result.crop == 50

    def test_zoom(self):
        """Zoom amount is detected."""
        result1 = VideoDescriber.parse("zoom 3")
        assert result1.zoom_amount == 3

        result2 = VideoDescriber.parse("5x zoom in")
        assert result2.zoom_amount == 5

        result3 = VideoDescriber.parse("slow zoom on a forest")
        assert result3.zoom_amount == 5  # "zoom" with number

    def test_transition_detection(self):
        """Transitions are detected."""
        result1 = VideoDescriber.parse("fade to black")
        assert result1.transition == "fade"

        result2 = VideoDescriber.parse("dissolve effect")
        assert result2.transition == "dissolve"

        result3 = VideoDescriber.parse("wipe transition")
        assert result3.transition == "wipe"

    def test_combined_effects(self):
        """Multiple effects can be combined."""
        result = VideoDescriber.parse(
            "grayscale with blur and brightness 20, 5 seconds duration"
        )
        assert result.grayscale is True
        assert result.blur_amount == 5
        assert result.brightness == 20
        assert result.duration == 5.0

    def test_complex_description(self):
        """Complex description with many features is parsed correctly."""
        desc = (
            "slow zoom on a forest, grayscale with blur, "
            'overlay text "Nature" at center, 10 second duration'
        )
        result = VideoDescriber.parse(desc)
        assert result.zoom_amount == 5  # from "zoom"
        assert result.grayscale is True
        assert result.blur_amount == 5
        assert result.overlay_text == "Nature"
        assert result.overlay_position == "center"
        assert result.duration == 10.0

    def test_case_insensitive(self):
        """Parsing is case-insensitive."""
        result = VideoDescriber.parse("GRAYSCALE with SEPIA and BLUR")
        assert result.grayscale is True
        assert result.sepia is True
        assert result.effect == "blur"


class TestEditingInstructions:
    """Test the EditingInstructions dataclass."""

    def test_has_effects_default(self):
        """Default instructions have no effects."""
        instructions = EditingInstructions()
        assert instructions.has_effects is False

    def test_has_effects_with_effect(self):
        """has_effects is True when effect is set."""
        instructions = EditingInstructions(effect="grayscale")
        assert instructions.has_effects is True

    def test_has_effects_with_grayscale(self):
        """has_effects is True when grayscale is True."""
        instructions = EditingInstructions(grayscale=True)
        assert instructions.has_effects is True

    def test_has_effects_with_overlay(self):
        """has_effects is True when overlay_text is set."""
        instructions = EditingInstructions(overlay_text="test")
        assert instructions.has_effects is True

    def test_raw_description_preserved(self):
        """Raw description is preserved."""
        desc = "This is my description"
        instructions = EditingInstructions(raw_description=desc)
        assert instructions.raw_description == desc
