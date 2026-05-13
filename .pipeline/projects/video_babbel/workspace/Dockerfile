# syntax=docker/dockerfile:1
# ----
# Multi-stage Dockerfile for VideoBabbel
#
# Stage 1 (builder): install Python dependencies into a virtualenv
# Stage 2 (runtime): minimal image with ffmpeg + the built wheel
# ----

# ---- Builder stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build setuptools wheel

# Copy project files
COPY pyproject.toml README.md ./
COPY video_babbel/ ./video_babbel/

# Build the wheel
RUN python -m build --wheel --outdir /dist

# ---- Runtime stage ----
FROM python:3.12-slim

# Install ffmpeg (required for video ingestion)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r video && useradd -r -g video -m video

WORKDIR /app

# Copy the wheel from builder
COPY --from=builder /dist/*.whl /tmp/

# Install the package (including dev extras for CLI)
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm /tmp/*.whl

# Switch to non-root user
USER video

# Default command: show help
ENTRYPOINT ["video-babbel"]
CMD ["--help"]
