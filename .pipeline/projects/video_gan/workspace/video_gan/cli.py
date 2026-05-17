"""
Command-line interface for VideoGAN.

Provides commands for:
  - Training the GAN
  - Generating videos
  - Evaluating models
  - Inspecting models
"""

import click
import torch
import numpy as np
import sys
import pathlib
import os
import json
import yaml

# Add workspace to path
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.video_gan import VideoGAN
from video_gan.video_processor import VideoProcessor
from video_gan.generator import Generator
from video_gan.discriminator import Discriminator


@click.command()
@click.version_option(version="1.0.0")
@click.option('--epochs', '-e', default=10, help='Number of training epochs')
@click.option('--batch-size', '-b', default=4, help='Batch size for training')
@click.option('--lr-g', default=2e-4, help='Learning rate for generator')
@click.option('--lr-d', default=2e-4, help='Learning rate for discriminator')
@click.option('--device', '-d', default='cpu', help='Device to train on (cpu/cuda)')
@click.option('--output-dir', '-o', default='outputs', help='Output directory for results')
@click.option('--save-interval', default=5, help='Save checkpoint every N epochs')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.option('--generate', '-g', type=int, default=None, help='Number of videos to generate')
@click.option('--classify', type=str, default=None, help='Classify a video file')
@click.option('--info', '-i', is_flag=True, default=False, help='Show model info')
@click.option('--save', '-s', type=str, default=None, help='Save model checkpoint')
@click.option('--load', '-l', type=str, default=None, help='Load model checkpoint')
def main(
    epochs, batch_size, lr_g, lr_d, device, output_dir, save_interval, config,
    generate, classify, info, save, load
):
    """VideoGAN - PyTorch-based Video Generative Adversarial Network."""
    
    # Train command
    if not any([generate, classify, info, save, load]):
        # Load config if provided
        if config:
            with open(config, 'r') as f:
                cfg = yaml.safe_load(f)
            epochs = cfg.get('epochs', epochs)
            batch_size = cfg.get('batch_size', batch_size)
            lr_g = cfg.get('lr_g', lr_g)
            lr_d = cfg.get('lr_d', lr_d)
            device = cfg.get('device', device)
            output_dir = cfg.get('output_dir', output_dir)
            save_interval = cfg.get('save_interval', save_interval)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize VideoGAN
        gan = VideoGAN(
            lr_g=lr_g,
            lr_d=lr_d,
            device=device
        )
        
        # Create video processor
        processor = VideoProcessor()
        
        # Training loop
        click.echo(f"Training VideoGAN for {epochs} epochs...")
        click.echo(f"Device: {device}")
        click.echo(f"Batch size: {batch_size}")
        
        for epoch in range(epochs):
            # Create random video data
            real_videos = processor.create_random_video(batch_size=batch_size)
            
            # Train for one epoch
            losses = gan.train_epoch(real_videos, batch_size=batch_size)
            
            # Print progress
            click.echo(
                f"Epoch {epoch+1}/{epochs} | "
                f"D Loss: {losses['d_loss']:.4f} | "
                f"G Loss: {losses['g_loss']:.4f}"
            )
            
            # Save checkpoint
            if (epoch + 1) % save_interval == 0:
                checkpoint_path = os.path.join(output_dir, f'checkpoint_epoch_{epoch+1}.pt')
                gan.save_checkpoint(checkpoint_path)
                click.echo(f"Checkpoint saved to {checkpoint_path}")
        
        # Save final model
        final_path = os.path.join(output_dir, 'final_model.pt')
        gan.save_checkpoint(final_path)
        click.echo(f"Final model saved to {final_path}")
    
    # Generate command
    elif generate is not None:
        # Initialize VideoGAN
        gan = VideoGAN()
        
        # Create video processor
        processor = VideoProcessor()
        
        # Generate videos
        click.echo(f"Generating {generate} videos...")
        
        for i in range(generate):
            # Create random input
            real_video = processor.create_random_video(batch_size=1)
            
            # Generate fake video
            fake_video = gan.generate(real_video)
            
            # Save video
            output_path = f'generated_{i:03d}.mp4'
            processor.save_video_frames(fake_video[0].cpu().numpy(), output_path, fps=10.0)
            click.echo(f"Generated video saved to {output_path}")
    
    # Classify command
    elif classify is not None:
        # Initialize VideoGAN
        gan = VideoGAN()
        
        # Create video processor
        processor = VideoProcessor()
        
        # Load video
        video_frames = processor.load_video_frames(classify)
        
        # Classify video
        real_score, fake_score = gan.classify(video_frames)
        
        click.echo(f"Real score: {real_score:.4f}")
        click.echo(f"Fake score: {fake_score:.4f}")
    
    # Info command
    elif info:
        # Initialize VideoGAN
        gan = VideoGAN()
        
        # Print model info
        click.echo("=== Generator ===")
        click.echo(f"Latent dim: {gan.generator_latent_dim}")
        click.echo(f"Num frames: {gan.generator_num_frames}")
        click.echo(f"Frame size: {gan.generator_frame_size}")
        click.echo(f"Input channels: {gan.discriminator_input_channels}")
        click.echo(f"Num frames: {gan.discriminator_num_frames}")
        click.echo(f"Frame size: {gan.discriminator_frame_size}")
    
    # Save command
    elif save is not None:
        # Initialize VideoGAN
        gan = VideoGAN()
        
        # Save model
        gan.save_checkpoint(save)
        click.echo(f"Model saved to {save}")
    
    # Load command
    elif load is not None:
        # Initialize VideoGAN
        gan = VideoGAN()
        
        # Load model
        gan.load_checkpoint(load)
        click.echo(f"Model loaded from {load}")


if __name__ == '__main__':
    main()
