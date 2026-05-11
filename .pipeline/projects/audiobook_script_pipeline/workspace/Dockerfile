FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install the package in development mode
RUN pip install --no-cache-dir -e .

# Default command (can be overridden)
ENTRYPOINT ["audiobook-pipeline"]
CMD ["--help"]
