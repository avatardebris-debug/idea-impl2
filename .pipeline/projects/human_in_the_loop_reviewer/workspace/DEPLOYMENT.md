# Deployment Guide — Human-in-the-Loop Reviewer

## Installation

### From PyPI (recommended)

```bash
pip install human_in_the_loop_reviewer
```

### From source

```bash
cd human_in_the_loop_reviewer
pip install -e .
```

### With development dependencies

```bash
pip install -e ".[dev]"
```

## CLI Usage

The package installs a `human-in-the-loop-reviewer` command-line tool:

```bash
# Create a checkpoint
human-in-the-loop-reviewer create "Review this draft document"

# Check status
human-in-the-loop-reviewer status <checkpoint_id>

# Approve a checkpoint
human-in-the-loop-reviewer approve <checkpoint_id>

# Reject a checkpoint
human-in-the-loop-reviewer reject <checkpoint_id> --reason "Needs revision"

# List all checkpoints
human-in-the-loop-reviewer list

# Wait for a checkpoint to be resolved (blocks)
human-in-the-loop-reviewer wait <checkpoint_id> --timeout 60
```

### State file

By default, checkpoints are persisted to `~/.human_in_the_loop_reviewer.json`.
Override the path with the `HUMAN_IN_THE_LOOP_STATE` environment variable:

```bash
HUMAN_IN_THE_LOOP_STATE=/tmp/review_state.json human-in-the-loop-reviewer create "Test"
```

## Production Considerations

### State persistence

The default JSON file store is suitable for development and single-process use.
For production deployments with multiple processes or high availability:

- Use a shared filesystem or network-mounted directory for the state file.
- Ensure file permissions restrict access to authorized users only.
- Consider implementing a custom `CheckpointStore` backed by a database (e.g., SQLite, PostgreSQL) for concurrent multi-process scenarios.

### Thread safety

The built-in `CheckpointStore` is thread-safe within a single process.
For cross-process coordination, use the CLI with a shared state file or implement a distributed store.

### Timeout handling

The `wait` command and `wait_for_response()` API both support configurable timeouts.
In production, always set explicit timeouts to avoid indefinite blocking:

```python
result = reviewer.wait_for_response(cp_id, timeout=300.0)  # 5 minutes
```

### Logging

The library does not emit log messages by default. Integrate with your application's logging framework:

```python
import logging
logging.basicConfig(level=logging.INFO)
reviewer = HumanInLoopReviewer()
```

## Integration with Agent Pipelines

### Pattern 1: Blocking wait

```python
from human_in_the_loop_reviewer import HumanInLoopReviewer

reviewer = HumanInLoopReviewer()
cp_id = reviewer.create_checkpoint("Review the generated report.")

# Block until human responds
result = reviewer.wait_for_response(cp_id, timeout=300.0)
if result.status == "approved":
    proceed_with_report(result)
else:
    handle_rejection(result)
```

### Pattern 2: Async integration

```python
import asyncio
from human_in_the_loop_reviewer import HumanInLoopReviewer

async def run_with_approval():
    reviewer = HumanInLoopReviewer()
    cp_id = reviewer.create_checkpoint("Review draft content.")

    loop = asyncio.get_event_loop()

    def _wait():
        return reviewer.wait_for_response(cp_id, timeout=60.0)

    result = await loop.run_in_executor(None, _wait)
    return result
```

### Pattern 3: Non-blocking with polling

```python
from human_in_the_loop_reviewer import HumanInLoopReviewer

reviewer = HumanInLoopReviewer()
cp_id = reviewer.create_checkpoint("Review this item.")

# Poll for status without blocking
import time
while True:
    cp = reviewer.get_checkpoint(cp_id)
    if cp.status in ("approved", "rejected"):
        break
    time.sleep(1)

print(f"Result: {cp.status}")
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Run CLI integration tests specifically:

```bash
pytest tests/test_cli.py
```

Run with coverage:

```bash
pytest tests/ --cov=human_in_the_loop_reviewer --cov-report=term-missing
```

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Run full test suite: `pytest tests/`
- [ ] Run CLI walkthrough: `python examples/cli_walkthrough.py`
- [ ] Run async example: `python examples/async_workflow.py`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Tag release: `git tag v<version>`
- [ ] Push tags: `git push --tags`
- [ ] Build distribution: `python -m build`
- [ ] Publish to PyPI: `twine upload dist/*`

## Troubleshooting

### Checkpoint not found

Ensure the state file is accessible and not corrupted:

```bash
cat ~/.human_in_the_loop_reviewer.json | python -m json.tool
```

### CLI command not found

Ensure the package is installed in the active Python environment:

```bash
pip show human_in_the_loop_reviewer
```

### State file permission errors

Check and fix permissions on the state file directory:

```bash
chmod 700 ~/.human_in_the_loop_reviewer.json
```
