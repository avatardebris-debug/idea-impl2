"""CLI entry point for sim_real_comparator."""

import os
import sys
import click
import numpy as np
from PIL import Image

from sim_real_comparator.frame_extractor import extract_frames
from sim_real_comparator.metrics import compute_ssim, compute_phash_distance, compute_color_distance
from sim_real_comparator.clip_wrapper import compute_clip_similarity
from sim_real_comparator.heatmaps import generate_heatmap_batch
from sim_real_comparator.scorer import compute_global_score
from sim_real_comparator.report import write_report
from sim_real_comparator.models import FrameResult


@click.command()
@click.option("--real-video", required=True, help="Path to the real video file.")
@click.option("--sim-video", required=True, help="Path to the simulated video file.")
@click.option("--output-dir", required=True, help="Output directory for results.")
@click.option("--num-frames", default=None, type=int, help="Number of frames to extract.")
@click.option("--fps-real", default=None, type=float, help="FPS of the real video for normalization.")
@click.option("--fps-sim", default=None, type=float, help="FPS of the simulated video for normalization.")
@click.option("--frame-start", default=0, type=int, help="Starting frame index.")
@click.option("--frame-end", default=None, type=int, help="Ending frame index (exclusive).")
def cli(
    real_video: str,
    sim_video: str,
    output_dir: str,
    num_frames: int | None,
    fps_real: float | None,
    fps_sim: float | None,
    frame_start: int,
    frame_end: int | None,
):
    """Compare real and simulated video similarity across multiple metrics.

    Extracts frames from both videos, computes SSIM, pHash distance, and CLIP
    cosine similarity per frame, generates heatmap overlays, and writes a JSON
    report with global scores.
    """
    # Extract frames
    click.echo(f"Extracting frames from {real_video}...")
    real_frames = extract_frames(real_video, num_frames=num_frames)
    click.echo(f"Extracted {len(real_frames)} frames from real video.")

    click.echo(f"Extracting frames from {sim_video}...")
    sim_frames = extract_frames(sim_video, num_frames=num_frames)
    click.echo(f"Extracted {len(sim_frames)} frames from sim video.")

    # Determine number of frames to compare (min of both)
    n_frames = min(len(real_frames), len(sim_frames))

    # Apply frame range constraints
    start = frame_start
    end = frame_end if frame_end is not None else n_frames
    start = max(0, start)
    end = min(n_frames, end)
    if start >= end:
        click.echo("Error: frame_start >= frame_end results in no frames to compare.")
        sys.exit(1)

    real_frames = real_frames[start:end]
    sim_frames = sim_frames[start:end]
    n_frames = len(real_frames)

    # FPS normalization: if fps_real and fps_sim differ, subsample to match
    if fps_real and fps_sim and fps_real != fps_sim:
        click.echo(f"Normalizing FPS: real={fps_real}, sim={fps_sim}")
        # Resample to the lower FPS
        target_fps = min(fps_real, fps_sim)
        if fps_real > fps_sim:
            # Downsample real frames
            ratio = fps_sim / fps_real
            indices = [int(i / ratio) for i in range(n_frames)]
            indices = [min(i, len(real_frames) - 1) for i in indices]
            real_frames = real_frames[indices]
        else:
            # Downsample sim frames
            ratio = fps_real / fps_sim
            indices = [int(i / ratio) for i in range(n_frames)]
            indices = [min(i, len(sim_frames) - 1) for i in indices]
            sim_frames = sim_frames[indices]
        n_frames = min(len(real_frames), len(sim_frames))

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Compute metrics per frame
    click.echo("Computing similarity metrics...")
    frame_results = []
    for i in range(n_frames):
        fa = real_frames[i]
        fb = sim_frames[i]

        # SSIM
        ssim = compute_ssim(fa, fb)

        # pHash distance
        phash_dist = compute_phash_distance(fa, fb)

        # CLIP similarity
        img_a = Image.fromarray(fa)
        img_b = Image.fromarray(fb)
        clip_sim = compute_clip_similarity(img_a, img_b)

        # Color distance
        color_dist = compute_color_distance(fa, fb)

        frame_results.append(FrameResult(
            frame_index=i,
            ssim=ssim,
            phash_distance=phash_dist,
            clip_similarity=clip_sim,
            color_distance=color_dist,
        ))

    # Generate heatmaps
    click.echo("Generating heatmaps...")
    heatmap_dir = os.path.join(output_dir, "heatmaps")
    heatmap_paths = generate_heatmap_batch(real_frames, sim_frames, heatmap_dir)
    click.echo(f"Generated {len(heatmap_paths)} heatmaps in {heatmap_dir}")

    # Compute global score
    click.echo("Computing global score...")
    global_result = compute_global_score(frame_results)

    # Write report
    click.echo("Writing report...")
    report_path = write_report(frame_results, global_result, output_dir)
    click.echo(f"Report written to {report_path}")
    click.echo(f"Global score: {global_result.global_score:.4f}")
    click.echo(f"  avg_ssim: {global_result.avg_ssim:.4f}")
    click.echo(f"  avg_phash_similarity: {global_result.avg_phash_similarity:.4f}")
    click.echo(f"  avg_clip_similarity: {global_result.avg_clip_similarity:.4f}")


if __name__ == "__main__":
    cli()
