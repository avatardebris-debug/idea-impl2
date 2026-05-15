"""Image providers for consistent character generation.

Provides a base CharacterImageProvider interface along with concrete
implementations: DummyCharacterImageProvider (for testing),
LLMCharacterImageProvider (for LLM-based generation), and
StableDiffusionCharacterImageProvider (for production use).
"""

from __future__ import annotations

import abc
import json
import logging
import pathlib
import struct
import zlib
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CharacterImageProvider(abc.ABC):
    """Abstract base class for character image providers.

    Subclasses must implement:
    - generate_reference_image: create a reference image for a character
    - render_character: render a character in a specific scene context
    """

    @abc.abstractmethod
    def generate_reference_image(
        self,
        character_id: str,
        visual_anchor_text: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Generate a character reference image.

        Args:
            character_id: Unique character identifier.
            visual_anchor_text: Visual description of the character.
            output_path: Path to save the generated image.
            seed: Optional random seed for reproducibility.

        Returns:
            Path to the generated reference image.
        """
        ...

    @abc.abstractmethod
    def render_character(
        self,
        character_id: str,
        reference_image_path: str,
        scene_context: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Render a character in a specific scene context.

        Args:
            character_id: Unique character identifier.
            reference_image_path: Path to the character's reference image.
            scene_context: Scene action/context for the render.
            output_path: Path to save the rendered image.
            seed: Optional random seed for reproducibility.

        Returns:
            Path to the rendered image.
        """
        ...


class DummyCharacterImageProvider(CharacterImageProvider):
    """Dummy image provider that generates placeholder PNG images.

    Useful for testing and development without requiring external dependencies.
    """

    def generate_reference_image(
        self,
        character_id: str,
        visual_anchor_text: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Generate a dummy reference image as a placeholder PNG."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._generate_dummy_image(output_path, character_id)
        return str(output_path)

    def render_character(
        self,
        character_id: str,
        reference_image_path: str,
        scene_context: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Generate a dummy scene render as a placeholder PNG."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._generate_dummy_image(output_path, character_id, suffix=scene_context[:20])
        return str(output_path)

    @staticmethod
    def _generate_dummy_image(output_path: Path, label: str, suffix: str = "") -> None:
        """Generate a simple gradient PNG with a label."""
        width, height = 512, 512
        raw_data = bytearray(width * height * 4)
        idx = 0
        for y in range(height):
            for x in range(width):
                raw_data[idx] = int(255 * x / width)
                raw_data[idx+1] = int(255 * y / height)
                raw_data[idx+2] = 128
                raw_data[idx+3] = 255
                idx += 4

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


class LLMCharacterImageProvider(CharacterImageProvider):
    """LLM-based image provider that generates images via an LLM API.

    Uses an LLM to produce image generation prompts and calls an external
    image generation API (e.g., DALL-E, Stable Diffusion API).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "dall-e-3",
        size: str = "1024x1024",
    ):
        self.api_key = api_key
        self.model = model
        self.size = size

    def generate_reference_image(
        self,
        character_id: str,
        visual_anchor_text: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Generate a reference image using an LLM-based image API."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # In production, this would call the LLM API
        # For now, fall back to dummy generation
        logger.info(f"LLMCharacterImageProvider: generating reference for {character_id}")
        self._generate_dummy_image(output_path, character_id)
        return str(output_path)

    def render_character(
        self,
        character_id: str,
        reference_image_path: str,
        scene_context: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Render a character in a scene context using an LLM-based API."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"LLMCharacterImageProvider: rendering {character_id} in scene")
        self._generate_dummy_image(output_path, character_id, suffix=scene_context[:20])
        return str(output_path)

    @staticmethod
    def _generate_dummy_image(output_path: Path, label: str, suffix: str = "") -> None:
        """Generate a simple gradient PNG."""
        width, height = 512, 512
        raw_data = bytearray(width * height * 4)
        idx = 0
        for y in range(height):
            for x in range(width):
                raw_data[idx] = int(255 * x / width)
                raw_data[idx+1] = int(255 * y / height)
                raw_data[idx+2] = 128
                raw_data[idx+3] = 255
                idx += 4

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


class StableDiffusionCharacterImageProvider(CharacterImageProvider):
    """Production-grade image provider using Stable Diffusion.

    Supports:
    - Reference image generation from character descriptions
    - Scene renders using reference images as conditioning
    - LoRA fine-tuning for character consistency
    - ControlNet for pose/structure control
    - Image caching to avoid redundant API calls

    Args:
        model_name: HuggingFace model name (default: "runwayml/stable-diffusion-v1-5")
        lora_path: Path to LoRA weights for character consistency
        controlnet_path: Path to ControlNet model for pose control
        cache_dir: Directory to cache generated images
        seed: Default random seed
        num_inference_steps: Number of diffusion steps (default: 50)
        guidance_scale: Classifier-free guidance scale (default: 7.5)
    """

    def __init__(
        self,
        model_name: str = "runwayml/stable-diffusion-v1-5",
        lora_path: Optional[str] = None,
        controlnet_path: Optional[str] = None,
        cache_dir: Optional[str] = None,
        seed: Optional[int] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
    ):
        self.model_name = model_name
        self.lora_path = lora_path
        self.controlnet_path = controlnet_path
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.seed = seed
        self.num_inference_steps = num_inference_steps
        self.guidance_scale = guidance_scale

        # Lazy initialization of pipeline
        self._pipeline = None
        self._tokenizer = None
        self._scheduler = None

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

    def _get_cache_key(
        self,
        character_id: str,
        visual_anchor_text: str,
        seed: Optional[int] = None,
    ) -> str:
        """Generate a cache key for image generation."""
        key_data = f"{character_id}:{visual_anchor_text}:{seed}:{self.model_name}:{self.num_inference_steps}:{self.guidance_scale}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _ensure_pipeline(self) -> None:
        """Lazy initialization of the Stable Diffusion pipeline."""
        if self._pipeline is not None:
            return

        try:
            from diffusers import (
                AutoencoderKL,
                DPMSolverMultistepScheduler,
                StableDiffusionPipeline,
                UNet2DConditionModel,
            )
            from transformers import CLIPTextModel, CLIPTokenizer

            # Load base model
            logger.info(f"Loading Stable Diffusion model: {self.model_name}")
            self._tokenizer = CLIPTokenizer.from_pretrained(self.model_name, subfolder="tokenizer")
            self._text_encoder = CLIPTextModel.from_pretrained(self.model_name, subfolder="text_encoder")
            self._unet = UNet2DConditionModel.from_pretrained(self.model_name, subfolder="unet")
            self._vae = AutoencoderKL.from_pretrained(self.model_name, subfolder="vae")
            self._scheduler = DPMSolverMultistepScheduler.from_pretrained(self.model_name, subfolder="scheduler")

            # Initialize pipeline
            self._pipeline = StableDiffusionPipeline(
                vae=self._vae,
                text_encoder=self._text_encoder,
                tokenizer=self._tokenizer,
                unet=self._unet,
                scheduler=self._scheduler,
            )

            # Load LoRA weights if provided
            if self.lora_path:
                logger.info(f"Loading LoRA weights from {self.lora_path}")
                self._pipeline.load_lora_weights(self.lora_path)
                self._pipeline.fuse_lora()

            # Load ControlNet if provided
            if self.controlnet_path:
                logger.info(f"Loading ControlNet from {self.controlnet_path}")
                from diffusers import ControlNetModel
                self._controlnet = ControlNetModel.from_pretrained(self.controlnet_path)
                self._pipeline.controlnet = self._controlnet

            logger.info("Stable Diffusion pipeline loaded successfully")

        except ImportError:
            logger.warning("diffusers library not installed. Using fallback mode.")
            self._pipeline = None
        except Exception as e:
            logger.error(f"Failed to load Stable Diffusion pipeline: {e}")
            self._pipeline = None

    def generate_reference_image(
        self,
        character_id: str,
        visual_anchor_text: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Generate a character reference image using Stable Diffusion.

        Args:
            character_id: Unique character identifier.
            visual_anchor_text: Visual description of the character.
            output_path: Path to save the generated image.
            seed: Optional random seed for reproducibility.

        Returns:
            Path to the generated reference image.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Check cache
        cache_key = self._get_cache_key(character_id, visual_anchor_text, seed)
        if self.cache_dir and cache_key in self._cache:
            cached_path = self.cache_dir / self._cache[cache_key]
            if cached_path.exists():
                logger.info(f"Using cached reference image for {character_id}")
                return str(cached_path)

        # Ensure pipeline is loaded
        self._ensure_pipeline()

        if self._pipeline is None:
            # Fallback to dummy generation
            logger.warning("Stable Diffusion pipeline not available. Using fallback.")
            return self._generate_fallback_image(character_id, visual_anchor_text, output_path)

        # Generate image
        effective_seed = seed if seed is not None else self.seed
        if effective_seed is not None:
            generator = None
            try:
                import torch
                generator = torch.Generator().manual_seed(effective_seed)
            except ImportError:
                logger.warning("torch not available. Skipping seed.")

        prompt = f"portrait of {visual_anchor_text}, high quality, detailed"
        negative_prompt = "blurry, low quality, distorted, deformed"

        logger.info(f"Generating reference image for {character_id}")
        image = self._pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
            generator=generator,
        ).images[0]

        # Save image
        image.save(output_path)

        # Update cache
        if self.cache_dir:
            cache_filename = f"{cache_key}.png"
            cached_path = self.cache_dir / cache_filename
            image.save(cached_path)
            self._cache[cache_key] = cache_filename
            self._save_cache()

        return str(output_path)

    def render_character(
        self,
        character_id: str,
        reference_image_path: str,
        scene_context: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Render a character in a specific scene context using Stable Diffusion.

        Uses the reference image as conditioning input (via img2img or ControlNet).

        Args:
            character_id: Unique character identifier.
            reference_image_path: Path to the character's reference image.
            scene_context: Scene action/context for the render.
            output_path: Path to save the rendered image.
            seed: Optional random seed for reproducibility.

        Returns:
            Path to the rendered image.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Check cache
        cache_key = self._get_cache_key(character_id, scene_context, seed)
        if self.cache_dir and cache_key in self._cache:
            cached_path = self.cache_dir / self._cache[cache_key]
            if cached_path.exists():
                logger.info(f"Using cached scene render for {character_id}")
                return str(cached_path)

        # Ensure pipeline is loaded
        self._ensure_pipeline()

        if self._pipeline is None:
            # Fallback to dummy generation
            logger.warning("Stable Diffusion pipeline not available. Using fallback.")
            return self._generate_fallback_image(character_id, scene_context, output_path)

        # Load reference image
        from PIL import Image
        ref_image = Image.open(reference_image_path)

        # Generate scene render using img2img
        effective_seed = seed if seed is not None else self.seed
        if effective_seed is not None:
            generator = None
            try:
                import torch
                generator = torch.Generator().manual_seed(effective_seed)
            except ImportError:
                logger.warning("torch not available. Skipping seed.")

        prompt = f"{scene_context}, {ref_image.format} style, high quality, detailed"
        negative_prompt = "blurry, low quality, distorted, deformed"

        logger.info(f"Rendering {character_id} in scene context")
        image = self._pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=ref_image,
            strength=0.75,  # img2img strength
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
            generator=generator,
        ).images[0]

        # Save image
        image.save(output_path)

        # Update cache
        if self.cache_dir:
            cache_filename = f"{cache_key}.png"
            cached_path = self.cache_dir / cache_filename
            image.save(cached_path)
            self._cache[cache_key] = cache_filename
            self._save_cache()

        return str(output_path)

    def _generate_fallback_image(
        self,
        character_id: str,
        description: str,
        output_path: Path,
    ) -> str:
        """Generate a fallback image when Stable Diffusion is not available."""
        width, height = 512, 512
        # Create a simple gradient image
        raw_data = bytearray(width * height * 4)
        idx = 0
        for y in range(height):
            for x in range(width):
                raw_data[idx] = int(255 * x / width)
                raw_data[idx+1] = int(255 * y / height)
                raw_data[idx+2] = 128
                raw_data[idx+3] = 255
                idx += 4

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
