"""Tests for spatial grounding module (Phase 3)."""

import pytest
from video_recipe_mu.spatial_grounding import (
    KeyFrame,
    SpatialGroundingResult,
    estimate_xyz_delta_from_frames,
    ground_steps_with_key_frames,
    infer_xyz_delta_from_text,
)


class TestEstimateXyzDeltaFromFrames:
    """Tests for estimate_xyz_delta_from_frames."""

    def test_first_frame_returns_zero_delta(self):
        """First frame should return zero delta (no baseline)."""
        curr = KeyFrame(
            frame_index=0,
            timestamp_s=0.0,
            description="first frame",
            objects=["cup"],
            bounding_boxes=[{"label": "cup", "x": 100, "y": 200, "w": 50, "h": 50}],
        )
        result = estimate_xyz_delta_from_frames(None, curr)
        assert result == {"x": 0.0, "y": 0.0, "z": 0.0}

    def test_horizontal_displacement(self):
        """Object moving right should produce positive x_delta."""
        prev = KeyFrame(
            frame_index=0,
            timestamp_s=0.0,
            description="frame 0",
            objects=["cup"],
            bounding_boxes=[{"label": "cup", "x": 100, "y": 200, "w": 50, "h": 50}],
        )
        curr = KeyFrame(
            frame_index=1,
            timestamp_s=1.0,
            description="frame 1",
            objects=["cup"],
            bounding_boxes=[{"label": "cup", "x": 150, "y": 200, "w": 50, "h": 50}],
        )
        result = estimate_xyz_delta_from_frames(prev, curr)
        assert result["x"] > 0  # moved right
        assert result["y"] == 0.0
        assert result["z"] == 0.0  # same size, no z change

    def test_size_change_produces_z_delta(self):
        """Object getting larger should produce negative z_delta (closer)."""
        prev = KeyFrame(
            frame_index=0,
            timestamp_s=0.0,
            description="frame 0",
            objects=["cup"],
            bounding_boxes=[{"label": "cup", "x": 100, "y": 200, "w": 100, "h": 100}],
        )
        curr = KeyFrame(
            frame_index=1,
            timestamp_s=1.0,
            description="frame 1",
            objects=["cup"],
            bounding_boxes=[{"label": "cup", "x": 100, "y": 200, "w": 50, "h": 50}],
        )
        result = estimate_xyz_delta_from_frames(prev, curr)
        # Object got smaller → moved away (positive z)
        assert result["z"] > 0

    def test_no_bounding_boxes_returns_zero(self):
        """No bounding boxes should return zero delta."""
        prev = KeyFrame(
            frame_index=0,
            timestamp_s=0.0,
            description="frame 0",
            objects=[],
            bounding_boxes=[],
        )
        curr = KeyFrame(
            frame_index=1,
            timestamp_s=1.0,
            description="frame 1",
            objects=[],
            bounding_boxes=[],
        )
        result = estimate_xyz_delta_from_frames(prev, curr)
        assert result == {"x": 0.0, "y": 0.0, "z": 0.0}


class TestGroundStepsWithKeyFrames:
    """Tests for ground_steps_with_key_frames."""

    def test_grounding_matches_steps_to_frames(self):
        """Each step should be matched to the closest key frame."""
        steps = [
            {"step": 1, "timestamp_s": 0.0},
            {"step": 2, "timestamp_s": 1.0},
            {"step": 3, "timestamp_s": 2.0},
        ]
        key_frames = [
            KeyFrame(frame_index=0, timestamp_s=0.0, description="f0", objects=[], bounding_boxes=[]),
            KeyFrame(frame_index=1, timestamp_s=1.0, description="f1", objects=[], bounding_boxes=[]),
            KeyFrame(frame_index=2, timestamp_s=2.0, description="f2", objects=[], bounding_boxes=[]),
        ]
        results = ground_steps_with_key_frames(steps, key_frames)
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.step == i + 1
            assert result.confidence > 0

    def test_confidence_decreases_with_time_distance(self):
        """Confidence should be lower when step and frame are far apart."""
        steps = [
            {"step": 1, "timestamp_s": 0.0},
            {"step": 2, "timestamp_s": 10.0},  # far from any frame
        ]
        key_frames = [
            KeyFrame(frame_index=0, timestamp_s=0.0, description="f0", objects=[], bounding_boxes=[]),
            KeyFrame(frame_index=1, timestamp_s=1.0, description="f1", objects=[], bounding_boxes=[]),
        ]
        results = ground_steps_with_key_frames(steps, key_frames)
        # Second step should have lower confidence
        assert results[1].confidence < results[0].confidence


class TestInferXyzDeltaFromText:
    """Tests for infer_xyz_delta_from_text."""

    def test_left_keyword(self):
        result = infer_xyz_delta_from_text("move left")
        assert result["x"] < 0

    def test_right_keyword(self):
        result = infer_xyz_delta_from_text("move right")
        assert result["x"] > 0

    def test_up_keyword(self):
        result = infer_xyz_delta_from_text("lift up")
        assert result["z"] > 0

    def test_down_keyword(self):
        result = infer_xyz_delta_from_text("place down")
        assert result["z"] < 0

    def test_forward_keyword(self):
        result = infer_xyz_delta_from_text("move forward")
        assert result["y"] > 0

    def test_backward_keyword(self):
        result = infer_xyz_delta_from_text("move backward")
        assert result["y"] < 0

    def test_no_keyword_returns_default(self):
        result = infer_xyz_delta_from_text("do something")
        assert result == {"x": 0.0, "y": 0.0, "z": 0.0}

    def test_multiple_keywords_accumulate(self):
        result = infer_xyz_delta_from_text("move right and up")
        assert result["x"] > 0
        assert result["z"] > 0


class TestKeyFrame:
    """Tests for KeyFrame dataclass."""

    def test_keyframe_creation(self):
        kf = KeyFrame(
            frame_index=10,
            timestamp_s=5.0,
            description="test frame",
            objects=["cup"],
            bounding_boxes=[{"label": "cup", "x": 100, "y": 200, "w": 50, "h": 50}],
        )
        assert kf.frame_index == 10
        assert kf.timestamp_s == 5.0
        assert kf.description == "test frame"
        assert kf.objects == ["cup"]
        assert len(kf.bounding_boxes) == 1


class TestSpatialGroundingResult:
    """Tests for SpatialGroundingResult dataclass."""

    def test_result_creation(self):
        result = SpatialGroundingResult(
            step=1,
            xyz_delta={"x": 0.1, "y": 0.0, "z": 0.0},
            confidence=0.9,
            method="bounding_box_displacement",
            notes="test note",
        )
        assert result.step == 1
        assert result.xyz_delta == {"x": 0.1, "y": 0.0, "z": 0.0}
        assert result.confidence == 0.9
        assert result.method == "bounding_box_displacement"
        assert result.notes == "test note"
