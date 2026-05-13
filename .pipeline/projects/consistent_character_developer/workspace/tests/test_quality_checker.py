"""Phase 3 tests: quality_checker, visual_anchor_refiner, character_comparator."""

from __future__ import annotations

import pathlib
import pytest
import tempfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def dummy_image(tmp_path):
    """Create a minimal PNG-like dummy image file."""
    p = tmp_path / "dummy.png"
    # PNG header bytes
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return str(p)


@pytest.fixture
def empty_image(tmp_path):
    p = tmp_path / "empty.png"
    p.write_bytes(b"")
    return str(p)


@pytest.fixture
def character_registry():
    """Build a minimal CharacterRegistry with 2 characters."""
    from ai_movie_gen_suite.models import Character, CharacterRegistry
    registry = CharacterRegistry()
    registry.add_character(Character(
        id="hero",
        name="Alice",
        role="protagonist",
        motivation="Save the world",
        physical_description="Tall, blonde hair, blue eyes, athletic build",
        personality_traits=["brave"],
        voice_notes="Confident",
        costume_notes="Leather jacket",
        visual_anchor="blonde hair, blue eyes",
        backstory="Orphaned hero",
        arc_summary="Growth",
    ))
    registry.add_character(Character(
        id="villain",
        name="Bob",
        role="antagonist",
        motivation="World domination",
        physical_description="Short, dark hair, green eyes, stocky build",
        personality_traits=["cunning"],
        voice_notes="Low",
        costume_notes="Black suit",
        visual_anchor="dark hair, green eyes",
        backstory="Former ally",
        arc_summary="Descent",
    ))
    return registry


# ---------------------------------------------------------------------------
# QualityChecker Tests
# ---------------------------------------------------------------------------

class TestQualityChecker:

    def test_import(self):
        from ai_consistent_char.quality_checker import QualityChecker, QualityReport
        assert callable(QualityChecker)
        assert callable(QualityReport)

    def test_check_valid_image(self, dummy_image):
        from ai_consistent_char.quality_checker import QualityChecker
        qc = QualityChecker(quality_threshold=0.5)
        report = qc.check_reference_image("hero", dummy_image)
        assert report.character_id == "hero"
        assert report.score > 0.0
        assert isinstance(report.passed, bool)
        assert isinstance(report.issues, list)

    def test_check_missing_image(self):
        from ai_consistent_char.quality_checker import QualityChecker
        qc = QualityChecker()
        report = qc.check_reference_image("hero", "/nonexistent/path/img.png")
        assert report.passed is False
        assert report.score == 0.0
        assert len(report.issues) > 0

    def test_check_empty_image(self, empty_image):
        from ai_consistent_char.quality_checker import QualityChecker
        qc = QualityChecker()
        report = qc.check_reference_image("hero", empty_image)
        assert report.passed is False
        assert len(report.issues) > 0

    def test_invalid_threshold(self):
        from ai_consistent_char.quality_checker import QualityChecker
        with pytest.raises(ValueError):
            QualityChecker(quality_threshold=1.5)
        with pytest.raises(ValueError):
            QualityChecker(quality_threshold=-0.1)

    def test_compute_fingerprint(self, dummy_image):
        from ai_consistent_char.quality_checker import QualityChecker
        qc = QualityChecker()
        fp = qc.compute_image_fingerprint(dummy_image)
        assert fp is not None
        assert len(fp) == 64  # SHA-256 hex

    def test_compute_fingerprint_missing(self):
        from ai_consistent_char.quality_checker import QualityChecker
        qc = QualityChecker()
        fp = qc.compute_image_fingerprint("/nonexistent/file.png")
        assert fp is None

    def test_check_registry(self, dummy_image, character_registry):
        from ai_consistent_char.quality_checker import QualityChecker
        qc = QualityChecker(quality_threshold=0.5)
        # Set reference paths
        for char in character_registry.characters.values():
            char.reference_image_path = dummy_image
        reports = qc.check_registry(character_registry)
        assert len(reports) == 2
        assert all(r.character_id in ("hero", "villain") for r in reports)

    def test_check_registry_no_path(self, character_registry):
        from ai_consistent_char.quality_checker import QualityChecker
        qc = QualityChecker()
        # No reference paths set
        reports = qc.check_registry(character_registry)
        assert all(not r.passed for r in reports)

    def test_summary_all_pass(self, dummy_image):
        from ai_consistent_char.quality_checker import QualityChecker, QualityReport
        qc = QualityChecker(quality_threshold=0.5)
        reports = [
            QualityReport("a", dummy_image, 0.9, True),
            QualityReport("b", dummy_image, 0.8, True),
        ]
        s = qc.summary(reports)
        assert s["total"] == 2
        assert s["passed"] == 2
        assert s["failed"] == 0
        assert s["pass_rate"] == 1.0

    def test_summary_mixed(self, dummy_image):
        from ai_consistent_char.quality_checker import QualityChecker, QualityReport
        qc = QualityChecker()
        reports = [
            QualityReport("a", dummy_image, 0.9, True),
            QualityReport("b", dummy_image, 0.0, False),
        ]
        s = qc.summary(reports)
        assert s["passed"] == 1
        assert s["failed"] == 1
        assert s["pass_rate"] == 0.5

    def test_report_to_dict(self, dummy_image):
        from ai_consistent_char.quality_checker import QualityReport
        report = QualityReport("hero", dummy_image, 0.9, True, issues=[], warnings=["minor"])
        d = report.to_dict()
        assert d["character_id"] == "hero"
        assert d["score"] == 0.9
        assert d["passed"] is True
        assert "minor" in d["warnings"]


# ---------------------------------------------------------------------------
# VisualAnchorRefiner Tests
# ---------------------------------------------------------------------------

class TestVisualAnchorRefiner:

    def test_import(self):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        assert callable(VisualAnchorRefiner)

    def test_init_no_llm(self):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        refiner = VisualAnchorRefiner()
        assert refiner.llm_client is None
        assert refiner._use_llm is False

    def test_refine_adds_physical_detail(self):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        refiner = VisualAnchorRefiner()
        result = refiner.refine_visual_anchor(
            "hero",
            current_anchor="blonde hair",
            physical_description="Tall, blonde hair, blue eyes, athletic build, scar on left cheek"
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_refine_preserves_existing_anchor(self):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        refiner = VisualAnchorRefiner()
        result = refiner.refine_visual_anchor(
            "hero",
            current_anchor="distinctive red hat",
            physical_description="Medium height, brown hair"
        )
        # Should keep the existing anchor
        assert "red hat" in result

    def test_refine_empty_anchor(self):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        refiner = VisualAnchorRefiner()
        result = refiner.refine_visual_anchor(
            "hero",
            current_anchor="",
            physical_description="Tall with long black hair and green eyes"
        )
        assert isinstance(result, str)

    def test_score_anchor_strong(self):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        refiner = VisualAnchorRefiner()
        strong = "tall athletic build, long blonde hair, vivid blue eyes, leather jacket"
        score = refiner.score_anchor(strong)
        assert 0.0 <= score <= 1.0
        assert score > 0.3  # should score reasonably well

    def test_score_anchor_weak(self):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        refiner = VisualAnchorRefiner()
        score_empty = refiner.score_anchor("")
        assert score_empty == 0.0

    def test_refine_registry(self, character_registry):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        refiner = VisualAnchorRefiner()
        refined = refiner.refine_registry(character_registry)
        assert "hero" in refined
        assert "villain" in refined
        assert isinstance(refined["hero"], str)
        # Character objects should be updated in place
        assert character_registry.characters["hero"].visual_anchor == refined["hero"]

    def test_refine_registry_returns_all_characters(self, character_registry):
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        refiner = VisualAnchorRefiner()
        refined = refiner.refine_registry(character_registry)
        assert len(refined) == len(character_registry.characters)


# ---------------------------------------------------------------------------
# CharacterComparator Tests
# ---------------------------------------------------------------------------

class TestCharacterComparator:

    def test_import(self):
        from ai_consistent_char.character_comparator import CharacterComparator, DriftReport
        assert callable(CharacterComparator)
        assert callable(DriftReport)

    def test_invalid_threshold(self):
        from ai_consistent_char.character_comparator import CharacterComparator
        with pytest.raises(ValueError):
            CharacterComparator(drift_threshold=1.5)

    def test_compare_identical_files(self, dummy_image):
        from ai_consistent_char.character_comparator import CharacterComparator
        comp = CharacterComparator(drift_threshold=0.3)
        report = comp.compare("hero", "scene_1", dummy_image, dummy_image)
        assert report.drift_score == 0.0
        assert report.drifted is False

    def test_compare_missing_reference(self, dummy_image):
        from ai_consistent_char.character_comparator import CharacterComparator
        comp = CharacterComparator()
        report = comp.compare("hero", "scene_1", "/no/such/file.png", dummy_image)
        assert report.drifted is True
        assert report.drift_score == 1.0

    def test_compare_missing_render(self, dummy_image):
        from ai_consistent_char.character_comparator import CharacterComparator
        comp = CharacterComparator()
        report = comp.compare("hero", "scene_1", dummy_image, "/no/such/render.png")
        assert report.drifted is True
        assert report.drift_score == 1.0

    def test_compare_different_files(self, tmp_path):
        from ai_consistent_char.character_comparator import CharacterComparator
        ref = tmp_path / "ref.png"
        ren = tmp_path / "render.png"
        ref.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\xAA" * 200)
        ren.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\xBB" * 50)
        comp = CharacterComparator(drift_threshold=0.3)
        report = comp.compare("hero", "s1", str(ref), str(ren))
        assert isinstance(report.drift_score, float)
        assert 0.0 <= report.drift_score <= 1.0

    def test_drift_report_to_dict(self, dummy_image):
        from ai_consistent_char.character_comparator import DriftReport
        report = DriftReport("hero", "s1", dummy_image, dummy_image, 0.0, False, ["identical"])
        d = report.to_dict()
        assert d["character_id"] == "hero"
        assert d["drift_score"] == 0.0
        assert d["drifted"] is False
        assert "identical" in d["notes"]

    def test_summary_empty(self):
        from ai_consistent_char.character_comparator import CharacterComparator
        comp = CharacterComparator()
        s = comp.summary([])
        assert s["total"] == 0
        assert s["drift_rate"] == 0.0

    def test_compare_collection(self, dummy_image, character_registry):
        from ai_consistent_char.character_comparator import CharacterComparator
        from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

        comp = CharacterComparator(drift_threshold=0.3)
        collection = SceneCharacterRenderCollection()
        collection.add_render(SceneCharacterRender(
            scene_id="1", character_id="hero",
            render_path=dummy_image, scene_context="test"
        ))
        collection.add_render(SceneCharacterRender(
            scene_id="1", character_id="villain",
            render_path=dummy_image, scene_context="test"
        ))

        ref_map = {"hero": dummy_image, "villain": dummy_image}
        reports = comp.compare_collection(ref_map, collection)
        assert len(reports) == 2
        # Identical files → no drift
        assert all(not r.drifted for r in reports)

    def test_summary_with_drift(self, dummy_image):
        from ai_consistent_char.character_comparator import CharacterComparator, DriftReport
        comp = CharacterComparator()
        reports = [
            DriftReport("a", "s1", dummy_image, dummy_image, 0.0, False),
            DriftReport("b", "s1", dummy_image, "/missing.png", 1.0, True),
        ]
        s = comp.summary(reports)
        assert s["total"] == 2
        assert s["drifted"] == 1
        assert s["ok"] == 1
        assert s["drift_rate"] == 0.5


# ---------------------------------------------------------------------------
# Integration: Phase 3 full pipeline
# ---------------------------------------------------------------------------

class TestPhase3Integration:

    def test_full_phase3_pipeline(self, tmp_path, character_registry):
        """Generate reference images, check quality, refine anchors, compare."""
        from ai_consistent_char.image_provider import DummyCharacterImageProvider
        from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator
        from ai_consistent_char.quality_checker import QualityChecker
        from ai_consistent_char.visual_anchor_refiner import VisualAnchorRefiner
        from ai_consistent_char.character_comparator import CharacterComparator
        from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

        provider = DummyCharacterImageProvider()
        ref_dir = tmp_path / "refs"
        ref_dir.mkdir()

        # Generate reference images
        gen = ReferenceSheetGenerator(provider, ref_dir)
        gen.generate_for_registry(character_registry)

        # Set reference paths
        for char_id, char in character_registry.characters.items():
            char.reference_image_path = str(ref_dir / f"{char_id}_reference.png")

        # Quality check
        qc = QualityChecker(quality_threshold=0.5)
        reports = qc.check_registry(character_registry)
        summary = qc.summary(reports)
        assert summary["total"] == 2
        assert summary["passed"] > 0

        # Refine anchors
        refiner = VisualAnchorRefiner()
        refined = refiner.refine_registry(character_registry)
        assert len(refined) == 2

        # Build render collection (same as reference for dummy provider)
        collection = SceneCharacterRenderCollection()
        for char_id, char in character_registry.characters.items():
            collection.add_render(SceneCharacterRender(
                scene_id="scene_1",
                character_id=char_id,
                render_path=char.reference_image_path,
                scene_context="test context",
            ))

        # Drift comparison
        ref_map = {cid: char.reference_image_path for cid, char in character_registry.characters.items()}
        comp = CharacterComparator(drift_threshold=0.3)
        drift_reports = comp.compare_collection(ref_map, collection)
        drift_summary = comp.summary(drift_reports)
        assert drift_summary["total"] == 2
        # Dummy provider writes identical files → no drift
        assert drift_summary["drifted"] == 0
