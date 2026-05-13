# video_langfake

> Translate videos to any language with AI-powered lip-sync

Video Language Fake is a Python library and CLI tool that translates videos from one language to another, generating synthetic speech and lip-sync parameters to make the translation look natural.

## Features

- **Multi-language support**: Translate to/from 12+ languages
- **Lip-sync generation**: AI-generated lip movements aligned to target audio
- **CLI interface**: Command-line tool for batch processing
- **REST API**: Flask-based API for integration with other systems
- **Docker support**: Containerized deployment ready
- **Mock mode**: Works without external dependencies for testing

## Quick Start

### Installation

```bash
pip install -e .
```

### CLI Usage

```bash
# Translate a video
video_langfake translate input.mp4 es output.mp4

# Detect language
video_langfake detect-language input.mp4

# View video info
video_langfake info input.mp4

# List supported languages
video_langfake languages

# Start the API server
video_langfake api
```

### API Usage

```bash
# Start the server
video_langfake api

# Translate via API
curl -X POST -F "video=@input.mp4" -F "target_language=es" http://localhost:5000/translate -o output.mp4
```

## Project Structure

```
workspace/
├── video_langfake/
│   ├── __init__.py      # Package init, version
│   ├── cli.py           # CLI entry point with subcommands
│   ├── api.py           # Flask REST API
│   ├── pipeline.py      # Main VideoLangFake pipeline class
│   ├── audio.py         # Audio extraction & transcription
│   ├── translate.py     # Text translation module
│   ├── synthesis.py     # Speech synthesis & lip-sync
│   ├── exceptions.py    # Custom exceptions
│   └── config.py        # Configuration management
├── tests/
│   ├── test_pipeline.py
│   ├── test_audio.py
│   ├── test_translate.py
│   ├── test_synthesis.py
│   ├── test_api.py
│   └── test_cli.py
├── requirements.txt
├── setup.py
├── Dockerfile
├── docker-compose.yml
├── DEPLOYMENT.md
└── README.md
```

## Supported Languages

| Code | Language   | Code | Language   |
|------|------------|------|------------|
| en   | English    | ja   | Japanese   |
| es   | Spanish    | ko   | Korean     |
| fr   | French     | zh   | Chinese    |
| de   | German     | ru   | Russian    |
| it   | Italian    | ar   | Arabic     |
| pt   | Portuguese | hi   | Hindi      |

## API Reference

### Endpoints

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "video_langfake",
  "version": "0.1.0",
  "timestamp": "2024-01-01T00:00:00"
}
```

#### `GET /languages`
List supported languages.

**Response:**
```json
{
  "supported_languages": [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
    ...
  ],
  "count": 12
}
```

#### `POST /translate`
Translate a video to a target language.

**Form Data:**
- `video` (required): Video file
- `target_language` (required): Target language code
- `source_language` (optional): Source language code
- `output_filename` (optional): Output filename

**Response:** Video file (MP4)

#### `GET /jobs`
List all active jobs.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_20240101120000_1234",
      "status": "completed",
      "target_language": "es",
      "started_at": "2024-01-01T12:00:00"
    }
  ],
  "count": 1
}
```

#### `GET /jobs/<job_id>`
Get job status.

**Response:**
```json
{
  "job_id": "job_20240101120000_1234",
  "status": "completed",
  "target_language": "es",
  "started_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:05:00",
  "output_path": "/app/output/job_20240101120000_1234.mp4"
}
```

## Configuration

Create a `config.yaml` file:

```yaml
whisper:
  model: "base"
  device: "auto"

translation:
  provider: "mock"  # mock, google, deep_lizard
  api_key: ""

synthesis:
  voice: "default"
  speed: 1.0

processing:
  max_video_size_mb: 500
  temp_dir: "/tmp/video_langfake"
  cleanup: true
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=video_langfake --cov-report=html

# Run specific test file
pytest tests/test_pipeline.py
```

## Docker

### Build

```bash
docker build -t video_langfake .
```

### Run API

```bash
docker run -p 5000:5000 video_langfake
```

### Run CLI

```bash
docker run --rm -v $(pwd)/videos:/app/videos video_langfake translate /app/videos/input.mp4 es /app/videos/output.mp4
```

### Docker Compose

```bash
docker-compose up -d          # Start API
docker-compose run --rm cli translate input.mp4 es output.mp4  # CLI command
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Development

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd video_langfake

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
pytest
```

### Adding a New Language

1. Add language code to `SUPPORTED_LANGUAGES` in `config.py`
2. Add language name to `LANG_NAMES` in `config.py`
3. Test with mock data
4. Update documentation

## License

MIT License

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [MoviePy](https://github.com/Zulko/moviepy) for video processing
- [Flask](https://flask.palletsprojects.com/) for the REST API

## Disclaimer

This is a proof-of-concept implementation. The lip-sync generation uses mock data and does not produce realistic results. For production use, integrate with real lip-sync APIs or models.
