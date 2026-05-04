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

# Start fresh — bind to all interfaces so SSH tunnels work
OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 3

# Verify it's running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  ✓ Ollama running on :11434"
else
    echo "  ✗ Ollama failed to start. Check /tmp/ollama.log"
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
echo "[5/6] Setting up Python environment..."
AGENT_DIR="${AGENT_DIR:-$(pwd)}"

if [ ! -d "${AGENT_DIR}/.venv" ]; then
    python3 -m venv "${AGENT_DIR}/.venv"
fi
source "${AGENT_DIR}/.venv/bin/activate"

pip install -q --upgrade pip
# No external dependencies needed — the pipeline uses only Python stdlib
# Optionally install openai/anthropic if you want those providers:
# pip install -q openai anthropic

echo "  ✓ Python environment ready"

# --- 6. Write the model config ---
echo "[6/6] Writing runtime config..."
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
echo "==========================================="
echo "  ✓ Setup complete!"
echo "==========================================="
echo ""
echo "  Model:    ${MODEL}"
echo "  Provider: ollama"
echo "  Base URL: http://localhost:11434"
echo ""
echo "  Quick smoke test (single idea):"
echo ""
echo "    source .venv/bin/activate"
echo "    cd /path/to/idea-impl"
echo "    python pipeline/runner.py \"Build a Python word counter CLI\""
echo ""
echo "  Run from idea backlog (overnight):"
echo ""
echo "    python pipeline/runner.py \\"
echo "        --from-list \\"
echo "        --provider ollama \\"
echo "        --model ${MODEL} \\"
echo "        --time-limit 480"
echo ""
echo "  Multi-day run (no time limit):"
echo ""
echo "    nohup python pipeline/runner.py \\"
echo "        --from-list \\"
echo "        --provider ollama \\"
echo "        --model ${MODEL} \\"
echo "        > pipeline_run.log 2>&1 &"
echo "    echo \"Pipeline running. tail -f pipeline_run.log to monitor.\""
echo ""
