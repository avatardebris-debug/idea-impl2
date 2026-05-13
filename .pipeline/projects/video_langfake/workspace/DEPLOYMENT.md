# Deployment Guide for video_langfake

## Prerequisites

- Python 3.11+
- FFmpeg (system dependency for audio/video processing)
- Docker (optional, for containerized deployment)

## Quick Start (Local)

```bash
# 1. Clone and setup
cd workspace
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Run CLI
video_langfake translate input.mp4 es output.mp4
video_langfake detect-language input.mp4
video_langfake info input.mp4
video_langfake languages

# 3. Run API server
video_langfake api
# or
python -m video_langfake.api
```

## Docker Deployment

```bash
# Build the image
docker build -t video_langfake .

# Run the API server
docker run -p 5000:5000 video_langfake

# Run CLI commands in a container
docker run --rm -v $(pwd)/videos:/app/videos video_langfake translate /app/videos/input.mp4 es /app/videos/output.mp4

# Using docker-compose
docker-compose up -d          # Start API server
docker-compose run --rm cli translate input.mp4 es output.mp4  # CLI command
```

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 video_langfake.api:create_app()
```

### Using systemd (Linux)

Create `/etc/systemd/system/video_langfake.service`:

```ini
[Unit]
Description=Video Language Fake API Server
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/video_langfake
ExecStart=/opt/video_langfake/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 video_langfake.api:create_app()
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable video_langfake
sudo systemctl start video_langfake
```

### Using Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 500M;  # For large video uploads
    }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host to bind the API server |
| `PORT` | `5000` | Port to bind the API server |
| `DEBUG` | `false` | Enable debug mode |
| `WHISPER_MODEL` | `base` | Whisper model to use (tiny, base, small, medium, large) |
| `MAX_VIDEO_SIZE_MB` | `500` | Maximum video file size in MB |

## Scaling

For production deployments:

1. **Horizontal scaling**: Run multiple API instances behind a load balancer
2. **Queue-based processing**: Use Redis/RabbitMQ for async job processing
3. **Storage**: Use S3-compatible storage for video files
4. **Monitoring**: Add Prometheus metrics and Grafana dashboards

## API Usage Examples

```bash
# Translate a video
curl -X POST -F "video=@input.mp4" -F "target_language=es" http://localhost:5000/translate -o output.mp4

# Check job status
curl http://localhost:5000/jobs/job_20240101120000_1234

# List all jobs
curl http://localhost:5000/jobs

# Health check
curl http://localhost:5000/health
```

## Troubleshooting

### FFmpeg not found
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Memory issues with large videos
- Use a smaller Whisper model (tiny, base)
- Process videos in chunks
- Increase available memory

### Audio extraction fails
- Ensure the video has an audio track
- Check video codec compatibility
- Try converting the video to MP4 first
