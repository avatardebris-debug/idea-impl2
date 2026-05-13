# Chronovision2 — Self-improving AI agent with hypothesis-driven RL

A modular, provider-agnostic AI agent pipeline that:

- **Swaps LLM providers** with a single string (OpenAI, Claude, Gemini, Ollama, Grok)
- **Manages hypotheses** with reinforcement learning-style weight updates
- **Executes tools** (file I/O, shell commands, environment variables)
- **Maintains persistent memory** (facts, decisions, tasks)
- **Runs interactively** or via CLI

## Quick Start

```bash
# Install dependencies
pip install openai anthropic google-generativeai ollama

# Run with Ollama (local)
python pipeline/runner.py --provider ollama --model qwen3:32b

# Run with OpenAI
python pipeline/runner.py --provider openai --model gpt-4o

# Run with Claude
python pipeline/runner.py --provider claude --model claude-sonnet-4-20250514

# Run with Gemini
python pipeline/runner.py --provider gemini --model gemini-2.5-pro-preview-06-05

# Run with Grok (xAI)
export XAI_API_KEY=xai-...
python pipeline/runner.py --provider grok --model grok-3
```

## Architecture

```
chronovision2/
├── __init__.py
├── agent.py              # Main agent loop
├── llm_interface.py      # Provider-agnostic LLM adapter
├── tools.py              # Tool registry
├── memory.py             # Persistent memory system
├── core/
│   ├── __init__.py
│   └── hypothesis_manager.py  # RL hypothesis management
├── pipeline/
│   └── runner.py         # CLI entry point
└── tests/
    └── test_agent.py     # Unit tests
```

## Provider Setup

### OpenAI
```bash
export OPENAI_API_KEY=sk-...
```

### Claude (Anthropic)
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Gemini (Google)
```bash
export GOOGLE_API_KEY=AIza...
```

### Ollama (local)
```bash
# Install Ollama from https://ollama.ai
ollama pull qwen3:32b
python pipeline/runner.py --provider ollama --model qwen3:32b
```

### Grok (xAI)
```bash
export XAI_API_KEY=xai-...
python pipeline/runner.py --provider grok --model grok-3
```

## Running Tests

```bash
python -m pytest tests/test_agent.py -v
```

## License

MIT
