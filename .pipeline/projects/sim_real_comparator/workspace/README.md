# sim_real_comparator

Multi-metric similarity comparison between real and simulated MuJoCo videos.

## Features

- **SSIM** (Structural Similarity Index) for perceptual structural comparison
- **pHash** (Perceptual Hash) distance for perceptual similarity
- **Per-frame heatmap** overlays saved as PNG
- **Global [0,1] similarity score** via weighted aggregation
- **JSON report** with per-frame and global results

## Installation

```bash
pip install -e .
```

## Usage

```bash
sim-compare --real real_video.mp4 --sim sim_video.mp4 --output ./results
```

## Dependencies

- imageio
- scikit-image
- imagehash
- click
- pydantic
- numpy

## License

MIT
