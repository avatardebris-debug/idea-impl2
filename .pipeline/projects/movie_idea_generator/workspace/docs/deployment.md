# Deployment Guide

This guide covers building, testing, publishing, and installing the Movie Idea Generator package.

## Prerequisites

- Python 3.9 or later
- `build` and `twine` installed:

```bash
pip install build twine
```

## Building the Package

From the project root directory:

```bash
python -m build
```

This produces two artifacts in the `dist/` directory:

- `movie_idea_generator-0.1.0.tar.gz` — source distribution (sdist)
- `movie_idea_generator-0.1.0-py3-none-any.whl` — wheel distribution

You can also use `make release` as a shortcut.

## Testing Locally

### Run the test suite

```bash
pytest -v
```

### Install the wheel locally

```bash
pip install dist/movie_idea_generator-0.1.0-py3-none-any.whl
```

### Verify the installation

```bash
movie-idea-generator --help
movie-idea-generator --count 2 --format json
python -m movie_idea_generator --genre Horror --seed 42
```

## Publishing to PyPI

### Step 1: Verify the build artifacts

```bash
twine check dist/*
```

### Step 2: Upload to TestPyPI (recommended first)

```bash
twine upload --repository testpypi dist/*
```

Install from TestPyPI to verify:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ movie-idea-generator
```

### Step 3: Upload to PyPI (production)

```bash
twine upload dist/*
```

You will be prompted for your PyPI username and password (or API token).

> **Tip:** Use an API token instead of a password for better security. Generate one at https://pypi.org/manage/account/

## Quick-Start for End Users

### Install from PyPI

```bash
pip install movie-idea-generator
```

### Generate your first movie idea

```bash
movie-idea-generator
```

### Generate multiple ideas in JSON format

```bash
movie-idea-generator --genre Sci-Fi --count 5 --format json
```

### Use as a Python library

```python
from movie_idea_generator import MovieIdeaGenerator

gen = MovieIdeaGenerator(seed=42)
idea = gen.generate(genre="Comedy")
print(idea["title"])
print(idea["logline"])
```

## Troubleshooting

### "movie-idea-generator command not found"

Make sure the package is installed in the active Python environment:

```bash
pip install movie-idea-generator
```

### "ModuleNotFoundError: movie_idea_generator"

You may have installed the package but are running from the source directory. Either:

1. Move out of the source directory, or
2. Use `pip install -e .` for editable install

### Build fails with "setuptools not found"

```bash
pip install setuptools wheel build
```
