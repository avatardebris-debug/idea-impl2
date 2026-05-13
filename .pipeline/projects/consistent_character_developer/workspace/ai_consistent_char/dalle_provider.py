"""DALL-E image provider — OpenAI API-based image generation.

Uses OpenAI's DALL-E API for reference image and scene render generation.
Handles API rate limits, retries, and error recovery.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

from .image_provider import CharacterImageProvider

logger = logging.getLogger(__name__)


class DALLECharacterImageProvider(CharacterImageProvider):
    """Image provider using OpenAI's DALL-E API.

    Supports:
    - Reference image generation from character descriptions
    - Scene renders using image-to-image capabilities
    - API rate limit handling with exponential backoff
    - Retry logic for transient errors

    Args:
        api_key: OpenAI API key
        model: DALL-E model version (default: "dall-e-3")
        image_size: Output image size (default: "1024x1024")
        max_retries: Maximum number of retries (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1)
        cache_dir: Directory to cache generated images
    """

    def __init__(
        self,
        api_key: str,
        model: str = "dall-e-3",
        image_size: str = "1024x1024",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        cache_dir: Optional[str] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.image_size = image_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache_dir = Path(cache_dir) if cache_dir else None

        # Lazy initialization of OpenAI client
        self._client = None

        # Cache for generated images
        self._cache: dict[str, str] = {}
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_cache()

    def _load_cache(self) -> None:
        """Load image cache from disk."""
        cache_file = self.cache_dir / "image_cache.json"
        if cache_file.exists():
            with open(cache_file, "r") as f:
                self._cache = json.load(f)

    def _save_cache(self) -> None:
        """Save image cache to disk."""
        if self.cache_dir:
            cache_file = self.cache_dir / "image_cache.json"
            with open(cache_file, "w") as f:
                json.dump(self._cache, f, indent=2)

    def _ensure_client(self) -> None:
        """Lazy initialization of OpenAI client."""
        if self._client is not None:
            return

        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.warning("openai library not installed. Using fallback mode.")
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self._client = None

    def _call_api_with_retry(
        self,
        api_func,
        *args,
        **kwargs
    ) -> Any:
        """Call API with exponential backoff retry logic.

        Args:
            api_func: API function to call
            *args: Positional arguments for API function
            **kwargs: Keyword arguments for API function

        Returns:
            API response

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return api_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        raise last_exception

    def generate_reference_image(
        self,
        character_id: str,
        visual_anchor_text: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Generate a character reference image using DALL-E.

        Args:
            character_id: Unique character identifier.
            visual_anchor_text: Visual description of the character.
            output_path: Path to save the generated image.
            seed: Optional random seed (not used by DALL-E).

        Returns:
            Path to the generated reference image.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._ensure_client()

        if self._client is None:
            # Fallback to dummy generation
            logger.warning("OpenAI client not available. Using fallback.")
            return self._generate_fallback_image(character_id, visual_anchor_text, output_path)

        prompt = f"Portrait of {visual_anchor_text}, high quality, detailed, professional photography style"

        def generate_image():
            return self._client.images.generate(
                model=self.model,
                prompt=prompt,
                n=1,
                size=self.image_size,
                response_format="url",
            )

        response = self._call_api_with_retry(generate_image)

        # Download image
        import requests
        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        output_path.write_bytes(image_data)

        return str(output_path)

    def render_character(
        self,
        character_id: str,
        reference_image_path: str,
        scene_context: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Render a character in a specific scene context using DALL-E.

        Uses the reference image as input for image-to-image generation.

        Args:
            character_id: Unique character identifier.
            reference_image_path: Path to the character's reference image.
            scene_context: Scene action/context for the render.
            output_path: Path to save the rendered image.
            seed: Optional random seed (not used by DALL-E).

        Returns:
            Path to the rendered image.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._ensure_client()

        if self._client is None:
            # Fallback to dummy generation
            logger.warning("OpenAI client not available. Using fallback.")
            return self._generate_fallback_image(character_id, scene_context, output_path)

        # Load reference image
        from PIL import Image
        from io import BytesIO
        ref_image = Image.open(reference_image_path)

        # Convert to base64 for API
        import base64
        buffered = BytesIO()
        ref_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        prompt = f"{scene_context}, maintaining character consistency with reference image, high quality, detailed"

        def generate_image():
            return self._client.images.generate(
                model=self.model,
                prompt=prompt,
                n=1,
                size=self.image_size,
                response_format="url",
                image=img_base64,  # For image-to-image
            )

        response = self._call_api_with_retry(generate_image)

        # Download image
        import requests
        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        output_path.write_bytes(image_data)

        return str(output_path)

    def _generate_fallback_image(
        self,
        character_id: str,
        description: str,
        output_path: Path,
    ) -> str:
        """Generate a fallback image when DALL-E is not available."""
        import struct
        import zlib

        width, height = 512, 512
        # Create a simple gradient image
        raw_data = b""
        for y in range(height):
            for x in range(width):
                r = int(255 * x / width)
                g = int(255 * y / height)
                b = 128
                raw_data += bytes([r, g, b, 255])  # RGBA

        compressed = zlib.compress(raw_data)
        png_data = (
            b"\x89PNG\r\n\x1a\n"
            + struct.pack(">I", width)
            + struct.pack(">I", height)
            + b"\x08\x06\x00\x00\x00"
            + struct.pack(">I", len(compressed))
            + compressed
            + struct.pack(">I", 0)
        )
        output_path.write_bytes(png_data)
        return str(output_path)
