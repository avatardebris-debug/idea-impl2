#!/usr/bin/env bash
# =============================================================================
# run_ship_prove.sh — Controlled ship-prove for local or cloud overnight runs
# =============================================================================
# Clears stale ship-agent bus messages, then runs --ship-prove with safe defaults.
#
# Usage (from factory repo root):
#   chmod +x scripts/run_ship_prove.sh
#   ./scripts/run_ship_prove.sh                          # serial, all eligible
#   ./scripts/run_ship_prove.sh --slug ship_canary      # one project
#   ./scripts/run_ship_prove.sh --provider grok --model grok-4.3
#   ./scripts/run_ship_prove.sh --main-pipeline          # list/polish overnight instead
#
# Env (optional):
#   PIPELINE_DIR          output root (projects/, state/, …)
#   PIPELINE_CLOUD=1      cloud layout (.pipeline under factory)
#   XAI_API_KEY           required for --provider grok
#   MAX_FIELD_TEST_LOOPS  default 2 in this script (override if set)
#   SHIP_SKIP_THERMO=1    same as --skip-thermo
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Load .env if present (KEY=VALUE lines; no export keyword required)
if [[ -f "$ROOT/.env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
      export "$line"
    fi
  done <"$ROOT/.env"
fi

PROVIDER="${PIPELINE_PROVIDER:-ollama}"
MODEL="${PIPELINE_MODEL:-qwen3.6:35b-a3b-q4_K_M}"
SLUG=""
SERIAL=1
SKIP_THERMO=1
TIME_LIMIT=0
BASE_BUDGET=90
PHASE_BUDGET=45
CLEAR_BUS=1
MODE="ship"   # ship | main
LOG_DIR=""
EXTRA_ARGS=()

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \?//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --slug) SLUG="${2:-}"; shift 2 ;;
    --provider) PROVIDER="${2:-}"; shift 2 ;;
    --model) MODEL="${2:-}"; shift 2 ;;
    --serial) SERIAL=1; shift ;;
    --batch) SERIAL=0; shift ;;
    --skip-thermo) SKIP_THERMO=1; shift ;;
    --with-thermo) SKIP_THERMO=0; shift ;;
    --time-limit) TIME_LIMIT="${2:-0}"; shift 2 ;;
    --base-budget) BASE_BUDGET="${2:-90}"; shift 2 ;;
    --phase-budget) PHASE_BUDGET="${2:-45}"; shift 2 ;;
    --no-clear-bus) CLEAR_BUS=0; shift ;;
    --main-pipeline) MODE="main"; shift ;;
    --log-dir) LOG_DIR="${2:-}"; shift 2 ;;
    -h|--help) usage 0 ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

export PYTHONUTF8="${PYTHONUTF8:-1}"
export MAX_FIELD_TEST_LOOPS="${MAX_FIELD_TEST_LOOPS:-2}"
export PIPELINE_PROVIDER="$PROVIDER"
export PIPELINE_MODEL="$MODEL"

if [[ -n "${PIPELINE_CLOUD:-}" ]]; then
  export PIPELINE_CLOUD
fi

TS="$(date +%Y%m%d_%H%M%S)"
if [[ -z "$LOG_DIR" ]]; then
  if [[ -n "${PIPELINE_DIR:-}" && -d "${PIPELINE_DIR}/logs" ]]; then
    LOG_DIR="${PIPELINE_DIR}/logs"
  elif [[ -d "$ROOT/.pipeline/logs" ]]; then
    LOG_DIR="$ROOT/.pipeline/logs"
  else
    LOG_DIR="$ROOT/logs"
  fi
fi
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/ship_prove_${MODE}_${TS}.log"

echo "============================================"
echo "  run_ship_prove  mode=$MODE"
echo "  root=$ROOT"
echo "  provider=$PROVIDER  model=$MODEL"
echo "  log=$LOG_FILE"
echo "============================================"

clear_ship_bus() {
  python - <<'PY'
from pipeline.message_bus import MessageBus
from pipeline.pipeline_config import SHIP_AGENT_ROLES
from pipeline.paths import queues_dir, message_bus_db
import sqlite3

bus = MessageBus(queues_dir())
total = 0
for role in SHIP_AGENT_ROLES:
    n = bus.clear_queue(role)
    total += n
    print(f"  cleared {role}: {n}")

conn = sqlite3.connect(str(message_bus_db()))
cur = conn.execute(
    "UPDATE messages SET status='failed' WHERE status='processing' AND to_agent IN ({})".format(
        ",".join("?" * len(SHIP_AGENT_ROLES))
    ),
    list(SHIP_AGENT_ROLES),
)
print(f"  released processing: {cur.rowcount}")
conn.commit()
print(f"  ship bus clear done (pending removed≈{total})")
for role in SHIP_AGENT_ROLES:
    print(f"  depth {role}={bus.queue_depth(role)}")
PY
}

if [[ "$CLEAR_BUS" -eq 1 && "$MODE" == "ship" ]]; then
  echo "[1/2] Clearing ship-agent message bus..."
  clear_ship_bus
else
  echo "[1/2] Skipping bus clear"
fi

echo "[2/2] Starting runner..."

set +e
if [[ "$MODE" == "main" ]]; then
  # Overnight main pipeline (polish-first if env set by operator)
  export PIPELINE_POLISH_FIRST="${PIPELINE_POLISH_FIRST:-1}"
  nohup python pipeline/runner.py --from-list \
    --provider "$PROVIDER" \
    --model "$MODEL" \
    --time-limit "$TIME_LIMIT" \
    --base-budget "$BASE_BUDGET" \
    --phase-budget "$PHASE_BUDGET" \
    "${EXTRA_ARGS[@]}" \
    >"$LOG_FILE" 2>&1 &
  echo $! >"$LOG_DIR/ship_prove_${MODE}_${TS}.pid"
  echo "  PID $(cat "$LOG_DIR/ship_prove_${MODE}_${TS}.pid")"
  echo "  tail -f $LOG_FILE"
  exit 0
fi

CMD=(
  python pipeline/runner.py
  --ship-prove
  --provider "$PROVIDER"
  --model "$MODEL"
  --time-limit "$TIME_LIMIT"
  --base-budget "$BASE_BUDGET"
  --phase-budget "$PHASE_BUDGET"
)

if [[ -n "$SLUG" ]]; then
  CMD+=(--ship-slug "$SLUG")
fi
if [[ "$SERIAL" -eq 1 && -z "$SLUG" ]]; then
  CMD+=(--ship-serial)
fi
if [[ "$SKIP_THERMO" -eq 1 ]]; then
  CMD+=(--ship-skip-thermo)
fi
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_ARGS[@]}")
fi

echo "  cmd: ${CMD[*]}"

# Foreground by default so cloud nohup wrappers can wrap this script;
# set SHIP_PROVE_BACKGROUND=1 to detach here.
if [[ "${SHIP_PROVE_BACKGROUND:-0}" == "1" ]]; then
  nohup "${CMD[@]}" >"$LOG_FILE" 2>&1 &
  echo $! >"$LOG_DIR/ship_prove_${MODE}_${TS}.pid"
  echo "  PID $(cat "$LOG_DIR/ship_prove_${MODE}_${TS}.pid")"
  echo "  tail -f $LOG_FILE"
  exit 0
fi

"${CMD[@]}" 2>&1 | tee "$LOG_FILE"
rc=${PIPESTATUS[0]}
echo "exit=$rc  log=$LOG_FILE"
exit "$rc"
