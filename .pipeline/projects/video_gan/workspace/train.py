#!/usr/bin/env python3
"""
Standalone training script for VideoGAN.

Usage:
    python train.py
    python train.py --config config.yaml
    python train.py --epochs 50 --batch-size 8 --device cuda
"""

import argparse
import os
import sys
import pathlib
import json
import yaml
import time
from datetime import datetime

# Add workspace to path
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.video_gan import VideoGAN
from video_gan.video_processor import VideoProcessor


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def save_training_log(log: dict, output_dir: str):
    """Save training log to JSON file."""
    log_path = os.path.join(output_dir, 'training_log.json')
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2, default=str)
    print(f"Training log saved to {log_path}")


def train(args: argparse.Namespace):
    """Main training function."""
    # Load config if provided
    config = {}
    if args.config:
        config = load_config(args.config)
        print(f"Loaded config from {args.config}")
    
    # Merge args and config
    epochs = args.epochs or config.get('epochs', 10)
    batch_size = args.batch_size or config.get('batch_size', 4)
    lr_g = args.lr_g or config.get('lr_g', 2e-4)
    lr_d = args.lr_d or config.get('lr_d', 2e-4)
    device = args.device or config.get('device', 'cpu')
    output_dir = args.output_dir or config.get('output_dir', 'outputs')
    save_interval = args.save_interval or config.get('save_interval', 5)
    num_samples = args.num_samples or config.get('num_samples', 10)
    
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = os.path.join(output_dir, f'run_{timestamp}')
    os.makedirs(run_dir, exist_ok=True)
    print(f"Output directory: {run_dir}")
    
    # Initialize VideoGAN
    gan = VideoGAN(
        lr_g=lr_g,
        lr_d=lr_d,
        device=device
    )
    
    # Create video processor
    processor = VideoProcessor()
    
    # Training log
    training_log = {
        'start_time': datetime.now().isoformat(),
        'config': {
            'epochs': epochs,
            'batch_size': batch_size,
            'lr_g': lr_g,
            'lr_d': lr_d,
            'device': device,
            'output_dir': run_dir,
        },
        'epoch_losses': [],
    }
    
    print(f"\n{'='*60}")
    print(f"VideoGAN Training")
    print(f"{'='*60}")
    print(f"Device: {device}")
    print(f"Batch size: {batch_size}")
    print(f"Generator LR: {lr_g}")
    print(f"Discriminator LR: {lr_d}")
    print(f"Epochs: {epochs}")
    print(f"Save interval: {save_interval}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    # Training loop
    for epoch in range(epochs):
        epoch_start = time.time()
        
        # Create random video data
        real_videos = processor.create_random_video(batch_size=batch_size)
        
        # Train for one epoch
        losses = gan.train_epoch(real_videos, batch_size=batch_size)
        
        epoch_time = time.time() - epoch_start
        elapsed_time = time.time() - start_time
        
        # Update training log
        training_log['epoch_losses'].append({
            'epoch': epoch + 1,
            'd_loss': losses['d_loss'],
            'g_loss': losses['g_loss'],
            'epoch_time': epoch_time,
            'elapsed_time': elapsed_time,
        })
        
        # Print progress
        if (epoch + 1) % 1 == 0:
            print(
                f"Epoch {epoch+1:3d}/{epochs} | "
                f"D Loss: {losses['d_loss']:.4f} | "
                f"G Loss: {losses['g_loss']:.4f} | "
                f"Time: {epoch_time:.2f}s | "
                f"Elapsed: {elapsed_time:.0f}s"
            )
        
        # Save checkpoint
        if (epoch + 1) % save_interval == 0:
            checkpoint_path = os.path.join(run_dir, f'checkpoint_epoch_{epoch+1}.pt')
            gan.save_checkpoint(checkpoint_path)
            print(f"  ✓ Checkpoint saved to {checkpoint_path}")
    
    # Save final model
    final_path = os.path.join(run_dir, 'final_model.pt')
    gan.save_checkpoint(final_path)
    print(f"\n✓ Final model saved to {final_path}")
    
    # Save training log
    training_log['end_time'] = datetime.now().isoformat()
    training_log['total_time'] = time.time() - start_time
    save_training_log(training_log, run_dir)
    
    # Generate sample videos
    print(f"\nGenerating {num_samples} sample videos...")
    os.makedirs(os.path.join(run_dir, 'samples'), exist_ok=True)
    
    for i in range(num_samples):
        real_video = processor.create_random_video(batch_size=1)
        fake_video = gan.generate(real_video)
        
        output_path = os.path.join(run_dir, 'samples', f'sample_{i:03d}.mp4')
        processor.save_video_frames(fake_video[0].cpu().numpy(), output_path, fps=10.0)
    
    print(f"✓ Sample videos saved to {os.path.join(run_dir, 'samples')}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Training Complete!")
    print(f"{'='*60}")
    print(f"Total time: {training_log['total_time']:.0f}s")
    print(f"Final D Loss: {training_log['epoch_losses'][-1]['d_loss']:.4f}")
    print(f"Final G Loss: {training_log['epoch_losses'][-1]['g_loss']:.4f}")
    print(f"Output directory: {run_dir}")
    print(f"{'='*60}")


def main():
    """Parse arguments and run training."""
    parser = argparse.ArgumentParser(description='Train VideoGAN')
    parser.add_argument('--config', '-c', type=str, help='Path to config file')
    parser.add_argument('--epochs', '-e', type=int, help='Number of training epochs')
    parser.add_argument('--batch-size', '-b', type=int, help='Batch size for training')
    parser.add_argument('--lr-g', type=float, help='Learning rate for generator')
    parser.add_argument('--lr-d', type=float, help='Learning rate for discriminator')
    parser.add_argument('--device', '-d', type=str, help='Device to train on (cpu/cuda)')
    parser.add_argument('--output-dir', '-o', type=str, help='Output directory for results')
    parser.add_argument('--save-interval', type=int, help='Save checkpoint every N epochs')
    parser.add_argument('--num-samples', type=int, help='Number of sample videos to generate')
    
    args = parser.parse_args()
    train(args)


if __name__ == '__main__':
    main()
