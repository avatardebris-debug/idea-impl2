FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY droppain/ ./droppain/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m -s /bin/bash droppain
USER droppain

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import droppain; print(droppain.__version__)" || exit 1

ENTRYPOINT ["droppain"]
CMD ["--help"]
