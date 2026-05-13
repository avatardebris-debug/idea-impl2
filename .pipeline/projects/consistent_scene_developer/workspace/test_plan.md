# Test Plan: Pipeline Validator & Executor Harness

## Overview
This test plan verifies the complete pipeline system: the validator (which checks code quality), the executor harness (which runs agents), and the tools they use.

## Test Categories

### A. Validator Tests
1. **Syntax validation** — Python files with syntax errors are rejected
2. **Import validation** — Missing imports are caught
3. **Type hint validation** — Incorrect type hints are flagged
4. **Docstring validation** — Missing docstrings on public functions are flagged
5. **Complexity validation** — Overly complex functions are flagged
6. **Security validation** — Dangerous patterns (eval, exec, etc.) are flagged
7. **Style validation** — PEP 8 violations are caught
8. **Config validation** — Invalid validator config is rejected
9. **Multi-file validation** — Multiple files are validated together
10. **Passing code** — Clean code passes all checks

### B. Executor Harness Tests
1. **Agent initialization** — Agent starts with correct tools and config
2. **Tool execution** — Each tool works correctly
3. **Message passing** — Messages flow between agents correctly
4. **State management** — Agent state persists across turns
5. **Error handling** — Agent errors are caught and reported
6. **Timeout handling** — Long-running tasks are terminated
7. **Resource limits** — Memory/CPU limits are enforced
8. **Multi-agent coordination** — Multiple agents work together
9. **Recovery** — Failed agents can be restarted
10. **Cleanup** — Resources are cleaned up after execution

### C. Integration Tests
1. **Full pipeline run** — Validator + executor work together
2. **End-to-end task** — Complete coding task from start to finish
3. **Error recovery** — Pipeline handles errors gracefully
4. **Performance** — Pipeline runs within time limits
5. **Scalability** — Pipeline handles large codebases
6. **Config variations** — Different configs produce different results
7. **Edge cases** — Empty files, special characters, etc.
8. **Cross-platform** — Works on Linux, macOS, Windows

### D. Tool Tests
1. **File operations** — Read, write, delete, list files
2. **Shell execution** — Commands run correctly
3. **Search** — File search works
4. **Patch** — File patching works
5. **Git operations** — Git commands work
6. **Package management** — pip install works
7. **Web access** — curl/wget work for web access
8. **Self-extension** — Agents can add new tools

## Test Execution Order
1. Unit tests (A, B, D)
2. Integration tests (C)
3. End-to-end tests (C)

## Success Criteria
- All tests pass
- No warnings that indicate broken functionality
- Pipeline completes within time limits
- Resources are cleaned up properly
