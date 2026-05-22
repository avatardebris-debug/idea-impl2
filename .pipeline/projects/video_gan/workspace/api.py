"""
REST API for VideoGAN using FastAPI.

Provides endpoints for:
  - Generating fake videos
  - Classifying videos as real or fake
  - Training the GAN
  - Model inspection
"""

import sys
import pathlib
import os
import tempfile
import uuid
from typing import Optional

import torch
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Add workspace to path
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.video_gan import VideoGAN
from video_gan.video_processor import VideoProcessor

# ── app ────────────────────────────────────────────────────────────

app = FastAPI(
    title="VideoGAN API",
    description="REST API for Video Generative Adversarial Network",
    version="1.0.0",
)

# Global model instance (lazy-loaded)
_gan: Optional[VideoGAN] = None
_processor: Optional[VideoProcessor] = None


def _get_gan() -> VideoGAN:
    """Get or create the global GAN instance."""
    global _gan
    if _gan is None:
        _gan = VideoGAN()
    return _gan


def _get_processor() -> VideoProcessor:
    """Get or create the global processor instance."""
    global _processor
    if _processor is None:
        _processor = VideoProcessor()
    return _processor


# ── request/response models ─────────────────────────────────────────

class TrainRequest(BaseModel):
    """Training request parameters."""
    epochs: int = Field(10, ge=1, le=1000, description="Number of training epochs")
    batch_size: int = Field(4, ge=1, le=128, description="Batch size")
    lr_g: float = Field(2e-4, gt=0, le=1, description="Generator learning rate")
    lr_d: float = Field(2e-4, gt=0, le=1, description="Discriminator learning rate")
    device: str = Field("cpu", pattern="^(cpu|cuda)$", description="Device to train on")


class TrainResponse(BaseModel):
    """Training response."""
    status: str = "completed"
    epochs: int
    final_d_loss: float
    final_g_loss: float


class GenerateRequest(BaseModel):
    """Video generation request."""
    num_samples: int = Field(1, ge=1, le=100, description="Number of videos to generate")
    batch_size: int = Field(1, ge=1, le=32, description="Batch size for generation")


class GenerateResponse(BaseModel):
    """Video generation response."""
    status: str = "completed"
    num_generated: int
    video_paths: list[str] = Field(default_factory=list, description="Paths to generated video files")


class ClassifyRequest(BaseModel):
    """Video classification request."""
    video_path: str = Field(..., description="Path to video file")


class ClassifyResponse(BaseModel):
    """Video classification response."""
    is_real: bool
    real_score: float
    fake_score: float


class ModelInfoResponse(BaseModel):
    """Model information response."""
    generator_latent_dim: int
    generator_num_frames: int
    generator_frame_size: int
    discriminator_input_channels: int
    discriminator_num_frames: int
    discriminator_frame_size: int


# ── endpoints ────────────────────────────────────────────────────────

@app.post("/train", response_model=TrainResponse)
async def train_model(request: TrainRequest, background_tasks: BackgroundTasks):
    """Train the VideoGAN model."""
    gan = _get_gan()
    processor = _get_processor()
    
    # Run training in background to avoid blocking
    def _train():
        for epoch in range(request.epochs):
            real_videos = processor.create_random_video(batch_size=request.batch_size)
            losses = gan.train_epoch(real_videos, batch_size=request.batch_size)
            final_d_loss = losses['d_loss']
            final_g_loss = losses['g_loss']
        return final_d_loss, final_g_loss
    
    # Run training synchronously for simplicity
    final_d_loss, final_g_loss = _train()
    
    return TrainResponse(
        status="completed",
        epochs=request.epochs,
        final_d_loss=final_d_loss,
        final_g_loss=final_g_loss,
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_videos(request: GenerateRequest):
    """Generate fake videos using the trained model."""
    gan = _get_gan()
    processor = _get_processor()
    
    # Create temporary directory for outputs
    temp_dir = tempfile.mkdtemp()
    video_paths = []
    
    for i in range(request.num_samples):
        # Create random input
        real_video = processor.create_random_video(batch_size=request.batch_size)
        
        # Generate fake videos
        fake_videos = gan.generate(real_video)
        
        # Save each video
        for j in range(request.batch_size):
            video_path = os.path.join(temp_dir, f"generated_{i}_{j}.mp4")
            processor.save_video_frames(fake_videos[j].cpu().numpy(), video_path, fps=10.0)
            video_paths.append(video_path)
    
    return GenerateResponse(
        status="completed",
        num_generated=request.num_samples * request.batch_size,
        video_paths=video_paths,
    )


@app.post("/classify", response_model=ClassifyResponse)
async def classify_video(request: ClassifyRequest):
    """Classify a video as real or fake."""
    gan = _get_gan()
    processor = _get_processor()
    
    # Load video
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    video = processor.load_video(request.video_path)
    if video is None:
        raise HTTPException(status_code=400, detail="Failed to load video")
    
    # Convert to tensor
    video_tensor = torch.from_numpy(video).permute(0, 3, 1, 2).unsqueeze(0).float()
    
    # Classify
    scores, _ = gan.classify(video_tensor)
    
    # Determine if real or fake
    is_real = scores > 0.5
    
    return ClassifyResponse(
        is_real=is_real,
        real_score=scores.item(),
        fake_score=1.0 - scores.item(),
    )


@app.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the current model."""
    gan = _get_gan()
    
    return ModelInfoResponse(
        generator_latent_dim=gan.generator.latent_dim,
        generator_num_frames=gan.generator.num_frames,
        generator_frame_size=gan.generator.frame_size,
        discriminator_input_channels=gan.discriminator.input_channels,
        discriminator_num_frames=gan.discriminator.num_frames,
        discriminator_frame_size=gan.discriminator.frame_size,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the API server."""
    uvicorn.run(
        "video_gan.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
