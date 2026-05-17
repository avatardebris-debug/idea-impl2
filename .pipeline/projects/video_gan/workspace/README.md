# Video GAN

A PyTorch-based Video Generative Adversarial Network (GAN) that generates fake video frames from real video input.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Video GAN System                       │
├───────────────────┬───────────────────┬─────────────────────┤
│   Generator       │   Discriminator   │   VideoProcessor    │
│                   │                   │                     │
│  Input:           │  Input:           │  Input:             │
│  real_video +     │  video            │  video_path or      │
│  noise            │                   │  numpy array        │
│                   │                   │                     │
│  ┌─────────────┐  │                   │  ┌───────────────┐  │
│  │ Input       │  │                   │  │ load_video    │  │
│  │ Encoder     │  │                   │  │ normalize     │  │
│  └──────┬──────┘  │                   │  │ denormalize   │  │
│         │        │                   │  │ create_random │  │
│  ┌──────▼──────┐  │                   │  │ create_const  │  │
│  │ Noise       │  │                   │  └───────────────┘  │
│  │ Projection  │  │                   │                     │
│  └──────┬──────┘  │                   │                     │
│         │        │                   │                     │
│  ┌──────▼──────┐  │                   │                     │
│  │ Decoder     │  │                   │                     │
│  │ (Conv3d)    │  │                   │                     │
│  └──────┬──────┘  │                   │                     │
│         │        │                   │                     │
│  Output:  │        │                   │                     │
│  fake_video│       │                   │                     │
└─────────┬─┴────────┴───────────────────┴─────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────────────┐
│                    VideoGAN (Orchestrator)                    │
│                                                             │
│  train_step()  →  One G+D update cycle                      │
│  train_epoch() →  Full epoch over dataset                   │
│  generate()    →  Generate fake videos                      │
│  classify()    →  Classify real vs fake                     │
│  save/load_checkpoint() →  Training state I/O               │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- PyTorch 1.10+
- OpenCV (opencv-python)
- NumPy

### Setup

```bash
cd workspace
python install_all.py
```

Or install manually:

```bash
pip install torch opencv-python numpy
```

## Usage

### Training Loop

```python
from video_gan.video_gan import VideoGAN
from video_gan.video_processor import VideoProcessor

# Initialize the VideoGAN
gan = VideoGAN(
    lr_g=2e-4,
    lr_d=2e-4,
    device="cuda"  # or "cpu"
)

# Create a video processor
processor = VideoProcessor()

# Generate random video data for training
real_videos = processor.create_random_video(batch_size=8)

# Train for one epoch
losses = gan.train_epoch(real_videos, batch_size=8)
print(f"Generator loss: {losses['g_loss']:.4f}")
print(f"Discriminator loss: {losses['d_loss']:.4f}")

# Generate fake videos
fake_videos = gan.generate(real_videos)

# Classify videos
scores, features = gan.classify(real_videos)
```

### Saving and Loading

```python
# Save checkpoint
gan.save_checkpoint("checkpoints/video_gan.pt")

# Load checkpoint
gan.load_checkpoint("checkpoints/video_gan.pt")
```

### Video I/O

```python
# Load frames from a video file
frames = processor.load_video_frames("input.mp4")

# Save frames to a video file
processor.save_video_frames(frames, "output.mp4", fps=10.0)

# Normalize/denormalize frames
normalized = processor.normalize(frames)
denormalized = processor.denormalize(normalized)
```

## CLI Usage

### Training

```bash
# Basic training
python train.py

# With custom parameters
python train.py --epochs 50 --batch-size 8 --device cuda

# With config file
python train.py --config config.yaml

# Custom output directory
python train.py --output-dir /path/to/outputs
```

### API Server

```bash
# Start the API server
python -m video_gan.api

# The server runs on http://localhost:8000
```

## API Documentation

The API server provides the following endpoints:

### Training

```bash
curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{"epochs": 10, "batch_size": 4}'
```

**Response:**
```json
{
  "status": "completed",
  "epochs": 10,
  "final_d_loss": 0.693,
  "final_g_loss": 0.693
}
```

### Generate Videos

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"num_samples": 5, "batch_size": 1}'
```

**Response:**
```json
{
  "status": "completed",
  "num_generated": 5,
  "video_paths": [
    "/tmp/tmp123/generated_0_0.mp4",
    "/tmp/tmp123/generated_1_0.mp4"
  ]
}
```

### Classify Video

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"video_path": "/path/to/video.mp4"}'
```

**Response:**
```json
{
  "is_real": false,
  "real_score": 0.23,
  "fake_score": 0.77
}
```

### Model Info

```bash
curl http://localhost:8000/model/info
```

**Response:**
```json
{
  "generator_latent_dim": 128,
  "generator_num_frames": 16,
  "generator_frame_size": 64,
  "discriminator_input_channels": 3,
  "discriminator_num_frames": 16,
  "discriminator_frame_size": 64
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

## Configuration

### Generator Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `latent_dim` | 128 | Dimension of latent noise vector |
| `input_channels` | 3 | Number of input video channels |
| `output_channels` | 3 | Number of output video channels |
| `num_frames` | 16 | Number of frames in output video |
| `frame_size` | (64, 64) | Height and width of each frame |

### Discriminator Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `input_channels` | 3 | Number of input video channels |
| `num_frames` | 16 | Number of frames in input video |
| `frame_size` | (64, 64) | Height and width of each frame |

### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `lr_g` | 2e-4 | Learning rate for generator |
| `lr_d` | 2e-4 | Learning rate for discriminator |
| `beta1` | 0.5 | Beta1 for Adam optimizer |
| `beta2` | 0.999 | Beta2 for Adam optimizer |

## Docker Support

### Build and Run

```bash
# Build the Docker image
docker build -t video-gan .

# Run the API server
docker run -p 8000:8000 video-gan python -m video_gan.api

# Run training
docker run -v $(pwd)/outputs:/app/outputs video-gan python train.py --epochs 50
```

### Docker Compose

```bash
# Start all services (API, trainer, inference)
docker-compose up -d

# Stop all services
docker-compose down
```

## CI/CD Pipeline

The project includes a GitHub Actions workflow for:

- **Linting**: Black, Flake8, MyPy
- **Testing**: Pytest with coverage
- **Docker Build**: Multi-stage Docker builds
- **Deployment**: Automated deployment to production

### Running Locally

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linters
black --check .
flake8 .
mypy video_gan/

# Run tests
pytest tests/ -v --cov=video_gan
```

## Project Structure

```
workspace/
├── README.md
├── install_all.py
├── train.py                  # CLI training script
├── config.yaml               # Configuration file
├── Dockerfile                # Docker build file
├── docker-compose.yml        # Docker Compose configuration
├── .github/
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline
├── video_gan/
│   ├── __init__.py
│   ├── generator.py          # Generator network
│   ├── discriminator.py      # Discriminator network
│   ├── video_gan.py          # Training orchestrator
│   ├── video_processor.py    # Video I/O utilities
│   └── api.py                # FastAPI server
├── tests/
│   ├── test_generator.py
│   ├── test_discriminator.py
│   ├── test_video_gan.py
│   └── test_video_processor.py
└── outputs/                  # Training outputs and checkpoints
```

## Error Handling

All modules include comprehensive error handling:

- **Type checking**: All inputs are validated for correct types
- **Shape validation**: Tensor shapes are checked against expected dimensions
- **Device consistency**: Device mismatches between tensors and models are caught
- **Path validation**: Video file paths are validated for existence and accessibility
- **Batch size validation**: Zero or negative batch sizes are rejected

Example:

```python
try:
    gan.train_step(real_video)
except TypeError as e:
    print(f"Type error: {e}")
except ValueError as e:
    print(f"Value error: {e}")
except RuntimeError as e:
    print(f"Device error: {e}")
```

## License

MIT License
