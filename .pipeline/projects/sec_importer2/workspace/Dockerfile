FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY sec_importer/ ./sec_importer/

# Install dependencies
RUN pip install --no-cache-dir .[scheduler]

# Create non-root user
RUN useradd -m -s /bin/bash appuser
USER appuser

# Default command
CMD ["sec-importer", "scheduler", "start"]
