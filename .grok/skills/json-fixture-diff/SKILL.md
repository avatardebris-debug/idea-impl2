---
name: json-fixture-diff
description: >
  Compare two JSON fixtures and report a clear diff for field tests or MCP invoke checks.
  Use when the user runs /json-fixture-diff, asks to "diff two json files", "compare fixtures",
  or needs a small oracle for json_diff_tool / mcp_json_diff_tool.
---

# JSON fixture diff

## When to use
- Field-test oracles that need A vs B JSON
- Checking mcp_json_diff_tool / json_diff_tool behavior

## Steps
1. Confirm both paths exist and are readable.
2. Prefer pipeline capability when available:

```powershell
$env:PIPELINE_DIR = "C:\Users\avata\aicompete\thepipeline"
python -c "from pipeline.capability_tools import invoke_capability; print(invoke_capability('json_diff_tool', r'PATH1 PATH2'))"
```

3. Report equal vs keys added/removed/changed; fail only on missing/invalid JSON.

## Done when
- Diff summary printed; invalid JSON called out; no secret sprawl beyond the diff.
