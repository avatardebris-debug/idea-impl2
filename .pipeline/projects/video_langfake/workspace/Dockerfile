# Dockerfile for video_langfake
#
# Multi-stage build:
#   Stage 1 (builder): Install system dependencies
#   Stage 2 (runtime): Minimal Python image with the app
#
# Usage:
#   docker build -t video_langfake .
#   docker run -p 5000:5000 video_langfake
#   docker run -v $(pwd)/videos:/app/videos video_langfake translate /app/videos/input.mp4 es /app/videos/output.mp4

# ---- Builder stage ----
FROM python:3.11-slim AS builder

# Install system dependencies for moviepy (FFmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.11-slim

# Install FFmpeg runtime dependency
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Create app user (non-root)
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy application code
COPY video_langfake/ ./video_langfake/

# Create directories for input/output
RUN mkdir -p /app/videos /app/output && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose API port
EXPOSE 5000

# Default command: start the API server
CMD ["python", "-m", "video_langfake.api"]
