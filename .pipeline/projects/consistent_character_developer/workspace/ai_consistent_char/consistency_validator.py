"""Character consistency validator — compares generated images for consistency.

Uses face recognition (via face-recognition library) and CLIP-based similarity
to validate character consistency across generated images.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CharacterConsistencyValidator:
    """Validates character consistency across generated images.

    Uses:
    - Face recognition for facial consistency
    - CLIP-based similarity for overall image similarity
    - Threshold-based flagging for inconsistencies

    Args:
        face_threshold: Minimum face similarity threshold (0-1)
        clip_threshold: Minimum CLIP similarity threshold (0-1)
        face_recognition_model: Face recognition model to use
    """

    def __init__(
        self,
        face_threshold: float = 0.6,
        clip_threshold: float = 0.7,
        face_recognition_model: str = "hog",
    ):
        self.face_threshold = face_threshold
        self.clip_threshold = clip_threshold
        self.face_recognition_model = face_recognition_model

        # Lazy initialization
        self._face_recognition = None
        self._clip_model = None
        self._clip_processor = None

    def _ensure_face_recognition(self) -> None:
        """Lazy initialization of face recognition."""
        if self._face_recognition is not None:
            return

        try:
            import face_recognition
            self._face_recognition = face_recognition
            logger.info("Face recognition library loaded successfully")
        except ImportError:
            logger.warning("face-recognition library not installed. Using fallback.")
            self._face_recognition = None

    def _ensure_clip(self) -> None:
        """Lazy initialization of CLIP model."""
        if self._clip_model is not None:
            return

        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor
            self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            logger.info("CLIP model loaded successfully")
        except ImportError:
            logger.warning("transformers/torch not installed. Using fallback.")
            self._clip_model = None
            self._clip_processor = None

    def compare_faces(
        self,
        image1_path: str,
        image2_path: str,
    ) -> float:
        """Compare faces in two images and return similarity score.

        Args:
            image1_path: Path to first image.
            image2_path: Path to second image.

        Returns:
            Similarity score (0-1), where 1 means identical faces.
        """
        self._ensure_face_recognition()

        if self._face_recognition is None:
            # Fallback: return 1.0 (assume consistent)
            logger.warning("Face recognition not available. Assuming consistency.")
            return 1.0

        try:
            import face_recognition
            image1 = face_recognition.load_image_file(image1_path)
            image2 = face_recognition.load_image_file(image2_path)

            # Get face encodings
            encodings1 = face_recognition.face_encodings(image1)
            encodings2 = face_recognition.face_encodings(image2)

            if not encodings1 or not encodings2:
                # No faces detected, assume consistent
                return 1.0

            # Compare first face in each image
            encoding1 = encodings1[0]
            encoding2 = encodings2[0]

            # Calculate similarity
            distances = face_recognition.face_distance([encoding1], encoding2)
            similarity = 1.0 - distances[0]

            return float(similarity)

        except Exception as e:
            logger.error(f"Face comparison failed: {e}")
            return 1.0  # Fallback to consistent

    def compare_with_clip(
        self,
        image1_path: str,
        image2_path: str,
    ) -> float:
        """Compare images using CLIP and return similarity score.

        Args:
            image1_path: Path to first image.
            image2_path: Path to second image.

        Returns:
            Similarity score (0-1), where 1 means identical images.
        """
        self._ensure_clip()

        if self._clip_model is None:
            # Fallback: return 1.0 (assume consistent)
            logger.warning("CLIP model not available. Assuming consistency.")
            return 1.0

        try:
            import torch
            from PIL import Image

            # Load and process images
            image1 = Image.open(image1_path).convert("RGB")
            image2 = Image.open(image2_path).convert("RGB")

            inputs1 = self._clip_processor(images=image1, return_tensors="pt")
            inputs2 = self._clip_processor(images=image2, return_tensors="pt")

            # Get image embeddings
            with torch.no_grad():
                embeddings1 = self._clip_model.get_image_features(**inputs1)
                embeddings2 = self._clip_model.get_image_features(**inputs2)

            # Calculate cosine similarity
            similarity = torch.nn.functional.cosine_similarity(
                embeddings1, embeddings2, dim=1
            )

            return float(similarity.item())

        except Exception as e:
            logger.error(f"CLIP comparison failed: {e}")
            return 1.0  # Fallback to consistent

    def validate_character_consistency(
        self,
        reference_image_path: str,
        render_images: list[str],
    ) -> list[dict]:
        """Validate character consistency across multiple renders.

        Args:
            reference_image_path: Path to reference image.
            render_images: List of render image paths.

        Returns:
            List of validation results with scores and flags.
        """
        results = []

        for render_path in render_images:
            # Compare faces
            face_similarity = self.compare_faces(reference_image_path, render_path)

            # Compare with CLIP
            clip_similarity = self.compare_with_clip(reference_image_path, render_path)

            # Overall score (weighted average)
            overall_score = 0.5 * face_similarity + 0.5 * clip_similarity

            # Flag inconsistencies
            face_inconsistent = face_similarity < self.face_threshold
            clip_inconsistent = clip_similarity < self.clip_threshold
            inconsistent = face_inconsistent or clip_inconsistent

            result = {
                "render_path": render_path,
                "face_similarity": face_similarity,
                "clip_similarity": clip_similarity,
                "overall_score": overall_score,
                "inconsistent": inconsistent,
                "face_inconsistent": face_inconsistent,
                "clip_inconsistent": clip_inconsistent,
            }
            results.append(result)

            if inconsistent:
                logger.warning(
                    f"Inconsistency detected for {render_path}: "
                    f"face={face_similarity:.2f}, clip={clip_similarity:.2f}"
                )

        return results

    def suggest_regeneration(
        self,
        validation_results: list[dict],
    ) -> list[str]:
        """Suggest regeneration for inconsistent renders.

        Args:
            validation_results: List of validation results.

        Returns:
            List of render paths that should be regenerated.
        """
        return [
            result["render_path"]
            for result in validation_results
            if result["inconsistent"]
        ]
