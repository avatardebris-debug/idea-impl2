#!/bin/bash
# =============================================================================
# cloud_setup.sh — One-shot cloud compute setup for Cognitive Architecture
# =============================================================================
# Run this on a fresh cloud instance (Vast.ai, RunPod, Lambda, etc.)
#
# Requirements:
#   - Ubuntu/Debian with NVIDIA GPU (24GB+ VRAM recommended for Qwen3 30B-A3B)
#   - SSH access
#
# Usage:
#   chmod +x cloud_setup.sh
#   ./cloud_setup.sh
# =============================================================================

set -euo pipefail

echo "==========================================="
echo "  Cognitive Architecture — Cloud Setup"
echo "==========================================="

# --- 1. System dependencies ---
echo "[1/6] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl jq

# --- 2. Install Ollama ---
echo "[2/6] Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "  Ollama already installed: $(ollama --version)"
fi

# --- 3. Start Ollama in the background ---
echo "[3/6] Starting Ollama server..."
# Kill any existing instance
pkill ollama 2>/dev/null || true
sleep 1

# ── VRAM-aware parallelism ────────────────────────────────────────────────────
# Detect VRAM now (may already be set from step 4 preview, but do it early)
_VRAM_MB_FOR_PARALLEL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ' || echo 0)
_VRAM_GB_INT=$(( _VRAM_MB_FOR_PARALLEL / 1024 ))

# Model footprint heuristic (MoE 30-35B at Q4_K_M ~ 18-20 GB)
_MODEL_VRAM_GB=20
case "${MODEL:-qwen3.6:35b-a3b-q4_K_M}" in
  *235b*)  _MODEL_VRAM_GB=120 ;;
  *72b*|*70b*) _MODEL_VRAM_GB=40 ;;
  *32b*)   _MODEL_VRAM_GB=20  ;;
  *30b*|*35b*) _MODEL_VRAM_GB=18 ;;
  *14b*)   _MODEL_VRAM_GB=9   ;;
  *8b*)    _MODEL_VRAM_GB=5   ;;
  *4b*)    _MODEL_VRAM_GB=3   ;;
esac

# KV cache per concurrent slot (GB)
_KV_PER_SLOT=4
case "${MODEL:-qwen3.6:35b-a3b-q4_K_M}" in
  *8b*|*4b*|*1.7b*) _KV_PER_SLOT=2 ;;
  *14b*)             _KV_PER_SLOT=3 ;;
esac

_HEADROOM=$(( _VRAM_GB_INT - _MODEL_VRAM_GB - 2 ))   # -2 OS/Ollama overhead
[[ $_HEADROOM -lt 0 ]] && _HEADROOM=0
_OLLAMA_PARALLEL=$(( _HEADROOM / _KV_PER_SLOT ))
[[ $_OLLAMA_PARALLEL -lt 1 ]] && _OLLAMA_PARALLEL=1
[[ $_OLLAMA_PARALLEL -gt 4 ]] && _OLLAMA_PARALLEL=4

# Runner seeds: 1 more than Ollama slots (extras do CPU work while LLM is busy)
_PARALLEL_SEEDS=$(( _OLLAMA_PARALLEL + 1 ))
_MAX_SEEDS=$(( _OLLAMA_PARALLEL + 2 ))
[[ $_PARALLEL_SEEDS -gt 6 ]] && _PARALLEL_SEEDS=6
[[ $_MAX_SEEDS -gt 8 ]]      && _MAX_SEEDS=8

echo "  VRAM detected:       ${_VRAM_GB_INT} GB"
echo "  Model footprint:     ~${_MODEL_VRAM_GB} GB"
echo "  OLLAMA_NUM_PARALLEL: ${_OLLAMA_PARALLEL}"
echo "  --parallel-seeds:    ${_PARALLEL_SEEDS}  --max-seeds: ${_MAX_SEEDS}"
# ─────────────────────────────────────────────────────────────────────────────

# Start fresh — bind to all interfaces so SSH tunnels work
OLLAMA_HOST=0.0.0.0:11434 \
OLLAMA_NUM_PARALLEL=${_OLLAMA_PARALLEL} \
OLLAMA_MAX_LOADED_MODELS=1 \
nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 3

# Verify it's running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  Ollama running on :11434 (NUM_PARALLEL=${_OLLAMA_PARALLEL})"
else
    echo "  Ollama failed to start. Check /tmp/ollama.log"
    exit 1
fi

# Remove any pre-installed models that aren't what we want.
# Vast.ai instance templates often pre-load qwen3.5 — remove it so it
# can't be accidentally used or loaded by background processes.
echo "  Removing pre-installed models that aren't qwen3.6..."
ollama list | awk 'NR>1 {print $1}' | grep -v "qwen3.6" | while read -r model; do
    echo "    Removing: ${model}"
    ollama rm "${model}" 2>/dev/null || true
done
echo "  ✓ Model cleanup done"

# --- 4. Pull the model ---
echo "[4/6] Pulling Qwen3 model (this takes a few minutes on first run)..."

# Default model: qwen3.6:35b-a3b-q4_K_M (MoE quantised, ~3B active params)
# Fits any GPU with 16GB+ VRAM, fast inference, strong tool-calling.
# Override with MODEL env var if you want something different:
#   MODEL=qwen3.6:35b bash cloud_setup.sh       # full MoE (needs 48GB+)
#   MODEL=qwen3.6:72b-q4_K_M bash cloud_setup.sh # largest (needs 80GB+)

MODEL="${MODEL:-qwen3.6:35b-a3b-q4_K_M}"

if command -v nvidia-smi &> /dev/null; then
    VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 | tr -d ' ')
    echo "  Detected ${VRAM_MB}MB VRAM"
else
    echo "  No GPU detected — will run on CPU (slowly)"
fi

echo "  Selected model: ${MODEL}"
# Export so the runner picks it up without needing --model flag
export PIPELINE_MODEL="${MODEL}"
echo "  PIPELINE_MODEL=${PIPELINE_MODEL}"
ollama pull "${MODEL}"
echo "  ✓ Model pulled"

# --- 5. Set up the Python environment ---
echo "[5/7] Setting up Python environment..."
AGENT_DIR="${AGENT_DIR:-$(pwd)}"

if [ ! -d "${AGENT_DIR}/.venv" ]; then
    python3 -m venv "${AGENT_DIR}/.venv"
fi
source "${AGENT_DIR}/.venv/bin/activate"

pip install -q --upgrade pip
pip install -q -r "${AGENT_DIR}/requirements.txt"

# --- API key handling ---
# If using Gemini (--provider gemini), set GOOGLE_API_KEY before running.
# You can pass it as an env var when invoking this script:
#   GOOGLE_API_KEY=AIza... ./cloud_setup.sh
# Or export it in your shell session after setup.
if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
    echo "  GOOGLE_API_KEY is set — Gemini provider ready"
    # Persist to .env file so the runner can source it on startup
    echo "export GOOGLE_API_KEY=${GOOGLE_API_KEY}" >> "${AGENT_DIR}/.env"
    echo "  Saved to ${AGENT_DIR}/.env"
else
    echo "  GOOGLE_API_KEY not set — to use Gemini: export GOOGLE_API_KEY=AIza..."
fi

echo "  ✓ Python environment ready"

# --- 6. Pipeline output repo + Hermes ---
echo "[6/7] Bootstrapping pipeline output + Hermes..."
export PIPELINE_CLOUD=1
export PIPELINE_DIR="${AGENT_DIR}/.pipeline"

if [ ! -d "${PIPELINE_DIR}/.git" ]; then
    echo "  Cloning pipeline output → ${PIPELINE_DIR}"
    git clone --depth 1 -b main https://github.com/avatardebris-debug/pipeline.git "${PIPELINE_DIR}" \
        || mkdir -p "${PIPELINE_DIR}/projects" "${PIPELINE_DIR}/state"
else
    echo "  Pipeline output already cloned — git pull"
    git -C "${PIPELINE_DIR}" pull --ff-only origin main || true
fi

echo "  Ensuring Hermes agent (for --hermes / goal attempts)..."
python - <<'PY' || true
from pipeline.output_bootstrap import bootstrap_hermes
bootstrap_hermes()
PY

# --- 7. Write the model config ---
echo "[7/7] Writing runtime config..."
cat > "${AGENT_DIR}/.agent/cloud_config.json" << EOF
{
    "provider": "ollama",
    "model": "${MODEL}",
    "base_url": "http://localhost:11434",
    "temperature": 0.2,
    "setup_date": "$(date -Iseconds)",
    "gpu": "$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'none')",
    "vram_mb": ${VRAM_MB:-0}
}
EOF

echo ""
echo "=========================================="
echo "  Setup complete!"
echo "=========================================="
echo ""
echo "  Model:              ${MODEL}"
echo "  OLLAMA_NUM_PARALLEL: ${_OLLAMA_PARALLEL}"
echo "  Provider:           ollama"
echo "  Base URL:           http://localhost:11434"
echo "  Output dir:         ${PIPELINE_DIR} (PIPELINE_CLOUD=1)"
echo ""
echo "  Quick smoke test (single idea):"
echo ""
echo "    source .venv/bin/activate"
echo "    export PIPELINE_CLOUD=1"
echo "    python pipeline/runner.py \"Build a Python word counter CLI\""
echo ""
echo "  Recommended run (VRAM-tuned for ${_VRAM_GB_INT}GB):"
echo ""
echo "    export PIPELINE_CLOUD=1"
echo "    python pipeline/runner.py \\"
echo "        --from-list \\"
echo "        --provider ollama \\"
echo "        --model ${MODEL} \\"
echo "        --parallel-seeds ${_PARALLEL_SEEDS} \\"
echo "        --executors 2 \\"
echo "        --auto-tune \\"
echo "        --max-seeds ${_MAX_SEEDS}"
echo ""
echo "  Goals (decomposed --goal entries):"
echo "    python pipeline/runner.py --list-goals"
echo "    python pipeline/runner.py --attempt-goal GOAL_ID --provider ollama --model ${MODEL}"
echo ""
echo "  Second instance (unstarted backlog only, no overlap):"
echo ""
echo "    python pipeline/runner.py \\"
echo "        --from-list \\"
echo "        --fresh-list-only \\"
echo "        --provider ollama \\"
echo "        --model ${MODEL} \\"
echo "        --ideas-file unstarted_projects_backlog.md \\"
echo "        --parallel-seeds ${_PARALLEL_SEEDS} \\"
echo "        --auto-tune \\"
echo "        --max-seeds ${_MAX_SEEDS}"
echo ""
echo "  Monitor VRAM:   watch -n 5 nvidia-smi"
echo "  Ollama logs:    tail -f /tmp/ollama.log"
echo "  Corpus stats:   python -m pipeline.corpus_collector --stats"
echo ""
