# Idea Development Pipeline (Factory)

A multi-agent system that autonomously implements ideas. Give it an idea → it plans, codes, tests, reviews, and iterates — designed to run unattended for hours.

**Factory vs output:** This repo (`idea impl`) holds code, agents, and prompts. Runtime state (projects, queues, finetune corpus) lives in a separate **output** directory resolved by `pipeline/pipeline_config.py`:

| Environment | Output directory |
|---|---|
| Local dev (default) | `../thepipeline` if it has `projects/` |
| Custom | Set `PIPELINE_DIR` (e.g. `C:\Users\avata\aicompete\.pipeline`) |
| Cloud | `idea impl/.pipeline` (clone of [avatardebris-debug/pipeline](https://github.com/avatardebris-debug/pipeline)) when `PIPELINE_CLOUD=1` |

On startup, `runner.py` calls `bootstrap_output_repo()` and prints the resolved output path.

## Quick Start

```bash
# One idea, run until done
python pipeline/runner.py "Build a CLI tool that converts markdown to HTML"

# Run from your idea backlog (master_ideas.md in output dir or repo root)
python pipeline/runner.py --from-list

# Run overnight with a time limit
python pipeline/runner.py --from-list --provider ollama --model qwen3.6:35b-a3b-q4_K_M --time-limit 480

# Resume a stopped pipeline
python pipeline/runner.py --resume

# Decomposed goals (--goal entries in master_ideas.md)
python pipeline/runner.py --list-goals
python pipeline/runner.py --attempt-goal my_goal_id --provider ollama --model qwen3.6:35b-a3b-q4_K_M
```

## How It Works

7 specialized agents run as subprocesses, communicating via file-based message queues:

```
Idea → Idea Planner → Phase Planner → Executor → Validator → Reviewer → Manager
                                         ↑                                  │
                                         └──── fix bugs ───────────────────┘
                                                                            │
                                                              Ideator ◄─────┘
                                                         (brainstorms next ideas)
```

| Agent | Role |
|---|---|
| **Idea Planner** | Turns raw idea into multi-phase master plan |
| **Phase Planner** | Decomposes each phase into 3-8 coding tasks |
| **Executor** | Writes the actual code |
| **Validator** | Runs tests + linting, gates quality |
| **Reviewer** | Line-by-line code review |
| **Manager** | Routes everything, manages queues, never interrupts (except emergencies) |
| **Ideator** | Always-on brainstorming engine; uses `mission.yaml` for construct/deconstruct passes |

## File Structure

```
idea impl/                     # Factory (this repo)
├── pipeline/
│   ├── runner.py              # Main entry point — starts everything
│   ├── pipeline_config.py     # Resolves PIPELINE_DIR (output)
│   ├── output_bootstrap.py    # Cloud: clone/pull output repo + Hermes
│   ├── goal_decomposer.py     # --goal lines → branches + goals/*.json
│   ├── goal_attempt.py        # --attempt-goal CLI
│   ├── mission.py             # Loads mission.yaml
│   ├── message_bus.py         # JSONL queue system
│   ├── agent_process.py       # Base class for all agents
│   ├── agents/                # 7 agent implementations
│   └── prompts/               # System prompts (markdown, easy to edit)
│
├── agent.py                   # Core ReAct loop (used by all agents)
├── llm_interface.py           # Model-agnostic LLM adapter
├── mission.yaml               # Mission, hard/soft values, ideator passes
├── master_ideas.md            # Idea backlog (also synced in output repo)
├── cloud_setup.sh             # One-shot cloud GPU setup
│
└── _archive/                  # Original self-improvement system (preserved)

thepipeline/ or .pipeline/     # Output (separate repo or cloud clone)
├── projects/                  # One folder per built project
├── queues/                    # Agent message queues
├── state/                     # Registry, activity, completions
├── finetune_corpus/           # Training data shards
└── goals/                     # Decomposed goal trees (JSON)
```

## Configuration

Edit `constitution.yaml` to tune quality standards, agent weights, ideator settings, and pipeline limits.

Edit `mission.yaml` for product mission, hard/soft values, and ideator construct/deconstruct prompt blocks.

## Environment Variables

| Variable | Purpose |
|---|---|
| `PIPELINE_DIR` | Override output directory path |
| `PIPELINE_CLOUD=1` | Use `.pipeline/` inside factory repo (cloud) |
| `PIPELINE_MODEL` | Default model when `--model` omitted |
| `PIPELINE_REPO_URL` | Output repo to clone (default: avatardebris-debug/pipeline) |
| Ollama | *(none — runs locally)* |
| OpenAI | `OPENAI_API_KEY` |
| Claude | `ANTHROPIC_API_KEY` |
| Gemini | `GOOGLE_API_KEY` |

**Windows**: Set `PYTHONUTF8=1` for consistent encoding.

## Cloud Setup

```bash
git clone https://github.com/avatardebris-debug/idea.git "idea impl"
cd "idea impl"
pip install pyyaml ruff pytest
bash cloud_setup.sh   # Ollama, qwen3.6, .pipeline clone, Hermes, venv

source .venv/bin/activate
export PIPELINE_CLOUD=1
python pipeline/runner.py --from-list --provider ollama \
    --model qwen3.6:35b-a3b-q4_K_M --parallel-seeds 3 --executors 2 \
    --auto-tune --max-seeds 4
```

See `COMMANDS.md` for the full command reference.
