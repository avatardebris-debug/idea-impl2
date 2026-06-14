"""Tests for dropbox.md parsing."""

from pipeline.dropbox import parse_user_messages


def test_parse_user_messages_ignores_fenced_template_example() -> None:
    text = """# Pipeline Dropbox

Example:

```
### USER msg-20260520-001
target: project_slug_optional
Your message: steer, revise, add requirements.
```

### USER msg-20260614-001
Real user message here.
"""
    messages = parse_user_messages(text)
    assert len(messages) == 1
    assert messages[0]["id"] == "msg-20260614-001"
    assert messages[0]["body"] == "Real user message here."
